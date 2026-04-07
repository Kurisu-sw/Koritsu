"""
steps_applier.py — конвертация steps.md → tag_values.json (формат Engrafo).

Теги с изображениями кодируются через JSON-сентинел:
    __ctx__:{"content": "...", "images": [...], "options": {...}}

Теги без изображений — просто текст (совместимо с существующим docx_processor.py).
Нумерация рисунков глобальная: назначается в порядке тегов из списка.
"""

import json
import os
import re
from typing import Optional

from .steps_parser import parse_steps_file

_FILES_BASE = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../server/files")
)


def _report_dir(user_uuid: str, report_id: str) -> str:
    return os.path.join(_FILES_BASE, "users", user_uuid, "engrafo", "reports", report_id)


def _read_json(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


_MD_IMG_RE = re.compile(r"!\[([^\]]*)\]\((img_\d+)\)")


def _build_ocr_image_index(ocr_md_path: str) -> list[str]:
    """
    Парсит OCR.md и возвращает список имён файлов изображений
    в порядке следования секций ## Image:.
    Поддерживает новый формат (**filename**) и старый (**path**) для совместимости.
    """
    if not os.path.isfile(ocr_md_path):
        return []
    with open(ocr_md_path, encoding="utf-8") as f:
        content = f.read()
    filenames = []
    for m in re.finditer(r"\*\*filename\*\*:\s*(.+)", content):
        filenames.append(os.path.basename(m.group(1).strip()))
    if not filenames:
        # backward compat: старые OCR.md с **path**
        for m in re.finditer(r"\*\*path\*\*:\s*(.+)", content):
            filenames.append(os.path.basename(m.group(1).strip()))
    return filenames


def _resolve_image_refs(content: str, ocr_index: list[str]) -> tuple[str, list[dict]]:
    """
    Находит markdown-ссылки на картинки ![caption](img_N) в тексте,
    заменяет их на пустую строку (убирает из текста) и формирует
    список images[] для __ctx__ payload.

    inline_after — последнее предложение перед ссылкой (или всё до ссылки).
    """
    images = []
    matches = list(_MD_IMG_RE.finditer(content))

    if not matches:
        return content, images

    for m in matches:
        caption = m.group(1).strip()
        img_ref = m.group(2)  # "img_1", "img_2", ...
        n = int(img_ref.split("_")[1]) - 1  # 0-based index

        path = ocr_index[n] if 0 <= n < len(ocr_index) else ""

        # inline_after = последнее предложение ДО ссылки
        before = content[: m.start()].rstrip()
        sent_end = max(
            before.rfind("."),
            before.rfind("!"),
            before.rfind("?"),
        )
        if sent_end != -1:
            inline_after = before[sent_end - before[:sent_end + 1].rfind("\n") if "\n" in before[:sent_end + 1] else 0 : sent_end + 1].strip()
            # Упрощённо: берём последнее предложение целиком
            inline_after = re.split(r"(?<=[.!?])\s+", before.strip())[-1].strip() if before.strip() else ""
        else:
            inline_after = before.strip()

        images.append({
            "path": path,
            "caption": caption or f"Рисунок {n + 1}",
            "inline_after": inline_after,
        })

    # Убираем все ссылки из текста
    clean_content = _MD_IMG_RE.sub("", content).strip()
    # Убираем двойные пробелы и лишние переносы
    clean_content = re.sub(r"[ \t]+", " ", clean_content)
    clean_content = re.sub(r"\n{3,}", "\n\n", clean_content)

    return clean_content, images


def _assign_figure_numbers(steps: list[dict]) -> list[dict]:
    """
    Присвоить глобальные номера рисунков в порядке следования тегов.
    Заменяет 'Рисунок N' внутри content на правильные номера.
    """
    figure_counter = 0
    result = []
    for step in steps:
        if step["status"] != "ok":
            result.append(step)
            continue

        images = step["images"]
        content = step["content"]

        # Присваиваем номера рисункам этого тега
        numbered_images = []
        for img in images:
            figure_counter += 1
            new_img = dict(img)
            # Обновляем caption если он содержит "Рисунок N"
            if new_img.get("caption"):
                new_img["caption"] = f"Рисунок {figure_counter} — {new_img['caption'].split('—', 1)[-1].strip()}" \
                    if "—" in new_img["caption"] \
                    else f"Рисунок {figure_counter}"
            numbered_images.append((figure_counter, new_img))

        # Обновляем ссылки на рисунки в тексте: "Рисунок X" → правильный номер
        # Порядок рисунков в тексте может не совпадать с порядком в images,
        # поэтому ставим номера последовательно
        import re
        ref_numbers = sorted(
            {int(m) for m in re.findall(r"[Рр]исун(?:ок|ке|ка)\s+(\d+)", content)}
        )
        base = figure_counter - len(images) + 1
        for old_n, new_n in zip(ref_numbers, range(base, figure_counter + 1)):
            content = re.sub(
                rf"([Рр]исун(?:ок|ке|ка)\s+){old_n}\b",
                lambda m, n=new_n: m.group(1) + str(n),
                content,
            )

        new_step = {
            **step,
            "content": content,
            "images": [img for _, img in numbered_images],
        }
        result.append(new_step)

    return result


def _encode_tag_value(step: dict) -> str:
    """
    Конвертировать запись steps в значение тега для tag_values.json.
    - Нет изображений → plain text
    - Есть изображения → __ctx__:{...}
    """
    if not step["images"]:
        return step["content"]

    payload = {
        "content": step["content"],
        "images": step["images"],
        "options": step["options"],
    }
    return "__ctx__:" + json.dumps(payload, ensure_ascii=False)


def apply_steps(
    user_uuid: str,
    report_id: str,
    tag_order: Optional[list[str]] = None,
) -> dict:
    """
    Применить steps.md к tag_values.json отчёта.

    Args:
        user_uuid:  UUID пользователя
        report_id:  ID отчёта
        tag_order:  желательный порядок тегов для нумерации рисунков
                    (обычно берётся из template_manager.extract_tags)

    Returns:
        {
            "applied_tags": [...],
            "skipped_tags": [...],   # parse_error или отсутствуют в steps
            "warnings": [...],
        }
    """
    rdir = _report_dir(user_uuid, report_id)
    steps_path = os.path.join(rdir, "steps.md")
    ocr_md_path = os.path.join(rdir, "OCR.md")

    if not os.path.isfile(steps_path):
        return {"error": "steps.md не найден — сначала запустите sequencer"}

    parsed = parse_steps_file(steps_path)
    if not parsed:
        return {"error": "steps.md пуст или не удалось разобрать"}

    # Строим индекс изображений из OCR.md для разрешения img_N ссылок.
    # Индекс содержит только имена файлов (без серверных путей).
    ocr_index = _build_ocr_image_index(ocr_md_path)
    files_dir = os.path.join(rdir, "files")

    def _resolve_img_path(name: str) -> str:
        """Имя файла → абсолютный путь. Полные пути пропускаются (backward compat)."""
        if os.path.isabs(name):
            return name
        return os.path.join(files_dir, os.path.basename(name))

    # Разрешаем img_N ссылки в content → images[]
    for step in parsed:
        if step["status"] == "ok" and step.get("content"):
            clean_content, img_list = _resolve_image_refs(step["content"], ocr_index)
            if img_list:
                step["content"] = clean_content
                # Объединяем с уже имеющимися images (если были)
                step["images"] = step.get("images", []) + img_list

    # Резолвим имена файлов изображений → абсолютные пути (только для docx_processor)
    for step in parsed:
        if step["status"] == "ok":
            step["images"] = [
                {**img, "path": _resolve_img_path(img.get("path", ""))}
                for img in step.get("images", [])
            ]

    # Сортируем шаги по порядку тегов из шаблона (если передан)
    if tag_order:
        order_map = {t: i for i, t in enumerate(tag_order)}
        parsed.sort(key=lambda s: order_map.get(s["tag"], 9999))

    # Глобальная нумерация рисунков
    numbered = _assign_figure_numbers(parsed)

    applied_tags = []
    skipped_tags = []
    warnings = []

    # Читаем существующие tag_values чтобы не стереть теги не из steps
    tv_path = os.path.join(rdir, "tag_values.json")
    tag_values = _read_json(tv_path)

    for step in numbered:
        tag = step["tag"]
        if step["status"] != "ok":
            skipped_tags.append(tag)
            warnings.append(f"Тег '{tag}' пропущен: {step.get('error', 'parse_error')}")
            continue

        tag_values[tag] = _encode_tag_value(step)
        applied_tags.append(tag)

    _write_json(tv_path, tag_values)

    # Обновляем meta.json
    meta_path = os.path.join(rdir, "meta.json")
    if os.path.isfile(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        from datetime import datetime, timezone
        ctx = meta.setdefault("contextualizer", {})
        ctx["last_applied_at"] = datetime.now(timezone.utc).isoformat()
        _write_json(meta_path, meta)

    return {
        "applied_tags": applied_tags,
        "skipped_tags": skipped_tags,
        "warnings": warnings,
    }
