import random
import time
import os
import platform
import psutil

from telethon import events
from telethon.version import __version__ as telethon_version


def register(kiyoshi):
    @kiyoshi.on(events.NewMessage(pattern=r"\.alive$", outgoing=True))
    async def cmd_alive(event):
        me = await kiyoshi.get_me()

        try:
            await event.delete()
        except Exception:
            pass

        def _human_size(b):
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if b < 1024:
                    return f"{b:.2f}{unit}"
                b /= 1024
            return f"{b:.2f}PB"

        os_name = platform.system()
        os_release = platform.release()
        os_distro = ""

        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME"):
                            os_distro = line.split("=", 1)[1].strip().strip('"')
                            break
        except Exception:
            pass

        os_full = os_distro or f"{os_name} {os_release}"

        cpu_cores = psutil.cpu_count(logical=True) or 1
        cpu_usage = psutil.cpu_percent(interval=1)

        try:
            la1, la5, la15 = os.getloadavg()
            load_pct = (
                round((la1 / cpu_cores) * 100, 1),
                round((la5 / cpu_cores) * 100, 1),
                round((la15 / cpu_cores) * 100, 1),
            )
        except Exception:
            load_pct = ("?", "?", "?")

        vm = psutil.virtual_memory()
        ram_used = _human_size(vm.used)
        ram_total = _human_size(vm.total)
        ram_percent = vm.percent

        disk = psutil.disk_usage("/")
        disk_used = _human_size(disk.used)
        disk_total = _human_size(disk.total)
        disk_percent = disk.percent

        boot = psutil.boot_time()
        uptime_sec = int(time.time() - boot)
        days, rem = divmod(uptime_sec, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        uptime = f"{days}d {hours}h {minutes}m"

        python_ver = platform.python_version()

        full_name = " ".join(x for x in [me.first_name, me.last_name] if x).strip()
        username = f"@{me.username}" if me.username else "—"

        caption = (
            f"👤 **User:** {full_name}\n"
            f"🔖 **Username:** {username}\n"
            f"🆔 **ID:** `{me.id}`\n\n"
            f"🖥️ **OS:** {os_full}\n"
            f"⚙️ **CPU:** {cpu_cores} cores • {cpu_usage}% usage\n"
            f"📊 **Load Avg:** {load_pct[0]}% / {load_pct[1]}% / {load_pct[2]}%\n\n"
            f"🧠 **RAM:** {ram_used} / {ram_total} ({ram_percent}%)\n"
            f"💾 **Disk:** {disk_used} / {disk_total} ({disk_percent}%)\n\n"
            f"🕒 **Uptime:** {uptime}\n"
            f"🐍 **Python:** {python_ver}\n"
            f"📡 **Telethon:** v{telethon_version}\n\n"
            f"✨ **Status:** All systems operational"
        )

        banner_path = "assets/banner.png"

        if os.path.exists(banner_path):
            await kiyoshi.send_file(
                event.chat_id,
                banner_path,
                caption=caption
            )
        else:
            await kiyoshi.send_message(event.chat_id, caption)

