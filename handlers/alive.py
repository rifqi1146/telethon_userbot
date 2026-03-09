import time
import os
import platform
import psutil
import telethon

from telethon import events
from telethon.version import __version__ as telethon_version

def _system_info():
    cpu_usage = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()

    return {
        "cpu": f"{cpu_usage}%",
        "ram_used": f"{_bytes_to_mb(mem.used)} MB",
        "ram_total": f"{_bytes_to_mb(mem.total)} MB",
        "hostname": socket.gethostname(),
        "user": getpass.getuser(),
        "os": f"{platform.system()} {platform.release()}",
        "arch": platform.machine(),
        "python": platform.python_version(),
        "telethon": telethon.__version__,
    }

def register(kiyoshi):
    @kiyoshi.on(events.NewMessage(pattern=r"\.alive$", outgoing=True))
    async def cmd_alive(event):
        me = await kiyoshi.get_me()

        topic_id = None
        try:
            reply = getattr(event.message, "reply_to", None)
            if reply:
                topic_id = getattr(reply, "reply_to_top_id", None) or getattr(reply, "reply_to_msg_id", None)
        except Exception:
            topic_id = None

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
            "**System Info**\n"
            f"• Hostname: `{info['hostname']}`\n"
            f"• **OS:** {os_full}\n"
            f"• **Arch:** `{info['arch']}`\n"
            f"• **CPU:** {cpu_cores} cores • {cpu_usage}% usage\n"
            f"• **Load Avg:** {load_pct[0]}% / {load_pct[1]}% / {load_pct[2]}%\n\n"
            f"• **RAM:** {ram_used} / {ram_total} ({ram_percent}%)\n"
            f"• **Disk:** {disk_used} / {disk_total} ({disk_percent}%)\n\n"
            f"• **Uptime:** {uptime}\n"
            f"• **Python:** {python_ver}\n"
            f"• **Telethon:** v{telethon_version}\n\n"
            "🌸 **Powered by Kiyoshi Userbot**"
        )

        try:
            await event.delete()
        except Exception:
            pass

        banner_path = "assets/banner.png"

        send_kwargs = {}
        if topic_id:
            send_kwargs["reply_to"] = topic_id

        if os.path.exists(banner_path):
            await kiyoshi.send_file(
                event.chat_id,
                banner_path,
                caption=caption,
                **send_kwargs
            )
        else:
            await kiyoshi.send_message(
                event.chat_id,
                caption,
                **send_kwargs
            )

