from typing import Optional, Tuple

from telethon import events
from telethon.tl.functions.channels import EditAdminRequest
from telethon.tl.types import ChatAdminRights


PROMOTE_RIGHTS = ChatAdminRights(
    change_info=True,
    delete_messages=True,
    ban_users=True,
    invite_users=True,
    pin_messages=True,
    add_admins=False,
    anonymous=False,
    manage_call=True,
    manage_topics=True,
)


DEMOTE_RIGHTS = ChatAdminRights(
    change_info=False,
    post_messages=False,
    edit_messages=False,
    delete_messages=False,
    ban_users=False,
    invite_users=False,
    pin_messages=False,
    add_admins=False,
    anonymous=False,
    manage_call=False,
    manage_topics=False,
)


async def resolve_target(kiyoshi, event, raw: Optional[str]) -> Optional[int]:
    if event.is_reply:
        reply = await event.get_reply_message()
        if reply and reply.sender_id:
            return reply.sender_id

    if not raw:
        return None

    raw = raw.strip()
    raw = raw.lstrip("@")

    if raw.isdigit():
        return int(raw)

    try:
        ent = await kiyoshi.get_entity(raw)
        return ent.id
    except Exception:
        return None


def parse_promote_input(event, text: str) -> Tuple[Optional[str], str]:
    text = (text or "").strip()

    if event.is_reply:
        return None, (text or "Admin")

    if not text:
        return None, "Admin"

    parts = text.split(maxsplit=1)
    target_raw = parts[0]
    title = parts[1].strip() if len(parts) > 1 else "Admin"
    return target_raw, title


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"^[./]promote(?:\s+(.+))?$", outgoing=True))
    async def promote_handler(event):
        if not event.is_group:
            return await event.edit("Gunakan di grup.")

        raw_text = event.pattern_match.group(1) or ""
        target_raw, title = parse_promote_input(event, raw_text)
        target = await resolve_target(kiyoshi, event, target_raw)

        if not target:
            return await event.edit(
                "**Usage:**\n"
                "• Reply user: `.promote magang`\n"
                "• Username/ID: `.promote @username magang`\n"
                "• Username/ID: `.promote 123456789 magang`"
            )

        try:
            await kiyoshi(
                EditAdminRequest(
                    channel=event.chat_id,
                    user_id=target,
                    admin_rights=PROMOTE_RIGHTS,
                    rank=title,
                )
            )
            await event.edit(
                f"**Promoted** `{target}`\n"
                f"**Title:** `{title}`"
            )
        except Exception as e:
            await event.edit(f"Error: `{e}`")

    @kiyoshi.on(events.NewMessage(pattern=r"^[./]demote(?:\s+(.+))?$", outgoing=True))
    async def demote_handler(event):
        if not event.is_group:
            return await event.edit("Gunakan di grup.")

        raw = (event.pattern_match.group(1) or "").strip()
        target = await resolve_target(kiyoshi, event, raw)

        if not target:
            return await event.edit(
                "**Usage:**\n"
                "• Reply user: `.demote`\n"
                "• Username/ID: `.demote @username`\n"
                "• Username/ID: `.demote 123456789`"
            )

        try:
            await kiyoshi(
                EditAdminRequest(
                    channel=event.chat_id,
                    user_id=target,
                    admin_rights=DEMOTE_RIGHTS,
                    rank="",
                )
            )
            await event.edit(f"**Demoted** `{target}`")
        except Exception as e:
            await event.edit(f"Error: `{e}`")
            