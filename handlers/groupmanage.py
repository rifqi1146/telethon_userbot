import asyncio
from telethon import events
from telethon.errors import FloodWaitError
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.tl.functions.channels import EditTitleRequest
from telethon.tl.functions.messages import UpdatePinnedMessageRequest

chat_titles = {}

def _get_topic_id(msg):
    try:
        reply = getattr(msg, "reply_to", None)
        if reply:
            return getattr(reply, "reply_to_top_id", None)
    except Exception:
        pass
    return None

async def is_admin(kiyoshi, chat_id: int, user_id: int) -> bool:
    try:
        async for user in kiyoshi.iter_participants(
            chat_id,
            filter=ChannelParticipantsAdmins
        ):
            if user.id == user_id:
                return True
        return False
    except Exception:
        return False


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.settitle(?:\s+(.*))?$", outgoing=True))
    async def set_title(event):
        if not event.is_group:
            return await event.edit("This command can only be used in groups.")

        me = await kiyoshi.get_me()
        if not await is_admin(kiyoshi, event.chat_id, me.id):
            return await event.edit("I'm not an admin here.")

        title = event.pattern_match.group(1)
        if not title:
            return await event.edit("Provide a title to set.")

        try:
            chat = await event.get_chat()
            if event.chat_id not in chat_titles:
                chat_titles[event.chat_id] = chat.title

            await kiyoshi(EditTitleRequest(event.chat_id, title))
            await event.edit(f"**Chat title changed to:** {title}")
        except Exception as e:
            await event.edit(f"Error: {e}")

    @kiyoshi.on(events.NewMessage(pattern=r"\.restoretitle$", outgoing=True))
    async def restore_title(event):
        if not event.is_group:
            return await event.edit("This command can only be used in groups.")

        me = await kiyoshi.get_me()
        if not await is_admin(kiyoshi, event.chat_id, me.id):
            return await event.edit("I'm not an admin here.")

        if event.chat_id not in chat_titles:
            return await event.edit("No original title stored for this chat.")

        try:
            original = chat_titles.pop(event.chat_id)
            await kiyoshi(EditTitleRequest(event.chat_id, original))
            await event.edit(f"**Chat title restored to:** {original}")
        except Exception as e:
            await event.edit(f"Error: {e}")

    @kiyoshi.on(events.NewMessage(pattern=r"\.stats$", outgoing=True))
    async def chat_stats(event):
        if not event.is_group:
            return await event.edit("This command can only be used in groups.")

        try:
            chat = await event.get_chat()
        except Exception as e:
            return await event.edit(f"Failed to fetch chat info: {e}")

        try:
            members = await kiyoshi.get_participants(event.chat_id)
            members_count = len(members)
        except Exception:
            members_count = "—"

        try:
            admins_count = 0
            async for _ in kiyoshi.iter_participants(
                event.chat_id,
                filter=ChannelParticipantsAdmins
            ):
                admins_count += 1
        except Exception:
            admins_count = "—"

        text = (
            "**CHAT STATS**\n\n"
            f"🏷️ Title   : {chat.title or '—'}\n"
            f"🆔 ID      : {chat.id}\n"
            f"👥 Members : {members_count}\n"
            f"👮 Admins  : {admins_count}\n"
            f"🧭 Type    : {'Supergroup' if chat.megagroup else 'Group'}"
        )

        await event.edit(text)

    @kiyoshi.on(events.NewMessage(pattern=r"\.admins$", outgoing=True))
    async def list_admins(event):
        if not event.is_group:
            return await event.edit("This command can only be used in groups.")

        try:
            admins = []
            async for user in kiyoshi.iter_participants(
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

    @kiyoshi.on(events.NewMessage(pattern=r"^[./]purge$", outgoing=True))
    async def purge(event):
        if not event.is_group:
            return await event.edit("This command can only be used in groups.")
    
        me = await kiyoshi.get_me()
        if not await is_admin(kiyoshi, event.chat_id, me.id):
            return await event.edit("I'm not an admin here.")
    
        if not event.is_reply:
            return await event.edit("Reply to a message to start purging from.")
    
        start_id = event.reply_to_msg_id
        end_id = event.id
        topic_id = _get_topic_id(event.message)
    
        try:
            messages = await kiyoshi.get_messages(
                event.chat_id,
                None,
                min_id=start_id - 1,
                max_id=end_id,
            )
        except Exception as e:
            return await event.edit(f"Failed to collect messages.\nError: {e}")
    
        ids_to_delete = []
        for msg in messages:
            if not msg:
                continue
    
            if topic_id:
                msg_topic_id = _get_topic_id(msg)
                if msg.id != topic_id and msg_topic_id != topic_id:
                    continue
    
            ids_to_delete.append(msg.id)
    
        if not ids_to_delete:
            return await event.edit("No messages found to purge.")
    
        try:
            await kiyoshi.delete_messages(event.chat_id, ids_to_delete)
            msg = await event.edit(f"Purged {len(ids_to_delete)} messages.")
            await asyncio.sleep(1)
            await msg.delete()
        except FloodWaitError as e:
            await event.edit(f"Flood wait: {e.seconds}s")
        except Exception as e:
            await event.edit(f"Failed to purge messages.\nError: {e}")

    @kiyoshi.on(events.NewMessage(pattern=r"\.del$", outgoing=True))
    async def delete_message(event):
        if not event.is_reply:
            return await event.edit("Reply to a message to delete.")

        try:
            await kiyoshi.delete_messages(
                event.chat_id,
                [event.reply_to_msg_id, event.id]
            )
        except Exception as e:
            await event.edit(f"Error: {e}")

    @kiyoshi.on(events.NewMessage(pattern=r"\.pin$", outgoing=True))
    async def pin_message(event):
        if not event.is_group:
            return await event.edit("This command can only be used in groups.")

        if not event.is_reply:
            return await event.edit("Reply to a message to pin.")

        me = await kiyoshi.get_me()
        if not await is_admin(kiyoshi, event.chat_id, me.id):
            return await event.edit("I'm not an admin here.")

        try:
            await kiyoshi(
                UpdatePinnedMessageRequest(
                    peer=event.chat_id,
                    id=event.reply_to_msg_id,
                    silent=False
                )
            )
            await event.edit("📌 **Pinned!**")
        except Exception as e:
            await event.edit(f"Failed to pin: {e}")

    @kiyoshi.on(events.NewMessage(pattern=r"\.unpin$", outgoing=True))
    async def unpin_message(event):
        if not event.is_group:
            return await event.edit("This command can only be used in groups.")
            
        if not event.is_reply:
            return await event.edit("Reply to the pinned message to unpin.")

        me = await kiyoshi.get_me()
        if not await is_admin(kiyoshi, event.chat_id, me.id):
            return await event.edit("I'm not an admin here.")

        try:
            await kiyoshi(
                UpdatePinnedMessageRequest(
                    peer=event.chat_id,
                    id=event.reply_to_msg_id,
                    unpin=True
                )
            )
            await event.edit("📎 **Unpinned.**")
        except Exception as e:
            await event.edit(f"Failed to unpin: {e}")
    