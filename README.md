![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-GPL--3.0-blue?style=flat)
![Telethon](https://img.shields.io/badge/Telethon-Async%20Telegram%20Client-26A5E4?style=flat&logo=telegram&logoColor=white)

# Step Install

# Dependency
```
apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    ffmpeg \
    tesseract-ocr
```

# Clone repo

```
git clone https://github.com/rifqi1146/telethon_userbot.git
```
# Masuk folder
```
cd telethon_userbot
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

## 🙏 Credits

This project was developed using ideas and architectural references from:

- Moon Userbot (GPL-3.0)  
  https://github.com/The-MoonTg-project/Moon-Userbot


