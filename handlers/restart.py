import os
import sys
import asyncio

from telethon import events


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.restart$", outgoing=True))
    async def restart_bot(event):

        FRAMES = [
            "🌸 Rebooting… 0%",
            "🌸💞 Rebooting… 15%",
            "🌸🌈 Rebooting… 40%",
            "🌸✨ Rebooting… 60%",
            "🌸💫 Rebooting… 80%",
            "🌸🔥 Rebooting… 95%",
            "🌸💖 Rebooting… 100%\n\nRestarting userbot…",
        ]

        for frame in FRAMES:
            try:
                await event.edit(frame)
            except Exception:
                pass
            await asyncio.sleep(0.35)

        try:
            await event.edit("Userbot restarting... Please wait.")
        except Exception:
            pass

        os.execl(sys.executable, sys.executable, *sys.argv)
        