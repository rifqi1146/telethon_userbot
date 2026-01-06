import os
import re
import json
import time
import html
import base64
import asyncio
from io import BytesIO
from typing import List

import aiohttp
import pytesseract
from PIL import Image
from telethon import events

from utils.config import (
    get_http_session,
    OPENROUTER_API_KEY,
    OPENROUTER_URL,
    OPENROUTER_TEXT_MODEL,
    OPENROUTER_IMAGE_MODEL,
    GROQ_API_KEY,
    GROQ_BASE,
    GROQ_MODEL,
    GROQ_COOLDOWN,
    _GROQ_LAST,
    GEMINI_API_KEY,
    GEMINI_MODELS,
)
    


pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
os.environ["TESSDATA_PREFIX"] = "/usr/share/tesseract-ocr/5/tessdata"


os.makedirs("data", exist_ok=True)
AI_MODE_FILE = "data/ai_mode.json"


def _load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass



AI_MODE = _load_json(AI_MODE_FILE, {})

def split_message(text: str, limit: int = 4000) -> List[str]:
    return [text[i:i + limit] for i in range(0, len(text), limit)]


def sanitize(text: str) -> str:
    if not text:
        return ""
    text = html.escape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def ocr_image(path: str) -> str:
    img = Image.open(path).convert("L")
    img = img.point(lambda x: 0 if x < 160 else 255, "1")
    return await asyncio.to_thread(
        pytesseract.image_to_string,
        img,
        lang="ind+eng",
        config="--psm 6"
    )


async def openrouter_ask(prompt: str) -> str:
    session = await get_http_session()
    async with session.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_TEXT_MODEL,
            "messages": [
                {"role": "system", "content": "Jawab pakai Bahasa Indonesia santai ala gen z. Langsung ke inti."},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=aiohttp.ClientTimeout(total=60),
    ) as r:
        data = await r.json()
    return data["choices"][0]["message"]["content"]


async def openrouter_image(prompt: str) -> List[str]:
    session = await get_http_session()
    async with session.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_IMAGE_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "extra_body": {"modalities": ["image"]},
        },
        timeout=aiohttp.ClientTimeout(total=60),
    ) as r:
        data = await r.json()

    images = []
    for img in data.get("choices", [{}])[0].get("message", {}).get("images", []):
        url = img.get("image_url", {}).get("url")
        if url:
            images.kiyoshiend(url)
    return images


async def gemini_ask(prompt: str, model: str) -> str:
    if not GEMINI_API_KEY:
        return "Gemini API key belum diset."

    session = await get_http_session()
    async with session.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": GEMINI_API_KEY},
        json={"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
        timeout=aiohttp.ClientTimeout(total=60),
    ) as r:
        if r.status != 200:
            return f"Gemini HTTP {r.status}"
        data = await r.json()

    parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts") or []
    texts = [p.get("text") for p in parts if isinstance(p.get("text"), str)]
    return "\n".join(texts).strip() if texts else "Gemini tidak mengirim teks."


def _groq_can(uid: int) -> bool:
    now = time.time()
    if now - _GROQ_LAST.get(uid, 0) < GROQ_COOLDOWN:
        return False
    _GROQ_LAST[uid] = now
    return True


async def groq_ask(prompt: str) -> str:
    session = await get_http_session()
    async with session.post(
        f"{GROQ_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "Jawab pakai Bahasa Indonesia santai ala gen z. Langsung ke inti."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.9,
            "max_tokens": 2048,
        },
        timeout=aiohttp.ClientTimeout(total=45),
    ) as r:
        data = await r.json()
    return data["choices"][0]["message"]["content"]


