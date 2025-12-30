import os
import io
import asyncio
import tempfile
from pathlib import Path
from PIL import Image

from telethon import events
from telethon.errors import YouBlockedUserError
from telethon.tl.types import DocumentAttributeSticker


def register(app):

    @app.on(events.NewMessage(pattern=r"\.kang$", outgoing=True))
    async def kang(event):
        if not event.is_reply:
            return await event.edit("Reply ke sticker / gambar.")

        reply = await event.get_reply_message()
        status = await event.edit("🧩 Processing...")

        tmpdir = tempfile.mkdtemp(prefix="kang_")
        file_path = None
        is_animated = False
        emoji = "✨"

        try:
            if reply.sticker:
                for attr in reply.document.attributes:
                    if isinstance(attr, DocumentAttributeSticker):
                        emoji = attr.alt or emoji
                if reply.document.mime_type == "application/x-tgsticker":
                    is_animated = True
                file_path = await reply.download_media(file=tmpdir)

            elif reply.photo or (reply.document and reply.document.mime_type.startswith("image")):
                file_path = await reply.download_media(file=tmpdir)

            else:
                return await status.edit("Media tidak didukung.")

            if not is_animated:
                img = Image.open(file_path).convert("RGBA")
                max_side = max(img.width, img.height)
                scale = 512 / max_side
                img = img.resize(
                    (int(img.width * scale), int(img.height * scale)),
                    Image.LANCZOS
                )
                png_path = Path(tmpdir) / "sticker.png"
                img.save(png_path, "PNG")
                file_path = str(png_path)

            me = await app.get_me()
            shortname = f"kiyoshi_{me.id}"
            packname = f"{me.first_name}'s Pack"

            async with app.conversation("Stickers", timeout=120) as conv:
                try:
                    await conv.send_message("/addsticker")
                except YouBlockedUserError:
                    await app.unblock_user("Stickers")
                    await conv.send_message("/addsticker")

                await conv.get_response()
                await conv.send_message(shortname)
                r = await conv.get_response()

                if "Invalid set selected" in r.text:
                    await conv.send_message("/newanimated" if is_animated else "/newpack")
                    await conv.get_response()
                    await conv.send_message(packname)
                    await conv.get_response()

                await conv.send_file(file_path, force_document=True)
                await conv.get_response()

                await conv.send_message(emoji)
                await conv.get_response()

                await conv.send_message("/publish")
                await conv.get_response()

                if not is_animated:
                    await conv.send_message("/skip")
                    await conv.get_response()

                await conv.send_message(shortname)
                await conv.get_response()

            await status.edit(f"✅ Sticker added\nhttps://t.me/addstickers/{shortname}")

        except Exception as e:
            await status.edit(f"❌ Failed to kang sticker.\n{e}")

        finally:
            try:
                for f in os.listdir(tmpdir):
                    os.remove(os.path.join(tmpdir, f))
                os.rmdir(tmpdir)
            except Exception:
                pass