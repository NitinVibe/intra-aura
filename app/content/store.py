import json
from pathlib import Path
from threading import Lock

CONTENT_PATH = Path(__file__).resolve().parent / "site_content.json"
_LOCK = Lock()

def load_content():
    with _LOCK:
        try:
            return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

def save_content(data):
    with _LOCK:
        CONTENT_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONTENT_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(CONTENT_PATH)

def get_page(name):
    return load_content().get(name, {})
