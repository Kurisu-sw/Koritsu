"""
router.py — FastAPI APIRouter для contextualizer.
Регистрируется в service_api.py через app.include_router(ctx_router).

Эндпоинты:
  POST /contextualizer/report/{report_id}/upload      — загрузка файла
  POST /contextualizer/report/{report_id}/sequencer/run — запуск LLM
  GET  /contextualizer/report/{report_id}/steps       — чтение steps.md
  POST /contextualizer/report/{report_id}/prompt      — кастомный промпт
  POST /contextualizer/report/{report_id}/apply       — применить steps → tag_values

Тяжёлые операции (OCR, LLM) запускаются через балансер асинхронно.
"""

import json
import os
import re as _re

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from .context_builder import build_context
from .file_processor import process_upload
from .sequencer import run_sequencer
from .steps_applier import apply_steps
from .steps_parser import parse_steps_file

router = APIRouter(prefix="/contextualizer", tags=["contextualizer"])

_FILES_BASE = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../server/files")
)

# UUID regex (импортируем паттерн аналогичный service_api.py)
_UUID_RE = _re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    _re.IGNORECASE,
)
# Report ID: 8 hex символов
_REPORT_ID_RE = _re.compile(r"^[0-9a-f]{8}$")


def _valid_uuid(s: str) -> bool:
    return bool(_UUID_RE.match(s))


def _valid_report_id(s: str) -> bool:
    return bool(_REPORT_ID_RE.match(s))


def _report_dir(user_uuid: str, report_id: str) -> str:
    return os.path.join(_FILES_BASE, "users", user_uuid, "engrafo", "reports", report_id)


# ── Pydantic models ───────────────────────────────────────────────────────────


class SequencerRunRequest(BaseModel):
    user_uuid: str
    tags: list[str] | None = None
    custom_prompts: dict = {}


class CustomPromptRequest(BaseModel):
    user_uuid: str
    tag_key: str
    system: str
    user: str
    context_level: str = "global"
    include_ocr: bool = False


class ApplyRequest(BaseModel):
    user_uuid: str
    tag_order: list[str] | None = None


# ── Balancer handler ──────────────────────────────────────────────────────────


async def ctx_handler(payload: dict) -> dict:
    """
    Balancer handler для contextualizer.
    Вызывается из service_api.py:
        balancer.register_handler("contextualizer", ctx_handler)

    payload fields:
        action: "build_context" | "run_sequencer"
        user_uuid, report_id
        + action-specific fields
    """
    action = payload.get("action")
    user_uuid = payload.get("user_uuid", "")
    report_id = payload.get("report_id", "")

    if action == "run_sequencer":
        tags = payload.get("tags")
        custom_prompts = payload.get("custom_prompts", {})
        result = run_sequencer(user_uuid, report_id, tags=tags, custom_prompts=custom_prompts)
        tokens = result.get("total_tokens", 0)
        return {
            **result,
            "cost_rub": 0,
            "charged_tokens": tokens,
        }

    return {"error": f"Unknown contextualizer action: {action}"}


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/report/{report_id}/upload")
async def upload_file(
    report_id: str,
    user_uuid: str,
    file: UploadFile = File(...),
):
    """
    Загрузить исходный файл (PDF, Word, изображение, архив).
    Запускает context builder синхронно для малых файлов.
    Возвращает результат сразу.
    """
    if not _valid_uuid(user_uuid):
        return {"error": "Invalid UUID"}
    if not _valid_report_id(report_id):
        return {"error": "Invalid report_id"}

    rdir = _report_dir(user_uuid, report_id)
    if not os.path.isdir(rdir):
        return {"error": "Report not found"}

    data = await file.read()
    if not data:
        return {"error": "Пустой файл"}

    filename = file.filename or "upload"

    processed_files, top_warnings = process_upload(filename, data)

    if not processed_files:
        return {
            "error": f"Не удалось обработать файл: {filename}",
            "warnings": top_warnings,
        }

    result = build_context(user_uuid, report_id, processed_files)
    result["warnings"] = top_warnings + result.get("warnings", [])
    result["files_processed"] = len(processed_files)

    return result


