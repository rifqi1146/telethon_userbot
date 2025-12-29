import asyncio
import json
from pathlib import Path
from urllib.parse import quote_plus
from io import BytesIO

from telethon import events
from utils.config import get_http_session


_QR_CONFIG_FILE = Path("data/qr_config.json")
_QR_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

_QR_STYLE_TEMPLATES = {
    "kawaii_pink": {
        "gen_status": "**🌸✨ Generating cute QR code... hold on~**",
        "caption":    "**🌸 QR for you, senpai:**\n{txt}",
        "error":      "**❣️ Failed to generate QR. Try again later.**"
    },
    "cyber_y2k": {
        "gen_status": "**🔮 Generating QR code… neon flux engaged**",
        "caption":    "**🔷 QR Generated • {txt}**",
        "error":      "**🚫 QR generation failed (server).**"
    },
    "minimal_anime": {
        "gen_status": "**✨ Creating QR… please wait**",
        "caption":    "**✨ QR for: {txt}**",
        "error":      "**⚠️ Couldn't create QR, try later.**"
    },
    "playful": {
        "gen_status": "**🛠️ Cookin' a QR… 1%… 99%… DONE 🍳**",
        "caption":    "**🤣 QR for: **{txt}\n(Scan it or suffer the consequences)",
        "error":      "**🚫 Oops, QR server kaput.**"
    },
}

_QR_STYLES = {
    "kawaii_pink": {"size": "400x400"},
    "cyber_y2k": {"size": "420x420"},
    "minimal_anime": {"size": "400x400"},
    "playful": {"size": "400x400"},
}

_AVAILABLE_STYLES = list(_QR_STYLES.keys())
QR_STYLE = _AVAILABLE_STYLES[0]


def _load_qr_config():
    global QR_STYLE
    try:
        if _QR_CONFIG_FILE.exists():
            data = json.loads(_QR_CONFIG_FILE.read_text())
            if data.get("qr_style") in _QR_STYLES:
                QR_STYLE = data["qr_style"]
    except Exception:
        pass


def _save_qr_config(name: str):
    try:
        _QR_CONFIG_FILE.write_text(json.dumps({"qr_style": name}))
        return True
    except Exception:
        return False


_load_qr_config()


def _build_qr_url(style: str, text: str) -> str:
    size = _QR_STYLES.get(style, {}).get("size", "400x400")
    encoded = quote_plus(text)
    return f"https://api.qrserver.com/v1/create-qr-code/?data={encoded}&size={size}"


def register(app):

    @app.on(events.NewMessage(pattern=r"\.qrstyle(?:\s+(.+))?$", outgoing=True))
    async def qrstyle_cmd(event):
        global QR_STYLE
        arg = (event.pattern_match.group(1) or "").strip().lower()

        if not arg:
            styles = ", ".join(f"`{k}`" for k in _QR_STYLES)
            return await event.edit(
                f"**✨ QR Style Manager ✨**\n\n"
                f"• Current default: `{QR_STYLE}`\n"
                f"• Available styles: {styles}\n\n"
                f"Set default with: `.qrstyle <style>`\n"
                f"Reset with: `.qrstyle reset`"
            )

        if arg == "reset":
            QR_STYLE = _AVAILABLE_STYLES[0]
            _save_qr_config(QR_STYLE)
            return await event.edit(f"✅ QR style reset to `{QR_STYLE}`")

        if arg not in _QR_STYLES:
            return await event.edit("❌ Unknown QR style.")

        QR_STYLE = arg
        _save_qr_config(arg)
        await event.edit(f"✨ Default QR style set to `{arg}`")


    @app.on(events.NewMessage(pattern=r"\.qr(?:\s+(.+))?$", outgoing=True))
    async def generate_qr(event):
        text = (event.pattern_match.group(1) or "").strip()

        if not text and event.is_reply:
            rep = await event.get_reply_message()
            text = (rep.text or rep.message or "").strip()

        if not text:
            return await event.edit("**🌸❗Reply text or `.qr [text]` to generate a QR code.**")

        style = QR_STYLE
        tokens = text.split()
        if tokens and tokens[0].startswith("style:"):
            s = tokens[0].split(":", 1)[1]
            if s in _QR_STYLES:
                style = s
                text = " ".join(tokens[1:]).strip()

        tpl = _QR_STYLE_TEMPLATES.get(style, {})
        status_msg = await event.edit(tpl.get("gen_status", "Generating QR..."))

        FRAMES = ["🌸✨", "✨🌸", "🌸💫", "💫🌸"]
        running = True

        async def spinner():
            i = 0
            while running:
                try:
                    await status_msg.edit(f"{tpl['gen_status']}\n{FRAMES[i % len(FRAMES)]}")
                except:
                    pass
                i += 1
                await asyncio.sleep(0.3)

        spin = asyncio.create_task(spinner())

        try:
            session = await get_http_session()
            async with session.get(_build_qr_url(style, text)) as resp:
                data = await resp.read()

            running = False
            await spin

            qr = BytesIO(data)
            qr.name = "qr.png"

            await app.send_file(
                event.chat_id,
                qr,
                caption=tpl.get("caption", "{txt}").format(txt=text),
                force_document=False
            )
            await status_msg.delete()

        except Exception as e:
            running = False
            await spin
            await status_msg.edit(f"{tpl.get('error')}\n\n{e}")


    @app.on(events.NewMessage(pattern=r"\.(readqr|rqr|reqdqr)$", outgoing=True))
    async def read_qr(event):
        if not event.is_reply:
            return await event.edit("**🌸❗ Reply a QR image first, senpai.**")

        status = await event.edit("🔍 Reading QR…")

        rep = await event.get_reply_message()
        file_path = await app.download_media(rep)

        if not file_path:
            return await status.edit("❌ Failed to download image.")

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
                        return await status.edit("🚫 QR server error — try again later.")
                    data = await resp.json()

            decoded = None
            try:
                decoded = data[0]["symbol"][0].get("data")
            except Exception:
                decoded = None

            if not decoded:
                return await status.edit("💔 Could not decode QR.")

            await status.edit(f"🌸 Decoded QR:\n`{decoded}`")

        except Exception as e:
            await status.edit(f"❌ Failed to read QR\n{e}")

        finally:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception:
                pass
            