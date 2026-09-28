"""企业微信应用消息：获取 access_token、发送文本 / Markdown 消息。"""
import threading
import time

import requests

import config

_BASE = "https://qyapi.weixin.qq.com/cgi-bin"
_TOKEN_RETRY_CODES = {40014, 42001}

_token_lock = threading.Lock()
_token_cache = {"token": "", "expires_at": 0.0}


def get_access_token():
    """获取 access_token（有效期 7200 秒，这里做了内存缓存）。"""
    with _token_lock:
        now = time.time()
        if _token_cache["token"] and now < _token_cache["expires_at"]:
            return _token_cache["token"]

        response = requests.get(
            f"{_BASE}/gettoken",
            params={
                "corpid": config.WECOM_CORP_ID,
                "corpsecret": config.WECOM_CORP_SECRET,
            },
            timeout=10,
        )
        response.raise_for_status()
        resp = response.json()

        if resp.get("errcode") != 0:
            raise RuntimeError(f"获取 access_token 失败：{resp}")

        _token_cache["token"] = resp["access_token"]
        _token_cache["expires_at"] = now + resp.get("expires_in", 7200) - 300
        return _token_cache["token"]


def send_message(content, msgtype="markdown", to_user=None, _retried=False):
    """发送应用消息。msgtype: "text" 或 "markdown"。"""
    if msgtype not in {"text", "markdown"}:
        raise ValueError(f"不支持的消息类型：{msgtype}")
    if not content or not content.strip():
        raise ValueError("消息内容不能为空")

    token = get_access_token()
    payload = {
        "touser": to_user or config.WECOM_TO_USER,
        "msgtype": msgtype,
        "agentid": config.WECOM_AGENT_ID,
        msgtype: {"content": content},
    }
    response = requests.post(
        f"{_BASE}/message/send",
        params={"access_token": token},
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    resp = response.json()

    if resp.get("errcode") != 0:
        if resp.get("errcode") in _TOKEN_RETRY_CODES and not _retried:
            with _token_lock:
                _token_cache["token"] = ""
                _token_cache["expires_at"] = 0.0
            return send_message(content, msgtype, to_user, _retried=True)
        raise RuntimeError(f"发送失败：{resp}")


def send_text(content, to_user=None):
    send_message(content, "text", to_user)


def send_markdown(content, to_user=None):
    send_message(content, "markdown", to_user)
