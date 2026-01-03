import json
from pathlib import Path
from typing import Set

from telethon import events
from telethon.tl.functions.contacts import BlockRequest

from utils.autoreply import load_autoreply, save_autoreply

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

_APPROVED_FILE = DATA_DIR / "approved.json"


def _load_approved() -> Set[int]:
    try:
        if _APPROVED_FILE.exists():
            data = json.loads(_APPROVED_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return set(int(x) for x in data)
    except Exception:
        pass
    return set()


def _save_approved(s: Set[int]):
    try:
        _APPROVED_FILE.write_text(
            json.dumps(sorted(s), indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass


approved_users: Set[int] = _load_approved()
dm_spam_counter = {}
MAX_SPAM = 3

async def _resolve_target(kiyoshi, event):
    if event.is_reply:
        r = await event.get_reply_message()
        if r and r.sender_id:
            return r.sender_id

    arg = event.pattern_match.group(1)
    if arg:
        a = arg.strip().lstrip("@")
        if a.isdigit():
            return int(a)
        try:
            ent = await kiyoshi.get_entity(a)
            return ent.id
        except Exception:
            pass

    if event.is_private:
        return event.chat_id

    return None


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
    async def dm_protect(event):
        if not load_autoreply():
            return
    
        sender = await event.get_sender()
        if not sender or sender.bot:
            return
    
        uid = sender.id
    
        if uid in approved_users:
            dm_spam_counter.pop(uid, None)
            return
    
        count = dm_spam_counter.get(uid, 0) + 1
        dm_spam_counter[uid] = count
    
        if count > MAX_SPAM:
            try:
                await kiyoshi(BlockRequest(uid))
            except Exception:
                pass
    
            try:
                await event.reply(
                    "⛔ **You have been blocked**\n"
                    "Reason: repeated spam messages."
                )
            except Exception:
                pass
    
            dm_spam_counter.pop(uid, None)
            approved_users.discard(uid)
            _save_approved(approved_users)
            return
    
        try:
            await event.reply(
                "🌺 **Auto-Reply** 🌺\n"
                "The owner is currently offline. Please wait until they are back online.\n\n"
                f"⚠️ **Warning {count}/{MAX_SPAM}**\n"
                "Do not send repeated messages — spam will result in an automatic block."
            )
        except Exception:
            pass


    @kiyoshi.on(events.NewMessage(pattern=r"\.autoreply(?:\s+(on|off|status))?$", outgoing=True))
    async def autoreply_cmd(event):
        arg = event.pattern_match.group(1)
    
        if not arg:
            await event.edit(
                "📬 **Auto-Reply Control**\n\n"
                "**Usage:**\n"
                "• `.autoreply on` — enable auto-reply\n"
                "• `.autoreply off` — disable auto-reply\n"
                "• `.autoreply status` — show current status"
            )
            return
    
        if arg == "on":
            save_autoreply(True)
            await event.edit("✅ Auto-reply **enabled**")
            return
    
        if arg == "off":
            save_autoreply(False)
            await event.edit("🚫 Auto-reply **disabled**")
            return
    
        status = "ON ✅" if load_autoreply() else "OFF ❌"
        await event.edit(f"📬 Auto-reply status: **{status}**")
        
    @kiyoshi.on(events.NewMessage(pattern=r"\.approve(?:\s+(.+))?$", outgoing=True))
    async def approve_cmd(event):
        target = await _resolve_target(kiyoshi, event)
        if not target:
            await event.edit("Gunakan `.approve id/@username` atau reply user.")
            return

        approved_users.add(int(target))
        dm_spam_counter.pop(int(target), None)
        _save_approved(approved_users)

        await event.edit(f"✔️ Approved `{target}`")


    @kiyoshi.on(events.NewMessage(pattern=r"\.unapprove(?:\s+(.+))?$", outgoing=True))
    async def unapprove_cmd(event):
        target = await _resolve_target(kiyoshi, event)
        if not target:
            await event.edit("Gunakan `.unapprove id/@username` atau reply user.")
            return

        approved_users.discard(int(target))
        dm_spam_counter.pop(int(target), None)
        _save_approved(approved_users)

        await event.edit(f"❌ Unapproved `{target}`")


    @kiyoshi.on(events.NewMessage(pattern=r"\.block(?:\s+(.+))?$", outgoing=True))
    async def block_cmd(event):
        target = await _resolve_target(kiyoshi, event)
        if not target:
            await event.edit("Gunakan `.block id/@username` atau reply user.")
            return

        try:
            await kiyoshi(BlockRequest(int(target)))
            approved_users.discard(int(target))
            dm_spam_counter.pop(int(target), None)
            _save_approved(approved_users)
            await event.edit(f"⛔ Blocked `{target}`")
        except Exception:
            await event.edit("❌ Gagal block user")


    @kiyoshi.on(events.NewMessage(pattern=r"\.approved$", outgoing=True))
    async def approved_list(event):
        if not approved_users:
            await event.edit("Belum ada approved user.")
            return

        txt = "✅ **Approved users:**\n" + "\n".join(
            f"- `{x}`" for x in sorted(approved_users)
        )
        await event.edit(txt)