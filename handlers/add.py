from telethon import events
from telethon.tl.functions.channels import InviteToChannelRequest

from utils.permissions import is_allowed
from utils.config import log


async def _resolve_target(kiyoshi, event, arg):
    if event.is_reply:
        reply = await event.get_reply_message()
        if reply and reply.sender_id:
            return reply.sender_id

    if arg:
        a = arg.lstrip("@")
        try:
            if a.isdigit():
                return int(a)
            ent = await kiyoshi.get_entity(a)
            return ent.id
        except Exception:
            return None

    return None


async def _try_add(kiyoshi, chat_id, target):
    await kiyoshi(InviteToChannelRequest(chat_id, [target]))


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.add(?:\s+(.*))?$", outgoing=True))
    async def add_user(event):
        if not await is_allowed(kiyoshi, event.sender_id):
            return await event.edit("⛔ Kamu tidak punya izin.")

        if not event.is_group:
            return await event.edit("⚠️ Gunakan perintah ini di grup.")

        arg = (event.pattern_match.group(1) or "").strip()
        target = await _resolve_target(kiyoshi, event, arg)

        if not target:
            return await event.edit(
                "Format:\n"
                "`.add @username`\n"
                "`.add user_id`\n"
                "atau reply `.add`"
            )

        try:
            await _try_add(kiyoshi, event.chat_id, target)
            await event.edit(f"👥 User `{target}` berhasil ditambahkan.")
        except Exception as e:
            log.debug("Add failed (privacy/restriction): %s", e)
            await event.edit(
                "⚠️ Gagal menambahkan user.\n"
                "Kemungkinan karena **privacy settings**."
            )