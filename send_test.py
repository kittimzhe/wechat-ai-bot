"""第一步验证脚本：不调用 AI，直接发一条固定消息到当前推送渠道。

用法：
  python send_test.py
"""
import config
import notify

config.check_config(require_ai=False)  # 只需要推送渠道配置，不需要 AI Key
notify.send_text("✅ AI 机器人推送渠道配置成功！这是一条测试消息。")
print("已发送，去微信里看看是否收到。")
