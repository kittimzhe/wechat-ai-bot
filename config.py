"""集中读取 .env 配置。"""
import os

from dotenv import load_dotenv

load_dotenv()

# ---- 企业微信 ----
WECOM_CORP_ID = os.getenv("WECOM_CORP_ID", "").strip()
WECOM_CORP_SECRET = os.getenv("WECOM_CORP_SECRET", "").strip()
WECOM_AGENT_ID = int(os.getenv("WECOM_AGENT_ID", "0").strip() or "0")
WECOM_TO_USER = os.getenv("WECOM_TO_USER", "@all").strip()

# ---- AI（OpenAI 兼容接口）----
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
AI_API_KEY = os.getenv("AI_API_KEY", "").strip()
AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat").strip()


def check_config(require_ai=True):
    """启动前检查必填项，缺了直接报错并提示去哪里补。"""
    missing = []
    if not WECOM_CORP_ID:
        missing.append("WECOM_CORP_ID（企业微信后台 → 我的企业 → 企业信息 → 企业ID）")
    if not WECOM_CORP_SECRET:
        missing.append("WECOM_CORP_SECRET（应用详情页 → Secret）")
    if not WECOM_AGENT_ID:
        missing.append("WECOM_AGENT_ID（应用详情页 → AgentId）")
    if require_ai and not AI_API_KEY:
        missing.append("AI_API_KEY（模型平台注册后创建）")
    if missing:
        raise SystemExit("配置不完整，请在 .env 中补齐：\n  - " + "\n  - ".join(missing))
