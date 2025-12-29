import asyncio
import time
import statistics
import os
import sys
import platform
from datetime import datetime
from typing import Optional

from telethon import events
import aiohttp

from utils.config import get_http_session

try:
    import dns.resolver
    DNSPYTHON_AVAILABLE = True
except Exception:
    DNSPYTHON_AVAILABLE = False


DOWNLOAD_TEST_URLS = [
    "https://speed.hetzner.de/10MB.bin",
    "https://speed.hetzner.de/100MB.bin",
    "https://speed.cloudflare.com/__down?bytes=10000000",
]

UPLOAD_TEST_ENDPOINTS = [
    "https://speed.cloudflare.com/__up",
    "https://postman-echo.com/post",
    "https://eu.httpbin.org/post",
]

PING_SERVERS = {
    "Google": "https://www.google.com",
    "Cloudflare": "https://1.1.1.1",
    "GitHub": "https://github.com",
}

DNS_SERVERS = {
    "Cloudflare": "1.1.1.1",
    "Google": "8.8.8.8",
    "OpenDNS": "208.67.222.222",
}

FRAMES = ["🌸✨", "🌸💖", "🌸🌈", "🌸💫", "🌸🌟", "💮🌸"]

SPEED_EMOJI = {
    "title": "⚡️🌸 SpeedLab",
    "ping": "🏓",
    "download": "⬇️",
    "upload": "⬆️",
    "dns": "🔍",
    "ok": "✅",
    "bad": "❌",
}

SPINNER_INTERVAL = 0.6


async def _tcp_connect_time(host: str, port: int = 53, timeout: float = 2.0) -> Optional[float]:
    start = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return round((time.perf_counter() - start) * 1000, 1)
    except Exception:
        return None


async def _dns_query_time(nameserver: str, qname: str = "google.com", timeout: float = 3.0) -> Optional[float]:
    if DNSPYTHON_AVAILABLE:
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [nameserver]
            resolver.timeout = timeout
            resolver.lifetime = timeout
            start = time.perf_counter()
            resolver.resolve(qname, tcp=True)
            return round((time.perf_counter() - start) * 1000, 1)
        except Exception:
            pass
    return await _tcp_connect_time(nameserver, 53, timeout)


async def _try_upload_speed(payload_size_bytes: int = 2 * 1024 * 1024, timeout: float = 20.0):
    session = await get_http_session()
    data = b"0" * payload_size_bytes
    for url in UPLOAD_TEST_ENDPOINTS:
        try:
            start = time.perf_counter()
            async with session.post(url, data=data, timeout=timeout) as resp:
                if 200 <= resp.status < 300:
                    dur = time.perf_counter() - start
                    return round((len(data) * 8) / (dur * 1024 * 1024), 2), url
        except Exception:
            continue
    return 0.0, None


