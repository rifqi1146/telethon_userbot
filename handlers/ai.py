import os
import re
import json
import time
import html
import base64
import random
import asyncio
from io import BytesIO
from typing import List

import aiohttp
import pytesseract
from PIL import Image
from bs4 import BeautifulSoup

from telethon import events

from utils.config import get_http_session


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


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_TEXT_MODEL = "openai/gpt-oss-120b:free"
OPENROUTER_IMAGE_MODEL = "bytedance-seed/seedream-4.5"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_COOLDOWN = 2
_GROQ_LAST = {}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODELS = {
    "flash": "gemini-2.5-flash",
    "pro": "gemini-2.5-pro",
    "lite": "gemini-2.0-flash-lite-001",
}


def split_message(text: str, limit: int = 4000) -> List[str]:
    return [text[i:i + limit] for i in range(0, len(text), limit)]


def sanitize(text: str) -> str:
    if not text:
        return ""
    text = html.escape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def ocr_image(path: str) -> str:
    img = Image.open(path).convert("RGB")
    return await asyncio.to_thread(
        pytesseract.image_to_string,
        img,
        lang="ind+eng"
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
                {
                    "role": "system",
                    "content": "Jawab pakai Bahasa Indonesia santai ala gen z. Langsung ke inti."
                },
                {
                    "role": "user",
                    "content": prompt
                }
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
            "extra_body": {"modalities": ["image"]}
        },
        timeout=aiohttp.ClientTimeout(total=60),
    ) as r:
        data = await r.json()

    images = []
    for img in data.get("choices", [{}])[0].get("message", {}).get("images", []):
        url = img.get("image_url", {}).get("url")
        if url:
            images.append(url)
    return images


async def gemini_ask(prompt: str, model: str) -> str:
    session = await get_http_session()
    async with session.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ]
        },
        timeout=aiohttp.ClientTimeout(total=60),
    ) as r:
        if r.status != 200:
            return f"Gemini HTTP {r.status}"

        data = await r.json()

    candidates = data.get("candidates")
    if not candidates:
        return "Gemini tidak mengembalikan jawaban."

    content = candidates[0].get("content")
    if not content:
        return "Gemini response kosong."

    parts = content.get("parts")
    if not parts:
        return "Gemini tidak mengirim teks."

    texts = []
    for p in parts:
        t = p.get("text")
        if isinstance(t, str):
            texts.append(t)

    if not texts:
        return "Gemini tidak mengirim teks."

    return "\n".join(texts).strip()


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
                {
                    "role": "system",
                    "content": "Jawab pakai Bahasa Indonesia santai ala gen z. Langsung ke inti."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.9,
            "max_tokens": 2048,
        },
        timeout=aiohttp.ClientTimeout(total=45),
    ) as r:
        data = await r.json()

    return data["choices"][0]["message"]["content"]


def register(app):

    @app.on(events.NewMessage(pattern=r"\.ask(?:\s+(.*))?$", outgoing=True))
    async def ask_handler(event):
        arg = event.pattern_match.group(1)

        if arg and arg.startswith("img"):
            prompt = arg[3:].strip()
            if not prompt:
                return await event.edit("`.ask img deskripsi_gambar`")
            status = await event.edit("🎨 Lagi bikin gambar...")
            try:
                images = await openrouter_image(prompt)
                await status.delete()
                for img in images:
                    if img.startswith("data:image"):
                        header, encoded = img.split(",", 1)
                        bio = BytesIO(base64.b64decode(encoded))
                        bio.seek(0)
                        await event.reply(file=bio)
                    else:
                        await event.reply(file=img)
            except Exception as e:
                await status.edit(f"❌ {e}")
            return

        prompt = arg or ""
        ocr_text = ""

        if event.is_reply:
            reply = await event.get_reply_message()
            if reply and reply.photo:
                status = await event.edit("👁️ Lagi baca gambar...")
                path = await reply.download_media()
                ocr_text = await ocr_image(path)
                try:
                    os.remove(path)
                except Exception:
                    pass

        if not prompt and not ocr_text:
            return await event.edit("`.ask pertanyaan` atau reply foto lalu `.ask`")

        final_prompt = prompt or ocr_text
        status = await event.edit("🧠 Lagi mikir...")

        try:
            raw = await openrouter_ask(final_prompt)
            clean = sanitize(raw)
            parts = split_message(clean)
            await status.edit(parts[0])
            for p in parts[1:]:
                await event.reply(p)
        except Exception as e:
            await status.edit(f"❌ {e}")

    @app.on(events.NewMessage(pattern=r"\.ai(?:\s+(.*))?$", outgoing=True))
    async def ai_handler(event):
        arg = event.pattern_match.group(1) or ""
        chat = str(event.chat_id)
        mode = AI_MODE.get(chat, "flash")

        first = arg.split(maxsplit=1)
        if first and first[0] in GEMINI_MODELS:
            mode = first[0]
            prompt = first[1] if len(first) > 1 else ""
        else:
            prompt = arg

        if not prompt:
            return await event.edit("`.ai pertanyaan`")

        status = await event.edit("✨ Lagi mikir...")
        try:
            raw = await gemini_ask(prompt, GEMINI_MODELS[mode])
            clean = sanitize(raw)
            parts = split_message(clean)
            await status.edit(parts[0])
            for p in parts[1:]:
                await event.reply(p)
        except Exception as e:
            await status.edit(f"❌ {e}")

    @app.on(events.NewMessage(pattern=r"\.setmodeai\s+(flash|pro|lite)$", outgoing=True))
    async def setmode_handler(event):
        mode = event.pattern_match.group(1)
        chat = str(event.chat_id)
        AI_MODE[chat] = mode
        _save_json(AI_MODE_FILE, AI_MODE)
        await event.edit(f"✅ Default AI diset ke **{mode.upper()}**")

    @app.on(events.NewMessage(pattern=r"\.groq(?:\s+(.*))?$", outgoing=True))
    async def groq_handler(event):
        if not GROQ_API_KEY:
            return await event.edit("❌ GROQ_API_KEY belum diset.")

        prompt = event.pattern_match.group(1)

        if not prompt and event.is_reply:
            reply = await event.get_reply_message()
            prompt = reply.text or reply.caption

        if not prompt:
            return await event.edit("`.groq pertanyaan`")

        uid = event.sender_id or 0
        if uid and not _groq_can(uid):
            return await event.edit("⏳ Santai dulu~")

        status = await event.edit("⚡ Lagi mikir (Groq)...")

        try:
            raw = await groq_ask(prompt)
            clean = sanitize(raw)
            parts = split_message(clean)
            await status.edit(parts[0])
            for p in parts[1:]:
                await event.reply(p)
        except Exception as e:
            await status.edit(f"❌ {e}")