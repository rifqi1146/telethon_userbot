from telethon import events

def register(client):

    @app.on(events.NewMessage(pattern=r"\.menu$", outgoing=True))
    async def cmd_menu(event):
        menu = (
            "🌸 **Userbot Menu** 🌸\n\n"

            "💼 **General**\n"
            "• ✨ .ping — check latency\n"
            "• 💗 .alive — check userbot status\n"
            "• 🧾 .info — user / chat info\n"
            "• 📖 .menu — open this menu\n"
            "• 💤 .afk — enable AFK\n\n"

            "🛠️ **Utilities**\n"
            "• 🔤 .ascii — convert text to ASCII art\n"
            "• 🌀 .mock — mock text (aLtErNaTiNg cApS)\n"
            "• ▒  .spoiler — create spoiler text\n"
            "• 🕵️ .whois — advanced user info\n"
            "• ☁️ .weather — weather information\n"
            "• 📚 .unroll — summarize webpage\n"
            "• 🌍 .tr <lang> — translate text\n\n"

            "🌐 **Networking**\n"
            "• 🌍 .ip — IP lookup\n"
            "• 🏷️ .domain — domain info\n"
            "• 🧠 .whoisdomain — WHOIS lookup\n\n"

            "📥 **Downloader**\n"
            "• ⬇️ .dl — download TikTok / IG / YouTube\n\n"

            "🧠 **Artificial Intelligence**\n"
            "• 🌕 .ai — Gemini AI\n"
            "• 🧸 .groq — Groq AI\n"
            "• 🌐 .gsearch — Google search\n\n"

            "⚙️ **System**\n"
            "• 🔁 .restart — restart userbot\n\n"

            "💡 **Note**\n"
            "- Auto-reply aktif di DM kecuali approved\n"
            "- Spam >3x auto-block\n"
        )

        await event.edit(menu)

