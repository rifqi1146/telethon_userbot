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


async def _resolve_target(app, event, arg: str | None):
    if event.is_reply:
        reply = await event.get_reply_message()
        if reply and reply.sender_id:
            return reply.sender_id

    if arg:
        a = arg.strip().lstrip("@")
        try:
            if a.isdigit():
                return int(a)
            ent = await app.get_entity(a)
            return ent.id
        except Exception:
            return None

    return None


def _parse_args(arg: str):
    parts = arg.split()
    if not parts:
        return None, None, None

    target = parts[0]
    rest = parts[1:]

    dur = None
    reason = None

    if rest:
        parsed = parse_duration_to_datetime(rest[0])
        if parsed:
            dur = rest[0]
            reason = " ".join(rest[1:]) if len(rest) > 1 else None
        else:
            reason = " ".join(rest)

    return target, dur, reason


def register(app):

    @app.on(events.NewMessage(pattern=r"\.mute(?:\s+(.*))?$", outgoing=True))
    async def mute(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.is_group:
            return await event.edit("Gunakan di grup.")

        arg = (event.pattern_match.group(1) or "").strip()
        t_arg, dur, reason = _parse_args(arg)

        target = await _resolve_target(app, event, t_arg)
        if not target:
            return await event.edit("Reply user atau `.mute id/@username [durasi] [reason]`")

        until = parse_duration_to_datetime(dur)

        try:
            await app(EditBannedRequest(event.chat_id, target, _mute_rights(until)))
            text = (
                f"🔇 User `{target}` dimute"
                f"{f' selama {dur}' if until else ' permanen'}."
            )
            if reason:
                text += f"\n📝 Reason: {reason}"
            await event.edit(text)
        except Exception as e:
            log.exception("mute failed")
            await event.edit(f"mute failed: {e}")

    @app.on(events.NewMessage(pattern=r"\.unmute(?:\s+(.*))?$", outgoing=True))
    async def unmute(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.is_group:
            return await event.edit("Gunakan di grup.")

        arg = (event.pattern_match.group(1) or "").strip()
        t_arg, _, reason = _parse_args(arg)

        target = await _resolve_target(app, event, t_arg)
        if not target:
            return await event.edit("Reply user atau `.unmute id/@username [reason]`")

        try:
            await app(EditBannedRequest(event.chat_id, target, _unmute_rights()))
            text = f"🔊 User `{target}` di-unmute."
            if reason:
                text += f"\n📝 Reason: {reason}"
            await event.edit(text)
        except Exception as e:
            log.exception("unmute failed")
            await event.edit(f"unmute failed: {e}")

    @app.on(events.NewMessage(pattern=r"\.ban(?:\s+(.*))?$", outgoing=True))
    async def ban(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.is_group:
            return await event.edit("Gunakan di grup.")

        arg = (event.pattern_match.group(1) or "").strip()
        t_arg, dur, reason = _parse_args(arg)

        target = await _resolve_target(app, event, t_arg)
        if not target:
            return await event.edit("Reply user atau `.ban id/@username [durasi] [reason]`")

        until = parse_duration_to_datetime(dur)

        try:
            await app(EditBannedRequest(event.chat_id, target, _ban_rights(until)))
            text = (
                f"⛔ User `{target}` diban"
                f"{f' selama {dur}' if until else ' permanen'}."
            )
            if reason:
                text += f"\n📝 Reason: {reason}"
            await event.edit(text)
        except Exception as e:
            log.exception("ban failed")
            await event.edit(f"ban failed: {e}")

    @app.on(events.NewMessage(pattern=r"\.unban(?:\s+(.*))?$", outgoing=True))
    async def unban(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.is_group:
            return await event.edit("Gunakan di grup.")

        arg = (event.pattern_match.group(1) or "").strip()
        t_arg, _, reason = _parse_args(arg)

        target = await _resolve_target(app, event, t_arg)
        if not target:
            return await event.edit("Reply user atau `.unban id/@username [reason]`")

        try:
            await app(EditBannedRequest(event.chat_id, target, ChatBannedRights(until_date=None)))
            text = f"✅ User `{target}` di-unban."
            if reason:
                text += f"\n📝 Reason: {reason}"
            await event.edit(text)
        except Exception as e:
            log.exception("unban failed")
            await event.edit(f"unban failed: {e}")

    @app.on(events.NewMessage(pattern=r"\.kick(?:\s+(.*))?$", outgoing=True))
    async def kick(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.is_group:
            return await event.edit("Gunakan di grup.")

        arg = (event.pattern_match.group(1) or "").strip()
        t_arg, _, reason = _parse_args(arg)

        target = await _resolve_target(app, event, t_arg)
        if not target:
            return await event.edit("Reply user atau `.kick id/@username [reason]`")

        until = datetime.now(timezone.utc) + timedelta(seconds=10)

        try:
            await app(EditBannedRequest(event.chat_id, target, _ban_rights(until)))
            text = f"👢 User `{target}` dikick."
            if reason:
                text += f"\n📝 Reason: {reason}"
            await event.edit(text)
        except Exception as e:
            log.exception("kick failed")
            await event.edit(f"kick failed: {e}")