from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
from datetime import datetime, timedelta, timezone


OWNER_ID = None


async def is_allowed(kiyoshi, user_id: int) -> bool:
    if OWNER_ID and user_id == OWNER_ID:
        return True
    try:
        me = await kiyoshi.get_me()
        return user_id == me.id
    except Exception:
        return False


def _safe_chat_permissions(perms: dict) -> ChatBannedRights:
    return ChatBannedRights(
        until_date=None,
        send_messages=not perms.get("can_send_messages", True),
        send_media=not perms.get("can_send_media_messages", True),
        send_stickers=not perms.get("can_send_other_messages", True),
        send_gifs=not perms.get("can_send_other_messages", True),
        send_games=not perms.get("can_send_other_messages", True),
        send_inline=not perms.get("can_send_other_messages", True),
        embed_links=not perms.get("can_add_web_page_previews", True),
        send_polls=not perms.get("can_send_polls", True),
        change_info=False,
        invite_users=False,
        pin_messages=False,
    )


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