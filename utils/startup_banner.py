import os
import time
from utils.config import log

STARTUP_CHAT_ID = os.getenv("STARTUP_CHAT_ID")


async def send_startup_banner(app):
    if not STARTUP_CHAT_ID:
        log.warning("STARTUP_CHAT_ID not set, skip startup banner")
        return

    banner_path = "assets/startup.png"
    if not os.path.exists(banner_path):
        log.warning("startup.png not found, skip startup banner")
        return

    caption = (
        "✨ <b>Userbot Deployed</b>\n"
        "🚀 Status: <b>Online</b>\n"
        f"🕒 Started at: <code>{time.strftime('%Y-%m-%d %H:%M:%S')}</code>"
    )

    try:
        await app.send_file(
            STARTUP_CHAT_ID,
            banner_path,
            caption=caption,
            parse_mode="HTML",
        )
        log.info("Startup banner sent")
    except Exception as e:
        log.warning(f"Failed to send startup banner: {e}")
        