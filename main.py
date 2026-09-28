"""入口。

用法：
  python main.py                  启动定时服务
  python main.py --list           查看所有任务
  python main.py --run 晨间推送    立即执行某个任务（测试用）
"""
import argparse
import datetime as dt
import logging
import time
import traceback
from logging.handlers import RotatingFileHandler
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler

import ai_client
import config
import data_sources
import jobs
import wecom

logger = logging.getLogger("wechat_ai_bot")


def setup_logging():
    """同时输出到终端和滚动日志文件，重复调用时不重复添加 handler。"""
    if logger.handlers:
        return
    logger.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def _limit_message(content, msgtype):
    """保护企业微信消息长度，避免模型偶尔输出过长导致发送失败。"""
    max_bytes = 3800 if msgtype == "markdown" else 1900
    encoded = content.encode("utf-8")
    if len(encoded) <= max_bytes:
        return content
    logger.warning("内容超过 %s 字节，已截断", max_bytes)
    return encoded[:max_bytes].decode("utf-8", errors="ignore").rstrip() + "\n\n（内容已截断）"


def _send_failure_alert(job, error):
    """任务失败时给自己发一条简短告警；告警失败只记日志，避免递归。"""
    if not config.ALERT_ON_FAILURE:
        return
    try:
        message = (
            f"⚠️ AI 机器人任务失败\n"
            f"任务：{job['name']}\n"
            f"时间：{dt.datetime.now(ZoneInfo(config.TIMEZONE)):%Y-%m-%d %H:%M:%S}\n"
            f"原因：{str(error)[:500]}"
        )
        wecom.send_text(message)
    except Exception:
        logger.exception("发送失败告警也失败")


def run_job(job):
    """执行一个任务并返回结果；失败时重新抛出，便于云平台重试。"""
    started = time.monotonic()
    logger.info("开始执行任务：%s", job["name"])
    try:
        prompt = job["prompt"]
        context = data_sources.build_context(job.get("data"))
        if context:
            prompt = f"{prompt}\n\n请仅根据以下实时数据补充内容，不要编造数据：\n{context}"
        content = ai_client.chat(prompt, job.get("system", ""))
        msgtype = job.get("msgtype", "markdown")
        wecom.send_message(_limit_message(content, msgtype), msgtype)
        elapsed = time.monotonic() - started
        logger.info("任务成功：%s，耗时 %.1fs", job["name"], elapsed)
        return {"ok": True, "job": job["name"], "elapsed_seconds": round(elapsed, 1)}
    except Exception as exc:
        logger.error("任务失败：%s：%s", job["name"], exc)
        logger.debug(traceback.format_exc())
        _send_failure_alert(job, exc)
        raise


def _print_jobs():
    for job in jobs.JOBS:
        status = "✅ 启用" if job.get("enabled", True) else "⏸  停用"
        print(f"  {status}  {job['name']:<8} {job['cron']}  （{job['msgtype']}）")


def main():
    parser = argparse.ArgumentParser(description="微信 AI 定时推送机器人")
    parser.add_argument("--list", action="store_true", help="列出所有任务")
    parser.add_argument("--run", metavar="任务名", help="立即执行指定任务")
    args = parser.parse_args()

    if args.list:
        _print_jobs()
        return

    config.check_config(require_ai=True)
    setup_logging()

    if args.run:
        target = next((job for job in jobs.JOBS if job["name"] == args.run), None)
        if not target:
            raise SystemExit(f"找不到任务「{args.run}」，用 --list 查看任务名")
        run_job(target)
        return

    enabled_jobs = [job for job in jobs.JOBS if job.get("enabled", True)]
    if not enabled_jobs:
        raise SystemExit("没有启用的任务，请到 jobs.py 里把 enabled 改为 True")

    scheduler = BlockingScheduler(timezone=ZoneInfo(config.TIMEZONE))
    for job in enabled_jobs:
        scheduler.add_job(
            run_job,
            trigger="cron",
            id=job["name"],
            kwargs={"job": job},
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
            **job["cron"],
        )
        logger.info("已注册任务：%s，规则：%s", job["name"], job["cron"])

    logger.info("共 %s 个任务已启动，时区：%s，Ctrl+C 退出", len(enabled_jobs), config.TIMEZONE)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("已退出")


if __name__ == "__main__":
    main()
