import time
from datetime import datetime, timezone
from typing import Optional

from telethon import events


AFK_ACTIVE = False
AFK_REASON = ""
AFK_SINCE: Optional[datetime] = None


def _afk_human(d: Optional[datetime]) -> str:
    if not d:
        return "—"
    delta = datetime.now(timezone.utc) - d
    s = int(delta.total_seconds())
    if s < 60:
        return f"{s}s"
    m = s // 60
    if m < 60:
        return f"{m}m"
    h = m // 60
    if h < 24:
        return f"{h}h"
    return f"{h // 24}d"


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.afk(?:\s+(.+))?$", outgoing=True))
    async def afk_set(event):
        global AFK_ACTIVE, AFK_REASON, AFK_SINCE

        reason = event.pattern_match.group(1)
        AFK_REASON = reason.strip() if reason else "lagi sibuk~"
        AFK_SINCE = datetime.now(timezone.utc)
        AFK_ACTIVE = True

        try:
            await event.edit(
                f"💤 **AFK aktif!**\n"
                f"Reason: {AFK_REASON} ✨\n"
                f"(aku balik nanti~)"
            )
        except Exception:
            pass


    @kiyoshi.on(events.NewMessage(pattern=r"\.back$", outgoing=True))
    async def afk_back(event):
        global AFK_ACTIVE, AFK_REASON, AFK_SINCE

        if not AFK_ACTIVE:
            return await event.edit(
                "✨ Kamu udah gak AFK kok~ welcome back! (≧◡≦)"
            )

        dur = _afk_human(AFK_SINCE)

        AFK_ACTIVE = False
        AFK_REASON = ""
        AFK_SINCE = None

        try:
            await event.edit(
                f"🌟 **AFK dimatikan!**\n"
                f"Kamu balik setelah **{dur}** — welcome~ 💫"
            )
        except Exception:
            pass


    @kiyoshi.on(events.NewMessage(outgoing=True))
    async def afk_auto_off(event):
        global AFK_ACTIVE, AFK_REASON, AFK_SINCE

        if not AFK_ACTIVE:
            return

        text = (event.raw_text or "").strip()
        if text.startswith((".", "/", "!")):
            return

        dur = _afk_human(AFK_SINCE)

        AFK_ACTIVE = False
        AFK_REASON = ""
        AFK_SINCE = None

        try:
            await event.reply(
                f"🌸 **Okaeri~!** 🌸\n"
                f"Kamu kembali setelah **{dur}** — welcome back, senpai! (≧ω≦)ﾉ"
            )
        except Exception:
            pass


    @kiyoshi.on(events.NewMessage(incoming=True))
    async def afk_reply(event):
        if not AFK_ACTIVE:
            return

        try:
            me = await kiyoshi.get_me()
        except Exception:
            return

        replied = False
        if event.reply_to:
            reply = await event.get_reply_message()
            if reply and reply.sender_id == me.id:
                replied = True

        mentioned = False
        uname = f"@{me.username.lower()}" if me.username else None
        text = (event.raw_text or "").lower()

        if uname and uname in text:
            mentioned = True

        if not (replied or mentioned):
            return

        dur = _afk_human(AFK_SINCE)
        reason = AFK_REASON or "lagi sibuk~"

        replies = [
            f"💤 Lagi AFK: {reason}\n⌛ {dur} yang lalu — maaf ya~",
            f"🌙 Aku AFK nih: {reason}\n⏰ Udah {dur}, balik nanti ya~",
            f"🍡 AFK Mode: {reason}\n⏳ {dur} yang lalu — bakal bales begitu balik~",
        ]

        try:
            idx = int(time.time()) % len(replies)
            await event.reply(replies[idx])
        except Exception:
            pass
            