"""入口。

用法：
  python main.py              启动定时服务（前台常驻，Ctrl+C 退出）
  python main.py --list       查看所有任务
  python main.py --run 晨间推送   立即执行某个任务（测试用）
"""
import argparse
import datetime
import traceback

from apscheduler.schedulers.blocking import BlockingScheduler

import ai_client
import config
import jobs
import wecom


def run_job(job):
    """执行一个任务：AI 生成内容 → 推送到微信。"""
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] 开始执行任务：{job['name']}")
    try:
        content = ai_client.chat(job["prompt"], job.get("system", ""))
        wecom.send_message(content, job.get("msgtype", "markdown"))
        preview = content.replace("\n", " ")[:60]
        print(f"    ✅ 已推送，内容预览：{preview}…")
    except Exception:
        print(f"    ❌ 失败：\n{traceback.format_exc()}")


def main():
    parser = argparse.ArgumentParser(description="微信 AI 定时推送机器人")
    parser.add_argument("--list", action="store_true", help="列出所有任务")
    parser.add_argument("--run", metavar="任务名", help="立即执行指定任务")
    args = parser.parse_args()

    if args.list:
        for j in jobs.JOBS:
            status = "✅ 启用" if j.get("enabled", True) else "⏸  停用"
            print(f"  {status}  {j['name']:<8} {j['cron']}  （{j['msgtype']}）")
        return

    config.check_config(require_ai=True)

    if args.run:
        target = next((j for j in jobs.JOBS if j["name"] == args.run), None)
        if not target:
            raise SystemExit(f"找不到任务「{args.run}」，用 --list 查看任务名")
        run_job(target)
        return

    enabled_jobs = [j for j in jobs.JOBS if j.get("enabled", True)]
    if not enabled_jobs:
        raise SystemExit("没有启用的任务，请到 jobs.py 里把 enabled 改为 True")

    scheduler = BlockingScheduler()
    for job in enabled_jobs:
        scheduler.add_job(
            run_job,
            trigger="cron",
            id=job["name"],
            kwargs={"job": job},
            **job["cron"],
        )
        print(f"  已注册：{job['name']}  {job['cron']}")

    print(f"\n🤖 共 {len(enabled_jobs)} 个任务已启动，保持本窗口运行即可（Ctrl+C 退出）")
    print("   先测试某个任务可另开终端运行：python main.py --run 任务名\n")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n已退出。")


if __name__ == "__main__":
    main()
