"""企业微信应用消息：获取 access_token、发送文本 / Markdown 消息。

接口文档：https://developer.work.weixin.qq.com/document/path/90235
"""
import threading
import time

import requests

import config

_BASE = "https://qyapi.weixin.qq.com/cgi-bin"

_token_lock = threading.Lock()
_token_cache = {"token": "", "expires_at": 0.0}


def get_access_token():
    """获取 access_token（有效期 7200 秒，这里做了内存缓存）。"""
    with _token_lock:
        now = time.time()
        if _token_cache["token"] and now < _token_cache["expires_at"]:
            return _token_cache["token"]

        resp = requests.get(
            f"{_BASE}/gettoken",
            params={
                "corpid": config.WECOM_CORP_ID,
                "corpsecret": config.WECOM_CORP_SECRET,
            },
            timeout=10,
        ).json()

        if resp.get("errcode") != 0:
            raise RuntimeError(f"获取 access_token 失败：{resp}")

        _token_cache["token"] = resp["access_token"]
        # 提前 5 分钟过期，避免边界失效
        _token_cache["expires_at"] = now + resp.get("expires_in", 7200) - 300
        return _token_cache["token"]


def send_message(content, msgtype="markdown", to_user=None, _retried=False):
    """发送应用消息。msgtype: "text" 或 "markdown"。"""
    token = get_access_token()
    payload = {
        "touser": to_user or config.WECOM_TO_USER,
        "msgtype": msgtype,
        "agentid": config.WECOM_AGENT_ID,
        msgtype: {"content": content},
    }
    resp = requests.post(
        f"{_BASE}/message/send",
        params={"access_token": token},
        json=payload,
        timeout=10,
    ).json()

    if resp.get("errcode") != 0:
        # token 失效：清缓存换新 token 重试一次
        if resp.get("errcode") in (40014, 42001) and not _retried:
            _token_cache["token"] = ""
            return send_message(content, msgtype, to_user, _retried=True)
        raise RuntimeError(f"发送失败：{resp}")


def send_text(content, to_user=None):
    send_message(content, "text", to_user)


def send_markdown(content, to_user=None):
    send_message(content, "markdown", to_user)
