import os
import re
import time
import uuid
import asyncio
import shutil
import aiohttp

from telethon import events

TMP_DIR = "downloads"
os.makedirs(TMP_DIR, exist_ok=True)

YT_DLP = shutil.which("yt-dlp")


def progress_bar(pct: float, size: int = 12) -> str:
    pct = max(0.0, min(100.0, pct))
    filled = int(size * pct / 100)
    return "▰" * filled + "▱" * (size - filled)


def clean_name(name: str, max_len=80) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    return name.strip()[:max_len] or "video"


def is_tiktok(url: str) -> bool:
    return "tiktok.com" in url or "vt.tiktok.com" in url


async def douyin_download(url: str, status):
    async with aiohttp.ClientSession() as s:
        async with s.post("https://www.tikwm.com/api/", data={"url": url}) as r:
            data = await r.json()

        info = data.get("data") or {}
        video_url = info.get("play")
        if not video_url:
            raise RuntimeError("Video tidak ditemukan")

        title = clean_name(info.get("title") or "tiktok")
        out = f"{TMP_DIR}/{uuid.uuid4().hex}.mp4"

        async with s.get(video_url) as r:
            total = int(r.headers.get("Content-Length", 0))
            done = 0
            last = 0

            with open(out, "wb") as f:
                async for chunk in r.content.iter_chunked(64 * 1024):
                    f.write(chunk)
                    done += len(chunk)

                    if total and time.time() - last > 1.2:
                        pct = done * 100 / total
                        await status.edit(
                            f"⬇️ **Download**\n\n"
                            f"`{progress_bar(pct)} {pct:.1f}%`"
                        )
                        last = time.time()

    return out, title


async def ytdlp_download(url: str, status):
    if not YT_DLP:
        raise RuntimeError("yt-dlp tidak ditemukan")

    out_tpl = f"{TMP_DIR}/%(title)s.%(ext)s"
    cmd = [
        YT_DLP,
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--newline",
        "--progress-template", "%(progress._percent_str)s",
        "-o", out_tpl,
        "--no-playlist",
        url
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    last = 0
    while True:
        line = await proc.stdout.readline()
        if not line:
            break

        raw = line.decode(errors="ignore").strip().replace("%", "")
        if raw.replace(".", "", 1).isdigit():
            pct = float(raw)
            if time.time() - last > 1.2:
                await status.edit(
                    f"⬇️ **Download**\n\n"
                    f"`{progress_bar(pct)} {pct:.1f}%`"
                )
                last = time.time()

    await proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("yt-dlp gagal")

    files = sorted(
        (os.path.join(TMP_DIR, f) for f in os.listdir(TMP_DIR)),
        key=os.path.getmtime,
        reverse=True
    )

    if not files:
        raise RuntimeError("File tidak ditemukan")

    path = files[0]
    title = clean_name(os.path.splitext(os.path.basename(path))[0])
    return path, title


async def upload_progress(cur, total, status):
    if total == 0:
        return

    if not hasattr(status, "_last"):
        status._last = 0

    now = time.time()
    if now - status._last < 1.5:
        return

    pct = cur * 100 / total
    await status.edit(
        f"⬆️ **Upload**\n\n"
        f"`{progress_bar(pct)} {pct:.1f}%`"
    )
    status._last = now


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.yt\s+(.*)$", outgoing=True))
    async def dl_handler(event):
        url = event.pattern_match.group(1).strip()
        status = await event.edit("🔍 **Memproses...**")

        path = None
        try:
            if is_tiktok(url):
                path, title = await douyin_download(url, status)
            else:
                path, title = await ytdlp_download(url, status)

            await kiyoshi.send_file(
                event.chat_id,
                path,
                caption=f"🎬 **{title}**",
                supports_streaming=True,
                progress_callback=lambda c, t: upload_progress(c, t, status),
                reply_to=event.id
            )

            await status.delete()

        except Exception as e:
            await status.edit(f"❌ **Gagal**\n`{e}`")

        finally:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
                