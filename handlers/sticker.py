import os
import shutil
import tempfile
from PIL import Image
from telethon import events
from telethon.errors import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest

STICKERS_BOT = "Stickers"
BASE_SHORTNAME = "kiyoshi"


def resize_png(src, dst):
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    scale = 512 / max(w, h)
    nw, nh = int(w * scale), int(h * scale)
    im = im.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    canvas.paste(im, ((512 - nw) // 2, (512 - nh) // 2))
    canvas.save(dst, "PNG")


def register(app):

    @app.on(events.NewMessage(pattern=r"\.kang$", outgoing=True))
    async def kang(event):
        if not event.is_reply:
            return await event.edit("Reply ke sticker / gambar")

        reply = await event.get_reply_message()
        emoji = "✨"

        is_animated = (
            reply.document
            and reply.document.mime_type == "application/x-tgsticker"
        )

        me = await app.get_me()
        short = f"{BASE_SHORTNAME}_{me.id}"
        if is_animated:
            short += "_vid"

        title = f"{me.first_name}'s Pack"

        tmp = tempfile.mkdtemp(prefix="kang_")

        try:
            if is_animated:
                file_path = await reply.download_media(
                    os.path.join(tmp, "sticker.tgs")
                )
            else:
                raw = await reply.download_media(os.path.join(tmp, "raw"))
                file_path = os.path.join(tmp, "sticker.png")
                resize_png(raw, file_path)

            await event.edit("🧩 Kanging...")

            try:
                async with app.conversation(STICKERS_BOT, timeout=90) as conv:
                    await conv.send_message("/addsticker")
                    await conv.get_response()

                    await conv.send_message(short)
                    r = await conv.get_response()

                    new_pack = False
                    if "Invalid set selected" in r.text:
                        new_pack = True
                        await conv.send_message(
                            "/newanimated" if is_animated else "/newpack"
                        )
                        await conv.get_response()
                        await conv.send_message(title)
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

                        await conv.send_message(short)
                        await conv.get_response()
                    else:
                        await conv.send_message("/done")
                        await conv.get_response()

            except YouBlockedUserError:
                await app(UnblockRequest(STICKERS_BOT))
                return await event.edit("Unblocked @Stickers, ulangi .kang")

            await event.edit(
                f"✅ Sticker added\nhttps://t.me/addstickers/{short}"
            )

        except Exception as e:
            await event.edit(f"❌ Gagal kang sticker\n{e}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)