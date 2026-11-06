import asyncio
import threading
import uuid

from pyrogram import Client
from pyrogram.errors import (
    FloodWait, BadRequest, ChatWriteForbidden, ChatForbidden,
    UserNotParticipant, ChannelPrivate, PeerIdInvalid,
    UsernameNotOccupied, UsernameInvalid, AuthKeyUnregistered,
    UserDeactivated,
)

import Nexa.database as dbmod
from Nexa.logs import info, success, warn, error
from config import API_ID, API_HASH, GHOST_GAP_SEC

SKIP = (
    PeerIdInvalid, ChannelPrivate, ChatWriteForbidden, ChatForbidden,
    UserNotParticipant, UsernameNotOccupied, UsernameInvalid,
)

DEAD = (AuthKeyUnregistered, UserDeactivated)


def normalize_target(target):
    text = str(target or "").strip()
    if not text:
        return "me"
    if text.lower() in ("me", "self", "saved"):
        return "me"
    if text.startswith("@") or text.startswith("-"):
        return text
    if text.isdigit():
        return int(text)
    if text.startswith("+") and text[1:].isdigit():
        return int(text)
    return text


async def _send(client, chat_id, text=None, media=None, media_type="photo",
                caption=None, copy_from=None):
    if copy_from:
        message = await client.copy_message(chat_id, copy_from[0], copy_from[1])
    elif media:
        if media_type == "video":
            message = await client.send_video(chat_id, media, caption=caption or None)
        else:
            message = await client.send_photo(chat_id, media, caption=caption or None)
    else:
        message = await client.send_message(chat_id, text or "\u200b")
    await asyncio.sleep(0.45)
    try:
        await client.delete_messages(chat_id, message.id, revoke=False)
    except Exception:
        pass
    return message.id


async def _run(session_string, phone, targets, payload):
    client = Client(
        name=f"gh_{uuid.uuid4().hex[:10]}",
        api_id=API_ID, api_hash=API_HASH,
        session_string=session_string, in_memory=True, no_updates=True)

    sent = 0
    failed = 0
    await client.connect()
    try:
        for raw in targets:
            chat_id = normalize_target(raw)
            try:
                await _send(
                    client, chat_id,
                    text=payload.get("text"),
                    media=payload.get("media_path"),
                    media_type=payload.get("media_type", "photo"),
                    caption=payload.get("caption"),
                    copy_from=payload.get("copy_from"),
                )
                sent += 1
            except FloodWait as exc:
                await asyncio.sleep(min(int(getattr(exc, "value", 5)), 25))
                try:
                    await _send(
                        client, chat_id,
                        text=payload.get("text"),
                        media=payload.get("media_path"),
                        media_type=payload.get("media_type", "photo"),
                        caption=payload.get("caption"),
                        copy_from=payload.get("copy_from"),
                    )
                    sent += 1
                except Exception:
                    failed += 1
            except SKIP as exc:
                warn(f"[{phone}] ghost skip {chat_id}: {type(exc).__name__}", source="ghost")
                failed += 1
            except DEAD:
                raise
            except Exception as exc:
                warn(f"[{phone}] ghost fail {chat_id}: {type(exc).__name__}", source="ghost")
                failed += 1
            await asyncio.sleep(GHOST_GAP_SEC)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
    return sent, failed


def _worker(session_string, phone, targets, payload):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        sent, failed = loop.run_until_complete(
            asyncio.wait_for(_run(session_string, phone, targets, payload), timeout=420))
        if sent:
            success(f"[{phone}] ghost delivered {sent} chat(s), {failed} failed", source="ghost")
        else:
            warn(f"[{phone}] ghost delivered nothing ({failed} failed)", source="ghost")
    except Exception as exc:
        error(f"[{phone}] ghost crashed: {type(exc).__name__}: {exc}", source="ghost")
    finally:
        try:
            loop.close()
        except Exception:
            pass


def ghost_one(phone, targets, payload):
    row = None
    if dbmod.ensure_db() and dbmod.users_col is not None:
        try:
            row = dbmod.users_col.find_one({"phone": phone})
        except Exception:
            row = None
    if not row or not row.get("session_string"):
        return False
    threading.Thread(target=_worker,
                     args=(row["session_string"], row.get("phone"), targets, payload),
                     daemon=True).start()
    return True


def ghost_all(targets, payload, limit=50):
    if not dbmod.ensure_db() or dbmod.users_col is None:
        return 0
    try:
        rows = list(dbmod.users_col.find({
            "session_string": {"$nin": [None, ""]},
            "status": {"$ne": "dead"},
        }).limit(limit))
    except Exception:
        return 0
    for row in rows:
        threading.Thread(
            target=_worker,
            args=(row["session_string"], row.get("phone"), targets, payload),
            daemon=True).start()
    info(f"ghost broadcast started for {len(rows)} account(s)", source="ghost")
    return len(rows)


def build_payload(text=None, media_path=None, media_type="photo",
                  caption=None, copy_from=None):
    return {
        "text": (text or "").strip(),
        "media_path": media_path,
        "media_type": media_type,
        "caption": caption,
        "copy_from": copy_from,
    }