async def quick_speedtest(event):
    msg = await event.edit(f"{FRAMES[0]} {SPEED_EMOJI['title']} — Preparing...")
    stop = False

    async def spinner():
        i = 0
        while not stop:
            try:
                await msg.edit(f"{FRAMES[i % len(FRAMES)]} {SPEED_EMOJI['title']} — Ping → Down → Up")
            except Exception:
                pass
            i += 1
            await asyncio.sleep(SPINNER_INTERVAL)

    spin = asyncio.create_task(spinner())

    try:
        session = await get_http_session()

        try:
            t0 = time.perf_counter()
            async with session.get("https://www.google.com", timeout=5):
                pass
            ping_ms = round((time.perf_counter() - t0) * 1000, 2)
        except Exception:
            ping_ms = 999.0

        download_speed = 0.0
        for url in DOWNLOAD_TEST_URLS:
            try:
                total = 0
                t0 = time.perf_counter()
                async with session.get(url, timeout=40) as r:
                    async for chunk in r.content.iter_chunked(8192):
                        total += len(chunk)
                        if total >= 5 * 1024 * 1024:
                            break
                dur = time.perf_counter() - t0
                if dur > 0:
                    download_speed = round((total * 8) / (dur * 1024 * 1024), 2)
                    break
            except Exception:
                continue

        upload_speed, up_url = await _try_upload_speed(1 * 1024 * 1024)

        quality = (
            "🟢 Excellent" if download_speed >= 100 else
            "🟡 Good" if download_speed >= 50 else
            "🟠 Fair" if download_speed >= 25 else
            "🔴 Poor"
        )

        stop = True
        await spin

        await msg.edit(
            f"{SPEED_EMOJI['ok']} {SPEED_EMOJI['title']} — Quick Results\n\n"
            f"{SPEED_EMOJI['ping']} Ping: {ping_ms} ms\n"
            f"{SPEED_EMOJI['download']} Download: {download_speed} Mbps\n"
            f"{SPEED_EMOJI['upload']} Upload: {upload_speed} Mbps\n\n"
            f"📊 Quality: {quality}\n"
            f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except Exception as e:
        stop = True
        try:
            await spin
        except Exception:
            pass
        await msg.edit(f"{SPEED_EMOJI['bad']} Speedtest error: {e}")


async def advanced_speedtest(event):
    msg = await event.edit(f"{FRAMES[0]} {SPEED_EMOJI['title']} — Collecting data...")
    stop = False

    async def spinner():
        i = 0
        while not stop:
            try:
                await msg.edit(f"{FRAMES[i % len(FRAMES)]} {SPEED_EMOJI['title']} — Advanced running...")
            except Exception:
                pass
            i += 1
            await asyncio.sleep(SPINNER_INTERVAL)

    spin = asyncio.create_task(spinner())

    try:
        session = await get_http_session()
        results = {}

        try:
            import psutil
            results["system"] = {
                "os": f"{platform.system()} {platform.release()}",
                "cpu": psutil.cpu_count(logical=True),
                "ram": round(psutil.virtual_memory().available / 1024**3, 1),
            }
        except Exception:
            results["system"] = {}

        try:
            async with session.get("https://api.ipify.org?format=json", timeout=6) as r:
                ip = (await r.json()).get("ip")
            async with session.get(f"https://ipapi.co/{ip}/json/", timeout=6) as r:
                geo = await r.json()
            results["network"] = {
                "ip": ip,
                "isp": geo.get("org"),
                "loc": f"{geo.get('city')}, {geo.get('country_name')}",
            }
        except Exception:
            results["network"] = {}

        ping_data = {}
        for name, url in PING_SERVERS.items():
            times = []
            for _ in range(3):
                try:
                    t0 = time.perf_counter()
                    async with session.get(url, timeout=4):
                        pass
                    times.append((time.perf_counter() - t0) * 1000)
                except Exception:
                    times.append(999.0)
            ping_data[name] = {
                "avg": round(statistics.mean(times), 1),
                "jitter": round(statistics.stdev(times), 1) if len(times) > 1 else 0.0,
            }
        results["ping"] = ping_data

        dns_data = {}
        for name, ns in DNS_SERVERS.items():
            t = await _dns_query_time(ns)
            dns_data[name] = t if t is not None else 999.0
        results["dns"] = dns_data

        download_results = {}
        for size in (5, 25, 50):
            val = 0.0
            for url in DOWNLOAD_TEST_URLS:
                try:
                    total = 0
                    t0 = time.perf_counter()
                    async with session.get(url, timeout=60) as r:
                        async for chunk in r.content.iter_chunked(8192):
                            total += len(chunk)
                            if total >= size * 1024 * 1024:
                                break
                    dur = time.perf_counter() - t0
                    if dur > 0:
                        val = round((total * 8) / (dur * 1024 * 1024), 2)
                        break
                except Exception:
                    continue
            download_results[f"{size}MB"] = val
        results["download"] = download_results

        up_speed, up_url = await _try_upload_speed(2 * 1024 * 1024)
        results["upload"] = up_speed

        stop = True
        await spin

        lines = [
            f"{SPEED_EMOJI['title']} — Advanced Results",
            "",
            f"💻 System: {results['system'].get('os')} • {results['system'].get('cpu')} cores • {results['system'].get('ram')} GB free",
            f"🌐 Network: {results['network'].get('isp')} • {results['network'].get('loc')}",
            "",
            "🏓 Ping:"
        ]
        for k, v in results["ping"].items():
            lines.append(f"• {k}: {v['avg']} ms (±{v['jitter']} ms)")
        lines += [
            "",
            "⬇️ Download:"
        ]
        for k, v in results["download"].items():
            lines.append(f"• {k}: {v} Mbps")
        lines += [
            "",
            f"⬆️ Upload: {results['upload']} Mbps",
            f"🔍 DNS fastest: {min(results['dns'].values())} ms",
            "",
            f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        await msg.edit("\n".join(lines))
    except Exception as e:
        stop = True
        try:
            await spin
        except Exception:
            pass
        await msg.edit(f"{SPEED_EMOJI['bad']} Advanced speedtest error: {e}")


def register(app):
    @app.on(events.NewMessage(pattern=r"\.speedtest(?:\s+(.*))?$", outgoing=True))
    async def handler(event):
        arg = (event.pattern_match.group(1) or "").lower()
        if arg in ("adv", "advanced"):
            await advanced_speedtest(event)
        else:
            await quick_speedtest(event)
            