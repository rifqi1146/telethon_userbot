from datetime import datetime, timedelta, timezone

from telethon import events
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

from utils.config import log
from utils.permissions import is_allowed, parse_duration_to_datetime


def _mute_rights(until):
    return ChatBannedRights(
        until_date=until,
        send_messages=True,
        send_media=True,
        send_stickers=True,
        send_gifs=True,
        send_games=True,
        send_inline=True,
        send_polls=True,
        embed_links=True,
    )


def _unmute_rights():
    return ChatBannedRights(
        until_date=None,
        send_messages=False,
        send_media=False,
        send_stickers=False,
        send_gifs=False,
        send_games=False,
        send_inline=False,
        send_polls=False,
        embed_links=False,
    )


def _ban_rights(until):
    return ChatBannedRights(
        until_date=until,
        view_messages=True,
    )


def register(app):

    @app.on(events.NewMessage(pattern=r"\.mute(?:\s+(.*))?$", outgoing=True))
    async def mute(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.is_group or not event.is_reply:
            return await event.edit("Reply ke user di grup.")

        reply = await event.get_reply_message()
        target = reply.sender_id

        arg = (event.pattern_match.group(1) or "").strip()
        until = parse_duration_to_datetime(arg)

        try:
            await app(
                EditBannedRequest(
                    event.chat_id,
                    target,
                    _mute_rights(until)
                )
            )
            await event.edit(
                f"🔇 User `{target}` dimute"
                f"{f' selama {arg}' if until else ' permanen'}."
            )
        except Exception as e:
            log.exception("mute failed")
            await event.edit(f"mute failed: {e}")

    @app.on(events.NewMessage(pattern=r"\.unmute$", outgoing=True))
    async def unmute(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.is_group or not event.is_reply:
            return await event.edit("Reply ke user di grup.")

        reply = await event.get_reply_message()
        target = reply.sender_id

        try:
            await app(
                EditBannedRequest(
                    event.chat_id,
                    target,
                    _unmute_rights()
                )
            )
            await event.edit(f"🔊 User `{target}` di-unmute.")
        except Exception as e:
            log.exception("unmute failed")
            await event.edit(f"unmute failed: {e}")

    @app.on(events.NewMessage(pattern=r"\.ban(?:\s+(.*))?$", outgoing=True))
    async def ban(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.is_group or not event.is_reply:
            return await event.edit("Reply ke user di grup.")

        reply = await event.get_reply_message()
        target = reply.sender_id

        arg = (event.pattern_match.group(1) or "").strip()
        until = parse_duration_to_datetime(arg)

        try:
            await app(
                EditBannedRequest(
                    event.chat_id,
                    target,
                    _ban_rights(until)
                )
            )
            await event.edit(
                f"⛔ User `{target}` diban"
                f"{f' selama {arg}' if until else ' permanen'}."
            )
        except Exception as e:
            log.exception("ban failed")
            await event.edit(f"ban failed: {e}")

    @app.on(events.NewMessage(pattern=r"\.unban$", outgoing=True))
    async def unban(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.is_group or not event.is_reply:
            return await event.edit("Reply ke user di grup.")

        reply = await event.get_reply_message()
        target = reply.sender_id

        try:
            await app(
                EditBannedRequest(
                    event.chat_id,
                    target,
                    ChatBannedRights(until_date=None)
                )
            )
            await event.edit(f"✅ User `{target}` di-unban.")
        except Exception as e:
            log.exception("unban failed")
            await event.edit(f"unban failed: {e}")

    @app.on(events.NewMessage(pattern=r"\.kick$", outgoing=True))
    async def kick(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.is_group or not event.is_reply:
            return await event.edit("Reply ke user di grup.")

        reply = await event.get_reply_message()
        target = reply.sender_id

        until = datetime.now(timezone.utc) + timedelta(seconds=10)

        try:
            await app(
                EditBannedRequest(
                    event.chat_id,
                    target,
                    _ban_rights(until)
                )
            )
            await event.edit(f"👢 User `{target}` dikick.")
        except Exception as e:
            log.exception("kick failed")
            await event.edit(f"kick failed: {e}")