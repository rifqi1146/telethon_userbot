from datetime import datetime, timedelta, timezone

from telethon import events

from utils.config import log
from utils.permissions import is_allowed, _safe_chat_permissions, parse_duration_to_datetime


def register(app):

    @app.on(events.NewMessage(pattern=r"\.mute(?:\s+(.+))?$", outgoing=True))
    async def cmd_mute(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.chat_id:
            return await event.edit("Gunakan di grup.")

        target_id = None
        args = (event.pattern_match.group(1) or "").split()

        if event.is_reply:
            reply = await event.get_reply_message()
            if reply and reply.sender_id:
                target_id = reply.sender_id
        elif args:
            a = args[0].lstrip("@")
            try:
                target_id = int(a) if a.isdigit() else (await app.get_entity(a)).id
            except Exception:
                pass

        if not target_id:
            return await event.edit("Reply ke pesan user atau `.mute id/@username`")

        dur = None
        reason = None

        if event.is_reply:
            if args:
                parsed = parse_duration_to_datetime(args[0])
                if parsed:
                    dur = args[0]
                    reason = " ".join(args[1:]) if len(args) > 1 else None
                else:
                    reason = " ".join(args)
        else:
            start = 1 if not args[0].isdigit() else 2
            if len(args) >= start:
                parsed = parse_duration_to_datetime(args[start - 1])
                if parsed:
                    dur = args[start - 1]
                    reason = " ".join(args[start:]) if len(args) > start else None
                else:
                    reason = " ".join(args[start - 1:])

        until_dt = parse_duration_to_datetime(dur)

        perms = _safe_chat_permissions({
            "can_send_messages": False,
            "can_send_media_messages": False,
            "can_send_polls": False,
            "can_send_other_messages": False,
            "can_add_web_page_previews": False,
        })

        try:
            await app.restrict_chat_member(
                event.chat_id,
                target_id,
                permissions=perms,
                until_date=until_dt
            )
            txt = f"🔇 User `{target_id}` dimute{' selama ' + dur if dur else ' permanen'}."
            if reason:
                txt += f" Reason: {reason}"
            await event.edit(txt)
        except Exception:
            log.exception("mute failed")
            await event.edit("mute failed: terjadi kesalahan.")

    @app.on(events.NewMessage(pattern=r"\.unmute(?:\s+(.+))?$", outgoing=True))
    async def cmd_unmute(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.chat_id:
            return await event.edit("Gunakan di grup.")

        target_id = None
        args = (event.pattern_match.group(1) or "").split()

        if event.is_reply:
            reply = await event.get_reply_message()
            if reply and reply.sender_id:
                target_id = reply.sender_id
        elif args:
            a = args[0].lstrip("@")
            try:
                target_id = int(a) if a.isdigit() else (await app.get_entity(a)).id
            except Exception:
                pass

        if not target_id:
            return await event.edit("Reply ke pesan user atau `.unmute id/@username`")

        perms = _safe_chat_permissions({
            "can_send_messages": True,
            "can_send_media_messages": True,
            "can_send_polls": True,
            "can_send_other_messages": True,
            "can_add_web_page_previews": True,
        })

        try:
            await app.restrict_chat_member(event.chat_id, target_id, permissions=perms)
            txt = f"🔊 User `{target_id}` di-unmute."
            if len(args) > 1:
                txt += f" Reason: {' '.join(args[1:])}"
            await event.edit(txt)
        except Exception:
            log.exception("unmute failed")
            await event.edit("unmute failed: terjadi kesalahan.")

    @app.on(events.NewMessage(pattern=r"\.ban(?:\s+(.+))?$", outgoing=True))
    async def cmd_ban(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.chat_id:
            return await event.edit("Gunakan di grup.")

        target_id = None
        args = (event.pattern_match.group(1) or "").split()

        if event.is_reply:
            reply = await event.get_reply_message()
            if reply and reply.sender_id:
                target_id = reply.sender_id
        elif args:
            a = args[0].lstrip("@")
            try:
                target_id = int(a) if a.isdigit() else (await app.get_entity(a)).id
            except Exception:
                pass

        if not target_id:
            return await event.edit("Reply ke pesan user atau `.ban id/@username`")

        dur = None
        reason = None

        if event.is_reply:
            if args:
                parsed = parse_duration_to_datetime(args[0])
                if parsed:
                    dur = args[0]
                    reason = " ".join(args[1:]) if len(args) > 1 else None
                else:
                    reason = " ".join(args)
        else:
            start = 1 if not args[0].isdigit() else 2
            if len(args) >= start:
                parsed = parse_duration_to_datetime(args[start - 1])
                if parsed:
                    dur = args[start - 1]
                    reason = " ".join(args[start:]) if len(args) > start else None
                else:
                    reason = " ".join(args[start - 1:])

        until_dt = parse_duration_to_datetime(dur)

        try:
            await app.ban_chat_member(
                event.chat_id,
                target_id,
                until_date=until_dt
            )
            txt = f"⛔ User `{target_id}` diban{' selama ' + dur if dur else ' permanen'}."
            if reason:
                txt += f" Reason: {reason}"
            await event.edit(txt)
        except Exception:
            log.exception("ban failed")
            await event.edit("ban failed: terjadi kesalahan.")

    @app.on(events.NewMessage(pattern=r"\.unban(?:\s+(.+))?$", outgoing=True))
    async def cmd_unban(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.chat_id:
            return await event.edit("Gunakan di grup.")

        target_id = None
        args = (event.pattern_match.group(1) or "").split()

        if event.is_reply:
            reply = await event.get_reply_message()
            if reply and reply.sender_id:
                target_id = reply.sender_id
        elif args:
            a = args[0].lstrip("@")
            try:
                target_id = int(a) if a.isdigit() else (await app.get_entity(a)).id
            except Exception:
                pass

        if not target_id:
            return await event.edit("Reply ke pesan user atau `.unban id/@username`")

        try:
            await app.unban_chat_member(event.chat_id, target_id)
            txt = f"✅ User `{target_id}` di-unban."
            if len(args) > 1:
                txt += f" Reason: {' '.join(args[1:])}"
            await event.edit(txt)
        except Exception:
            log.exception("unban failed")
            await event.edit("unban failed: terjadi kesalahan.")

    @app.on(events.NewMessage(pattern=r"\.kick(?:\s+(.+))?$", outgoing=True))
    async def cmd_kick(event):
        if not await is_allowed(app, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        if not event.chat_id:
            return await event.edit("Gunakan di grup.")

        target_id = None
        args = (event.pattern_match.group(1) or "").split()

        if event.is_reply:
            reply = await event.get_reply_message()
            if reply and reply.sender_id:
                target_id = reply.sender_id
        elif args:
            a = args[0].lstrip("@")
            try:
                target_id = int(a) if a.isdigit() else (await app.get_entity(a)).id
            except Exception:
                pass

        if not target_id:
            return await event.edit("Reply ke pesan user atau `.kick id/@username`")

        try:
            until_dt = datetime.now(timezone.utc) + timedelta(seconds=8)
            await app.ban_chat_member(event.chat_id, target_id, until_date=until_dt)
            await app.unban_chat_member(event.chat_id, target_id)

            txt = f"👢 User `{target_id}` telah dikick."
            if len(args) > 1:
                txt += f" Reason: {' '.join(args[1:])}"
            await event.edit(txt)
        except Exception:
            log.exception("kick failed")
            await event.edit("kick failed: terjadi kesalahan.")
            