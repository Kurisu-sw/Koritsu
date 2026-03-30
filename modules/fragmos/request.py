
import hashlib
import re
import os
import httpx

from yandex_ai_studio_sdk import AsyncAIStudio


# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

FILES_URL = "https://ai.api.cloud.yandex.net/v1/files"
TOKENIZE_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenize"

BASE_MODEL = "yandexgpt"

TOKEN_MULTIPLIER = 2
TOKEN_BUFFER = 5   # extra internal tokens added to estimate as safety margin

_DEFAULT_API_KEY = "2-"
_DEFAULT_PROJECT_ID = "2"

API_KEY = os.getenv("YC_API_KEY") or os.getenv("YANDEX_API_KEY") or _DEFAULT_API_KEY
PROJECT_ID = os.getenv("YANDEX_PROJECT_ID") or _DEFAULT_PROJECT_ID


# ─────────────────────────────────────────
# PROMPTS (загружаются один раз при импорте)
# ─────────────────────────────────────────

_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")

def _load_prompt(name: str) -> str:
    path = os.path.join(_PROMPTS_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

# Кэш промптов — грузятся 1 раз
PROMPTS: dict[str, str] = {}

def get_prompt(prompt_key: str) -> str:
    """Возвращает system prompt по ключу. Кэширует после первой загрузки."""
    if prompt_key not in PROMPTS:
        PROMPTS[prompt_key] = _load_prompt(prompt_key)
    return PROMPTS[prompt_key]

# Маппинг "модель" → файл промпта
PROMPT_MAP = {
    "literal": "bau.md",    # Дословный перевод кода
    "gost":    "gu.md",     # ГОСТ 19.701-90 русский псевдокод
}


# ─────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────

class AI_API:
    """
    Async клиент Yandex AI через yandex-ai-studio-sdk.

    api_key    — IAM или API-ключ Yandex Cloud
    project_id — folder_id / project_id
    """

    def __init__(self, api_key: str = None, project_id: str = None):
        self.api_key = api_key or API_KEY
        self.project_id = project_id or PROJECT_ID
        if not self.api_key:
            raise ValueError("API key не задан: передайте api_key или установите YC_API_KEY")
        if not self.project_id:
            raise ValueError("Project ID не задан: передайте project_id или установите YANDEX_PROJECT_ID")
        self._sdk: AsyncAIStudio | None = None

    @property
    def sdk(self) -> AsyncAIStudio:
        if self._sdk is None:
            self._sdk = AsyncAIStudio(
                folder_id=self.project_id,
                auth=self.api_key,
            )
        return self._sdk


    # ─────────────────────────────────────────
    # FILE IO
    # ─────────────────────────────────────────

    def read_file(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


    # ─────────────────────────────────────────
    # HASH
    # ─────────────────────────────────────────

    def make_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()


    # ─────────────────────────────────────────
    # TOKENIZER (via REST API)
    # ─────────────────────────────────────────

    async def _tokenize(self, text: str) -> int:
        """Подсчитывает количество токенов через REST Tokenize API."""
        model_uri = f"gpt://{self.project_id}/{BASE_MODEL}"
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "modelUri": model_uri,
            "text": text,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(TOKENIZE_URL, json=body, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        return len(data.get("tokens", []))

    async def estimate_tokens_from_text(
            self, text: str, prompt_key: str = None, max_tokens: int = 800) -> int:
        """
        Оценивает общее количество токенов для генерации:
        input (system prompt + текст) + output (max_tokens как worst-case).
        """
        input_tokens = await self._tokenize(text)

        # Добавляем токены system prompt если указан prompt_key
        if prompt_key:
            prompt_file = PROMPT_MAP.get(prompt_key, prompt_key)
            system_prompt = get_prompt(prompt_file)
            input_tokens += await self._tokenize(system_prompt)

        # Worst-case: модель выдаст max_tokens на выходе
        return input_tokens + max_tokens


    # ─────────────────────────────────────────
    # TOKENS (billing)
    # ─────────────────────────────────────────

    def yandex_tokens_from_usage(self, usage) -> int:
        """Возвращает фактическое количество токенов из объекта usage."""
        # DEBUG: показать структуру usage для отладки
        print(f"[tokens] usage type={type(usage).__name__}, repr={usage!r}")
        if hasattr(usage, "__dict__"):
            print(f"[tokens] usage.__dict__={usage.__dict__}")

        total = 0

        # 1. Объект SDK с атрибутами
        if hasattr(usage, "total_tokens") and usage.total_tokens:
            total = int(usage.total_tokens)
        elif hasattr(usage, "totalTokens") and usage.totalTokens:
            total = int(usage.totalTokens)

        # 2. Если total_tokens == 0 или отсутствует — суммируем input + completion
        if total == 0:
            inp = (getattr(usage, "input_text_tokens", 0)
                   or getattr(usage, "inputTextTokens", 0) or 0)
            comp = (getattr(usage, "completion_tokens", 0)
                    or getattr(usage, "completionTokens", 0) or 0)
            if inp or comp:
                total = int(inp) + int(comp)

        # 3. Словарь (fallback)
        if total == 0 and isinstance(usage, dict):
            total = int(usage.get("total_tokens", 0)
                        or usage.get("totalTokens", 0) or 0)
            if total == 0:
                inp = int(usage.get("input_text_tokens", 0)
                          or usage.get("inputTextTokens", 0) or 0)
                comp = int(usage.get("completion_tokens", 0)
                           or usage.get("completionTokens", 0) or 0)
                total = inp + comp

        print(f"[tokens] resolved total_tokens={total}")
        return total

    def charged_tokens(self, yandex_tokens: int) -> int:
        """
        Токены к списанию: 1 токен пользователя = 100 токенов Yandex × множитель.
        Минимум 1 токен за запрос.
        """
        return max(1, (yandex_tokens // 100) * TOKEN_MULTIPLIER)


    # ─────────────────────────────────────────
    # GENERATION (async via SDK + system prompt)
    # ─────────────────────────────────────────

    async def generate(
            self,
            prompt_key: str,
            input_text: str,
            max_tokens: int = 800,
            temperature: float = 0):
        """
        Запрос генерации с system prompt (async, deferred).
        prompt_key — ключ из PROMPT_MAP (literal / gost).
        Возвращает dict: {text, total_tokens, usage}.
        """
        prompt_file = PROMPT_MAP.get(prompt_key, prompt_key)
        system_prompt = get_prompt(prompt_file)

        model = self.sdk.models.completions(BASE_MODEL)
        model = model.configure(
            temperature=temperature,
            max_tokens=max_tokens,
        )

        messages = [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": input_text},
        ]

        operation = await model.run_deferred(messages)
        result = await operation

        # Извлекаем текст
        text = ""
        if hasattr(result, "alternatives") and result.alternatives:
            alt = result.alternatives[0]
            if hasattr(alt, "text"):
                text = (alt.text or "").strip()
            elif hasattr(alt, "message") and hasattr(alt.message, "text"):
                text = (alt.message.text or "").strip()
        elif hasattr(result, "text"):
            text = (result.text or "").strip()

        # Извлекаем usage
        usage = getattr(result, "usage", {})
        total_tokens = self.yandex_tokens_from_usage(usage)

        return {
            "text": text,
            "total_tokens": total_tokens,
            "usage": usage,
        }

    def clean_ai_output(self, text: str) -> str:
        """Убирает markdown-обёртки (```...```) из ответа нейронки."""
        # Убираем первую строку ```lang и последнюю строку ```
        text = re.sub(r'^```[a-zA-Z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        return text.strip()

    # Обратная совместимость
    clean_markdown_json = clean_ai_output


    # ─────────────────────────────────────────
    # CACHE
    # ─────────────────────────────────────────

    def cache_lookup(self, cache: dict, key: str):
        return cache.get(key)

    def cache_store(self, cache: dict, key: str, value):
        cache[key] = value


# ─────────────────────────────────────────
# STANDALONE REQUEST FUNCTION (async)
# ─────────────────────────────────────────

async def request(
        code_path: str,
        model_id: str = None,
        api_key: str = None,
        project_id: str = None) -> tuple:
    """
    Отправляет код в Yandex AI и возвращает (frg_text, charged_tokens).
    model_id = "literal" или "gost"
    """
    api = AI_API(api_key=api_key, project_id=project_id)
    code = api.read_file(code_path)

    if model_id is None:
        raise ValueError("model_id обязателен (literal / gost)")

    result = await api.generate(prompt_key=model_id, input_text=code)

    json_text = api.clean_markdown_json(result["text"])
    charge_tok = api.charged_tokens(result["total_tokens"])

    return json_text, charge_tok
