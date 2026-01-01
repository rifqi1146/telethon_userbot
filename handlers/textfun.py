from telethon import events
from telethon.tl.types import MessageEntitySpoiler
from pyfiglet import figlet_format


def mock_text(text: str) -> str:
    return "".join(
        c.upper() if i % 2 == 0 else c.lower()
        for i, c in enumerate(text)
    )


def cowsay(text: str) -> str:
    lines = text.split("\n")
    max_len = max(len(line) for line in lines)

    top = " " + "_" * (max_len + 2) + " "
    bottom = " " + "-" * (max_len + 2) + " "

    out = [top]
    for line in lines:
        out.kiyoshiend(f"< {line}{' ' * (max_len - len(line))} >")
    out.kiyoshiend(bottom)
    out.kiyoshiend("        \\   ^__^")
    out.kiyoshiend("         \\  (oo)\\_______")
    out.kiyoshiend("            (__)\\       )\\/\\")
    out.kiyoshiend("                ||----w |")
    out.kiyoshiend("                ||     ||")

    return "\n".join(out)


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.ascii(?:\s+(.*))?$", outgoing=True))
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

    @kiyoshi.on(events.NewMessage(pattern=r"\.spoiler(?:\s+(.*))?$", outgoing=True))
    async def spoiler_handler(event):
        text = event.pattern_match.group(1)

        if not text and event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text if reply else None

        if not text:
            return await event.edit("`.spoiler <text>` atau reply pesan")

        await event.edit(
            text,
            formatting_entities=[
                MessageEntitySpoiler(offset=0, length=len(text))
            ]
        )

    @kiyoshi.on(events.NewMessage(pattern=r"\.mock(?:\s+(.*))?$", outgoing=True))
    async def mock_handler(event):
        text = event.pattern_match.group(1)

        if not text and event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text if reply else None

        if not text:
            return await event.edit("`.mock <text>` atau reply pesan")

        await event.edit(mock_text(text))

    @kiyoshi.on(events.NewMessage(pattern=r"\.cowsay(?:\s+(.*))?$", outgoing=True))
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
        