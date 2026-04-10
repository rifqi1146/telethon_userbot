#!/usr/bin/env bash
set -euo pipefail

echo "== Telethon Userbot Installer =="
echo

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root:"
  echo "sudo bash $0"
  exit 1
fi

if [[ ! -f "requirements.txt" ]]; then
  echo "requirements.txt not found."
  echo "Run this script from your userbot project directory."
  exit 1
fi

if command -v apt-get >/dev/null 2>&1; then
    PM="apt"
elif command -v dnf >/dev/null 2>&1; then
    PM="dnf"
elif command -v yum >/dev/null 2>&1; then
    PM="yum"
elif command -v pacman >/dev/null 2>&1; then
    PM="pacman"
elif command -v zypper >/dev/null 2>&1; then
    PM="zypper"
elif command -v apk >/dev/null 2>&1; then
    PM="apk"
else
    echo "Unsupported package manager. Please install dependencies manually."
    exit 1
fi

echo "[1/5] Installing system dependencies using $PM..."

case "$PM" in
    apt)
        export DEBIAN_FRONTEND=noninteractive
        apt-get update
        apt-get install -y \
            python3 \
            python3-venv \
            python3-pip \
            git \
            ffmpeg \
            tesseract-ocr \
            curl \
            unzip \
            build-essential \
            libjpeg-dev \
            zlib1g-dev \
            libffi-dev \
            libssl-dev
        ;;
    dnf)
        dnf install -y epel-release || true
        dnf install -y \
            python3 \
            python3-pip \
            python3-devel \
            git \
            ffmpeg \
            tesseract \
            curl \
            unzip \
            gcc \
            gcc-c++ \
            make \
            libjpeg-turbo-devel \
            zlib-devel \
            libffi-devel \
            openssl-devel
        ;;
    yum)
        yum install -y epel-release || true
        yum install -y \
            python3 \
            python3-pip \
            python3-devel \
            git \
            ffmpeg \
            tesseract \
            curl \
            unzip \
            gcc \
            gcc-c++ \
            make \
            libjpeg-turbo-devel \
            zlib-devel \
            libffi-devel \
            openssl-devel
        ;;
    pacman)
        pacman -Sy --noconfirm --needed \
            python \
            python-pip \
            python-virtualenv \
            git \
            ffmpeg \
            tesseract \
            curl \
            unzip \
            base-devel \
            libjpeg-turbo \
            zlib \
            libffi \
            openssl
        ;;
    zypper)
        zypper refresh
        zypper install -y \
            python3 \
            python3-pip \
            python3-devel \
            git \
            ffmpeg \
            tesseract-ocr \
            curl \
            unzip \
            gcc \
            gcc-c++ \
            make \
            libjpeg8-devel \
            zlib-devel \
            libffi-devel \
            libopenssl-devel
        ;;
    apk)
        apk update
        apk add \
            python3 \
            py3-pip \
            py3-virtualenv \
            git \
            ffmpeg \
            tesseract-ocr \
            curl \
            unzip \
            build-base \
            jpeg-dev \
            zlib-dev \
            libffi-dev \
            openssl-dev
        ;;
esac

echo "✔ System dependencies installed"
echo

echo "[2/5] Preparing project directories..."

mkdir -p sessions data
echo "✔ Directories ready"

echo
echo "[3/5] Creating virtual environment..."

if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "Python is not installed correctly."
    exit 1
fi

if [[ ! -d "venv" ]]; then
    "$PYTHON_CMD" -m venv venv
    echo "✔ Virtual environment created"
else
    echo "✔ Virtual environment already exists"
fi

source venv/bin/activate

echo
echo "[4/5] Installing Python dependencies..."

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "✔ Python dependencies installed"

echo
echo "[5/5] Creating .env template..."

if [[ ! -f ".env" ]]; then
    cat > .env <<'EOF'
API_ID=
API_HASH=
SESSION_NAME=sessions/userbot_session
GROQ_API_KEY=
OPENROUTER_API_KEY=
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${GEMINI_API_KEY}
GOOGLE_SEARCH_API_KEY=
GOOGLE_CSE_ID=
STARTUP_CHAT_ID=
EOF
    echo "✔ .env template created"
else
    echo "✔ .env already exists, skipped"
fi

deactivate

echo
echo "Done!"
echo
echo "Next steps:"
echo "1. nano .env"
echo "2. Fill API_ID, API_HASH, SESSION_NAME, and API keys if needed"
echo "3. Run:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo
echo "Happy"