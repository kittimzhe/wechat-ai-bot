"""第一步验证脚本：不调用 AI，直接给微信发一条固定消息。

用法：
  python send_test.py
"""
import config
import wecom

config.check_config(require_ai=False)  # 这一步只需要企业微信配置
wecom.send_text("✅ 微信 AI 机器人配置成功！这是一条测试消息。")
print("已发送，去微信里看看「企业微信通知」吧。")
