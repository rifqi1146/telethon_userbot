from telethon import events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import User, Channel
from io import BytesIO


def register(kiyoshi):
    @kiyoshi.on(events.NewMessage(pattern=r"\.info(?:\s+(.+))?$", outgoing=True))
    async def cmd_info(event):
        try:
            await event.delete()
        except Exception:
            pass

        target = None

        if event.is_reply:
            reply = await event.get_reply_message()
            if reply and reply.sender_id:
                target = reply.sender_id

        arg = event.pattern_match.group(1)
        if not target and arg:
            a = arg.strip()
            if a.startswith("@"):
                a = a[1:]
            if a.isdigit():
                target = int(a)
            else:
                try:
                    ent = await kiyoshi.get_entity(a)
                    target = ent.id
                except Exception:
                    pass

        if not target:
            try:
                me = await kiyoshi.get_me()
                target = me.id
            except Exception:
                return

        try:
            entity = await kiyoshi.get_entity(target)
        except Exception:
            return

        eid = getattr(entity, "id", "—")
        username = getattr(entity, "username", None)

        fullname = "—"
        bio_text = None

        if isinstance(entity, User):
            first = entity.first_name or ""
            last = entity.last_name or ""
            fullname = (first + " " + last).strip() or "—"
            try:
                full = await kiyoshi(GetFullUserRequest(entity.id))
                bio_text = full.about or None
            except Exception:
                bio_text = None

        elif isinstance(entity, Channel):
            fullname = entity.title or "—"

        caption = (
            "🧾 **User Information**\n"
            f"🆔 **ID**       : `{eid}`\n"
            f"👤 **Name**     : {fullname}\n"
            f"🔖 **Username** : @{username if username else '—'}"
        )

        if bio_text:
            caption += f"\n📝 **Bio**      : {bio_text}"

        photo = None
        try:
            bio = BytesIO()
            bio.name = "profile.jpg"
            res = await kiyoshi.download_profile_photo(entity, file=bio)
            if res:
                if bio.tell() > 0:
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
                    force_document=False
                )
                return
            except Exception:
                pass

        await kiyoshi.send_message(event.chat_id, caption)