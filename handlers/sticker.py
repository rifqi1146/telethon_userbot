import os
import io
import asyncio
from PIL import Image
from telethon import events
from telethon.errors import YouBlockedUserError

def _resize_to_sticker(path):
    img = Image.open(path).convert("RGBA")
    max_side = max(img.size)
    scale = 512 / max_side
    new_size = (int(img.width * scale), int(img.height * scale))
    img = img.resize(new_size)
    out = "sticker.png"
    img.save(out)
    return out

def register(app):

    @app.on(events.NewMessage(pattern=r"\.kang(?:\s+(.*))?$", outgoing=True))
    async def kang(event):
        if not event.is_reply:
            return await event.edit("Reply to an image or sticker.")

        reply = await event.get_reply_message()
        status = await event.edit("✨ Processing...")

        try:
            media = await reply.download_media()
        except Exception:
            return await status.edit("Failed to download media.")

        try:
            sticker = _resize_to_sticker(media)
        except Exception:
            return await status.edit("Failed to convert image.")

        emoji = "✨"
        args = event.pattern_match.group(1)
        if args:
            emoji = args.strip()

        try:
            async with app.conversation("Stickers", timeout=60) as conv:
                try:
                    await conv.send_message("/addsticker")
                except YouBlockedUserError:
                    await app.unblock("Stickers")
                    await conv.send_message("/addsticker")

                await conv.get_response()
                me = await app.get_me()
                packname = f"a_{me.id}_by_{me.username or 'kiyoshi'}"
                await conv.send_message(packname)
                resp = await conv.get_response()

                if "Invalid set selected" in resp.text:
                    await conv.send_message("/newpack")
                    await conv.get_response()
                    await conv.send_message(f"{me.first_name}'s Pack")
                    await conv.get_response()

                await conv.send_file(sticker)
                await conv.get_response()
                await conv.send_message(emoji)
                await conv.get_response()
                await conv.send_message("/done")
                await conv.get_response()

        except Exception as e:
            return await status.edit(f"Kang failed: {e}")

        await status.edit(f"✅ Sticker added:\nhttps://t.me/addstickers/{packname}")

        try:
            os.remove(media)
            os.remove(sticker)
        except Exception:
            pass
            