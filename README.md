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
GROQ_API_KEY=
GEMINI_API_KEY=
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
