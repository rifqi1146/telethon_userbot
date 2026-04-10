from io import BytesIO

from telethon import events
from telethon.tl.functions.photos import GetUserPhotosRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import User


def escape_md(text: str) -> str:
    if not text:
        return ""
    for ch in ("\\", "`", "*", "_", "[", "]", "(", ")"):
        text = text.replace(ch, f"\\{ch}")
    return text


async def resolve_target(kiyoshi, event, arg):
    if event.is_reply:
        reply = await event.get_reply_message()
        if reply and reply.sender_id:
            return reply.sender_id

    if arg:
        arg = arg.strip()
        if arg.startswith("@"):
            arg = arg[1:]

        if arg.isdigit():
            return int(arg)

        try:
            ent = await kiyoshi.get_entity(arg)
            return ent.id
        except Exception:
            return None

    try:
        me = await kiyoshi.get_me()
        return me.id
    except Exception:
        return None


def register(kiyoshi):
    @kiyoshi.on(events.NewMessage(pattern=r"^[./]info(?:\s+(.+))?$", outgoing=True))
    async def cmd_info(event):
        try:
            await event.delete()
        except Exception:
            pass

        arg = event.pattern_match.group(1)
        target = await resolve_target(kiyoshi, event, arg)

        if not target:
            return

        try:
            entity = await kiyoshi.get_entity(target)
        except Exception:
            return

        if not isinstance(entity, User):
            return await kiyoshi.send_message(
                event.chat_id,
                "`Target bukan user.`"
            )

        try:
            full = await kiyoshi(GetFullUserRequest(entity.id))
            full_user = full.full_user
        except Exception:
            full_user = None

        try:
            photos = await kiyoshi(
                GetUserPhotosRequest(
                    user_id=entity,
                    offset=0,
                    max_id=0,
                    limit=1,
                )
            )
            photo_count = getattr(photos, "count", None)
            if photo_count is None:
                photo_count = len(getattr(photos, "photos", []) or [])
        except Exception:
            photo_count = 0

        user_id = entity.id
        username = getattr(entity, "username", None)
        first_name = entity.first_name or "First Name not found"
        last_name = entity.last_name or "Last Name not found"
        bio_text = getattr(full_user, "about", None) or "Bio not found"
        common_chats = getattr(full_user, "common_chats_count", 0) if full_user else 0

        is_restricted = bool(getattr(entity, "restricted", False))
        is_verified = bool(getattr(entity, "verified", False))
        is_premium = bool(getattr(entity, "premium", False))
        is_bot = bool(getattr(entity, "bot", False))

        dc_id = getattr(getattr(entity, "photo", None), "dc_id", None)
        dc_id = dc_id if dc_id is not None else "DC ID not found"

        if username:
            permanent_link = f"https://t.me/{username}"
        else:
            permanent_link = f"tg://user?id={user_id}"

        caption = (
            "**User Information**\n"
            f"• **Telegram ID:** `{user_id}`\n"
            f"• **Permanent Link:** [Click Here]({permanent_link})\n"
            f"• **First Name:** {escape_md(first_name)}\n"
            f"• **Last Name:** {escape_md(last_name)}\n"
            f"• **Bio:** {escape_md(bio_text)}\n"
            f"• **DC ID:** `{dc_id}`\n"
            f"• **Number of Profile Pictures:** `{photo_count}`\n"
            f"• **Is Restricted:** `{is_restricted}`\n"
            f"• **Verified:** `{is_verified}`\n"
            f"• **Is Premium:** `{is_premium}`\n"
            f"• **Is A Bot:** `{is_bot}`\n"
            f"• **Groups In Common:** `{common_chats}`"
        )

        photo = None
        try:
            bio = BytesIO()
            bio.name = "profile.jpg"
            res = await kiyoshi.download_profile_photo(entity, file=bio)
            if res and bio.tell() > 0:
                bio.seek(0)
                photo = bio
        except Exception:
            photo = None

        if photo:
            try:
                await kiyoshi.send_file(
                    event.chat_id,
                    photo,
                    caption=caption,
                    force_document=False,
                    link_preview=False,
                )
                return
            except Exception:
                pass

        await kiyoshi.send_message(
            event.chat_id,
            caption,
            link_preview=False,
        )