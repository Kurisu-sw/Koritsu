"""
report_manager.py — жизненный цикл отчёта: создание, редактирование, версии.

Структура файлов:
  server/files/users/{uuid}/engrafo/reports/{report_id}/
    ├── meta.json        — метаданные отчёта
    ├── tag_values.json  — текущие значения тегов
    ├── current.docx     — последний заполненный документ
    ├── current.pdf      — последний PDF preview
    └── versions/
        └── {vid}/
            ├── snapshot.docx
            └── meta.json
"""

import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from typing import Optional

# ── Пути ──────────────────────────────────────────────────────────────────────

_THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
FILES_BASE = os.path.normpath(os.path.join(_THIS_DIR, "../../server/files"))

MAX_VERSIONS = 3


def _reports_dir(user_uuid: str) -> str:
    return os.path.join(FILES_BASE, "users", user_uuid, "engrafo", "reports")


def _report_dir(user_uuid: str, report_id: str) -> str:
    return os.path.join(_reports_dir(user_uuid), report_id)


def _versions_dir(user_uuid: str, report_id: str) -> str:
    return os.path.join(_report_dir(user_uuid, report_id), "versions")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Reports ────────────────────────────────────────────────────────────────────

def create_report(user_uuid: str, template_id: str, template_name: str,
                  title: str = "") -> dict:
    report_id  = str(uuid.uuid4())[:8]
    report_dir = _report_dir(user_uuid, report_id)

    os.makedirs(os.path.join(report_dir, "versions"), exist_ok=True)

    meta = {
        "id":            report_id,
        "title":         title.strip() or f"Отчёт {report_id}",
        "template_id":   template_id,
        "template_name": template_name,
        "created_at":    _now(),
        "updated_at":    _now(),
    }

    _write_json(os.path.join(report_dir, "meta.json"),       meta)
    _write_json(os.path.join(report_dir, "tag_values.json"), {})

    return meta


def list_reports(user_uuid: str) -> list[dict]:
    reports_dir = _reports_dir(user_uuid)
    if not os.path.isdir(reports_dir):
        return []

    result = []
    for rid in os.listdir(reports_dir):
        meta = _read_report_meta(user_uuid, rid)
        if meta:
            result.append(meta)

    result.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
    return result


def get_report(user_uuid: str, report_id: str) -> Optional[dict]:
    meta = _read_report_meta(user_uuid, report_id)
    if not meta:
        return None
    meta["tag_values"] = _read_tag_values(user_uuid, report_id)
    return meta


def update_tag_values(user_uuid: str, report_id: str, tag_values: dict) -> bool:
    report_dir = _report_dir(user_uuid, report_id)
    if not os.path.isdir(report_dir):
        return False

    _write_json(os.path.join(report_dir, "tag_values.json"), tag_values)

    meta_path = os.path.join(report_dir, "meta.json")
    if os.path.isfile(meta_path):
        meta = _read_json(meta_path)
        meta["updated_at"] = _now()
        _write_json(meta_path, meta)

    return True


def delete_report(user_uuid: str, report_id: str) -> bool:
    report_dir = _report_dir(user_uuid, report_id)
    if not os.path.isdir(report_dir):
        return False
    shutil.rmtree(report_dir, ignore_errors=True)
    return True


def finalize_report(user_uuid: str, report_id: str):
    """Завершить работу: удалить все версии, оставить только current."""
    ver_dir = _versions_dir(user_uuid, report_id)
    if os.path.isdir(ver_dir):
        shutil.rmtree(ver_dir, ignore_errors=True)
    os.makedirs(ver_dir, exist_ok=True)


# ── Versions ───────────────────────────────────────────────────────────────────

def save_version(user_uuid: str, report_id: str) -> Optional[dict]:
    """Сохранить текущее состояние как версию."""
    report_dir   = _report_dir(user_uuid, report_id)
    current_docx = os.path.join(report_dir, "current.docx")

    if not os.path.isfile(current_docx):
        return None

    ver_dir = _versions_dir(user_uuid, report_id)
    os.makedirs(ver_dir, exist_ok=True)

    # Удалить старые версии если > MAX_VERSIONS
    existing = sorted(os.listdir(ver_dir))
    while len(existing) >= MAX_VERSIONS:
        shutil.rmtree(os.path.join(ver_dir, existing.pop(0)), ignore_errors=True)

    ts         = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    version_id = f"v_{ts}"
    vdir       = os.path.join(ver_dir, version_id)
    os.makedirs(vdir, exist_ok=True)

    shutil.copy2(current_docx, os.path.join(vdir, "snapshot.docx"))

    vmeta = {
        "id":         version_id,
        "saved_at":   _now(),
        "tag_values": _read_tag_values(user_uuid, report_id),
    }
    _write_json(os.path.join(vdir, "meta.json"), vmeta)
    return vmeta


def list_versions(user_uuid: str, report_id: str) -> list[dict]:
    ver_dir = _versions_dir(user_uuid, report_id)
    if not os.path.isdir(ver_dir):
        return []

    versions = []
    for vid in sorted(os.listdir(ver_dir), reverse=True):
        meta_path = os.path.join(ver_dir, vid, "meta.json")
        if os.path.isfile(meta_path):
            versions.append(_read_json(meta_path))
    return versions


def _delete_version(user_uuid: str, report_id: str, version_id: str) -> bool:
    """Удалить конкретную версию по ID."""
    vdir = os.path.join(_versions_dir(user_uuid, report_id), version_id)
    if not os.path.isdir(vdir):
        return False
    shutil.rmtree(vdir, ignore_errors=True)
    return True


def restore_version(user_uuid: str, report_id: str, version_id: str) -> bool:
    report_dir = _report_dir(user_uuid, report_id)
    vdir       = os.path.join(_versions_dir(user_uuid, report_id), version_id)
    snapshot   = os.path.join(vdir, "snapshot.docx")

    if not os.path.isfile(snapshot):
        return False

    shutil.copy2(snapshot, os.path.join(report_dir, "current.docx"))

    vmeta_path = os.path.join(vdir, "meta.json")
    if os.path.isfile(vmeta_path):
        vmeta = _read_json(vmeta_path)
        _write_json(
            os.path.join(report_dir, "tag_values.json"),
            vmeta.get("tag_values", {}),
        )

    return True


# ── Path helpers ───────────────────────────────────────────────────────────────

def get_current_docx_path(user_uuid: str, report_id: str) -> str:
    return os.path.join(_report_dir(user_uuid, report_id), "current.docx")


def get_current_pdf_path(user_uuid: str, report_id: str) -> str:
    return os.path.join(_report_dir(user_uuid, report_id), "current.pdf")


# ── Internal helpers ───────────────────────────────────────────────────────────

def _read_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _read_report_meta(user_uuid: str, report_id: str) -> Optional[dict]:
    path = os.path.join(_report_dir(user_uuid, report_id), "meta.json")
    if not os.path.isfile(path):
        return None
    return _read_json(path)


def _read_tag_values(user_uuid: str, report_id: str) -> dict:
    path = os.path.join(_report_dir(user_uuid, report_id), "tag_values.json")
    if not os.path.isfile(path):
        return {}
    return _read_json(path)
