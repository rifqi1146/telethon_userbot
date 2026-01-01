import os
import time
from telethon import events

from utils.ytdlp import ytdlp_download
from utils.fast_upload import FastUploader


def bar(p):
    f = int(p / 10)
    return "█" * f + "░" * (10 - f)


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.yt(?:\s+(mp3))?\s+(.*)$", outgoing=True))
    async def yt_cmd(event):
        is_mp3 = bool(event.pattern_match.group(1))
        url = event.pattern_match.group(2)

        status = await event.edit("🔍 Ambil video...")

        try:
            info = await ytdlp_download(url, audio=is_mp3)
        except Exception as e:
            await status.edit(f"❌ `{e}`")
            return

        uploader = FastUploader(kiyoshi)
        start = time.time()

        async def progress(cur, total):
            pct = cur * 100 // total
            if pct % 10 == 0:
                await status.edit(
                    f"⬆️ Uploading\n"
                    f"`{bar(pct)} {pct}%`"
                )

        try:
            with open(info["path"], "rb") as f:
                input_file = await uploader.upload(
                    f,
                    info["name"],
                    progress=progress
                )

            await kiyoshi.send_file(
                event.chat_id,
                input_file,
                caption=f"🎬 **{info['name']}**",
                supports_streaming=True,
                reply_to=event.id
            )

            await status.delete()

        except Exception as e:
            await status.edit(f"❌ Upload gagal\n`{e}`")

        finally:
            try:
                os.remove(info["path"])
            except:
                pass
                