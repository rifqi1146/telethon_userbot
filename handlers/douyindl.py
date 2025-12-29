import os
import time
import uuid
import asyncio

from telethon import events
from utils.config import get_http_session

TMP_DIR = "downloads"
os.makedirs(TMP_DIR, exist_ok=True)


def progress_bar(pct: float, width: int = 12) -> str:
    filled = int(width * pct / 100)
    return "█" * filled + "░" * (width - filled)


async def douyin_download_video(url: str, status_msg):
    uid = uuid.uuid4().hex
    out_path = f"{TMP_DIR}/{uid}.mp4"

    session = await get_http_session()

    async with session.post(
        "https://www.tikwm.com/api/",
        data={"url": url},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    ) as r:
        data = await r.json()

    if data.get("code") != 0:
        raise RuntimeError("Douyin API error")

    video_url = data.get("data", {}).get("play")
    if not video_url:
        raise RuntimeError("Video URL kosong")

    async with session.get(video_url) as r:
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        last_edit = 0

        with open(out_path, "wb") as f:
            async for chunk in r.content.iter_chunked(64 * 1024):
                f.write(chunk)
                downloaded += len(chunk)

                if total and time.time() - last_edit >= 1.5:
                    pct = downloaded / total * 100
                    await status_msg.edit(
                        f"⬇️ **Downloading TikTok...**\n"
                        f"`{progress_bar(pct)} {pct:.1f}%`"
                    )
                    last_edit = time.time()

    return out_path


async def convert_to_mp3(video_path: str):
    mp3_path = video_path.replace(".mp4", ".mp3")

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
        "-ab", "192k",
        "-ar", "44100",
        mp3_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )

    await proc.wait()

    if not os.path.exists(mp3_path):
        raise RuntimeError("Gagal convert MP3")

    return mp3_path


def register(app):

    @app.on(events.NewMessage(pattern=r"\.dl(?:\s+(.+))?$", outgoing=True))
    async def dl_handler(event):
        arg = (event.pattern_match.group(1) or "").strip()

        if not arg:
            return await event.edit(
                "**Usage:**\n"
                "`.dl <tiktok_url>`\n"
                "`.dl mp3 <tiktok_url>`"
            )

        parts = arg.split(maxsplit=1)
        is_mp3 = False

        if parts[0].lower() == "mp3":
            if len(parts) < 2:
                return await event.edit("❌ **Format:** `.dl mp3 <url>`")
            is_mp3 = True
            url = parts[1]
        else:
            url = parts[0]

        status = await event.edit("⏳ **Mengambil data TikTok...**")
        video_path = None

        try:
            video_path = await douyin_download_video(url, status)

            if is_mp3:
                await status.edit("🎵 **Convert ke MP3...**")
                mp3_path = await convert_to_mp3(video_path)

                await app.send_file(
                    event.chat_id,
                    mp3_path,
                    caption="🎧 **MP3 Done**"
                )
                os.remove(mp3_path)
            else:
                await app.send_file(
                    event.chat_id,
                    video_path,
                    caption="✅ **Upload selesai**"
                )

            await status.delete()

        except Exception as e:
            await status.edit(f"❌ **Error:** `{e}`")

        finally:
            try:
                if video_path and os.path.exists(video_path):
                    os.remove(video_path)
            except Exception:
                pass
                