async def _extract_prompt_with_ocr(event, arg: str, status):
    prompt = arg or ""
    ocr_text = ""

    if event.is_reply:
        reply = await event.get_reply_message()
        if reply and (reply.photo or reply.document):
            await status.edit("🖼️ Lagi baca gambar...")
            path = await reply.download_media()
            if path:
                ocr_text = await ocr_image(path)
                try:
                    os.remove(path)
                except Exception:
                    pass

    if ocr_text and prompt:
        return f"Berikut teks dari gambar:\n\n{ocr_text}\n\nPertanyaan user:\n{prompt}"
    if ocr_text:
        return f"Jelaskan isi teks dari gambar berikut:\n\n{ocr_text}"
    return prompt


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.ask(?:\s+(.*))?$", outgoing=True))
    async def ask_handler(event):
        if not OPENROUTER_API_KEY:
            return await event.edit(
                "❌ <b>OPENROUTER_API_KEY belum diset</b>\n\n"
                "Set dulu di <code>.env</code>:\n"
                "<code>OPENROUTER_API_KEY=your_key_here</code>",
                parse_mode="HTML"
            )

        arg = (event.pattern_match.group(1) or "").strip()

        if not arg and not event.is_reply:
            return await event.edit(
                "❓ <b>Usage</b>\n\n"
                "<code>.ask pertanyaan</code>\n"
                "<code>.ask</code> (reply gambar untuk OCR)\n"
                "<code>.ask img prompt</code> (generate image)",
                parse_mode="HTML"
            )

        status = await event.edit("⏳ Memproses...")

        if arg.startswith("img"):
            await status.edit("🎨 Lagi bikin gambar...")
            images = await openrouter_image(arg[3:].strip())
            await status.delete()
            for img in images:
                await event.reply(file=img)
            return

        final_prompt = await _extract_prompt_with_ocr(event, arg, status)
        if not final_prompt:
            return await status.edit("❌ Teks di gambar tidak terbaca.")

        await status.edit("🧠 Lagi mikir...")
        raw = await openrouter_ask(final_prompt)
        clean = sanitize(raw)
        parts = split_message(clean)
        await status.edit(parts[0])
        for p in parts[1:]:
            await event.reply(p)


    @kiyoshi.on(events.NewMessage(pattern=r"\.ai(?:\s+(.*))?$", outgoing=True))
    async def ai_handler(event):
        arg = (event.pattern_match.group(1) or "").strip()
        chat = str(event.chat_id)
        mode = AI_MODE.get(chat, "flash")

        if not arg and not event.is_reply:
            return await event.edit(
                "❓ <b>Usage</b>\n\n"
                "<code>.ai pertanyaan</code>\n"
                "<code>.ai</code> (reply gambar untuk OCR)\n"
                "<code>.ai flash|pro|lite pertanyaan</code>",
                parse_mode="HTML"
            )

        first = arg.split(maxsplit=1)
        if first and first[0] in GEMINI_MODELS:
            mode = first[0]
            arg = first[1] if len(first) > 1 else ""

        status = await event.edit("⏳ Memproses...")

        final_prompt = await _extract_prompt_with_ocr(event, arg, status)
        if not final_prompt:
            return await status.edit("❌ Teks di gambar tidak terbaca.")

        await status.edit("✨ Lagi mikir...")
        raw = await gemini_ask(final_prompt, GEMINI_MODELS[mode])
        clean = sanitize(raw)
        parts = split_message(clean)
        await status.edit(parts[0])
        for p in parts[1:]:
            await event.reply(p)


    @kiyoshi.on(events.NewMessage(pattern=r"\.groq(?:\s+(.*))?$", outgoing=True))
    async def groq_handler(event):
        if not GROQ_API_KEY:
            return await event.edit("❌ GROQ_API_KEY belum diset.")

        arg = (event.pattern_match.group(1) or "").strip()

        if not arg and not event.is_reply:
            return await event.edit(
                "❓ <b>Usage</b>\n\n"
                "<code>.groq pertanyaan</code>\n"
                "<code>.groq</code> (reply gambar untuk OCR)",
                parse_mode="HTML"
            )

        status = await event.edit("⏳ Memproses...")

        final_prompt = await _extract_prompt_with_ocr(event, arg, status)
        if not final_prompt:
            return await status.edit("❌ Teks di gambar tidak terbaca.")

        uid = event.sender_id or 0
        if uid and not _groq_can(uid):
            return await status.edit("⏳ Tunggu sebentar...")

        await status.edit("⚡ Lagi mikir...")
        raw = await groq_ask(final_prompt)
        clean = sanitize(raw)
        parts = split_message(clean)
        await status.edit(parts[0])
        for p in parts[1:]:
            await event.reply(p)

    @kiyoshi.on(events.NewMessage(pattern=r"\.setmodeai\s+(flash|pro|lite)$", outgoing=True))
    async def setmode_handler(event):
        mode = event.pattern_match.group(1)
        chat = str(event.chat_id)
        AI_MODE[chat] = mode
        _save_json(AI_MODE_FILE, AI_MODE)
        await event.edit(f"✅ Default AI diset ke **{mode.upper()}**")