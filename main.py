import asyncio
import random

from utils.startup_banner import send_startup_banner
from telethon import TelegramClient


from utils.config import (
    API_ID,
    API_HASH,
    SESSION_NAME,
    log,
    close_http_session,
)
from handlers import load_handlers


kiyoshi = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH
)

BANNERS = [
        r"""
 ⠀⠀⠀  (≧◡≦) ♡  B O O T   S E Q U E N C E 
   ✦ Initializing system…  
   ✦ Loading cute dependencies…  
   ✦ Activating pastel power cores…  
   ✦ Deploying neko-protocol…  
   Userbot is starting! (๑˃ᴗ˂)ﻭ
        """,
        r"""
 ／l、
（ﾟ､ ｡ ７   < Nya~ Master! Userbot waking up…
  l  ~ヽ       • Loading neko engine  
  じしf_, )     • Warming up whiskers  
               • Injecting kawaii into memory…  
 💖 Ready to serve!
        """,
        r"""
(っ◔◡◔)っ ♥  U S E R B O T   B O O T I N G  ♥

  🍥 Loading chibi modules...
  🍥 Initializing moe-engine...
  🍥 Importing pastel-particle shaders...

  ✨ System Status:         OK
  ✨ Kawaii Protocols:      OK
  ✨ Async Magic:           OK

  ❤️  Userbot is now online — yoroshiku ne~! ❤️
        """,

    ]

def _print_banner():
    """Print a random banner block in clean formatting."""
    try:
        import textwrap
        banner = random.choice(BANNERS).strip("\n")
        wrkiyoshied = "\n".join(
            textwrap.fill(line, width=78, replace_whitespace=False)
            for line in banner.splitlines()
        )
        sep = "═" * 78
        print("\n" + sep)
        print(wrkiyoshied)
        print(sep + "\n")
    except Exception:
        print("Userbot starting... (banner failed)")

async def main():

    _print_banner()
    
    log.info("Starting userbot")
    await kiyoshi.start()

    load_handlers(kiyoshi)
    
    await send_startup_banner(kiyoshi)

    log.info("Userbot ready")
    try:
        await kiyoshi.run_until_disconnected()
    finally:
        log.info("Closing HTTP session")
        await close_http_session()
        log.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Userbot stopped")