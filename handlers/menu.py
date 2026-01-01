from telethon import events


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"\.menu$", outgoing=True))
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
            "• 🐄 .cowsay — cowwww????????\n"
            "• 🕵️ .whois — advanced user info\n"
            "• ☁️ .weather — weather information\n"
            "• 🌍 .tr <lang> — translate text\n\n"

            "🌐 **Networking**\n"
            "• 🌍 .ip — IP lookup\n"
            "• 🏷️ .domain — domain info\n"
            "• 🧠 .whoisdomain — WHOIS lookup\n\n"

            "📥 **Downloader**\n"
            "• ⬇️ .dl — download TikTok\n\n"

            "🧠 **Artificial Intelligence**\n"
            "• 🌕 .ai — Gemini AI\n"
            "• 🧸 .groq — Groq AI\n"
            "• 🌏 .ask — OpenAi/ChatGpt\n"
            "• 🌐 .gsearch — Google search\n\n"

            "🛡️ **Moderation**\n"
            "• 🤫 .mute — mute user\n"
            "• 🔊 .unmute — unmute user\n"
            "• 🚫 .ban — ban user\n"
            "• ♻️ .unban — unban user\n"
            "• 👢 .kick — kick user\n\n"

            "👥 **User Management**\n"
            "• ➕ .add — add user to group\n"
            "• 👀 .id — show id user and chat id\n"
            "• 📈 .promote — promote to admin\n"
            "• 📉 .demote — demote admin\n\n"

            "📫 **DM Control**\n"
            "• 💌 .approve — allow DM\n"
            "• ❌ .unapprove — revoke DM\n"
            "• 📃 .approved — list approved users\n"
            "• 🔒 .block — block user\n\n"

            "📌 **Messages**\n"
            "• 📌 .pin — pin message\n"
            "• 📎 .unpin — unpin message\n"
            "• 🧹 .purge — delete messages\n"
            "• 🗑️ .del — delete replied message\n\n"

            "🎨 **Stickers**\n"
            "• 🖼️ .kang — create / add to sticker pack\n"
            "• ✨ .q / .quotly — make quote sticker\n\n"

            "🔍 **QR & Codes**\n"
            "• 🧾 .qr — generate QR code\n"
            "• 🔎 .readqr — read QR code from image\n"
            "• 🎀 .qrstyle — set default QR style\n\n"

            "⚡ **Performance**\n"
            "• 🏁 .speedtest — run speedtest\n"
            "• 🚀 .speedtest adv — advanced speedtest\n\n"

            "📊 **Group / Stats**\n"
            "• 📜 .admins — list admins\n"
            "• 📈 .stats — group statistics\n"
            "• 🏷️ .settitle — set chat title\n"
            "• ♻️ .restoretitle — restore original title\n\n"

            "⚙️ **System**\n"
            "• 🔁 .restart — restart userbot\n\n"

            "💡 **Note**\n"
            "- Auto-reply aktif di DM kecuali approved\n"
            "- Spam >3x auto-block\n"
        )

        await event.edit(menu)
