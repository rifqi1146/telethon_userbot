import os
import asyncio
import shutil
import tempfile
from PIL import Image
from telethon import events
from telethon.errors import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest

STICKERS_BOT = "Stickers"
BASE_SHORTNAME = "kiyoshi"


def resize_to_png(src, dst):
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    scale = 512 / max(w, h)
    nw, nh = int(w * scale), int(h * scale)
    im = im.resize((nw, nh), Image.LANCZOS)
    out = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    out.paste(im, ((512 - nw) // 2, (512 - nh) // 2))
    out.save(dst, "PNG")


def register(app):

    @app.on(events.NewMessage(pattern=r"\.kang$", outgoing=True))
    async def kang_handler(event):
        if not event.is_reply:
            return await event.edit("Reply ke sticker atau gambar")

        reply = await event.get_reply_message()
        emoji = "✨"

        args = event.raw_text.split()
        if len(args) > 1:
            emoji = args[1]

        is_animated = bool(
            reply.document
            and reply.document.mime_type == "application/x-tgsticker"
        )

        me = await app.get_me()
        uid = me.id

        shortname = f"{BASE_SHORTNAME}_{uid}"
        if is_animated:
            shortname = f"{shortname}_vid"

        pack_title = f"{me.first_name}'s Pack"

        tmp = tempfile.mkdtemp(prefix="kang_")

        try:
            if is_animated:
                file_path = await reply.download_media(
                    file=os.path.join(tmp, "sticker.tgs")
                )
            else:
                raw = await reply.download_media(
                    file=os.path.join(tmp, "raw")
                )
                file_path = os.path.join(tmp, "sticker.png")
                resize_to_png(raw, file_path)

            await event.edit("🧩 Kanging sticker...")

            try:
                await app.send_message(STICKERS_BOT, "/addsticker")
            except YouBlockedUserError:
                await app(UnblockRequest(STICKERS_BOT))
                await app.send_message(STICKERS_BOT, "/addsticker")

            async with app.conversation(STICKERS_BOT, timeout=60) as conv:
                await conv.get_response()
                await conv.send_message(shortname)
                r = await conv.get_response()

                new_pack = False
                if "Invalid set selected" in r.text:
                    new_pack = True
                    await conv.send_message(
                        "/newanimated" if is_animated else "/newpack"
                    )
                    await conv.get_response()
                    await conv.send_message(pack_title)
                    await conv.get_response()

                await conv.send_file(file_path, force_document=True)
                await conv.get_response()
                await conv.send_message(emoji)
                await conv.get_response()

                if new_pack:
                    await conv.send_message("/publish")
                    await conv.get_response()
                    if not is_animated:
                        await conv.send_message("/skip")
                        await conv.get_response()
                    await conv.send_message(shortname)
                    await conv.get_response()
                else:
                    await conv.send_message("/done")
                    await conv.get_response()

            await event.edit(
                f"✅ Sticker added\nhttps://t.me/addstickers/{shortname}"
            )

        except Exception as e:
            await event.edit(f"❌ Gagal kang sticker\n{e}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)