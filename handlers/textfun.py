from telethon import events
from pyfiglet import figlet_format
from telethon.tl.types import MessageEntitySpoiler


def mock_text(text: str) -> str:
    return "".join(
        c.upper() if i % 2 == 0 else c.lower()
        for i, c in enumerate(text)
    )


def spoiler_text(text: str) -> str:
    return f"||{text}||"


def cowsay(text: str) -> str:
    lines = text.split("\n")
    max_len = max(len(line) for line in lines)

    top = " " + "_" * (max_len + 2) + " "
    bottom = " " + "-" * (max_len + 2) + " "

    out = [top]
    for line in lines:
        out.append(f"< {line}{' ' * (max_len - len(line))} >")
    out.append(bottom)
    out.append("        \\   ^__^")
    out.append("         \\  (oo)\\_______")
    out.append("            (__)\\       )\\/\\")
    out.append("                ||----w |")
    out.append("                ||     ||")

    return "\n".join(out)


def _get_text(event):
    if event.pattern_match.group(1):
        return event.pattern_match.group(1)
    if event.is_reply:
        reply = event.reply_to_msg_id and event._client
        return None
    return None


def register(app):

    @app.on(events.NewMessage(pattern=r"\.ascii(?:\s+(.*))?$", outgoing=True))
    async def ascii_handler(event):
        text = event.pattern_match.group(1)

        if not text and event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text if reply else None

        if not text:
            return await event.edit("`.ascii <text>` atau reply pesan")

        try:
            art = figlet_format(text)
            if len(art) > 4000:
                art = art[:3990] + "..."
            await event.edit(f"```\n{art}\n```")
        except Exception as e:
            await event.edit(f"❌ {e}")

    @app.on(events.NewMessage(pattern=r"\.spoiler(?:\s+(.*))?$", outgoing=True))
    async def spoiler_handler(event):
        text = event.pattern_match.group(1)

        if not text and event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text if reply else None

       if not text:
            return await event.edit("`.spoiler <text>` atau reply pesan")

       await event.edit(
            text,
             formatting_entities=[MessageEntitySpoiler(offset=0, length=len(text))]
    )

    @app.on(events.NewMessage(pattern=r"\.mock(?:\s+(.*))?$", outgoing=True))
    async def mock_handler(event):
        text = event.pattern_match.group(1)

        if not text and event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text if reply else None

        if not text:
            return await event.edit("`.mock <text>` atau reply pesan")

        await event.edit(mock_text(text))

    @app.on(events.NewMessage(pattern=r"\.cowsay(?:\s+(.*))?$", outgoing=True))
    async def cowsay_handler(event):
        text = event.pattern_match.group(1)

        if not text and event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text if reply else None

        if not text:
            return await event.edit("`.cowsay <text>` atau reply pesan")

        art = cowsay(text)
        if len(art) > 4000:
            art = art[:3990] + "..."
        await event.edit(f"```\n{art}\n```")
        