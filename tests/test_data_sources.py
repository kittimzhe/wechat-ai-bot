import unittest
from unittest.mock import Mock, patch

import config
import data_sources


class TestDataSources(unittest.TestCase):
    def test_parse_rss(self):
        xml = """<?xml version='1.0'?><rss><channel><item><title>标题</title><description><![CDATA[<b>摘要</b>]]></description></item></channel></rss>"""
        with patch.object(config, "RSS_MAX_ITEMS", 8):
            result = data_sources._parse_feed(xml, "https://example.com/feed.xml")
        self.assertEqual(result, [("标题", "摘要", "example.com")])

    @patch.object(data_sources.requests, "get")
    def test_weather_context(self, get):
        response = Mock()
        response.json.return_value = {"current": {"temperature_2m": 20, "relative_humidity_2m": 40, "weather_code": 1, "wind_speed_10m": 3}}
        get.return_value = response
        with patch.object(config, "WEATHER_LAT", 39.9), patch.object(config, "WEATHER_LON", 116.4):
            result = data_sources.build_context({"weather": True})
        self.assertIn("温度：20°C", result)
        get.assert_called_once()

    def test_missing_weather_coordinates_is_safe(self):
        with patch.object(config, "WEATHER_LAT", None), patch.object(config, "WEATHER_LON", None):
            self.assertEqual(data_sources.build_context({"weather": True}), "")


if __name__ == "__main__":
    unittest.main()
