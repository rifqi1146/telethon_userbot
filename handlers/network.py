import socket
import whois

from telethon import events
from utils.config import get_http_session


def _clean_domain(raw: str) -> str:
    return (
        raw.replace("http://", "")
        .replace("https://", "")
        .split("/")[0]
        .strip()
    )


def register(app):

    # ===== .domain =====
    @app.on(events.NewMessage(pattern=r"\.domain(?:\s+(.+))?$", outgoing=True))
    async def domain_info(event):
        arg = event.pattern_match.group(1)
        if not arg:
            return await event.edit(
                "**Usage:** `.domain [domain]`\n"
                "**Example:** `.domain google.com`"
            )

        domain = _clean_domain(arg)
        await event.edit(f"**🔄 Analyzing domain `{domain}`...**")

        info = {}

        try:
            info["ip"] = socket.gethostbyname(domain)
        except Exception:
            info["ip"] = "Not found"

        try:
            w = whois.whois(domain)
            info["registrar"] = w.registrar or "Not available"
            info["created"] = str(w.creation_date) if w.creation_date else "Not available"
            info["expires"] = str(w.expiration_date) if w.expiration_date else "Not available"
            info["ns"] = w.name_servers or ["Not available"]
        except Exception:
            info.update({
                "registrar": "Not available",
                "created": "Not available",
                "expires": "Not available",
                "ns": ["Not available"]
            })

        try:
            session = await get_http_session()
            async with session.get(f"http://{domain}", timeout=10) as r:
                info["http"] = r.status
                info["server"] = r.headers.get("server", "Not available")
        except Exception:
            info["http"] = "Not available"
            info["server"] = "Not available"

        ns = info["ns"]
        ns_text = (
            "\n".join(f"• {x}" for x in ns[:5])
            if isinstance(ns, list) else str(ns)
        )

        result = (
            "**🌐 Domain Information**\n\n"
            f"**Domain:** {domain}\n"
            f"**IP Address:** {info['ip']}\n"
            f"**HTTP Status:** {info['http']}\n"
            f"**Server:** {info['server']}\n\n"
            "**📋 Registration Details**\n"
            f"**Registrar:** {info['registrar']}\n"
            f"**Created:** {info['created']}\n"
            f"**Expires:** {info['expires']}\n\n"
            "**🔧 Name Servers**\n"
            f"{ns_text}"
        )

        await event.edit(result)


    # ===== .whoisdomain =====
    @app.on(events.NewMessage(pattern=r"\.whoisdomain(?:\s+(.+))?$", outgoing=True))
    async def whois_domain(event):
        arg = event.pattern_match.group(1)
        if not arg:
            return await event.edit(
                "**Usage:** `.whoisdomain [domain]`\n"
                "**Example:** `.whoisdomain google.com`"
            )

        domain = _clean_domain(arg)
        await event.edit(f"**🔄 Getting WHOIS data for `{domain}`...**")

        try:
            w = whois.whois(domain)

            def fmt(v):
                if isinstance(v, list):
                    return str(v[0]) if v else "Not available"
                return str(v) if v else "Not available"

            ns = w.name_servers
            ns_text = (
                "\n".join(f"• {x}" for x in ns[:8])
                if isinstance(ns, list) else fmt(ns)
            )

            result = (
                "**📋 WHOIS Information**\n\n"
                f"**Domain:** `{domain}`\n"
                f"**Registrar:** `{fmt(w.registrar)}`\n"
                f"**WHOIS Server:** `{fmt(w.whois_server)}`\n\n"
                "**📅 Important Dates**\n"
                f"**Created:** `{fmt(w.creation_date)}`\n"
                f"**Updated:** `{fmt(w.updated_date)}`\n"
                f"**Expires:** `{fmt(w.expiration_date)}`\n\n"
                "**👤 Registrant**\n"
                f"**Name:** `{fmt(w.name)}`\n"
                f"**Organization:** `{fmt(w.org)}`\n"
                f"**Email:** `{fmt(w.emails)}`\n\n"
                "**🔧 Technical Details**\n"
                f"**Status:** `{fmt(w.status)}`\n"
                f"**DNSSEC:** `{fmt(w.dnssec)}`\n\n"
                "**🌐 Name Servers**\n"
                f"{ns_text}\n\n"
                "**🏢 Registrar Info**\n"
                f"**Registrar IANA ID:** `{fmt(w.registrar_iana_id)}`\n"
                f"**Registrar URL:** `{fmt(w.registrar_url)}`"
            )

            if len(result) > 4000:
                await event.edit(result[:4000])
                await event.reply(result[4000:])
            else:
                await event.edit(result)

        except Exception as e:
            await event.edit(f"**❌ WHOIS lookup failed:** `{e}`")


    # ===== .ip =====
    @app.on(events.NewMessage(pattern=r"\.ip(?:\s+(.+))?$", outgoing=True))
    async def ip_info(event):
        arg = event.pattern_match.group(1)
        if not arg:
            return await event.edit(
                "**Usage:** `.ip [ip]`\n"
                "**Example:** `.ip 8.8.8.8`"
            )

        ip = arg.strip()
        await event.edit(f"**🔄 Analyzing IP `{ip}`...**")

        try:
            session = await get_http_session()
            url = (
                "http://ip-api.com/json/"
                f"{ip}?fields=status,message,continent,country,countryCode,"
                "region,regionName,city,zip,lat,lon,timezone,offset,"
                "isp,org,as,reverse,mobile,proxy,hosting,query"
            )

            async with session.get(url, timeout=15) as r:
                data = await r.json()

            if data.get("status") != "success":
                return await event.edit(
                    f"**❌ Failed to get IP info:** {data.get('message')}"
                )

            result = (
                "**🌍 IP Address Information**\n\n"
                f"**IP:** {data.get('query')}\n"
                f"**ISP:** {data.get('isp')}\n"
                f"**Organization:** {data.get('org')}\n"
                f"**AS:** {data.get('as')}\n\n"
                "**📍 Location**\n"
                f"**Country:** {data.get('country')} ({data.get('countryCode')})\n"
                f"**Region:** {data.get('regionName')} ({data.get('region')})\n"
                f"**City:** {data.get('city')}\n"
                f"**ZIP Code:** {data.get('zip')}\n"
                f"**Coordinates:** {data.get('lat')}, {data.get('lon')}\n\n"
                "**🕐 Time Zone**\n"
                f"**Timezone:** {data.get('timezone')}\n"
                f"**UTC Offset:** {data.get('offset')}\n\n"
                "**🔍 Additional Info**\n"
                f"**Reverse DNS:** {data.get('reverse')}\n"
                f"**Mobile:** {'Yes' if data.get('mobile') else 'No'}\n"
                f"**Proxy:** {'Yes' if data.get('proxy') else 'No'}\n"
                f"**Hosting:** {'Yes' if data.get('hosting') else 'No'}"
            )

            await event.edit(result)

        except Exception as e:
            await event.edit(f"**❌ Error:** `{e}`")
            