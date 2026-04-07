"""
sequencer.py — LLM-агент, генерирующий содержимое тегов.

Читает context.md и OCR.md отчёта, для каждого тега подбирает промпт
из prompts.yaml и запрашивает LLM. Результат записывается в steps.md.

Поддерживаемые провайдеры (задаются в .env):
  LLM_PROVIDER=openai    (по умолчанию)
  LLM_PROVIDER=anthropic
  LLM_MODEL=gpt-4o       (перебивает prompts.yaml)
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Optional

import yaml
from dotenv import load_dotenv

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.normpath(os.path.join(_THIS_DIR, "../../.env")), override=False)

_PROMPTS_PATH = os.path.join(_THIS_DIR, "prompts.yaml")
_CONFIG_PATH  = os.path.join(_THIS_DIR, "config.yaml")

with open(_PROMPTS_PATH, encoding="utf-8") as _f:
    _PCFG = yaml.safe_load(_f)

with open(_CONFIG_PATH, encoding="utf-8") as _f:
    _CCFG = yaml.safe_load(_f)

_LLM_CFG = _PCFG.get("llm", {})
_TAG_PROMPTS = _PCFG.get("tag_prompts", {})
_NEVER_GENERATE: set = set(_PCFG.get("never_generate", []))
_DOC_TAG_MAPPING: dict = _CCFG.get("doc_tag_mapping", {})

# Теги с этими префиксами никогда не отправляются в LLM
_NO_GENERATE_PREFIXES = ("global_", "doc_")

_FILES_BASE = os.path.normpath(os.path.join(_THIS_DIR, "../../server/files"))


# ── Helpers ───────────────────────────────────────────────────────────────────


def _report_dir(user_uuid: str, report_id: str) -> str:
    return os.path.join(_FILES_BASE, "users", user_uuid, "engrafo", "reports", report_id)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_file(path: str) -> str:
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def _write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _read_json(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Подготовка контекста для LLM ─────────────────────────────────────────────


def _extract_header_section(context_md: str) -> str:
    """Извлечь только ## Header секцию из context.md."""
    parts = []
    in_header = False
    for line in context_md.splitlines():
        if line.startswith("## Header"):
            in_header = True
            parts.append(line)
            continue
        if in_header:
            if line.startswith("## ") and not line.startswith("## Header"):
                break
            parts.append(line)
    return "\n".join(parts)


def _build_ocr_image_index(ocr_md: str) -> list[str]:
    """
    Парсит OCR.md и возвращает список имён файлов изображений в порядке следования.
    Используется для построения символьных ссылок img_1, img_2, ...
    Поддерживает новый формат (**filename**) и старый (**path**) для совместимости.
    """
    filenames = []
    for m in re.finditer(r"\*\*filename\*\*:\s*(.+)", ocr_md):
        filenames.append(os.path.basename(m.group(1).strip()))
    if not filenames:
        # backward compat: старые OCR.md с **path**
        for m in re.finditer(r"\*\*path\*\*:\s*(.+)", ocr_md):
            filenames.append(os.path.basename(m.group(1).strip()))
    return filenames


def _build_llm_context(
    context_md: str,
    ocr_md: str,
    context_level: str,
    include_ocr: bool,
) -> str:
    """Собрать строку контекста для передачи в LLM."""
    parts = []

    if context_md:
        if context_level == "global":
            header = _extract_header_section(context_md)
            if header:
                parts.append("=== Основные данные работы ===\n" + header)
        else:
            parts.append("=== Контекст документа ===\n" + context_md)

    if include_ocr and ocr_md:
        parts.append("=== OCR изображений ===\n" + ocr_md)
        # Добавляем явный список доступных картинок с символьными именами
        image_paths = _build_ocr_image_index(ocr_md)
        if image_paths:
            img_list = "\n".join(
                f"  img_{i+1} = {os.path.basename(p)}"
                for i, p in enumerate(image_paths)
            )
            parts.append("=== Доступные изображения ===\n" + img_list)

    return "\n\n".join(parts) if parts else "[Контекст не предоставлен]"


