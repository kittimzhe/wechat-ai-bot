import unittest
from unittest.mock import Mock, patch

import ai_client
import config
import main
import wecom


class TestMessageLimit(unittest.TestCase):
    def test_short_content_is_unchanged(self):
        self.assertEqual(main._limit_message("hello", "text"), "hello")

    def test_long_content_is_truncated_at_utf8_boundary(self):
        result = main._limit_message("中" * 3000, "text")
        self.assertLessEqual(len(result.encode("utf-8")), 1900 + len("\n\n（内容已截断）".encode("utf-8")))
        self.assertTrue(result.endswith("（内容已截断）"))


class TestAIClient(unittest.TestCase):
    @patch.object(ai_client.time, "sleep")
    @patch.object(ai_client.requests, "post")
    def test_retries_temporary_status_then_succeeds(self, post, sleep):
        temporary = Mock(status_code=503, text="busy")
        success = Mock(status_code=200)
        success.json.return_value = {"choices": [{"message": {"content": "答案"}}]}
        post.side_effect = [temporary, success]

        with patch.object(config, "AI_MAX_RETRIES", 3), patch.object(config, "AI_RETRY_BASE_DELAY", 0), patch.object(config, "AI_RETRY_MAX_DELAY", 0):
            self.assertEqual(ai_client.chat("问题"), "答案")

        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once()

    @patch.object(ai_client.requests, "post")
    def test_non_retryable_status_fails_immediately(self, post):
        response = Mock(status_code=401, text="bad key")
        post.return_value = response
        with self.assertRaises(RuntimeError):
            ai_client.chat("问题")
        self.assertEqual(post.call_count, 1)


class TestWeComClient(unittest.TestCase):
    @patch.object(wecom.requests, "get")
    def test_access_token_is_cached(self, get):
        wecom._token_cache.update(token="", expires_at=0)
        response = Mock()
        response.json.return_value = {"errcode": 0, "access_token": "token", "expires_in": 7200}
        get.return_value = response
        with patch.object(config, "WECOM_CORP_ID", "corp"), patch.object(config, "WECOM_CORP_SECRET", "secret"):
            self.assertEqual(wecom.get_access_token(), "token")
            self.assertEqual(wecom.get_access_token(), "token")
        get.assert_called_once()

    @patch.object(wecom.requests, "post")
    @patch.object(wecom, "get_access_token", return_value="token")
    def test_invalid_message_type_is_rejected(self, _token, post):
        with self.assertRaises(ValueError):
            wecom.send_message("hello", "image")
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
