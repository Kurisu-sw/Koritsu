"""
steps_parser.py — разбор steps.md → список dict.

Формат steps.md:
    # Steps

    ## Tag: ход_работы
    content: |
      текст...
    images:
      - path: /abs/path/img.png
        caption: "Рисунок 1"
        inline_after: "предложение"
    options:
      image_align: center

    ## Tag: заключение
    ...

Каждая секция разбирается через yaml.safe_load().
Ошибочные секции получают status='parse_error' и не блокируют остальные.
"""

import os
import re
from typing import Any

import yaml

_SECTION_RE = re.compile(r"^## Tag:\s*(.+)$", re.MULTILINE)


def parse_steps_file(steps_path: str) -> list[dict]:
    """
    Разобрать steps.md и вернуть список dict.

    Каждый элемент:
        {
            "tag": str,
            "content": str,
            "images": [...],
            "options": {...},
            "status": "ok" | "parse_error",
            "error": str | None,
        }
    """
    if not os.path.isfile(steps_path):
        return []

    with open(steps_path, encoding="utf-8") as f:
        text = f.read()

    return parse_steps_text(text)


def parse_steps_text(text: str) -> list[dict]:
    """Разобрать строку steps.md."""
    # Убираем заголовок # Steps
    text = re.sub(r"^#\s+Steps\s*\n", "", text, count=1)

    # Ищем позиции всех секций ## Tag:
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        return []

    results = []
    for i, m in enumerate(matches):
        tag_key = m.group(1).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()

        entry = _parse_section(tag_key, body)
        results.append(entry)

    return results


def _parse_section(tag_key: str, body: str) -> dict:
    """Разобрать YAML-тело одной секции."""
    try:
        data = yaml.safe_load(body) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Ожидался dict, получен {type(data).__name__}")

        content = str(data.get("content", "")).strip()
        images = _normalise_images(data.get("images", []))
        options = _normalise_options(data.get("options", {}))

        return {
            "tag": tag_key,
            "content": content,
            "images": images,
            "options": options,
            "status": "ok",
            "error": None,
        }
    except Exception as e:
        return {
            "tag": tag_key,
            "content": "",
            "images": [],
            "options": {},
            "status": "parse_error",
            "error": str(e),
        }


def _normalise_images(raw: Any) -> list[dict]:
    """Привести images к стандартному формату."""
    if not isinstance(raw, list):
        return []
    result = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        result.append({
            "path": str(item.get("path", "")),
            "caption": str(item.get("caption", "")),
            "inline_after": str(item.get("inline_after", "")),
        })
    return result


def _normalise_options(raw: Any) -> dict:
    if not isinstance(raw, dict):
        return {}
    return {str(k): v for k, v in raw.items()}