def _build_formatting_instructions() -> str:
    """Инструкции по форматированию и вставке картинок для system prompt."""
    return """
ПРАВИЛА ФОРМАТИРОВАНИЯ (строго соблюдать):
- Жирный текст: **текст**
- Курсив: *текст*
- Маркированный список: - пункт (каждый пункт с новой строки)
- Нумерованный список: 1. пункт (каждый пункт с новой строки)

ВСТАВКА ИЗОБРАЖЕНИЙ (только если доступны изображения в контексте):
Используй синтаксис: ![Подпись к рисунку](img_N)
где N — номер изображения из списка доступных изображений.
Вставляй ссылку прямо в текст после предложения, к которому относится рисунок.
Пример: "Собранная схема установки представлена ниже. ![Схема лабораторной установки](img_1)"
Не придумывай изображения если их нет в списке доступных.
""".strip()


def auto_fill_doc_tags(user_uuid: str, report_id: str) -> dict:
    """
    Авто-заполнить doc_-теги из extracted_vars.json отчёта.
    Возвращает словарь {tag_key: value} заполненных тегов.
    """
    rdir = _report_dir(user_uuid, report_id)
    extracted_vars_path = os.path.join(rdir, "extracted_vars.json")
    extracted = _read_json(extracted_vars_path)

    if not extracted:
        return {}

    tv_path = os.path.join(rdir, "tag_values.json")
    tag_values = _read_json(tv_path)

    filled = {}
    for tag_key, var_name in _DOC_TAG_MAPPING.items():
        if var_name in extracted and extracted[var_name]:
            tag_values[tag_key] = extracted[var_name]
            filled[tag_key] = extracted[var_name]

    if filled:
        _write_json(tv_path, tag_values)

    return filled


# ── LLM клиент ────────────────────────────────────────────────────────────────


def _get_provider() -> str:
    return os.getenv("LLM_PROVIDER", "openai").strip().lower()


def _get_model() -> str:
    return os.getenv("LLM_MODEL", _LLM_CFG.get("model", "gpt-4o")).strip()


def _call_openai(system: str, user: str, model: str) -> tuple[str, int]:
    """Вызов OpenAI API. Возвращает (текст ответа, tokens_used)."""
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY не задан в .env")

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        temperature=_LLM_CFG.get("temperature", 0.3),
        max_tokens=_LLM_CFG.get("max_tokens", 2000),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    text = resp.choices[0].message.content or ""
    tokens = resp.usage.total_tokens if resp.usage else 0
    return text, tokens


def _call_anthropic(system: str, user: str, model: str) -> tuple[str, int]:
    """Вызов Anthropic Claude API. Возвращает (текст ответа, tokens_used)."""
    from anthropic import Anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY не задан в .env")

    client = Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=_LLM_CFG.get("max_tokens", 2000),
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = resp.content[0].text if resp.content else ""
    tokens = (resp.usage.input_tokens + resp.usage.output_tokens) if resp.usage else 0
    return text, tokens


