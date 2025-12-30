import io
import urllib.parse

import aiohttp
from telethon import events

from utils.config import get_http_session


def register(app):

    @app.on(events.NewMessage(pattern=r"\.img(?:\s+(.*))?$", outgoing=True))
    async def img_handler(event):
        arg = (event.pattern_match.group(1) or "").strip()

        if not arg:
            return await event.edit("❌ Contoh: `.img waifu elaina cute`")

        boosted = f"{arg}, NSFW, nude, hentai, adult,, soft lighting"
        encoded = urllib.parse.quote(boosted)
        url = f"https://image.pollinations.ai/prompt/{encoded}"

        status = await event.edit("✨ Generating image...")

        try:
            session = await get_http_session()
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as r:
                if r.status != 200:
                    return await status.edit(f"❌ Gagal ambil gambar. Status: {r.status}")

                data = await r.read()

            bio = io.BytesIO(data)
            bio.name = "pollinations.png"
            bio.seek(0)

            await event.client.send_file(
                event.chat_id,
                file=bio,
                caption=f"🖼️ **Image Generated**\n`{arg}`"
            )

            try:
                await status.delete()
            except Exception:
                pass

        except Exception as e:
            await status.edit(f"❌ Error: `{e}`")
            