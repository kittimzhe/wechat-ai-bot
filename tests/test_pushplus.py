import unittest
from unittest.mock import Mock, patch

import config
import notify
import pushplus
import wecom


class TestPushPlusClient(unittest.TestCase):
    @patch.object(pushplus.requests, "post")
    def test_send_markdown_uses_markdown_template(self, post):
        response = Mock()
        response.json.return_value = {"code": 200, "msg": "请求成功", "data": "abc"}
        post.return_value = response
        with patch.object(config, "PUSHPLUS_TOKEN", "token"):
            result = pushplus.send_message("# 标题\n内容", "markdown", title="晨间推送")
        self.assertEqual(result, "abc")
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["template"], "markdown")
        self.assertEqual(payload["title"], "晨间推送")

    @patch.object(pushplus.requests, "post")
    def test_non_200_code_raises(self, post):
        response = Mock()
        response.json.return_value = {"code": 905, "msg": "未实名认证"}
        post.return_value = response
        with patch.object(config, "PUSHPLUS_TOKEN", "token"):
            with self.assertRaisesRegex(RuntimeError, "905"):
                pushplus.send_message("内容", "text")

    def test_invalid_msgtype_rejected(self):
        with self.assertRaises(ValueError):
            pushplus.send_message("内容", "image")

    def test_empty_content_rejected(self):
        with self.assertRaises(ValueError):
            pushplus.send_message("  ", "text")


class TestChannelDispatch(unittest.TestCase):
    @patch.object(pushplus, "send_message")
    def test_pushplus_channel_is_used_when_configured(self, send):
        with patch.object(config, "CHANNEL", "pushplus"):
            notify.send_message("内容", "markdown", title="晨间推送")
        send.assert_called_once_with("内容", "markdown", "晨间推送")

    @patch.object(wecom, "send_message")
    def test_wecom_channel_is_used_by_default(self, send):
        with patch.object(config, "CHANNEL", "wecom"):
            notify.send_message("内容", "markdown", title="晨间推送")
        send.assert_called_once()


class TestChannelConfigCheck(unittest.TestCase):
    def test_pushplus_requires_token(self):
        with patch.object(config, "CHANNEL", "pushplus"), patch.object(
            config, "PUSHPLUS_TOKEN", ""
        ):
            with self.assertRaises(SystemExit):
                config.check_config(require_ai=False)

    def test_pushplus_does_not_require_wecom_fields(self):
        with patch.object(config, "CHANNEL", "pushplus"), patch.object(
            config, "PUSHPLUS_TOKEN", "token"
        ), patch.object(config, "AI_API_KEY", "key"):
            config.check_config(require_ai=True)


if __name__ == "__main__":
    unittest.main()
