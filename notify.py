"""统一推送出口：根据 CHANNEL 选择渠道，业务代码不关心用的是哪个。

CHANNEL 取值（.env）：
  pushplus  个人微信，经「pushplus 推送加」服务号送达（推荐）
  wecom     企业微信应用消息
"""
import config
import pushplus
import wecom


def send_message(content, msgtype, title=None):
    """发送一条消息到当前渠道；title 仅在支持的渠道生效。"""
    if config.CHANNEL == "pushplus":
        return pushplus.send_message(content, msgtype, title)
    return wecom.send_message(content, msgtype, title=title)


def send_text(content):
    """发送一条纯文本消息到当前渠道。"""
    if config.CHANNEL == "pushplus":
        return pushplus.send_text(content)
    return wecom.send_text(content)
