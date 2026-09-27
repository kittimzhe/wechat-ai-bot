"""定时任务定义：想改推送内容/时间，改这个文件就行。

每个任务的字段：
  name     任务名（命令行 --run / --list 用它）
  enabled  是否启用（False = 停用）
  cron     定时规则，同 Linux crontab 字段：
           minute / hour / day / day_of_week("mon"~"sun") / month，省略即 *
  msgtype  发送格式："markdown" 或 "text"
  system   给模型的人设/要求（system prompt）
  prompt   本次推送让模型生成什么

注意：模型本身不知道实时信息（新闻/天气），要推真实数据需先接数据源，
把数据拼进 prompt，详见 README「后续扩展」。
"""

JOBS = [
    {
        "name": "晨间推送",
        "enabled": True,
        "cron": {"hour": 8, "minute": 0},
        "msgtype": "markdown",
        "system": "你是一个简洁温暖的晨间助手，输出用 Markdown，总长度控制在 300 字以内。",
        "prompt": (
            "请生成今天的晨间推送，包含三部分：\n"
            "1. 一句不落俗套的激励语（别用『新的一天新的开始』这类套话）\n"
            "2. 一个值得今天思考的小问题（技术、职业或生活方向）\n"
            "3. 一条可操作的小建议\n"
            "用 Markdown 小标题分节。"
        ),
    },
    {
        "name": "每日一题",
        "enabled": True,
        "cron": {"hour": 12, "minute": 30},
        "msgtype": "markdown",
        "system": "你是一名资深面试官，出题严谨、讲解清晰，输出用 Markdown，总长度 400 字以内。",
        "prompt": (
            "请出一道今天的『每日一题』：从后端、算法、系统设计中随机选一个主题，"
            "给出题目、3 分钟内的思路提示、以及放在最后的答案要点。难度中等。"
        ),
    },
    {
        "name": "周一计划",
        "enabled": False,  # 想启用改成 True
        "cron": {"day_of_week": "mon", "hour": 9, "minute": 0},
        "msgtype": "markdown",
        "system": "你是一名务实的效率教练，输出用 Markdown，300 字以内。",
        "prompt": "帮我生成一份本周个人成长计划：技术学习、身体健康、生活各一块，具体到可勾选的行动项。",
    },
    {
        "name": "睡前提醒",
        "enabled": False,  # 想启用改成 True
        "cron": {"hour": 22, "minute": 30},
        "msgtype": "text",
        "system": "你是一个简短温和的睡前助手，输出不超过 80 字。",
        "prompt": "写一段今晚的睡前提醒，提醒复盘今天、放下手机，语气自然不说教。",
    },
]
