import asyncio
import time
from collections import deque
from telethon import events

QUOTLY_BOT = "QuotLyBot"
MAX_WAIT = 30
POLL_INTERVAL = 0.6
CACHE_SIZE = 50

_cache = deque(maxlen=CACHE_SIZE)


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(from_users=QUOTLY_BOT))
    async def _quotly_listener(event):
        _cache.appendleft(event.message)

    @kiyoshi.on(events.NewMessage(pattern=r"\.(q|quotly)(?:\s+(\d+))?$", outgoing=True))
    async def quotly_handler(event):
        if not event.is_reply:
            return await event.edit("Reply ke pesan yang mau di-quote")

        reply = await event.get_reply_message()
        count = int(event.pattern_match.group(2) or 1)
        count = max(1, min(count, 10))

        await event.edit("✨ Creating quote...")

        chat_id = event.chat_id
        start_ts = time.time()

        msgs = [reply]
        last_id = reply.id

        if count > 1:
            async for m in kiyoshi.iter_messages(chat_id, min_id=last_id, limit=count - 1):
                msgs.append(m)
                if len(msgs) >= count:
                    break

        msgs = sorted(msgs, key=lambda x: x.id)

        try:
            for m in msgs:
                await m.forward_to(QUOTLY_BOT)
                await asyncio.sleep(0.15)
        except Exception as e:
            return await event.edit(f"❌ Gagal kirim ke QuotLy\n{e}")

        deadline = time.time() + MAX_WAIT
        sent = set()

        while time.time() < deadline:
            await asyncio.sleep(POLL_INTERVAL)

            for m in list(_cache):
                if m.id in sent:
                    continue
                if not m.media:
                    continue
                if m.date.timestamp() < start_ts:
                    continue

                sent.add(m.id)

                await kiyoshi.send_file(
                    chat_id,
                    m.media,
                    reply_to=event.reply_to_msg_id
                )

                await event.delete()
                return

        await event.edit("❌ Timeout — QuotLy tidak ngerespon")
        