"""
profile_manager.py — управление профилями значений тегов.

Профиль = именованный набор значений тегов, который можно переиспользовать
для разных отчётов.

Хранится в: server/files/users/{uuid}/engrafo/profiles/{pid}.json
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

_THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
FILES_BASE = os.path.normpath(os.path.join(_THIS_DIR, "../../server/files"))


def _profiles_dir(user_uuid: str) -> str:
    return os.path.join(FILES_BASE, "users", user_uuid, "engrafo", "profiles")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Public API ─────────────────────────────────────────────────────────────────

def list_profiles(user_uuid: str) -> list[dict]:
    pdir = _profiles_dir(user_uuid)
    if not os.path.isdir(pdir):
        return []

    profiles = []
    for fname in sorted(os.listdir(pdir)):
        if fname.endswith(".json"):
            try:
                profiles.append(_read_json(os.path.join(pdir, fname)))
            except Exception:
                pass

    profiles.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return profiles


def create_profile(user_uuid: str, name: str, tag_values: dict) -> dict:
    pdir = _profiles_dir(user_uuid)
    os.makedirs(pdir, exist_ok=True)

    pid     = str(uuid.uuid4())[:8]
    profile = {
        "id":         pid,
        "name":       name.strip() or "Без названия",
        "tag_values": tag_values,
        "created_at": _now(),
    }
    _write_json(os.path.join(pdir, f"{pid}.json"), profile)
    return profile


def get_profile(user_uuid: str, profile_id: str) -> Optional[dict]:
    path = os.path.join(_profiles_dir(user_uuid), f"{profile_id}.json")
    if not os.path.isfile(path):
        return None
    return _read_json(path)


def delete_profile(user_uuid: str, profile_id: str) -> bool:
    path = os.path.join(_profiles_dir(user_uuid), f"{profile_id}.json")
    if not os.path.isfile(path):
        return False
    os.remove(path)
    return True
