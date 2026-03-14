"""
pipeline.py — полный пайплайн: код → .json → .xml

Три режима запуска:
  run_bypass(...)           — без проверки токенов, без ожидания (background)
  run_with_token_check(...) — с проверкой токенов и ожиданием завершения
  run(...)                  — стандартный (= run_with_token_check)

Использование:
    python pipeline.py <файл с кодом> [выход.xml]
"""

import os
import sys

from request import AI_API, TOKEN_MULTIPLIER
from builder import generate


# Минимальный буфер токенов (charged) сверх оценки перед отправкой
TOKEN_BUFFER = 200


# ─────────────────────────────────────────────────────────────────────────────
# ИСКЛЮЧЕНИЯ
# ─────────────────────────────────────────────────────────────────────────────

class InsufficientTokensError(Exception):
    """Недостаточно токенов на балансе для генерации."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# 1. run_bypass — без проверок и ожидания
# ─────────────────────────────────────────────────────────────────────────────

def run_bypass(
        code_path: str,
        model_id: str = None,
        api_key: str = None,
        project_id: str = None) -> str:
    """
    Отправляет код в AI без проверки баланса и без ожидания ответа.

    Возвращает task_id — идентификатор фонового задания в Yandex AI.
    Для получения результата используйте AI_API.wait_until_complete(task_id).
    """
    api  = AI_API(api_key=api_key, project_id=project_id)
    code = api.read_file(code_path)

    if model_id is None:
        raise ValueError("model_id обязателен")

    task_id = api.create_generation_request(prompt_id=model_id, input_text=code)
    print(f"[bypass] Задание отправлено: {task_id}")
    return task_id


# ─────────────────────────────────────────────────────────────────────────────
# 2. run_with_token_check — с проверкой токенов и ожиданием
# ─────────────────────────────────────────────────────────────────────────────

def run_with_token_check(
        code_path: str,
        out_xml: str = None,
        cfg_overrides: dict = None,
        model_id: str = None,
        token_budget: int = None,
        api_key: str = None,
        project_id: str = None) -> tuple:
    """
    Полный пайплайн с проверкой токенов:
      1. Оценивает количество токенов через Yandex Tokenizer
      2. Проверяет: token_budget >= estimated × TOKEN_MULTIPLIER + TOKEN_BUFFER
      3. Отправляет код в AI, ждёт завершения
      4. Сохраняет .json и генерирует .xml блок-схему

    Возвращает (путь_к_xml, yandex_tokens, charged_tokens).
    Поднимает InsufficientTokensError если токенов недостаточно.
    """
    api  = AI_API(api_key=api_key, project_id=project_id)
    code = api.read_file(code_path)

    if model_id is None:
        raise ValueError("model_id обязателен")

    step = 1

    # ── Шаг 0: оценка и проверка токенов ─────────────────────────────────
    if token_budget is not None:
        print(f"[{step}/3] Оценка токенов...")
        estimated  = api.estimate_tokens_from_text(code)
        # Формула должна соответствовать charged_tokens() в request.py
        required   = (estimated // 100) * TOKEN_MULTIPLIER + TOKEN_BUFFER
        print(f"      Оценка: ~{estimated} яндекс-токенов "
              f"→ ~{(estimated // 100) * TOKEN_MULTIPLIER} к списанию")
        print(f"      Баланс: {token_budget} | Требуется: {required}")
        if token_budget < required:
            raise InsufficientTokensError(
                f"Недостаточно токенов: баланс {token_budget}, "
                f"требуется не менее {required}"
            )
        step += 1

    # ── Шаг 1: отправка в AI ──────────────────────────────────────────────
    total = 3 if token_budget is not None else 2
    print(f"[{step}/{total}] Отправка кода в AI: {code_path}")
    task_id = api.create_generation_request(prompt_id=model_id, input_text=code)
    status  = api.wait_until_complete(task_id)

    if status.status != "completed":
        raise RuntimeError(f"Генерация завершилась со статусом: {status.status}")

    raw_text   = api.extract_output_text(status)
    json_text  = api.clean_markdown_json(raw_text)
    yandex_tok = api.yandex_tokens_from_usage(status.usage)
    charge_tok = api.charged_tokens(yandex_tok)

    print(f"      Фактически: {yandex_tok} яндекс-токенов "
          f"→ {charge_tok} к списанию")

    # ── Сохраняем .json ───────────────────────────────────────────────────
    base      = os.path.splitext(code_path)[0]
    json_path = base + ".json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_text)
    print(f"      Сохранён .json файл: {json_path}")

    step += 1

    # ── Шаг 2: генерация блок-схемы ──────────────────────────────────────
    print(f"[{step}/{total}] Генерация блок-схемы...")
    xml_path = generate(json_path, out_xml, cfg_overrides=cfg_overrides)

    return xml_path, yandex_tok, charge_tok


# ─────────────────────────────────────────────────────────────────────────────
# 3. run — стандартный пайплайн (= run_with_token_check)
# ─────────────────────────────────────────────────────────────────────────────

def run(
        code_path: str,
        out_xml: str = None,
        cfg_overrides: dict = None,
        model_id: str = None,
        token_budget: int = None,
        api_key: str = None,
        project_id: str = None) -> tuple:
    """
    Стандартный пайплайн (= run_with_token_check).
    Возвращает (путь_к_xml, charged_tokens).
    """
    xml_path, _, charge_tok = run_with_token_check(
        code_path=code_path,
        out_xml=out_xml,
        cfg_overrides=cfg_overrides,
        model_id=model_id,
        token_budget=token_budget,
        api_key=api_key,
        project_id=project_id,
    )
    return xml_path, charge_tok


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python pipeline.py <файл с кодом> [выход.xml]")
        sys.exit(1)

    code_file = sys.argv[1]
    out_file  = sys.argv[2] if len(sys.argv) > 2 else None

    result, tokens = run(code_file, out_file)
    print(f"\nГотово! Блок-схема: {result}")
    print(f"Списано токенов: {tokens}")
