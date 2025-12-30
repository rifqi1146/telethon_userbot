import asyncio
import os
import time
import tempfile
import shutil
from collections import deque
from pathlib import Path
from typing import Deque, List, Optional

from PIL import Image
from telethon import events
from telethon.tl import functions, types

# ===== CONFIG =====
QUOTLY_BOT = "QuotLyBot"
POLL_TIMEOUT = 35
POLL_INTERVAL = 0.7
CACHE_SIZE = 60
MAX_QUOTE = 20
DEFAULT_EMOJI = "✨"

# ===== QUOTLY CACHE =====
_quotly_cache: Deque[types.Message] = deque(maxlen=CACHE_SIZE)


def register(app):

    # ---------- QUOTLY CACHE LISTENER ----------
    @app.on(events.NewMessage(from_users=QUOTLY_BOT))
    async def _quotly_listener(event):
        _quotly_cache.appendleft(event.message)

    def _get_cached_after(ts: float) -> List[types.Message]:
        return [
            m for m in _quotly_cache
            if m.date and m.date.timestamp() >= ts
        ]

    # ---------- .q / .quotly ----------
    @app.on(events.NewMessage(pattern=r"\.(q|quotly)(?:\s+(.*))?$", outgoing=True))
    async def quotly_handler(event):
        if not event.is_reply:
            return await event.edit("⚠️ Reply ke pesan dulu.")

        args = (event.pattern_match.group(2) or "").split()
        count = 1
        color = ""

        if args:
            if args[0].isdigit():
                count = min(int(args[0]), MAX_QUOTE)
                color = " ".join(args[1:]) if len(args) > 1 else ""
            else:
                color = " ".join(args)

        status = await event.edit("✨ Creating quote…")

        reply = await event.get_reply_message()
        ids = [reply.id + i for i in range(count)]

        try:
            msgs = await app.get_messages(event.chat_id, ids)
            msgs = [m for m in msgs if m]
        except Exception:
            msgs = [reply]

        ts_start = time.time()

        try:
            if color:
                await app.send_message(QUOTLY_BOT, f"/q {color}")

            for m in msgs:
                await m.forward_to(QUOTLY_BOT)
                await asyncio.sleep(0.2)
        except Exception as e:
            return await status.edit(f"❌ Failed to send: {e}")

        deadline = time.time() + POLL_TIMEOUT
        results = []

        while time.time() < deadline and len(results) < len(msgs):
            await asyncio.sleep(POLL_INTERVAL)
            for m in reversed(_get_cached_after(ts_start)):
                if m.id not in [x.id for x in results]:
                    if m.sticker or m.photo or m.document:
                        results.append(m)
                        if len(results) >= len(msgs):
                            break

        if not results:
            return await status.edit("❌ Timeout dari QuotLyBot.")

        for r in results:
            await app.copy_messages(event.chat_id, QUOTLY_BOT, r.id)
            await asyncio.sleep(0.15)

        await status.delete()

    # ---------- IMAGE → WEBP ----------
    def _to_webp(src: str, dst: str):
        im = Image.open(src).convert("RGBA")
        scale = 512 / max(im.size)
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        im.save(dst, "WEBP", lossless=True)

    # ---------- .kang ----------
    @app.on(events.NewMessage(pattern=r"\.kang(?:\s+(.*))?$", outgoing=True))
    async def kang_handler(event):
        if not event.is_reply:
            return await event.edit("Reply ke image/sticker dulu.")

        args = (event.pattern_match.group(1) or "").split()
        emoji = DEFAULT_EMOJI
        short = None

        if args:
            if len(args) == 1:
                emoji = args[0]
            else:
                short, emoji = args[0], args[1]

        status = await event.edit("✨ Processing sticker…")
        tmp = tempfile.mkdtemp()

        try:
            reply = await event.get_reply_message()
            src = await reply.download_media(tmp)
            webp = os.path.join(tmp, "sticker.webp")

            _to_webp(src, webp)

            me = await app.get_me()
            uname = me.username or "user"
            base = short or f"{uname}_pack"

            for i in range(6):
                name = base if i == 0 else f"{base}_{i}"
                try:
                    await app(functions.stickers.CreateStickerSet(
                        user_id=me.id,
                        title=f"{uname}'s pack",
                        short_name=name,
                        stickers=[types.InputStickerSetItem(
                            document=await app.upload_file(webp),
                            emoji=emoji
                        )]
                    ))
                    return await status.edit(
                        f"✅ Added\nhttps://t.me/addstickers/{name}"
                    )
                except Exception:
                    try:
                        await app(functions.stickers.AddStickerToSet(
                            stickerset=types.InputStickerSetShortName(name),
                            sticker=types.InputStickerSetItem(
                                document=await app.upload_file(webp),
                                emoji=emoji
                            )
                        ))
                        return await status.edit(
                            f"✅ Added\nhttps://t.me/addstickers/{name}"
                        )
                    except Exception:
                        continue

            await status.edit("❌ Failed to kang sticker.")

        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            