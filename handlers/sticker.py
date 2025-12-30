import asyncio
import io
import os
import random
import tempfile
from collections import deque
from pathlib import Path

from PIL import Image
from telethon import events
from telethon.errors import YouBlockedUserError
from telethon.tl import functions, types
from telethon.utils import get_input_document

QUOTLY_BOT = "QuotLyBot"
STICKERS_BOT = "Stickers"
CACHE_LIMIT = 50
WAIT_TIMEOUT = 30

_quotly_cache = deque(maxlen=CACHE_LIMIT)


def register(app):

    async def _is_quotly(event):
        try:
            s = await event.get_sender()
            return s and s.username == QUOTLY_BOT
        except Exception:
            return False

    @app.on(events.NewMessage(incoming=True))
    async def _quotly_listener(event):
        if await _is_quotly(event):
            _quotly_cache.appendleft(event.message)

    def _get_quotly_after(mid):
        return [m for m in reversed(_quotly_cache) if m.id and m.id > mid]

    @app.on(events.NewMessage(pattern=r"\.(q|quotly)(?:\s+(.*))?$", outgoing=True))
    async def quotly(event):
        if not event.is_reply:
            return await event.edit("Reply to a message first.")

        color = (event.pattern_match.group(2) or "").strip()

        try:
            async for m in app.iter_messages(QUOTLY_BOT, limit=1):
                last_id = m.id
                break
            else:
                last_id = 0
        except Exception:
            last_id = 0

        status = await event.edit("✨ Creating quote...")

        try:
            if color:
                await app.send_message(QUOTLY_BOT, f"/q {color}")
                await asyncio.sleep(0.3)
            await event.reply_to_msg_id.forward_to(QUOTLY_BOT)
        except Exception:
            return await status.edit("Failed to send to QuotLy.")

        end = asyncio.get_event_loop().time() + WAIT_TIMEOUT
        while asyncio.get_event_loop().time() < end:
            await asyncio.sleep(0.5)
            res = _get_quotly_after(last_id)
            if res:
                for m in res:
                    await app.copy_message(event.chat_id, QUOTLY_BOT, m.id)
                await status.delete()
                return

        await status.edit("QuotLy timeout.")

    def _resize(src, dst):
        img = Image.open(src).convert("RGBA")
        w, h = img.size
        scale = 512 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        img.save(dst, "WEBP")

    @app.on(events.NewMessage(pattern=r"\.kang(?:\s+(.*))?$", outgoing=True))
    async def kang(event):
        if not event.is_reply:
            return await event.edit("Reply to an image or sticker.")

        emoji = (event.pattern_match.group(1) or "✨").strip()
        status = await event.edit("🧸 Kang-ing...")

        reply = await event.get_reply_message()
        tmp = tempfile.mkdtemp()

        try:
            src = await reply.download_media(file=tmp)
            if not src:
                return await status.edit("Download failed.")

            webp = str(Path(tmp) / "sticker.webp")
            _resize(src, webp)

            me = await app.get_me()
            pack = f"ult_{me.id}_1"
            title = f"{me.first_name}'s Pack"

            async with app.conversation(STICKERS_BOT) as conv:
                try:
                    await conv.send_message("/addsticker")
                except YouBlockedUserError:
                    await app(functions.contacts.UnblockRequest(STICKERS_BOT))
                    await conv.send_message("/addsticker")

                await conv.get_response()
                await conv.send_message(pack)
                rsp = await conv.get_response()

                if "Invalid" in rsp.text:
                    await conv.send_message("/newpack")
                    await conv.get_response()
                    await conv.send_message(title)
                    await conv.get_response()

                await conv.send_file(webp)
                await conv.get_response()
                await conv.send_message(emoji)
                await conv.get_response()
                await conv.send_message("/done")
                await conv.get_response()

            await status.edit(f"✅ Sticker added:\nhttps://t.me/addstickers/{pack}")

        except Exception:
            await status.edit("❌ Failed to kang sticker.")
        finally:
            try:
                for f in Path(tmp).iterdir():
                    f.unlink()
                Path(tmp).rmdir()
            except Exception:
                pass