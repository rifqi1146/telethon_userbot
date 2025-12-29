import asyncio

from telethon import TelegramClient

from utils.config import (
    API_ID,
    API_HASH,
    SESSION_NAME,
    log,
    close_http_session,
)
from handlers import load_handlers


app = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH
)


async def main():
    log.info("Starting userbot")
    await app.start()

    load_handlers(app)

    log.info("Userbot ready")
    try:
        await app.run_until_disconnected()
    finally:
        log.info("Closing HTTP session")
        await close_http_session()
        log.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Userbot stopped")