import os
import sys
import logging
from dotenv import load_dotenv


# load env
load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "userbot")

if not API_ID or not API_HASH:
    print("API_ID / API_HASH belum diset")
    sys.exit(1)


# logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("userbot")

