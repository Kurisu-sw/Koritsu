"""
context_builder.py — оркестратор построения контекстных файлов для отчёта.

По каждому загруженному файлу:
  - Изображения → сохраняем байты в files/, добавляем запись в OCR.md отчёта
  - PDF/Word     → создаём/обновляем context.md с текстом и глобальными переменными
"""

import json
import os
import re
from datetime import datetime, timezone

import yaml

from .file_processor import ProcessedFile

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_THIS_DIR, "config.yaml")

with open(_CONFIG_PATH, encoding="utf-8") as _f:
    _CFG = yaml.safe_load(_f)

_GLOBAL_VARS = _CFG.get("global_variables", {})
_MAX_TEXT = _CFG["context"]["max_text_chars"]

# Путь к папке отчётов — аналог report_manager.FILES_BASE
_FILES_BASE = os.path.normpath(os.path.join(_THIS_DIR, "../../server/files"))


# ── Helpers ───────────────────────────────────────────────────────────────────


def _report_dir(user_uuid: str, report_id: str) -> str:
    return os.path.join(_FILES_BASE, "users", user_uuid, "engrafo", "reports", report_id)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Поиск глобальных переменных ───────────────────────────────────────────────


def _find_global_vars(text: str) -> list[dict]:
    """
    Ищет глобальные переменные в тексте по паттернам из config.yaml.
    Возвращает список {"variable": key, "label": label, "value": str, "line": int}.
    """
    results = []
    lines = text.splitlines()

    for var_key, var_cfg in _GLOBAL_VARS.items():
        label = var_cfg.get("label", var_key)
        patterns = var_cfg.get("patterns", [])
        extract = var_cfg.get("extract", "first_group")
        multiline = var_cfg.get("multiline", False)

        found_value = None
        found_line = None

        for line_no, line in enumerate(lines, start=1):
            for pattern in patterns:
                try:
                    m = re.search(pattern, line)
                    if not m:
                        continue

                    if extract == "first_group" and m.lastindex:
                        value = m.group(1).strip()
                    else:
                        value = m.group(0).strip()

                    if multiline:
                        # Добираем строки вниз до пустой
                        extra_lines = []
                        for next_line in lines[line_no:line_no + 10]:
                            if not next_line.strip():
                                break
                            extra_lines.append(next_line.strip())
                        if extra_lines:
                            value = value + " " + " ".join(extra_lines)

                    found_value = value
                    found_line = line_no
                    break
                except re.error:
                    pass
            if found_value:
                break

        if found_value:
            results.append({
                "variable": var_key,
                "label": label,
                "value": found_value,
                "line": found_line,
            })

    return results


# ── Форматирование context.md ─────────────────────────────────────────────────


def _build_context_md(filename: str, global_vars: list[dict], text: str) -> str:
    lines = [f"# Context: {filename}", ""]

    lines.append("## Header")
    if global_vars:
        lines.append("| Variable | Label | Value | Line |")
        lines.append("|----------|-------|-------|------|")
        for gv in global_vars:
            val = str(gv["value"]).replace("|", "\\|")
            lines.append(
                f"| {gv['variable']} | {gv['label']} | {val} | {gv['line']} |"
            )
    else:
        lines.append("_Глобальные переменные не найдены._")
    lines.append("")

    lines.append("## File")
    lines.append("")
    lines.append(text[:_MAX_TEXT] if text else "_Текст не извлечён._")

    return "\n".join(lines)


# ── Форматирование OCR.md ─────────────────────────────────────────────────────


def _build_ocr_entry(filename: str, image_path: str, ocr_text: str) -> str:
    # Храним только имя файла — абсолютный path не пишем в OCR.md,
    # чтобы не раскрывать структуру сервера. Путь резолвится на стороне
    # steps_applier по user_uuid + report_id + filename.
    lines = [
        f"## Image: {filename}",
        f"- **filename**: {filename}",
        "- **text**: |",
    ]
    for text_line in (ocr_text or "").splitlines():
        lines.append(f"  {text_line}")
    lines.append("")
    return "\n".join(lines)


# ── Запись extracted_vars.json ────────────────────────────────────────────────


