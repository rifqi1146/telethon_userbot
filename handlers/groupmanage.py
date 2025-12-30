from telethon import events
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.tl.functions.channels import EditTitleRequest

chat_titles = {}


async def is_admin(app, chat_id: int, user_id: int) -> bool:
    try:
        async for user in app.iter_participants(
            chat_id,
            filter=ChannelParticipantsAdmins
        ):
            if user.id == user_id:
                return True
        return False
    except Exception:
        return False


def register(app):

    @app.on(events.NewMessage(pattern=r"\.settitle(?:\s+(.*))?$", outgoing=True))
    async def set_title(event):
        if not event.is_group:
            return await event.edit("This command can only be used in groups.")

        if not await is_admin(app, event.chat_id, (await app.get_me()).id):
            return await event.edit("I'm not an admin here.")

        title = event.pattern_match.group(1)
        if not title:
            return await event.edit("Provide a title to set.")

        try:
            chat = await event.get_chat()
            if event.chat_id not in chat_titles:
                chat_titles[event.chat_id] = chat.title

            await app(EditTitleRequest(event.chat_id, title))
            await event.edit(f"**Chat title changed to:** {title}")
        except Exception as e:
            await event.edit(f"**Error:** {e}")

    @app.on(events.NewMessage(pattern=r"\.restoretitle$", outgoing=True))
    async def restore_title(event):
        if not event.is_group:
            return await event.edit("This command can only be used in groups.")

        if not await is_admin(app, event.chat_id, (await app.get_me()).id):
            return await event.edit("I'm not an admin here.")

        if event.chat_id not in chat_titles:
            return await event.edit("No original title stored for this chat.")

        try:
            original = chat_titles.pop(event.chat_id)
            await app(EditTitleRequest(event.chat_id, original))
            await event.edit(f"**Chat title restored to:** {original}")
        except Exception as e:
            await event.edit(f"**Error:** {e}")

    @app.on(events.NewMessage(pattern=r"\.stats$", outgoing=True))
    async def chat_stats(event):
        if not event.is_group:
            return await event.edit("This command can only be used in groups.")

        try:
            chat = await event.get_chat()
        except Exception as e:
            return await event.edit(f"Failed to fetch chat info: {e}")

        try:
            members = await app.get_participants(event.chat_id)
            members_count = len(members)
        except Exception:
            members_count = "—"

        try:
            admins_count = 0
            async for _ in app.iter_participants(
                event.chat_id,
                filter=ChannelParticipantsAdmins
            ):
                admins_count += 1
        except Exception:
            admins_count = "—"

        text = (
            "📊 **CHAT STATS**\n\n"
            f"🏷️ Title   : {chat.title or '—'}\n"
            f"🆔 ID      : {chat.id}\n"
            f"👥 Members : {members_count}\n"
            f"👮 Admins  : {admins_count}\n"
            f"🧭 Type    : {'Supergroup' if chat.megagroup else 'Group'}"
        )

        await event.edit(text)

    @app.on(events.NewMessage(pattern=r"\.admins$", outgoing=True))
    async def list_admins(event):
        if not event.is_group:
            return await event.edit("This command can only be used in groups.")

        try:
            admins = []
            async for user in app.iter_participants(
                event.chat_id,
                filter=ChannelParticipantsAdmins
            ):
                if user.bot:
                    continue
                name = user.first_name or "No Name"
                admins.append(f"• 👑 [{name}](tg://user?id={user.id})")

            if not admins:
                return await event.edit("No administrators found.")

            text = (
                "📜 **Group Administrators**\n"
                "———————————————\n"
                f"{chr(10).join(admins)}\n"
                "———————————————\n"
                f"📝 Total admins: **{len(admins)}**"
            )

            await event.edit(text, link_preview=False)
        except Exception as e:
            await event.edit(f"Error: {e}")
            