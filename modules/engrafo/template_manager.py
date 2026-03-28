"""
template_manager.py — загрузка шаблонов, извлечение тегов.

Шаблоны хранятся в двух местах:
  - server/files/global_templates/  — глобальные (для всех пользователей, только admin)
  - server/files/users/{uuid}/engrafo/templates/  — личные шаблоны пользователя
"""

import os
from typing import Optional


# ── Пути ──────────────────────────────────────────────────────────────────────

_THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
FILES_BASE = os.path.normpath(os.path.join(_THIS_DIR, "../../server/files"))

GLOBAL_TEMPLATES_DIR = os.path.join(FILES_BASE, "global_templates")


def _user_tpl_dir(user_uuid: str) -> str:
    return os.path.join(FILES_BASE, "users", user_uuid, "engrafo", "templates")


# ── Public API ─────────────────────────────────────────────────────────────────

def list_templates(user_uuid: str) -> list[dict]:
    """Вернуть список всех доступных шаблонов: глобальных + личных пользователя."""
    templates: list[dict] = []

    os.makedirs(GLOBAL_TEMPLATES_DIR, exist_ok=True)
    for fname in sorted(os.listdir(GLOBAL_TEMPLATES_DIR)):
        if fname.lower().endswith(".docx"):
            templates.append({
                "id":     f"global::{fname}",
                "name":   os.path.splitext(fname)[0],
                "source": "global",
            })

    tpl_dir = _user_tpl_dir(user_uuid)
    if os.path.exists(tpl_dir):
        for fname in sorted(os.listdir(tpl_dir)):
            if fname.lower().endswith(".docx"):
                templates.append({
                    "id":     f"personal::{fname}",
                    "name":   os.path.splitext(fname)[0],
                    "source": "personal",
                })

    return templates


def get_template_path(user_uuid: str, template_id: str) -> Optional[str]:
    """Вернуть абсолютный путь к файлу шаблона по его ID."""
    if template_id.startswith("global::"):
        fname = template_id[len("global::"):]
        path  = os.path.join(GLOBAL_TEMPLATES_DIR, fname)
        return path if os.path.isfile(path) else None

    if template_id.startswith("personal::"):
        fname = template_id[len("personal::"):]
        path  = os.path.join(_user_tpl_dir(user_uuid), fname)
        return path if os.path.isfile(path) else None

    return None


def extract_tags(template_path: str) -> list[dict]:
    """
    Извлечь теги из docx-шаблона напрямую через XML.
    Поддерживает формат {{key}} и {{key:Подсказка}}.
    Возвращает список [{"key": "имя", "label": "Подсказка или имя"}].
    """
    import zipfile, re
    try:
        with zipfile.ZipFile(template_path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        # Убираем XML-теги внутри {{ }} чтобы склеить разбитые runs
        clean = re.sub(r"<[^>]+>", "", xml)
        raw_tags = re.findall(r"\{\{([^}]+)\}\}", clean)
        seen: dict[str, str] = {}
        for raw in raw_tags:
            raw = raw.strip()
            if ":" in raw:
                key, _, label = raw.partition(":")
                key   = key.strip()
                label = label.strip()
            else:
                key   = raw
                label = raw
            if key and key not in seen:
                seen[key] = label
        return [{"key": k, "label": v} for k, v in seen.items()]
    except Exception:
        return []


def save_personal_template(user_uuid: str, filename: str, content: bytes) -> dict:
    """Сохранить личный шаблон пользователя."""
    tpl_dir = _user_tpl_dir(user_uuid)
    os.makedirs(tpl_dir, exist_ok=True)

    # Санитизация имени файла (кириллица разрешена)
    safe = "".join(c for c in filename if c.isalnum() or c.isalpha() or c in "-_. ")
    safe = safe.strip()
    if not safe.lower().endswith(".docx"):
        safe += ".docx"
    if safe == ".docx":
        safe = "template.docx"

    path = os.path.join(tpl_dir, safe)
    with open(path, "wb") as f:
        f.write(content)

    return {
        "id":     f"personal::{safe}",
        "name":   os.path.splitext(safe)[0],
        "source": "personal",
    }


def delete_personal_template(user_uuid: str, filename: str) -> bool:
    path = os.path.join(_user_tpl_dir(user_uuid), filename)
    if not os.path.isfile(path):
        return False
    os.remove(path)
    return True
