import asyncio

from telethon import TelegramClient

from utils.config import API_ID, API_HASH, SESSION_NAME, log
from handlers import load_handlers


# client
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
    await app.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Userbot stopped")

