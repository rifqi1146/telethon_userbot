from telethon import events
from deep_translator import GoogleTranslator, MyMemoryTranslator, LibreTranslator


DEFAULT_LANG = "en"

VALID_LANGS = {
    "en","id","ja","ko","zh","fr","de","es","it","ru","ar","hi","pt","tr",
    "vi","th","ms","nl","pl","uk","sv","fi"
}


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.tr(?:\s+(.*))?$", outgoing=True))
    async def tr_handler(event):
        arg = (event.pattern_match.group(1) or "").strip()
        args = arg.split() if arg else []

        target_lang = DEFAULT_LANG
        text = ""

        if args:
            first = args[0].lower()

            if first in VALID_LANGS and len(args) >= 2:
                target_lang = first
                text = " ".join(args[1:])
            elif first in VALID_LANGS and len(args) == 1:
                target_lang = first
            else:
                text = " ".join(args)

        if not text:
            if event.is_reply:
                reply = await event.get_reply_message()
                if reply and reply.text:
                    text = reply.text

        if not text:
            return await event.edit(
                "🔤 **Translator**\n\n"
                "Contoh:\n"
                "`.tr en hello bro`\n"
                "`.tr id good morning`\n"
                "`.tr apa kabar bro?`\n\n"
                "Atau reply pesan:\n"
                "`.tr en`"
            )

        status = await event.edit("🔤 Translating...")

        translators = []
        try:
            translators.append(("Google", GoogleTranslator))
        except Exception:
            pass
        try:
            translators.append(("MyMemory", MyMemoryTranslator))
        except Exception:
            pass
        try:
            translators.append(("Libre", LibreTranslator))
        except Exception:
            pass

        if not translators:
            return await status.edit("❌ Translator tidak tersedia")

        for name, T in translators:
            try:
                tr = T(source="auto", target=target_lang)
                translated = tr.translate(text)

                try:
                    detected = tr.detect(text)
                except Exception:
                    detected = "auto"

                out = (
                    f"✅ **Translated → {target_lang.upper()}**\n\n"
                    f"{translated}\n\n"
                    f"🔍 Source: `{detected}`\n"
                    f"🔧 Engine: `{name}`"
                )

                return await status.edit(out)

            except Exception:
                continue

        await status.edit("❌ Semua translator gagal")