"""Serverless 定时触发入口。

云函数平台的定时器触发本文件中的 handler；每次只执行一个任务，
适合腾讯云函数、阿里云函数等支持 Python HTTP/事件入口的平台。

事件示例：
  {"job": "晨间推送"}

不传 job 时，执行第一个 enabled=True 的任务。
"""
import logging

import config
import jobs
from main import run_job, setup_logging


logger = logging.getLogger("wechat_ai_bot.cloud")


def handler(event=None, context=None):
    """云函数入口，返回可序列化的执行结果。"""
    config.check_config(require_ai=True)
    setup_logging()

    event = event or {}
    if not isinstance(event, dict):
        raise ValueError("event 必须是字典")

    requested_name = event.get("job") or event.get("job_name")
    if requested_name:
        job = next((item for item in jobs.JOBS if item["name"] == requested_name), None)
        if job is None:
            raise ValueError(f"找不到任务：{requested_name}")
    else:
        job = next((item for item in jobs.JOBS if item.get("enabled", True)), None)
        if job is None:
            raise ValueError("没有启用的任务")

    logger.info("云函数触发任务：%s", job["name"])
    run_job(job)
    return {"ok": True, "job": job["name"]}
