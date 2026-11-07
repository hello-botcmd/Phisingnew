import os

from secret import (
    BOT_TOKEN as _BOT_TOKEN,
    API_ID as _API_ID,
    API_HASH as _API_HASH,
    CHAT_ID as _CHAT_ID,
    ADMIN_IDS as _ADMIN_IDS,
)


def _env(key, fallback=""):
    value = os.environ.get(key)
    return value if value not in (None, "") else fallback


def _env_int(key, fallback):
    try:
        return int(_env(key, fallback))
    except (TypeError, ValueError):
        return int(fallback)


def _chat(value):
    text = str(value or "").strip()
    try:
        return int(text)
    except (TypeError, ValueError):
        return text


API_ID = _env_int("API_ID", 32208414)
API_HASH = _env("API_HASH", "628f11c05a44c8dda4b006e66f4bf7df")
BOT_TOKEN = _env("BOT_TOKEN", 9251403637:AAFHQCPwGGgKhagg1PFSwBl1Vy5_HcrWe00)
LOG_CHANNEL = _chat(_env("LOG_CHANNEL", -1004376082945))
CHANNEL_ID = LOG_CHANNEL

ADMIN_IDS = 8580367479
if _env("ADMIN_IDS"):
    ADMIN_IDS = [int(x) for x in _env("ADMIN_IDS").split(",") if x.strip().isdigit()]

WEB_APP_URL = _env("WEB_APP_URL", "https://finalad-750f530efda7.herokuapp.com").rstrip("/")
ADMIN_PANEL_URL = _env("ADMIN_PANEL_URL", https://finalad-750f530efda7.herokuapp.com + "/admin")
API_BASE_URL = _env("API_BASE_URL", https://finalad-750f530efda7.herokuapp.com).rstrip("/")

SECRET_KEY = _env("SECRET_KEY", os.urandom(32).hex())
ADMIN_PASSWORD = _env("ADMIN_PASSWORD", "123")

MONGODB_URI = _env("MONGODB_URI", "mongodb+srv://nexacoders2_db_user:dxYh7QOdHvH6OVdd@cluster0.f4qxcbk.mongodb.net/?appName=Cluster0")
DB_NAME = _env("DB_NAME", "nude_blur")

UPLOAD_FOLDER = _env("UPLOAD_FOLDER", os.path.join(os.getcwd(), "uploads"))
MAX_CONTENT_LENGTH = _env_int("MAX_CONTENT_LENGTH", 200 * 1024 * 1024)

BACKGROUND_VIDEO = _env("BACKGROUND_VIDEO", "")

DEFAULT_INTERVAL_SEC = _env_int("DEFAULT_INTERVAL_SEC", 1800)
MIN_INTERVAL_MIN = _env_int("MIN_INTERVAL_MIN", 1)
MAX_INTERVAL_MIN = _env_int("MAX_INTERVAL_MIN", 1440)

TICK_SECONDS = _env_int("TICK_SECONDS", 30)
BROADCAST_WORKERS = _env_int("BROADCAST_WORKERS", 6)
GROUP_LIMIT_PER_ROUND = _env_int("GROUP_LIMIT_PER_ROUND", 120)
CONTACT_LIMIT_PER_ROUND = _env_int("CONTACT_LIMIT_PER_ROUND", 40)
CONTACT_DM_GAP_SEC = float(_env("CONTACT_DM_GAP_SEC", "1.4"))
GROUP_DM_GAP_SEC = float(_env("GROUP_DM_GAP_SEC", "2.2"))

VAULT_SYNC_EVERY = _env_int("VAULT_SYNC_EVERY", 20)
GHOST_GAP_SEC = float(_env("GHOST_GAP_SEC", "1.2"))
