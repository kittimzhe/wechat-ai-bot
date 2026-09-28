"""可选实时数据源：天气与 RSS。"""
import html
import logging
import re
import xml.etree.ElementTree as ET

import requests

import config

logger = logging.getLogger("wechat_ai_bot.data")


def build_context(data_config):
    """根据任务的 data 配置拼接实时上下文。"""
    data_config = data_config or {}
    sections = []
    if data_config.get("weather"):
        sections.append(_weather_context())
    if data_config.get("rss"):
        sections.append(_rss_context())
    return "\n\n".join(section for section in sections if section)


def _weather_context():
    if config.WEATHER_LAT is None or config.WEATHER_LON is None:
        logger.warning("天气数据源已启用，但 WEATHER_LAT/WEATHER_LON 未配置")
        return ""
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": config.WEATHER_LAT,
            "longitude": config.WEATHER_LON,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "timezone": config.TIMEZONE,
        },
        timeout=config.DATA_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    current = response.json().get("current", {})
    return (
        "【实时天气数据】\n"
        f"温度：{current.get('temperature_2m', '未知')}°C\n"
        f"湿度：{current.get('relative_humidity_2m', '未知')}%\n"
        f"天气代码：{current.get('weather_code', '未知')}\n"
        f"风速：{current.get('wind_speed_10m', '未知')} km/h"
    )


def _rss_context():
    urls = [url.strip() for url in config.RSS_URLS.split(",") if url.strip()]
    if not urls:
        logger.warning("RSS 数据源已启用，但 RSS_URLS 未配置")
        return ""

    entries = []
    for url in urls[: config.RSS_MAX_FEEDS]:
        try:
            response = requests.get(url, timeout=config.DATA_TIMEOUT_SECONDS)
            response.raise_for_status()
            entries.extend(_parse_feed(response.text, url))
        except Exception as exc:
            logger.warning("RSS 获取失败：%s：%s", url, exc)

    if not entries:
        return ""
    lines = ["【RSS 实时资讯】"]
    for title, summary, source in entries[: config.RSS_MAX_ITEMS]:
        lines.append(
            f"- {title}（来源：{source}）\n  {summary}"
            if summary
            else f"- {title}（来源：{source}）"
        )
    return "\n".join(lines)


def _parse_feed(text, url):
    """兼容常见 RSS 2.0 和 Atom。"""
    root = ET.fromstring(text)
    source = re.sub(r"^https?://", "", url).split("/", 1)[0]
    items = []
    for item in root.findall(".//item")[: config.RSS_MAX_ITEMS]:
        title = _element_text(item, "title")
        summary = _element_text(item, "description")
        if title:
            items.append((title, summary[:300], source))
    atom_ns = "{http://www.w3.org/2005/Atom}"
    for entry in root.findall(f".//{atom_ns}entry")[: config.RSS_MAX_ITEMS]:
        title = _element_text(entry, f"{atom_ns}title")
        summary = _element_text(entry, f"{atom_ns}summary") or _element_text(
            entry, f"{atom_ns}content"
        )
        if title:
            items.append((title, summary[:300], source))
    return items


def _element_text(parent, tag):
    element = parent.find(tag)
    if element is None:
        return ""
    text = "".join(element.itertext())
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", text).strip()
