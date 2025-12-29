from datetime import datetime, timedelta, timezone
from telethon.tl.types import ChatPermissions

OWNER_ID = None


async def is_allowed(app, user_id: int) -> bool:
    if OWNER_ID and user_id == OWNER_ID:
        return True
    try:
        me = await app.get_me()
        return user_id == me.id
    except Exception:
        return False


def _safe_chat_permissions(perms: dict) -> ChatPermissions:
    return ChatPermissions(**perms)


def parse_duration_to_datetime(text: str | None):
    if not text:
        return None

    try:
        num = int(text[:-1])
        unit = text[-1]

        if unit == "s":
            delta = timedelta(seconds=num)
        elif unit == "m":
            delta = timedelta(minutes=num)
        elif unit == "h":
            delta = timedelta(hours=num)
        elif unit == "d":
            delta = timedelta(days=num)
        else:
            return None

        return datetime.now(timezone.utc) + delta
    except Exception:
        return None
        