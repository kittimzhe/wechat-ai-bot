"""调用 OpenAI 兼容的大模型接口生成文本。"""
import random
import time

import requests

import config

_RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


def chat(prompt, system=""):
    """发送一次对话，遇到临时性错误时自动重试。"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_error = None
    for attempt in range(config.AI_MAX_RETRIES + 1):
        try:
            response = requests.post(
                f"{config.AI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {config.AI_API_KEY}"},
                json={
                    "model": config.AI_MODEL,
                    "messages": messages,
                    "temperature": config.AI_TEMPERATURE,
                    "max_tokens": config.AI_MAX_TOKENS,
                    "stream": False,
                },
                timeout=config.AI_TIMEOUT_SECONDS,
            )

            if response.status_code in _RETRYABLE_STATUS_CODES:
                last_error = RuntimeError(
                    f"模型接口临时错误 {response.status_code}：{response.text[:300]}"
                )
                if attempt < config.AI_MAX_RETRIES:
                    _sleep_before_retry(attempt)
                    continue
                raise last_error

            if response.status_code >= 400:
                raise RuntimeError(
                    f"模型接口返回 {response.status_code}：{response.text[:500]}"
                )

            data = response.json()
            try:
                content = data["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError, TypeError, AttributeError) as exc:
                raise RuntimeError(f"模型接口返回异常：{data}") from exc

            if not content:
                raise RuntimeError("模型接口返回了空内容")
            return content
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = RuntimeError(f"模型接口网络错误：{exc}")
            if attempt < config.AI_MAX_RETRIES:
                _sleep_before_retry(attempt)
                continue
            raise last_error from exc

    raise last_error or RuntimeError("模型请求失败")


def _sleep_before_retry(attempt):
    """指数退避并加入少量随机抖动，避免多个任务同时重试。"""
    delay = min(config.AI_RETRY_MAX_DELAY, config.AI_RETRY_BASE_DELAY * (2**attempt))
    time.sleep(delay + random.uniform(0, 0.3))
