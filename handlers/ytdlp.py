import os
import re
import time
import asyncio
from telethon import events
from utils.config import get_http_session

TMP_DIR = "downloads"
os.makedirs(TMP_DIR, exist_ok=True)

def bar(p):
    f = int(p / 10)
    return "█" * f + "░" * (10 - f)

def detect_platform(url):
    u = url.lower()
    if "tiktok.com" in u or "vt.tiktok.com" in u:
        return "tiktok"
    if "instagram.com" in u or "instagr.am" in u:
        return "instagram"
    if "youtube.com" in u or "youtu.be" in u or "music.youtube.com" in u:
        return "youtube"
    return "unknown"

async def douyin_download(url, status):
    session = await get_http_session()
    async with session.post("https://www.tikwm.com/api/", data={"url": url}, timeout=20) as r:
        data = await r.json()

    play = data.get("data", {}).get("play")
    title = data.get("data", {}).get("title") or "tiktok"
    if not play:
        raise RuntimeError("douyin failed")

    name = re.sub(r'[\\/:*?"<>|]', "", title)[:80]
    path = f"{TMP_DIR}/{name}.mp4"

    async with session.get(play) as r:
        total = int(r.headers.get("Content-Length", 0))
        cur = 0
        last = 0
        with open(path, "wb") as f:
            async for c in r.content.iter_chunked(64 * 1024):
                f.write(c)
                cur += len(c)
                if total and time.time() - last >= 1:
                    pct = cur * 100 / total
                    await status.edit(
                        f"📥 **Downloading**\n"
                        f"`{bar(pct)} {pct:.1f}%`"
                    )
                    last = time.time()

    return path

async def ytdlp_download(url, audio, status):
    out = f"{TMP_DIR}/%(title)s.%(ext)s"

    if audio:
        cmd = [
            "yt-dlp",
            "-f", "bestaudio/best",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--newline",
            "-o", out,
            url
        ]
    else:
        cmd = [
            "yt-dlp",
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "--newline",
            "-o", out,
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
        s = line.decode(errors="ignore")
        if "%" in s:
            try:
                pct = float(s.split("%")[0].split()[-1])
            except:
                continue
            if time.time() - last >= 1:
                await status.edit(
                    f"📥 **Downloading**\n"
                    f"`{bar(pct)} {pct:.1f}%`"
                )
                last = time.time()

    await proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("yt-dlp failed")

    files = sorted(
        (os.path.join(TMP_DIR, f) for f in os.listdir(TMP_DIR)),
        key=os.path.getmtime,
        reverse=True
    )
    if not files:
        raise RuntimeError("file missing")

    return files[0]

def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.ytdlp(?:\s+(mp3))?\s+(.+)", outgoing=True))
    async def ytdlp_cmd(event):
        is_mp3 = bool(event.pattern_match.group(1))
        url = event.pattern_match.group(2).strip()

        status = await event.edit("🔍 **Analyzing link…**")
        platform = detect_platform(url)
        path = None

        try:
            if platform == "tiktok" and not is_mp3:
                try:
                    path = await douyin_download(url, status)
                except:
                    path = await ytdlp_download(url, False, status)
            else:
                path = await ytdlp_download(url, is_mp3, status)

            start = time.time()

            async def upload_progress(cur, total):
                if total == 0:
                    return
                if not hasattr(status, "_u"):
                    status._u = 0
                if time.time() - status._u < 1:
                    return
                pct = cur * 100 / total
                await status.edit(
                    f"🚀 **Uploading**\n"
                    f"`{bar(pct)} {pct:.1f}%`"
                )
                status._u = time.time()

            await kiyoshi.send_file(
                event.chat_id,
                path,
                reply_to=event.id,
                supports_streaming=not is_mp3,
                progress_callback=upload_progress
            )

            await status.delete()

        except Exception as e:
            await status.edit(f"❌ `{e}`")

        finally:
            try:
                if path:
                    os.remove(path)
            except:
                pass