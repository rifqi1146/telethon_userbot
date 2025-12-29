import os
import re
import json
import time
import html
import base64
import random
import asyncio
from io import BytesIO
from typing import List, Optional

import aiohttp
import pytesseract
from PIL import Image
from bs4 import BeautifulSoup

from telethon import events

from utils.config import get_http_session
from utils.config import OWNER_ID, log
from utils.storage import load_json_file, save_json_file


AI_MODE_FILE = "data/ai_mode.json"
os.makedirs("data", exist_ok=True)

def load_ai_mode():
    return load_json_file(AI_MODE_FILE, {})

def save_ai_mode(data):
    save_json_file(AI_MODE_FILE, data)

AI_MODE = load_ai_mode()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_THINK = "openai/gpt-oss-120b:free"
IMAGE_MODEL = "bytedance-seed/seedream-4.5"

GROQ_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODELS = {
    "flash": "gemini-2.5-flash",
    "pro": "gemini-2.5-pro",
    "lite": "gemini-2.0-flash-lite-001",
}


def split_message(text: str, max_len: int = 4000) -> List[str]:
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]


def sanitize_ai_output(text: str) -> str:
    if not text:
        return ""
    text = html.escape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def ocr_from_file(path: str) -> str:
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
            "model": MODEL_THINK,
            "messages": [
                {"role": "system", "content": "Jawab pakai bahasa Indonesia santai, gen z."},
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
            "model": IMAGE_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "extra_body": {"modalities": ["image"]},
        },
    ) as r:
        data = await r.json()

    images = []
    for img in data.get("choices", [{}])[0].get("message", {}).get("images", []):
        url = img.get("image_url", {}).get("url")
        if url:
            images.append(url)
    return images


async def ask_gemini(prompt: str, model: str):
    session = await get_http_session()
    async with session.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
        json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}]
        },
    ) as r:
        data = await r.json()

    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    return parts[0]["text"] if parts else "Tidak ada jawaban."


def register(app):

    @app.on(events.NewMessage(pattern=r"\.ask(?:\s+(.*))?$", outgoing=True))
    async def ask_handler(event):
        arg = event.pattern_match.group(1)

        if arg and arg.startswith("img"):
            prompt = arg[3:].strip()
            status = await event.edit("🎨 Lagi bikin gambar...")
            try:
                imgs = await openrouter_image(prompt)
                await status.delete()
                for url in imgs:
                    await event.reply(file=url)
            except Exception as e:
                await status.edit(f"❌ {e}")
            return

        prompt = arg
        ocr_text = ""

        if event.is_reply:
            reply = await event.get_reply_message()
            if reply.photo:
                status = await event.edit("👁️ Lagi baca gambar...")
                path = await reply.download_media()
                ocr_text = await ocr_from_file(path)
                os.remove(path)

        if not prompt and not ocr_text:
            return await event.edit("`.ask pertanyaan` atau reply foto lalu `.ask`")

        final_prompt = prompt or ocr_text
        status = await event.edit("🧠 Lagi mikir...")

        try:
            raw = await openrouter_ask(final_prompt)
            clean = sanitize_ai_output(raw)
            chunks = split_message(clean)
            await status.edit(chunks[0])
            for ch in chunks[1:]:
                await event.reply(ch)
        except Exception as e:
            await status.edit(f"❌ {e}")

    @app.on(events.NewMessage(pattern=r"\.ai(?:\s+(.*))?$", outgoing=True))
    async def ai_handler(event):
        arg = event.pattern_match.group(1)
        chat = str(event.chat_id)
        mode = AI_MODE.get(chat, "flash")

        if arg and arg.split()[0] in GEMINI_MODELS:
            mode = arg.split()[0]
            prompt = arg[len(mode):].strip()
        else:
            prompt = arg

        if not prompt:
            return await event.edit("`.ai pertanyaan`")

        status = await event.edit("✨ Lagi mikir...")
        try:
            raw = await ask_gemini(prompt, GEMINI_MODELS[mode])
            clean = sanitize_ai_output(raw)
            chunks = split_message(clean)
            await status.edit(chunks[0])
            for ch in chunks[1:]:
                await event.reply(ch)
        except Exception as e:
            await status.edit(f"❌ {e}")

    @app.on(events.NewMessage(pattern=r"\.setmodeai\s+(flash|pro|lite)$", outgoing=True))
    async def setmode(event):
        chat = str(event.chat_id)
        mode = event.pattern_match.group(1)
        AI_MODE[chat] = mode
        save_ai_mode(AI_MODE)
        await event.edit(f"✅ Default AI diset ke **{mode.upper()}**")
        