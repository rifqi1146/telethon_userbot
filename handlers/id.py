from telethon import events


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.id(?:\s+(.*))?$", outgoing=True))
    async def id_command(event):
        chat_id = event.chat_id
        arg = (event.pattern_match.group(1) or "").strip()

        user_id = None

        if event.is_reply:
            reply = await event.get_reply_message()
            user_id = reply.sender_id if reply else None

        elif arg:
            a = arg.lstrip("@")
            try:
                if a.isdigit():
                    user_id = int(a)
                else:
                    ent = await kiyoshi.get_entity(a)
                    user_id = ent.id
            except Exception:
                return await event.edit("❌ User tidak ditemukan.")

        if user_id:
            await event.edit(
                f"**User ID:** `{user_id}`\n"
                f"**Chat ID:** `{chat_id}`"
            )
        else:
            await event.edit(f"**Chat ID:** `{chat_id}`")