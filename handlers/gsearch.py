import os
import aiohttp

from telethon import events

from utils.config import log, get_http_session
from utils.permissions import is_allowed


GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")


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
        if not await is_allowed(kiyoshi, event.sender_id):
            return await event.edit("Kamu tidak punya izin.")

        arg = (event.pattern_match.group(1) or "").strip()
        query = None

        if arg:
            query = arg
        elif event.is_reply:
            reply = await event.get_reply_message()
            if reply:
                query = reply.text or reply.caption

        if not query:
            return await event.edit(
                "Gunakan `.gsearch <query>` atau reply pesan."
            )

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_CSE_ID:
            return await event.edit(
                "❌ Google CSE belum dikonfigurasi.\n"
                "Set `GOOGLE_SEARCH_API_KEY` dan `GOOGLE_CSE_ID` di `.env`."
            )

        loading = await event.edit("🔎 Mencari di Google...")
        results = await google_search(query, num=3)

        if not results:
            return await loading.edit("Tidak ada hasil.")

        text = "🔎 **Hasil pencarian Google**\n\n"
        for i, r in enumerate(results, 1):
            text += (
                f"{i}. **{r['title']}**\n"
                f"{r['snippet']}\n"
                f"{r['link']}\n\n"
            )

        await loading.edit(text[:4000])
        