def _update_extracted_vars(report_dir: str, global_vars: list[dict]) -> None:
    """Обновить/создать extracted_vars.json с найденными переменными из документа."""
    path = os.path.join(report_dir, "extracted_vars.json")
    existing: dict = {}
    if os.path.isfile(path):
        try:
            existing = _read_json(path)
        except Exception:
            pass
    for gv in global_vars:
        existing[gv["variable"]] = gv["value"]
    _write_json(path, existing)


# ── Сохранение изображения ────────────────────────────────────────────────────


def _save_image(report_dir: str, filename: str, data: bytes) -> str:
    """Сохранить байты изображения в files/ папке отчёта. Вернуть абсолютный путь."""
    files_dir = os.path.join(report_dir, "files")
    os.makedirs(files_dir, exist_ok=True)
    dest = os.path.join(files_dir, filename)
    # Если файл с таким именем уже есть — не перезаписываем
    if not os.path.isfile(dest):
        with open(dest, "wb") as f:
            f.write(data)
    return dest


# ── Запись/обновление файлов в папке отчёта ───────────────────────────────────


def _append_ocr(report_dir: str, filename: str, image_path: str, ocr_text: str) -> None:
    ocr_path = os.path.join(report_dir, "OCR.md")

    entry = _build_ocr_entry(filename, image_path, ocr_text)

    if not os.path.isfile(ocr_path):
        with open(ocr_path, "w", encoding="utf-8") as f:
            f.write("# OCR Results\n\n" + entry)
        return

    with open(ocr_path, encoding="utf-8") as f:
        existing = f.read()

    # Не добавляем дубликат
    if f"## Image: {filename}" in existing:
        return

    with open(ocr_path, "w", encoding="utf-8") as f:
        f.write(existing.rstrip() + "\n\n" + entry)


def _write_context(report_dir: str, filename: str, global_vars: list[dict], text: str) -> None:
    context_path = os.path.join(report_dir, "context.md")

    new_section = _build_context_md(filename, global_vars, text)

    if not os.path.isfile(context_path):
        with open(context_path, "w", encoding="utf-8") as f:
            f.write(new_section)
        return

    with open(context_path, encoding="utf-8") as f:
        existing = f.read()

    # Не добавляем дубликат
    if f"# Context: {filename}" in existing:
        return

    with open(context_path, "w", encoding="utf-8") as f:
        f.write(existing.rstrip() + "\n\n---\n\n" + new_section)


# ── Обновление meta.json ──────────────────────────────────────────────────────


def _update_meta(report_dir: str) -> None:
    meta_path = os.path.join(report_dir, "meta.json")
    if not os.path.isfile(meta_path):
        return
    meta = _read_json(meta_path)
    ctx = meta.setdefault("contextualizer", {})
    ctx["context_built_at"] = _now()
    _write_json(meta_path, meta)


# ── Публичный интерфейс ───────────────────────────────────────────────────────


def build_context(
    user_uuid: str,
    report_id: str,
    processed_files: list[ProcessedFile],
) -> dict:
    """
    Обработать список ProcessedFile и построить context.md / OCR.md в папке отчёта.

    Возвращает:
        {
            "context_updated": bool,
            "ocr_updated": bool,
            "files_saved": int,
            "warnings": [...],
        }
    """
    rdir = _report_dir(user_uuid, report_id)
    if not os.path.isdir(rdir):
        return {"error": f"Report directory not found: {rdir}"}

    context_updated = False
    ocr_updated = False
    files_saved = 0
    all_warnings: list[str] = []

    for pf in processed_files:
        all_warnings.extend(pf.warnings)

        if pf.file_type == "image":
            if not pf.raw_data:
                all_warnings.append(f"Изображение {pf.original_filename} не содержит данных.")
                continue

            image_path = _save_image(rdir, pf.original_filename, pf.raw_data)
            files_saved += 1

            _append_ocr(rdir, pf.original_filename, image_path, pf.ocr_text or "")
            _update_meta(rdir)
            ocr_updated = True

        elif pf.file_type in ("pdf", "word"):
            text = pf.text_content or ""
            global_vars = _find_global_vars(text)
            _write_context(rdir, pf.original_filename, global_vars, text)
            _update_extracted_vars(rdir, global_vars)
            _update_meta(rdir)
            context_updated = True

    return {
        "context_updated": context_updated,
        "ocr_updated": ocr_updated,
        "files_saved": files_saved,
        "warnings": all_warnings,
    }