@router.post("/report/{report_id}/sequencer/run")
async def sequencer_run(report_id: str, data: SequencerRunRequest):
    """
    Запустить LLM-агент для генерации тегов.
    Тяжёлая операция — ставится в очередь балансера.
    Возвращает task_uuid для polling.
    """
    if not _valid_uuid(data.user_uuid):
        return {"error": "Invalid UUID"}
    if not _valid_report_id(report_id):
        return {"error": "Invalid report_id"}

    rdir = _report_dir(data.user_uuid, report_id)
    if not os.path.isdir(rdir):
        return {"error": "Report not found"}

    # Импортируем балансер здесь чтобы избежать циклического импорта
    try:
        import sys
        _server_dir = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../server")
        )
        if _server_dir not in sys.path:
            sys.path.insert(0, _server_dir)
        from balancer import balancer  # type: ignore
    except ImportError:
        # Если балансер недоступен — запускаем синхронно (fallback)
        result = run_sequencer(
            data.user_uuid, report_id,
            tags=data.tags, custom_prompts=data.custom_prompts
        )
        return result

    payload = {
        "action": "run_sequencer",
        "user_uuid": data.user_uuid,
        "report_id": report_id,
        "tags": data.tags,
        "custom_prompts": data.custom_prompts,
    }

    task_uuid = await balancer.submit(
        priority=2,
        task_dest="contextualizer",
        answ_to=data.user_uuid,
        username=data.user_uuid[:8],
        payload=payload,
    )

    # Сохраняем task_uuid в meta.json
    meta_path = os.path.join(rdir, "meta.json")
    if os.path.isfile(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        meta.setdefault("contextualizer", {})["sequencer_task_uuid"] = task_uuid
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    return {"task_uuid": task_uuid}


@router.get("/report/{report_id}/steps")
def get_steps(report_id: str, user_uuid: str):
    """Получить разобранный steps.md."""
    if not _valid_uuid(user_uuid):
        return {"error": "Invalid UUID"}
    if not _valid_report_id(report_id):
        return {"error": "Invalid report_id"}

    rdir = _report_dir(user_uuid, report_id)
    steps_path = os.path.join(rdir, "steps.md")

    if not os.path.isfile(steps_path):
        return {"steps": [], "needs_prompt": []}

    parsed = parse_steps_file(steps_path)
    needs_prompt = []

    # Добираем needs_prompt из meta.json
    meta_path = os.path.join(rdir, "meta.json")
    if os.path.isfile(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        needs_prompt = meta.get("contextualizer", {}).get("tags_needing_prompt", [])

    return {"steps": parsed, "needs_prompt": needs_prompt}


@router.post("/report/{report_id}/prompt")
def save_custom_prompt(report_id: str, data: CustomPromptRequest):
    """Сохранить кастомный промпт для неизвестного тега."""
    if not _valid_uuid(data.user_uuid):
        return {"error": "Invalid UUID"}
    if not _valid_report_id(report_id):
        return {"error": "Invalid report_id"}

    rdir = _report_dir(data.user_uuid, report_id)
    if not os.path.isdir(rdir):
        return {"error": "Report not found"}

    prompts_path = os.path.join(rdir, "prompts_custom.json")
    existing = {}
    if os.path.isfile(prompts_path):
        with open(prompts_path, encoding="utf-8") as f:
            existing = json.load(f)

    existing[data.tag_key] = {
        "system": data.system,
        "user": data.user,
        "context_level": data.context_level,
        "include_ocr": data.include_ocr,
    }

    os.makedirs(os.path.dirname(prompts_path), exist_ok=True)
    with open(prompts_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    return {"success": True, "tag_key": data.tag_key}


@router.post("/report/{report_id}/apply")
def apply_steps_endpoint(report_id: str, data: ApplyRequest):
    """Применить steps.md → tag_values.json."""
    if not _valid_uuid(data.user_uuid):
        return {"error": "Invalid UUID"}
    if not _valid_report_id(report_id):
        return {"error": "Invalid report_id"}

    rdir = _report_dir(data.user_uuid, report_id)
    if not os.path.isdir(rdir):
        return {"error": "Report not found"}

    result = apply_steps(data.user_uuid, report_id, tag_order=data.tag_order)
    return result
