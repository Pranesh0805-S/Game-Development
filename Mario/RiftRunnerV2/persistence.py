from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SAVE_FILE = DATA_DIR / "progress.json"


def load() -> dict:
    try:
        return json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"unlocked": 1, "volume": 0.5}


def save(data: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    SAVE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
