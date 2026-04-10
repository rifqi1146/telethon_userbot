import asyncio
from io import BytesIO
from pathlib import Path
from urllib.parse import quote_plus

from telethon import events
from utils.config import get_http_session


QR_SIZE = "400x400"


def _build_qr_url(text: str) -> str:
    encoded = quote_plus(text)
    return f"https://api.qrserver.com/v1/create-qr-code/?data={encoded}&size={QR_SIZE}"


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"^[./]qr(?:\s+(.+))?$", outgoing=True))
    async def generate_qr(event):
        text = (event.pattern_match.group(1) or "").strip()

        if not text and event.is_reply:
            rep = await event.get_reply_message()
            text = (rep.text or rep.message or "").strip()

        if not text:
            return await event.edit("Reply text or use `.qr <text>` to generate a QR code.")

        status_msg = await event.edit("Generating QR code...")

        frames = [".", "..", "..."]
        running = True

        async def spinner():
            i = 0
            while running:
                try:
                    await status_msg.edit(f"Generating QR code{frames[i % len(frames)]}")
                except Exception:
                    pass
                i += 1
                await asyncio.sleep(0.4)

        spin = asyncio.create_task(spinner())

        try:
            session = await get_http_session()
            async with session.get(_build_qr_url(text)) as resp:
                data = await resp.read()

            running = False
            await spin

            qr = BytesIO(data)
            qr.name = "qr.png"

            await kiyoshi.send_file(
                event.chat_id,
                qr,
                caption=f"QR for:\n{text}",
                force_document=False
            )
            await status_msg.delete()

        except Exception as e:
            running = False
            await spin
            await status_msg.edit(f"Failed to generate QR code.\n\n{e}")

    @kiyoshi.on(events.NewMessage(pattern=r"^[./](readqr|rqr|reqdqr)$", outgoing=True))
    async def read_qr(event):
        if not event.is_reply:
            return await event.edit("Reply to a QR image first.")

        status = await event.edit("Reading QR code...")

        rep = await event.get_reply_message()
        file_path = await kiyoshi.download_media(rep)

        if not file_path:
            return await status.edit("Failed to download image.")

        try:
            session = await get_http_session()

            from aiohttp import FormData
            with open(file_path, "rb") as f:
                form = FormData()
                form.add_field(
                    "file",
                    f,
                    filename="qr.png",
                    content_type="image/png"
                )

                async with session.post(
                    "https://api.qrserver.com/v1/read-qr-code/",
                    data=form,
                    timeout=20
                ) as resp:
                    if resp.status != 200:
                        return await status.edit("QR server error. Try again later.")
                    data = await resp.json()

            decoded = None
            try:
                decoded = data[0]["symbol"][0].get("data")
            except Exception:
                decoded = None

            if not decoded:
                return await status.edit("Could not decode QR code.")

            await status.edit(f"Decoded QR:\n`{decoded}`")

        except Exception as e:
            await status.edit(f"Failed to read QR code.\n{e}")

        finally:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception:
                pass