import asyncio

from telethon import events


def register(kiyoshi):
    if not hasattr(kiyoshi, "_anon_auto_next"):
        kiyoshi._anon_auto_next = False

    def _is_stop_message(text: str) -> bool:
        t = (text or "").strip().lower()
        return (
            "co"
            "your partner has stopped the chat" in t
            and "type /search to find a new partner" in t
            and "t.me/chatbot" in t
        )

    @kiyoshi.on(events.NewMessage(pattern=r"\.anon(?:\s+(on|off))?$", outgoing=True))
    async def anon_toggle(event):
        match = event.pattern_match.group(1)
        current = bool(getattr(kiyoshi, "_anon_auto_next", False))

        if not match:
            status = "ON" if current else "OFF"
            try:
                await event.edit(f"**Anon auto-next:** `{status}`")
            except Exception:
                pass
            return

        value = match.lower().strip()

        if value == "on":
            kiyoshi._anon_auto_next = True
            text = "**Anon auto-next enabled**"
        else:
            kiyoshi._anon_auto_next = False
            text = "**Anon auto-next disabled**"

        try:
            await event.edit(text)
            await asyncio.sleep(1.5)
            await event.delete()
        except Exception:
            pass

    @kiyoshi.on(events.NewMessage(incoming=True))
    async def anon_auto_next(event):
        if not getattr(kiyoshi, "_anon_auto_next", False):
            return

        if not event.is_private:
            return

        text = event.raw_text or ""
        if not _is_stop_message(text):
            return

        try:
            sender = await event.get_sender()
        except Exception:
            return

        username = (getattr(sender, "username", "") or "").lower()
        if username != "chatbot":
            return

        await asyncio.sleep(1)
        try:
            await kiyoshi.send_message(event.chat_id, "/next")
        except Exception:
            pass