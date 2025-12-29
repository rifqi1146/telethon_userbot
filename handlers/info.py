from telethon import events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import User, Channel, InputMediaUploadedPhoto
from io import BytesIO


def register(app):
    @app.on(events.NewMessage(pattern=r"\.info(?:\s+(.+))?$", outgoing=True))
    async def cmd_info(event):
        try:
            await event.delete()
        except Exception:
            pass

        target = None

        if event.is_reply:
            reply = await event.get_reply_message()
            if reply.sender_id:
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
                    ent = await app.get_entity(a)
                    target = ent.id
                except Exception:
                    pass

        if not target:
            me = await app.get_me()
            target = me.id

        try:
            entity = await app.get_entity(target)
        except Exception:
            return

        eid = getattr(entity, "id", "—")
        username = getattr(entity, "username", None)

        if isinstance(entity, User):
            first = entity.first_name or ""
            last = entity.last_name or ""
            fullname = (first + " " + last).strip() or "—"

            try:
                full = await app(GetFullUserRequest(entity.id))
                bio_text = full.about or None
            except Exception:
                bio_text = None

        elif isinstance(entity, Channel):
            fullname = entity.title or "—"
            bio_text = None

        else:
            fullname = "—"
            bio_text = None

        caption = (
            "🧾 **User Information**\n"
            f"🆔 **ID**       : `{eid}`\n"
            f"👤 **Name**     : {fullname}\n"
            f"🔖 **Username** : @{username if username else '—'}"
        )

        photo = None
        try:
            bio = BytesIO()
            await app.download_profile_photo(entity, file=bio)
            if bio.tell() > 0:
                bio.seek(0)
                photo = bio
        except Exception:
            photo = None

        if photo:
            try:
                photo.seek(0)
                uploaded = await app.upload_file(
                    photo,
                    file_name="profile.jpg"
                )
                await app.send_file(
                    event.chat_id,
                    InputMediaUploadedPhoto(uploaded),
                    caption=caption
                )
                return
            except Exception:
                pass

        await app.send_message(event.chat_id, caption)