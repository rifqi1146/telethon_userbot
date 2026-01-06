import os
import aiohttp

from telethon import events

from utils.config import (
    log, 
    get_http_session,
    GOOGLE_CSE_ID,
    GOOGLE_SEARCH_API_KEY,
)

from utils.permissions import is_allowed


async def google_search(query: str, num: int = 3) -> list:
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_CSE_ID:
        return []

    try:
        session = await get_http_session()
        params = {
            "key": GOOGLE_SEARCH_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": query,
            "num": min(max(1, num), 10),
        }

        async with session.get(
            "https://www.googleapis.com/customsearch/v1",
            params=params,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                log.warning(
                    "Google CSE error %s: %s",
                    resp.status,
                    text[:200],
                )
                return []

            data = await resp.json()

        items = data.get("items") or []
        return [
            {
                "title": it.get("title", "")[:200],
                "snippet": it.get("snippet", "")[:400],
                "link": it.get("link", ""),
            }
            for it in items[:num]
        ]

    except Exception:
        log.exception("google_search failed")
        return []


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.gsearch(?:\s+(.*))?$", outgoing=True))
    async def gsearch_cmd(event):
        arg = (event.pattern_match.group(1) or "").strip()
        query = None
        limit = 3

        if arg:
            parts = arg.split()
            for p in parts[:]:
                if p.startswith("--") and p[2:].isdigit():
                    limit = int(p[2:])
                    parts.remove(p)
            query = " ".join(parts).strip()

        if not query and event.is_reply:
            reply = await event.get_reply_message()
            if reply:
                query = reply.text or reply.caption

        if not query:
            await event.edit("Gunakan `.gsearch <query>` atau reply pesan `--5`")
            return

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_CSE_ID:
            await event.edit(
                "❌ Google CSE belum dikonfigurasi.\n"
                "Set `GOOGLE_SEARCH_API_KEY` dan `GOOGLE_CSE_ID` di `.env`."
            )
            return

        limit = max(1, min(limit, 10))

        loading = await event.edit(f"🔎 Mencari di Google ({limit} hasil)...")
        results = await google_search(query, num=limit)

        if not results:
            await loading.edit("Tidak ada hasil.")
            return

        text = f"🔎 **Hasil pencarian Google ({limit})**\n\n"
        for i, r in enumerate(results, 1):
            text += (
                f"{i}. **{r['title']}**\n"
                f"{r['snippet']}\n"
                f"{r['link']}\n\n"
            )

        await loading.edit(text[:4000])