import json
from pathlib import Path
from typing import Set

from telethon import events
from telethon.tl.functions.contacts import BlockRequest


# ===== storage =====
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


def register(app):

    # ===== DM auto protection =====
    @app.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
    async def dm_protect(event):
        sender = await event.get_sender()
        if not sender or sender.bot:
            return

        uid = sender.id

        if uid in approved_users:
            dm_spam_counter.pop(uid, None)
            return

        dm_spam_counter[uid] = dm_spam_counter.get(uid, 0) + 1

        if dm_spam_counter[uid] > MAX_SPAM:
            try:
                await app(BlockRequest(uid))
            except Exception:
                pass

            try:
                await event.reply("⛔ You have been blocked for repeated spam.")
            except Exception:
                pass

            dm_spam_counter.pop(uid, None)
            approved_users.discard(uid)
            _save_approved(approved_users)
            return

        try:
            await event.reply(
                "🌺 **Auto-Reply** 🌺\n"
                "Owner lagi offline.\n"
                "⚠️ Jangan spam — sistem akan auto-block."
            )
        except Exception:
            pass


    # ===== approve =====
    @app.on(events.NewMessage(pattern=r"\.approve(?:\s+(.+))?$", outgoing=True))
    async def approve_cmd(event):
        target = None

        if event.is_reply:
            r = await event.get_reply_message()
            target = r.sender_id if r else None

        arg = event.pattern_match.group(1)
        if not target and arg:
            try:
                ent = await app.get_entity(arg)
                target = ent.id
            except Exception:
                pass

        if not target and event.is_private:
            target = event.chat_id

        if not target:
            return await event.edit("Gunakan di DM / reply / `.approve id/@user`")

        approved_users.add(int(target))
        dm_spam_counter.pop(int(target), None)
        _save_approved(approved_users)

        await event.edit(f"✔️ Approved `{target}`")


    # ===== unapprove =====
    @app.on(events.NewMessage(pattern=r"\.unapprove(?:\s+(.+))?$", outgoing=True))
    async def unapprove_cmd(event):
        target = None

        if event.is_reply:
            r = await event.get_reply_message()
            target = r.sender_id if r else None

        arg = event.pattern_match.group(1)
        if not target and arg:
            try:
                ent = await app.get_entity(arg)
                target = ent.id
            except Exception:
                pass

        if not target and event.is_private:
            target = event.chat_id

        if not target:
            return await event.edit("Gunakan di DM / reply / `.unapprove id/@user`")

        approved_users.discard(int(target))
        dm_spam_counter.pop(int(target), None)
        _save_approved(approved_users)

        await event.edit(f"❌ Unapproved `{target}`")


    # ===== block =====
    @app.on(events.NewMessage(pattern=r"\.block(?:\s+(.+))?$", outgoing=True))
    async def block_cmd(event):
        target = None

        if event.is_reply:
            r = await event.get_reply_message()
            target = r.sender_id if r else None

        arg = event.pattern_match.group(1)
        if not target and arg:
            try:
                ent = await app.get_entity(arg)
                target = ent.id
            except Exception:
                pass

        if not target and event.is_private:
            target = event.chat_id

        if not target:
            return await event.edit("Reply / `.block id/@user` / jalankan di DM")

        try:
            await app(BlockRequest(int(target)))
            approved_users.discard(int(target))
            dm_spam_counter.pop(int(target), None)
            _save_approved(approved_users)
            await event.edit(f"⛔ Blocked `{target}`")
        except Exception:
            await event.edit("❌ Gagal block user")


    # ===== approved list =====
    @app.on(events.NewMessage(pattern=r"\.approved$", outgoing=True))
    async def approved_list(event):
        if not approved_users:
            return await event.edit("Belum ada approved user.")

        txt = "✅ **Approved users:**\n" + "\n".join(
            f"- `{x}`" for x in sorted(approved_users)
        )
        await event.edit(txt)