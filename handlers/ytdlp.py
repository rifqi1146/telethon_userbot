import asyncio
import os
import re
import time
import uuid

from telethon import events

TMP_DIR = "downloads"
os.makedirs(TMP_DIR, exist_ok=True)

YTDLP_BIN = "yt-dlp"


def safe(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "", name)[:200]


def progress_bar(pct: int, width: int = 10) -> str:
    filled = int(width * pct / 100)
    return "█" * filled + "░" * (width - filled)


async def ytdlp_download(url: str, audio: bool, status):
    uid = uuid.uuid4().hex
    out_tpl = os.path.join(TMP_DIR, f"{uid}.%(ext)s")

    cmd = [
        YTDLP_BIN,
        "-f", "bestaudio/best" if audio else "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--newline",
        "--print", "after_move:filepath",
        "--no-playlist",
        "-o", out_tpl,
        url,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    last_update = 0

    while True:
        line = await proc.stdout.readline()
        if not line:
            break

        text = line.decode(errors="ignore").strip()

        if "%" in text:
            m = re.search(r"(\d+(?:\.\d+)?)%", text)
            if m:
                pct = int(float(m.group(1)))
                now = time.time()
                if now - last_update >= 3:
                    await status.edit(
                        f"⬇️ **Downloading**\n\n"
                        f"`{progress_bar(pct)} {pct}%`"
                    )
                    last_update = now

    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(stderr.decode(errors="ignore").strip())

    path = (await proc.stdout.read()).decode().strip()
    if not path or not os.path.exists(path):
        raise RuntimeError("Gagal mengambil file hasil download")

    return {
        "path": path,
        "name": safe(os.path.basename(path)),
    }


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.yt(?:\s+(mp3))?\s+(.*)$", outgoing=True))
    async def yt_cmd(event):
        is_mp3 = bool(event.pattern_match.group(1))
        url = event.pattern_match.group(2)

        status = await event.edit("🔍 **Ambil info YouTube...**")

        try:
            info = await ytdlp_download(url, is_mp3, status)
        except Exception as e:
            await status.edit(f"❌ **Download gagal**\n`{e}`")
            return

        start = time.time()
        last_update = 0

        async def upload_progress(cur, total):
            nonlocal last_update
            if not total:
                return

            pct = int(cur * 100 / total)
            now = time.time()
            if now - last_update >= 3:
                await status.edit(
                    f"⬆️ **Uploading**\n\n"
                    f"`{progress_bar(pct)} {pct}%`"
                )
                last_update = now

        try:
            await kiyoshi.send_file(
                event.chat_id,
                info["path"],
                caption=f"🎬 **{info['name']}**",
                supports_streaming=not is_mp3,
                progress_callback=upload_progress,
                reply_to=event.id,
            )
            await status.delete()

        except Exception as e:
            await status.edit(f"❌ **Upload gagal**\n`{e}`")

        finally:
            try:
                os.remove(info["path"])
            except Exception:
                pass
                