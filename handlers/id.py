from telethon import events


def register(app):

    @app.on(events.NewMessage(pattern=r"\.id$", outgoing=True))
    async def id_command(event):
        chat_id = event.chat_id

        if event.is_reply:
            reply = await event.get_reply_message()

            user_id = reply.sender_id or "—"
            await event.edit(
                f"**User ID:** `{user_id}`\n"
                f"**Chat ID:** `{chat_id}`"
            )
            return

        await event.edit(f"**Chat ID:** `{chat_id}`")