def _call_yandex(system: str, user: str, model: str) -> tuple[str, int]:
    """
    Вызов Yandex GPT API через OpenAI-совместимый endpoint.

    .env переменные:
        YC_API_KEY       — API-ключ Yandex Cloud (предпочтительно)
        YANDEX_PROJECT_ID — folder_id проекта (для modelUri)
        LLM_MODEL        — модель: 'yandexgpt' | 'yandexgpt-lite' | 'yandexgpt-32k'
                           (по умолчанию 'yandexgpt')

    Yandex предоставляет OpenAI-совместимый API на базе:
        https://llm.api.cloud.yandex.net/foundationModels/v1/completion
    Используем нативный REST так как openai SDK не поддерживает modelUri.
    """
    import urllib.request

    api_key = os.getenv("YC_API_KEY", "").strip()
    folder_id = os.getenv("YANDEX_PROJECT_ID", "").strip()

    if not api_key:
        raise RuntimeError("YC_API_KEY не задан в .env")
    if not folder_id:
        raise RuntimeError("YANDEX_PROJECT_ID не задан в .env")

    # Имя модели: 'yandexgpt', 'yandexgpt-lite', 'yandexgpt-32k'
    yandex_model = model if model.startswith("yandex") else "yandexgpt"
    model_uri = f"gpt://{folder_id}/{yandex_model}/latest"

    payload = {
        "modelUri": model_uri,
        "completionOptions": {
            "stream": False,
            "temperature": _LLM_CFG.get("temperature", 0.3),
            "maxTokens": str(_LLM_CFG.get("max_tokens", 2000)),
        },
        "messages": [
            {"role": "system", "text": system},
            {"role": "user", "text": user},
        ],
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        data=body,
        headers={
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Yandex GPT API error: {e}") from e

    text = (
        result.get("result", {})
        .get("alternatives", [{}])[0]
        .get("message", {})
        .get("text", "")
    )
    usage = result.get("result", {}).get("usage", {})
    tokens = int(usage.get("totalTokens", 0))
    return text, tokens


def _call_llm(system: str, user: str) -> tuple[str, int]:
    """Вызов LLM в зависимости от LLM_PROVIDER."""
    provider = _get_provider()
    model = _get_model()
    if provider == "anthropic":
        return _call_anthropic(system, user, model)
    if provider == "yandex":
        return _call_yandex(system, user, model)
    return _call_openai(system, user, model)


# ── Форматирование steps.md ───────────────────────────────────────────────────


def _format_steps_section(tag_key: str, content: str, images: list[dict], options: dict) -> str:
    """Сформировать YAML-блок для одного тега в steps.md."""
    lines = [f"## Tag: {tag_key}"]

    # content как YAML literal block
    lines.append("content: |")
    for line in content.splitlines():
        lines.append(f"  {line}")

    # images
    if images:
        lines.append("images:")
        for img in images:
            lines.append(f"  - path: {img.get('path', '')}")
            caption = img.get("caption", "")
            lines.append(f"    caption: \"{caption}\"")
            inline = img.get("inline_after", "")
            lines.append(f"    inline_after: \"{inline}\"")
    else:
        lines.append("images: []")

    # options
    if options:
        lines.append("options:")
        for k, v in options.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append("options: {}")

    return "\n".join(lines)


# ── Извлечение образов из LLM-ответа ─────────────────────────────────────────


def _parse_image_refs_from_response(content: str, ocr_md: str) -> list[dict]:
    """
    Пытается выстроить список изображений из ответа LLM.
    LLM может упомянуть "Рисунок N" — сопоставляем с OCR.md.
    """
    if not ocr_md:
        return []

    # Парсим OCR.md: достаём имена файлов в порядке следования
    image_paths = []
    for m in re.finditer(r"\*\*filename\*\*:\s*(.+)", ocr_md):
        image_paths.append(os.path.basename(m.group(1).strip()))
    if not image_paths:
        # backward compat
        for m in re.finditer(r"\*\*path\*\*:\s*(.+)", ocr_md):
            image_paths.append(os.path.basename(m.group(1).strip()))

    if not image_paths:
        return []

    # Ищем упоминания рисунков в тексте: "Рисунок 1", "рисунке 2", "Figure 1" и т.д.
    ref_pattern = re.compile(
        r"(?:Рисун(?:ок|ке|ка)|рисун(?:ок|ке|ка)|Figure|figure)\s*(\d+)",
        re.IGNORECASE,
    )
    refs = {int(m.group(1)) for m in ref_pattern.finditer(content)}

    result = []
    for n in sorted(refs):
        idx = n - 1
        if 0 <= idx < len(image_paths):
            # Ищем предложение, за которым идёт рисунок
            sent_pattern = re.compile(
                r"[^.!?]*[Рр]исун(?:ок|ке|ка)\s*" + str(n) + r"[^.!?]*[.!?]"
            )
            sm = sent_pattern.search(content)
            inline_after = sm.group(0).strip() if sm else ""

            result.append({
                "path": image_paths[idx],
                "caption": f"Рисунок {n}",
                "inline_after": inline_after,
            })

    return result


# ── Главная функция ───────────────────────────────────────────────────────────


def run_sequencer(
    user_uuid: str,
    report_id: str,
    tags: Optional[list[str]] = None,
    custom_prompts: Optional[dict] = None,
) -> dict:
    """
    Запустить sequencer для указанных тегов отчёта.

    Args:
        user_uuid: UUID пользователя
        report_id: ID отчёта
        tags: список ключей тегов для обработки; None = все теги из шаблона
        custom_prompts: dict[tag_key -> {system, user, context_level}] — кастомные промпты

    Returns:
        {
            "steps_path": str,
            "processed": [tag_key, ...],
            "needs_prompt": [tag_key, ...],
            "errors": {tag_key: error_str, ...},
            "total_tokens": int,
        }
    """
    rdir = _report_dir(user_uuid, report_id)
    if not os.path.isdir(rdir):
        return {"error": f"Report directory not found: {rdir}"}

    context_md = _read_file(os.path.join(rdir, "context.md"))
    ocr_md = _read_file(os.path.join(rdir, "OCR.md"))
    steps_path = os.path.join(rdir, "steps.md")
    prompts_custom_path = os.path.join(rdir, "prompts_custom.json")
    custom_prompts_stored = _read_json(prompts_custom_path)

    # Загружаем пользовательские промпты (сохранённые через UI)
    user_prompts_path = os.path.join(
        _FILES_BASE, "users", user_uuid, "engrafo", "prompts_custom.json"
    )
    user_prompts_stored = _read_json(user_prompts_path)

    # Приоритет: параметр вызова > per-report custom > user custom > system prompts.yaml
    all_custom = {**user_prompts_stored, **custom_prompts_stored, **(custom_prompts or {})}

    # Если список тегов не указан — пробуем взять из tag_values.json
    if tags is None:
        tv = _read_json(os.path.join(rdir, "tag_values.json"))
        tags = list(tv.keys()) if tv else []

    # Если шаблон вообще пустой — нечего делать
    if not tags:
        return {
            "steps_path": steps_path,
            "processed": [],
            "needs_prompt": [],
            "errors": {},
            "total_tokens": 0,
        }

    # Авто-заполняем doc_-теги из extracted_vars
    auto_fill_doc_tags(user_uuid, report_id)

    processed = []
    needs_prompt = []
    errors = {}
    total_tokens = 0
    sections = []
    formatting_instructions = _build_formatting_instructions()

    for tag_key in tags:
        # Пропускаем теги из never_generate
        if tag_key in _NEVER_GENERATE:
            continue
        # Пропускаем global_ и doc_ теги — они заполняются из профиля / контекста
        if any(tag_key.startswith(p) for p in _NO_GENERATE_PREFIXES):
            continue

        # Выбираем промпт: кастомный → prompts.yaml → needs_prompt
        if tag_key in all_custom:
            pcfg = all_custom[tag_key]
        elif tag_key in _TAG_PROMPTS:
            pcfg = _TAG_PROMPTS[tag_key]
        else:
            needs_prompt.append(tag_key)
            continue

        context_level = pcfg.get("context_level", "global")
        include_ocr = pcfg.get("include_ocr", False)
        base_system = pcfg.get("system", "Ты — технический писатель.")
        user_template = pcfg.get("user", "Заполни тег.")

        # Добавляем инструкции по форматированию к system prompt
        system_prompt = base_system + "\n\n" + formatting_instructions

        context_text = _build_llm_context(context_md, ocr_md, context_level, include_ocr)
        user_message = f"{user_template}\n\n{context_text}"

        try:
            llm_response, tokens_used = _call_llm(system_prompt, user_message)
            total_tokens += tokens_used
        except Exception as e:
            errors[tag_key] = str(e)
            continue

        # Изображения будут разрешены в steps_applier через img_N ссылки
        # Оставляем images: [] — steps_applier сам извлечёт из markdown
        options = {"image_align": "center"}
        sections.append(_format_steps_section(tag_key, llm_response, [], options))
        processed.append(tag_key)

    # Записываем steps.md
    if sections:
        content = "# Steps\n\n" + "\n\n".join(sections) + "\n"
        _write_file(steps_path, content)

    # Обновляем meta.json
    meta_path = os.path.join(rdir, "meta.json")
    if os.path.isfile(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            import json as _json
            meta = _json.load(f)
        ctx = meta.setdefault("contextualizer", {})
        ctx["sequencer_task_uuid"] = None  # будет задан из балансера
        ctx["tags_needing_prompt"] = needs_prompt
        _write_json(meta_path, meta)

    return {
        "steps_path": steps_path,
        "processed": processed,
        "needs_prompt": needs_prompt,
        "errors": errors,
        "total_tokens": total_tokens,
    }
