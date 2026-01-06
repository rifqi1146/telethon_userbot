import random
from typing import Optional

from telethon import events
from telethon.tl.functions.channels import EditAdminRequest
from telethon.tl.types import ChatAdminRights


FALLBACK_EMOJIS = ["🌸", "✨", "💖", "🎀", "⭐"]

ROLES = {
    "owner": {
        "full": True,
        "emoji": "🌸",
        "desc": "Ultimate control • kawaii edition ✨",
    },
    "admin": {
        "full": True,
        "emoji": "🌟",
        "desc": "Administrative magic powers ✨",
    },
    "mod": {
        "can_delete_messages": True,
        "can_restrict_members": True,
        "can_pin_messages": True,
        "emoji": "🍡",
        "desc": "Sweet but strict moderator 🍬",
    },
    "helper": {
        "can_invite_users": True,
        "can_pin_messages": True,
        "emoji": "🧸",
        "desc": "Soft helper vibes 🎀",
    },
    "manager": {
        "can_delete_messages": True,
        "can_manage_video_chats": True,
        "can_change_info": True,
        "emoji": "🎀",
        "desc": "Pretty manager energy 💖",
    },
}


def get_rights(role: str) -> ChatAdminRights:
    cfg = ROLES.get(role, ROLES["admin"])

    if cfg.get("full"):
        return ChatAdminRights(
            change_info=True,
            post_messages=True,
            edit_messages=True,
            delete_messages=True,
            ban_users=True,
            invite_users=True,
            pin_messages=True,
            add_admins=True,
            manage_call=True,
        )

    return ChatAdminRights(
        change_info=cfg.get("can_change_info", False),
        post_messages=False,
        edit_messages=False,
        delete_messages=cfg.get("can_delete_messages", False),
        ban_users=cfg.get("can_restrict_members", False),
        invite_users=cfg.get("can_invite_users", False),
        pin_messages=cfg.get("can_pin_messages", False),
        add_admins=False,
        manage_call=cfg.get("can_manage_video_chats", False),
    )


def revoke_rights() -> ChatAdminRights:
    return ChatAdminRights(
        change_info=False,
        post_messages=False,
        edit_messages=False,
        delete_messages=False,
        ban_users=False,
        invite_users=False,
        pin_messages=False,
        add_admins=False,
        manage_call=False,
    )


def format_message(action: str, role: str, user_id: int) -> str:
    cfg = ROLES.get(role, {})
    emoji = cfg.get("emoji") or random.choice(FALLBACK_EMOJIS)

    if action == "promote":
        return (
            f"{emoji} **{role.upper()}** promoted `{user_id}`\n"
            f"**{cfg.get('desc', 'No description')}**"
        )

    return (
        f"💔 **DEMOTED** `{user_id}`\n"
        f"All privileges have been taken away~"
    )


async def resolve_target(kiyoshi, event, arg: Optional[str]) -> Optional[int]:
    if event.is_reply:
        r = await event.get_reply_message()
        if r and r.sender_id:
            return r.sender_id

    if arg:
        a = arg.lstrip("@")
        if a.isdigit():
            return int(a)
        try:
            ent = await kiyoshi.get_entity(a)
            return ent.id
        except Exception:
            return None

    return None


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.promote(?:\s+(.*))?$", outgoing=True))
    async def promote_handler(event):
        if not event.is_group:
            return await event.edit("Gunakan di grup.")
    
        raw = (event.pattern_match.group(1) or "").split()
    
        target = None
        role = "admin"
    
        if event.is_reply:
            target = await resolve_target(kiyoshi, event, None)
            if raw:
                role = raw[0].lower()
        else:
            if raw:
                target = await resolve_target(kiyoshi, event, raw[0])
                if len(raw) > 1:
                    role = raw[1].lower()
    
        if role not in ROLES:
            role = "admin"
    
        if not target:
            roles = "\n".join(
                f"• `{k}` {v.get('emoji','')} — {v.get('desc','')}"
                for k, v in ROLES.items()
            )
            return await event.edit(
                "**Usage:** `.promote [user] [role]` atau reply\n\n"
                f"**Roles:**\n{roles}"
            )
    
        try:
            rights = get_rights(role)
            await kiyoshi(
                EditAdminRequest(
                    event.chat_id,
                    target,
                    rights,
                    role.title(),
                )
            )
            await event.edit(format_message("promote", role, target))
        except Exception as e:
            await event.edit(f"❌ Error: `{e}`")

    @kiyoshi.on(events.NewMessage(pattern=r"\.demote(?:\s+(.*))?$", outgoing=True))
    async def demote_handler(event):
        if not event.is_group:
            return await event.edit("Gunakan di grup.")

        arg = (event.pattern_match.group(1) or "").strip()
        target = await resolve_target(kiyoshi, event, arg)

        if not target:
            return await event.edit(
                "**Usage:** `.demote [user|@username]` atau reply"
            )

        try:
            await kiyoshi(
                EditAdminRequest(
                    event.chat_id,
                    target,
                    revoke_rights(),
                    "",
                )
            )
            await event.edit(format_message("demote", "", target))
        except Exception as e:
            await event.edit(f"❌ Error: `{e}`")
            