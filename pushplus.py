"""PushPlus 推送渠道：消息经「pushplus 推送加」服务号进个人微信。

一次性准备（约 3 分钟，不需要企业微信）：
  1. 微信扫码登录 https://www.pushplus.plus
  2. 关注服务号「pushplus 推送加」（消息通过它送达微信）
  3. 完成实名认证（2024-08 起必须，否则接口返回 905）
  4. 官网「一对一推送」页面复制 token 填入 .env 的 PUSHPLUS_TOKEN

接口文档：https://www.pushplus.plus/doc/guide/api.html
官方限制（实名用户）：每天 200 条、每分钟 5 次、相同内容每小时 3 条；
标题最多 100 字、内容最多 2 万字。
"""
import logging

import requests

import config

logger = logging.getLogger("wechat_ai_bot.pushplus")


def send_message(content, msgtype, title=None):
    """发送一条消息；markdown 用 markdown 模板，text 用 txt 模板。"""
    if msgtype not in {"text", "markdown"}:
        raise ValueError(f"不支持的消息类型：{msgtype}")
    if not content or not content.strip():
        raise ValueError("消息内容不能为空")
    template = "markdown" if msgtype == "markdown" else "txt"
    return _push(title or "AI 推送", content, template)


def send_text(content):
    """发送纯文本消息（告警等简短通知用）。"""
    return send_message(content, "text", title="AI 机器人通知")


def _push(title, content, template):
    """调用发送接口；code=200 仅代表请求已受理（接口是异步的）。"""
    response = requests.post(
        config.PUSHPLUS_URL,
        json={
            "token": config.PUSHPLUS_TOKEN,
            "title": title[:100],  # 官方限制标题 100 字
            "content": content,
            "template": template,
        },
        timeout=config.PUSHPLUS_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    code = data.get("code")
    if code != 200:
        # 常见错误码：905 未实名认证；900 当日额度用尽或被限制；999 参数错误
        raise RuntimeError(
            f"PushPlus 发送失败（code={code}）：{data.get('msg') or data.get('data')}"
        )
    logger.debug("PushPlus 已受理，流水号：%s", data.get("data"))
    return data.get("data")
