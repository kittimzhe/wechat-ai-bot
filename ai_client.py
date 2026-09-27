"""调用 OpenAI 兼容的大模型接口生成文本。

DeepSeek / 智谱 / OpenAI / Kimi 等都兼容这个格式，
换模型只需改 .env 里的 AI_BASE_URL / AI_MODEL / AI_API_KEY。
"""
import requests

import config


def chat(prompt, system=""):
    """发送一次对话，返回模型生成的文本。"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = requests.post(
        f"{config.AI_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {config.AI_API_KEY}"},
        json={
            "model": config.AI_MODEL,
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 1024,
            "stream": False,
        },
        timeout=120,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"模型接口返回 {resp.status_code}：{resp.text[:500]}")

    data = resp.json()
    if "choices" not in data:
        raise RuntimeError(f"模型接口返回异常：{data}")
    return data["choices"][0]["message"]["content"].strip()
