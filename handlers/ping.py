from telethon import events


def register(app):
    @app.on(events.NewMessage(outgoing=True, pattern=r"\.ping"))
    async def ping_cmd(event):
        start = event.date
        msg = await event.edit("🏓 Pong...")
        end = msg.date

        ms = int((end - start).total_seconds() * 1000)
        await msg.edit(f"⚡ Pong! `{ms} ms`")

