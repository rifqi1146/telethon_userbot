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
class ColorFormatter(logging.Formatter):
    RESET = "\033[0m"
    COLORS = {
        logging.DEBUG: "\033[90m",     # gray
        logging.INFO: "\033[94m",      # light blue
        logging.WARNING: "\033[93m",   # yellow
        logging.ERROR: "\033[91m",     # red
        logging.CRITICAL: "\033[91m",  # red
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        record.name = f"{color}{record.name}{self.RESET}"
        record.msg = f"{color}{record.msg}{self.RESET}"
        return super().format(record)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    ColorFormatter("%(asctime)s | %(name)s/%(levelname)s | %(message)s")
)

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler],
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


