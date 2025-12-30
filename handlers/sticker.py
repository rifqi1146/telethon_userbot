import asyncio
import os
import time
import shutil
import tempfile
from pathlib import Path
from collections import deque
from typing import Optional, List

from PIL import Image
from telethon import events, utils
from telethon.tl import functions, types
from telethon.tl.functions.messages import UploadMediaRequest
from telethon.tl.types import InputPeerSelf

BOT_USERNAME = "QuotLyBot"
POLL_TIMEOUT = 35.0
POLL_INTERVAL = 0.7
BOT_CACHE_SIZE = 60
MAX_QUOTE_COUNT = 20
SHORTNAME_MAX_TRIES = 6
STICKER_EMOJI_DEFAULT = "✨"

_last_from_quotly = deque(maxlen=BOT_CACHE_SIZE)


def _safe_shortname_candidate(base: str) -> str:
    s = base.lower()
    s = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in s)
    while "__" in s:
        s = s.replace("__", "_")
    if not s or not s[0].isalpha():
        s = "a" + s
    return s[:48]


def _resize_image_to_webp(input_path: str, output_path: str):
    im = Image.open(input_path).convert("RGBA")
    m = max(im.width, im.height)
    if m != 512:
        s = 512 / float(m)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    im.save(output_path, "WEBP", lossless=True, quality=100, method=6)


async def _upload_and_get_inputdocument(app, file_path: str):
    file = await app.upload_file(file_path)
    res = await app(
        UploadMediaRequest(
            peer=InputPeerSelf(),
            media=types.InputMediaUploadedDocument(
                file=file,
                mime_type="image/webp",
                attributes=[types.DocumentAttributeFilename("sticker.webp")],
            ),
        )
    )
    return res.document


def _find_cached_after(ts: float, only_types: Optional[List[str]] = None):
    out = []
    for msg in _last_from_quotly:
        try:
            if msg.date.timestamp() >= ts:
                if only_types:
                    ok = False
                    if "sticker" in only_types and msg.sticker:
                        ok = True
                    if "photo" in only_types and msg.photo:
                        ok = True
                    if "document" in only_types and msg.document:
                        ok = True
                    if not ok:
                        continue
                out.append(msg)
        except Exception:
            continue
    return out


def register(app):

    @app.on(events.NewMessage(from_users=BOT_USERNAME))
    async def quotly_listener(event):
        _last_from_quotly.appendleft(event.message)

    @app.on(events.NewMessage(pattern=r"\.(q|quotly)(?:\s+(.*))?$", outgoing=True))
    async def quotly(event):
        if not event.is_reply:
            return await event.edit("Reply ke pesan dulu.")

        parts = (event.raw_text or "").split()
        count = 1
        color = " "
        if len(parts) >= 2:
            if parts[1].isdigit():
                count = int(parts[1])
                if len(parts) >= 3:
                    color = " ".join(parts[2:])
            else:
                color = " ".join(parts[1:])

        count = max(1, min(count, MAX_QUOTE_COUNT))
        reply = await event.get_reply_message()
        status = await event.edit("✨ Membuat quote")

        msgs = []
        try:
            base = reply.id
            ids = [base + i for i in range(count)]
            fetched = await app.get_messages(event.chat_id, ids)
            if not isinstance(fetched, list):
                fetched = [fetched]
            msgs = [m for m in fetched if m]
        except Exception:
            msgs = [reply]

        ts = time.time()

        try:
            await app.send_message(BOT_USERNAME, f"/q {color}")
            for m in msgs:
                await m.forward_to(BOT_USERNAME)
                await asyncio.sleep(0.18)
        except Exception as e:
            return await status.edit(f"❌ Gagal kirim ke QuotLy: {e}")

        deadline = time.time() + POLL_TIMEOUT
        collected = []
        seen = set()

        while time.time() < deadline and len(collected) < len(msgs):
            await asyncio.sleep(POLL_INTERVAL)
            cand = _find_cached_after(ts, ["sticker", "photo", "document"])
            for c in reversed(cand):
                if c.id in seen:
                    continue
                collected.append(c)
                seen.add(c.id)
                if len(collected) >= len(msgs):
                    break

        if not collected:
            return await status.edit("❌ QuotLy timeout.")

        for r in collected:
            await app.copy_message(event.chat_id, BOT_USERNAME, r.id)
            await asyncio.sleep(0.12)

        await status.delete()

    @app.on(events.NewMessage(pattern=r"\.kang(?:\s+(.*))?$", outgoing=True))
    async def kang(event):
        if not event.is_reply:
            return await event.edit("Reply ke gambar / sticker.")

        args = (event.raw_text or "").split()[1:]
        emoji = STICKER_EMOJI_DEFAULT
        custom = None

        if args:
            if len(args) == 1:
                if len(args[0]) <= 3:
                    emoji = args[0]
                else:
                    custom = args[0]
            else:
                custom = args[0]
                emoji = args[1]

        status = await event.edit("✨ Processing...")
        reply = await event.get_reply_message()
        tmp = tempfile.mkdtemp(prefix="kang_")

        try:
            src = await reply.download_media(file=tmp)
            if os.path.isdir(src):
                files = [os.path.join(src, f) for f in os.listdir(src)]
                files.sort(key=os.path.getsize, reverse=True)
                src = files[0]

            webp = str(Path(tmp) / "sticker.webp")
            _resize_image_to_webp(src, webp)

            me = await app.get_me()
            uname = (me.username or me.first_name or "user").strip()
            base = _safe_shortname_candidate(custom or f"{uname}_pack")

            doc = await _upload_and_get_inputdocument(app, webp)

            success = False
            chosen = None

            for i in range(SHORTNAME_MAX_TRIES):
                name = base if i == 0 else f"{base}_{i}"
                try:
                    await app(functions.stickers.AddStickerToSet(
                        stickerset=types.InputStickerSetShortName(name),
                        sticker=types.InputStickerSetItem(document=doc, emoji=emoji)
                    ))
                    chosen = name
                    success = True
                    break
                except Exception:
                    try:
                        await app(functions.stickers.CreateStickerSet(
                            user_id=me.id,
                            title=f"{uname}'s pack",
                            short_name=name,
                            stickers=[types.InputStickerSetItem(document=doc, emoji=emoji)],
                        ))
                        chosen = name
                        success = True
                        break
                    except Exception:
                        continue

            if not success:
                return await status.edit("❌ Gagal kang sticker.")

            await status.edit(f"✅ https://t.me/addstickers/{chosen}")

        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            