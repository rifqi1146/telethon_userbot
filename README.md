![Python](https://img.shields.io/badge/Python-3.13-2b5b84?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-GPLv3-5c2d91?style=for-the-badge)
![Telethon](https://img.shields.io/badge/Telethon-Async%20Client-229ED9?style=for-the-badge&logo=telegram&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-ChatGPT-10A37F?style=for-the-badge&logo=openai&logoColor=white)

# Telethon Userbot

Simple modular Telegram userbot built with **Telethon**.

## Features

- User management
- Group moderation
- AI commands
- QR generate / read
- Sticker tools
- Downloader
- Networking tools
- Weather lookup
- Speedtest
- Backup / restore data
- Modular handler structure

---

## Quick Installation (Recommended)

The recommended installation method is to use the provided installer script:

### 1. Clone repository
```bash
git clone https://github.com/rifqi1146/telethon_userbot.git
cd telethon_userbot
sudo bash install.sh
```
## Manual Installation
```
apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    ffmpeg \
    tesseract-ocr
```
# Create venv
```
python3 -m venv venv
source venv/bin/activate
```
# Install dependencies 
```
pip install -r requirements.txt
```
# Setup env
```
nano .env
```
# Sample .env
```
API_ID=
API_HASH=
SESSION_NAME=sessions/userbot_session
GROQ_API_KEY=
OPENROUTER_API_KEY=
GEMINI_API_URL="https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${GEMINI_API_KEY}"
GEMINI_API_KEY=
GOOGLE_SEARCH_API_KEY=
GOOGLE_CSE_ID=
STARTUP_CHAT_ID=-8187383
```
# Reload .env
``` 
source .env
```
# Run userbot
```
python main.py
 ```

## Credits

- [Moon-Tg](https://github.com/The-MoonTg-project/Moon-Userbot)
- [Groq Cloud](https://console.groq.com/home)
- [Google Gemini](https://ai.google.dev/)
- [TikWm](https://www.tikwm.com/)
- [Telethon](https://github.com/lonamiwebs/telethon)
- [Team Ultroid](https://github.com/TeamUltroid/Ultroid/)

