import asyncio
import json
import os
import re
import uuid

TMP_DIR = "downloads"
os.makedirs(TMP_DIR, exist_ok=True)

YTDLP_BIN = "/opt/yt-dlp/userbot/yt-dlp"


def safe(name):
    return re.sub(r'[\\/:*?"<>|]', '', name)[:200]


async def ytdlp_download(url: str, audio=False):
    uid = uuid.uuid4().hex
    out = os.path.join(TMP_DIR, f"{uid}.%(ext)s")

    cmd = [
        YTDLP_BIN,
        "-f", "bestaudio/best" if audio else "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--print", "after_move:filepath",
        "-o", out,
        "--no-playlist",
        url
    ]

    p = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await p.communicate()
    if p.returncode != 0:
        raise RuntimeError(stderr.decode())

    path = stdout.decode().strip()
    return {
        "path": path,
        "name": safe(os.path.basename(path))
    }