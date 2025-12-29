from telethon import events
from telethon.tl.functions.channels import InviteToChannelRequest, ExportInviteRequest
from telethon.tl.functions.messages import ExportChatInviteRequest

from utils.permissions import is_allowed
from utils.config import log


async def _resolve_target(app, event, arg):
    if event.is_reply:
        reply = await event.get_reply_message()
        if reply and reply.sender_id:
            return reply.sender_id

    if arg:
        a = arg.lstrip("@")
        try:
            if a.isdigit():
                return int(a)
            ent = await app.get_entity(a)
            return ent.id
        except Exception:
            return None

    return None


async def _create_invite_link(app, chat_id):
    try:
        try:
            res = await app(ExportChatInviteRequest(chat_id))
            return res.link
        except Exception:
            res = await app(ExportInviteRequest(chat_id))
            return res.link
    except Exception:
        return None


async def _try_add(app, chat_id, target):
    await app(InviteToChannelRequest(chat_id, [target]))


def register(app):

    @app.on(events.NewMessage(pattern=r"\.add(?:\s+(.*))?$", outgoing=True))
    async def add_user(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.is_group:
            return await event.edit("Gunakan di grup.")

        arg = (event.pattern_match.group(1) or "").strip()
        target = await _resolve_target(app, event, arg)

        if not target:
            return await event.edit("Format: `.add @username` / `.add user_id` / reply `.add`")

        try:
            await _try_add(app, event.chat_id, target)
            return await event.edit(f"👥 User `{target}` berhasil ditambahkan ke grup.")
        except Exception as e:
            log.debug("Add failed: %s", e)

        invite = await _create_invite_link(app, event.chat_id)
        if not invite:
            return await event.edit(
                "⚠️ Gagal add user dan gagal bikin invite link.\n"
                "Pastikan kamu admin dan punya izin invite."
            )

        dm_sent = False
        try:
            await app.send_message(
                target,
                f"👋 Kamu diundang ke grup:\n\n{invite}"
            )
            dm_sent = True
        except Exception as e:
            log.debug("DM failed: %s", e)

        if dm_sent:
            await event.edit(
                f"⚠️ Tidak bisa add langsung.\n"
                f"Invite link sudah dikirim via DM ke `{target}`."
            )
        else:
            await event.edit(
                f"⚠️ Tidak bisa add langsung.\n\n"
                f"Invite link:\n{invite}\n\n"
                "DM ke user juga gagal (privacy settings)."
            )

    @app.on(events.NewMessage(pattern=r"\.addsilent(?:\s+(.*))?$", outgoing=True))
    async def add_silent(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.is_group:
            return await event.edit("Gunakan di grup.")

        arg = (event.pattern_match.group(1) or "").strip()
        target = await _resolve_target(app, event, arg)

        if not target:
            return await event.edit("Format: `.addsilent @username` / `.addsilent user_id` / reply")

        try:
            await _try_add(app, event.chat_id, target)
            await event.edit(f"👥 User `{target}` berhasil ditambahkan ke grup.")
        except Exception:
            await event.edit("⚠️ Gagal add user (silent mode).")
            