"""集中读取 .env 配置。"""
import os

from dotenv import load_dotenv

load_dotenv()


def _int_env(name, default):
    value = os.getenv(name, str(default)).strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"配置 {name} 必须是整数，当前值：{value!r}") from exc


def _float_env(name, default):
    value = os.getenv(name, str(default)).strip()
    if not value:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise SystemExit(f"配置 {name} 必须是数字，当前值：{value!r}") from exc


def _optional_float_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise SystemExit(f"配置 {name} 必须是数字，当前值：{value!r}") from exc


# ---- 企业微信 ----
WECOM_CORP_ID = os.getenv("WECOM_CORP_ID", "").strip()
WECOM_CORP_SECRET = os.getenv("WECOM_CORP_SECRET", "").strip()
WECOM_AGENT_ID = _int_env("WECOM_AGENT_ID", 0)
WECOM_TO_USER = os.getenv("WECOM_TO_USER", "@all").strip()

# ---- AI（OpenAI 兼容接口）----
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
AI_API_KEY = os.getenv("AI_API_KEY", "").strip()
AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat").strip()
AI_TIMEOUT_SECONDS = _int_env("AI_TIMEOUT_SECONDS", 120)
AI_MAX_RETRIES = _int_env("AI_MAX_RETRIES", 3)
AI_RETRY_BASE_DELAY = _float_env("AI_RETRY_BASE_DELAY", 1.0)
AI_RETRY_MAX_DELAY = _float_env("AI_RETRY_MAX_DELAY", 8.0)
AI_TEMPERATURE = _float_env("AI_TEMPERATURE", 0.8)
AI_MAX_TOKENS = _int_env("AI_MAX_TOKENS", 1024)

# ---- 运行参数 ----
TIMEZONE = os.getenv("TIMEZONE", "Asia/Shanghai").strip()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()
LOG_FILE = os.getenv("LOG_FILE", "bot.log").strip()
ALERT_ON_FAILURE = os.getenv("ALERT_ON_FAILURE", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# ---- 可选实时数据源 ----
DATA_TIMEOUT_SECONDS = _int_env("DATA_TIMEOUT_SECONDS", 15)
WEATHER_LAT = _optional_float_env("WEATHER_LAT")
WEATHER_LON = _optional_float_env("WEATHER_LON")
RSS_URLS = os.getenv("RSS_URLS", "").strip()
RSS_MAX_FEEDS = _int_env("RSS_MAX_FEEDS", 3)
RSS_MAX_ITEMS = _int_env("RSS_MAX_ITEMS", 8)


def check_config(require_ai=True):
    """启动前检查必填项，缺了直接报错并提示去哪里补。"""
    missing = []
    if not WECOM_CORP_ID:
        missing.append("WECOM_CORP_ID（企业微信后台 → 我的企业 → 企业信息 → 企业ID）")
    if not WECOM_CORP_SECRET:
        missing.append("WECOM_CORP_SECRET（应用详情页 → Secret）")
    if not WECOM_AGENT_ID:
        missing.append("WECOM_AGENT_ID（应用详情页 → AgentId）")
    if not WECOM_TO_USER:
        missing.append("WECOM_TO_USER（通讯录里的成员 userid）")
    if require_ai and not AI_API_KEY:
        missing.append("AI_API_KEY（模型平台注册后创建）")
    if missing:
        raise SystemExit("配置不完整，请在 .env 中补齐：\n  - " + "\n  - ".join(missing))
