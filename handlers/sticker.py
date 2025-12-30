import os
import asyncio
from PIL import Image
from telethon import events
from telethon.errors import YouBlockedUserError

def _to_png(path):
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    scale = 512 / max(w, h)
    img = img.resize((int(w * scale), int(h * scale)))
    out = "sticker.png"
    img.save(out)
    return out

def register(app):

    @app.on(events.NewMessage(pattern=r"\.kang(?:\s+(.*))?$", outgoing=True))
    async def kang(event):
        if not event.is_reply:
            return await event.edit("Reply to a sticker or image.")

        reply = await event.get_reply_message()
        status = await event.edit("✨ Processing...")

        emoji = event.pattern_match.group(1) or "✨"
        me = await app.get_me()
        shortname = f"kiyoshi_{me.id}"
        title = f"{me.first_name}'s Pack"

        animated = False
        media_path = None

        try:
            if reply.sticker and reply.sticker.mime_type == "application/x-tgsticker":
                animated = True
                media_path = await reply.download_media(file="sticker.tgs")
            else:
                media_path = await reply.download_media()
        except Exception:
            return await status.edit("Failed to download media.")

        try:
            async with app.conversation("Stickers", timeout=90) as conv:
                try:
                    await conv.send_message("/addsticker")
                except YouBlockedUserError:
                    await app.unblock("Stickers")
                    await conv.send_message("/addsticker")

                await conv.get_response()
                await conv.send_message(shortname)
                resp = await conv.get_response()

                if "Invalid set selected" in resp.text:
                    await conv.send_message("/newanimated" if animated else "/newpack")
                    await conv.get_response()
                    await conv.send_message(title)
                    await conv.get_response()

                if animated:
                    await conv.send_file(media_path, force_document=True)
                else:
                    png = _to_png(media_path)
                    await conv.send_file(png, force_document=True)

                await conv.get_response()
                await conv.send_message(emoji)
                await conv.get_response()
                await conv.send_message("/done")
                await conv.get_response()

        except Exception as e:
            return await status.edit(f"❌ Kang failed: {e}")

        await status.edit(
            f"✅ Sticker added\nhttps://t.me/addstickers/{shortname}"
        )

        try:
            os.remove(media_path)
            if os.path.exists("sticker.png"):
                os.remove("sticker.png")
        except Exception:
            pass
            