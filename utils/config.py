import os
import sys
import logging
from dotenv import load_dotenv
import aiohttp
import asyncio

# load env
load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "sessions/userbot")

if not API_ID or not API_HASH:
    print("API_ID / API_HASH belum diset")
    sys.exit(1)


# logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | Kiyoshi/%(levelname)s | %(message)s"
)

log = logging.getLogger("Kiyoshi")

#http
_HTTP_SESSION: aiohttp.ClientSession | None = None
_HTTP_LOCK = asyncio.Lock()

async def get_http_session() -> aiohttp.ClientSession:
    global _HTTP_SESSION
    async with _HTTP_LOCK:
        if _HTTP_SESSION is None or _HTTP_SESSION.closed:
            _HTTP_SESSION = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            )
        return _HTTP_SESSION

async def close_http_session():
    global _HTTP_SESSION
    if _HTTP_SESSION and not _HTTP_SESSION.closed:
        await _HTTP_SESSION.close()
        _HTTP_SESSION = None

#openrouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_TEXT_MODEL = "openai/gpt-oss-120b:free"
OPENROUTER_IMAGE_MODEL = "bytedance-seed/seedream-4.5"

#groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_COOLDOWN = 2
_GROQ_LAST = {}

#gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODELS = {
    "flash": "gemini-2.5-flash",
    "pro": "gemini-2.5-pro",
    "lite": "gemini-2.0-flash-lite-001",
}

#gsearch
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")