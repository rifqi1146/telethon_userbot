import json
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

_FILE = DATA_DIR / "autoreply.json"

def load_autoreply():
    try:
        if _FILE.exists():
            return json.loads(_FILE.read_text()).get("enabled", True)
    except Exception:
        pass
    return True

def save_autoreply(v: bool):
    try:
        _FILE.write_text(json.dumps({"enabled": v}, indent=2))
    except Exception:
        pass