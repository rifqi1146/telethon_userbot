import os
import time
import socket
import getpass
import platform

import telethon
import psutil

from utils.config import log

STARTUP_CHAT_ID = os.getenv("STARTUP_CHAT_ID")
BANNER_PATH = "assets/banner.png"


def _bytes_to_mb(value):
    return round(value / 1024 / 1024, 2)


def _system_info():
    cpu_usage = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()

    return {
        "cpu": f"{cpu_usage}%",
        "ram_used": f"{_bytes_to_mb(mem.used)} MB",
        "ram_total": f"{_bytes_to_mb(mem.total)} MB",
        "hostname": socket.gethostname(),
        "user": getpass.getuser(),
        "os": f"{platform.system()} {platform.release()}",
        "arch": platform.machine(),
        "python": platform.python_version(),
        "telethon": telethon.__version__,
    }


async def send_startup_banner(kiyoshi):
    if not STARTUP_CHAT_ID:
        log.warning("STARTUP_CHAT_ID not set, skip startup banner")
        return

    if not os.path.exists(BANNER_PATH):
        log.warning("startup banner not found, skip")
        return

    try:
        chat = await kiyoshi.get_entity(int(STARTUP_CHAT_ID))
    except Exception as e:
        log.warning(f"Cannot resolve STARTUP_CHAT_ID: {e}")
        return

    info = _system_info()
    started_at = time.strftime("%Y-%m-%d %H:%M:%S")

    caption = (
        "💦 **Userbot Deployed**\n"
        "👻 **Status**: Online\n"
        f"🕒 **Started at**: `{started_at}`\n\n"
        "🖥 **System Info**\n"
        f"• Hostname: `{info['hostname']}`\n"
        f"• User: `{info['user']}`\n"
        f"• OS: `{info['os']}`\n"
        f"• Arch: `{info['arch']}`\n"
        f"• CPU Usage: `{info['cpu']}`\n"
        f"• RAM: `{info['ram_used']} / {info['ram_total']}`\n"
        f"• Python: `{info['python']}`\n"
        f"• Telethon: `{info['telethon']}`\n"
        "• Prefix: `.`\n\n"
        "🌸 **Powered by Kiyoshi Userbot**"
    )

    try:
        await kiyoshi.send_file(
            chat,
            BANNER_PATH,
            caption=caption,
        )
        log.info("Startup banner successfully")
    except Exception as e:
        log.warning(f"Failed to send startup banner: {e}")
        