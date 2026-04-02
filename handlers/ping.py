from telethon import events
import time


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.ping$", outgoing=True))
    async def cmd_ping(event):
        t0 = time.perf_counter()
        msg = await event.edit("Ponging...")
        t1 = time.perf_counter()
        ms = int((t1 - t0) * 1000)
        await msg.edit(f"**Pong!** `{ms} ms`")

