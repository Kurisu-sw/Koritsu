
import openai
import requests
import hashlib
import queue
import threading
import time
import re
import os


# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

YANDEX_API_BASE = "https://ai.api.cloud.yandex.net/v1"
TOKENIZER_URL   = "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenize"
FILES_URL       = "https://ai.api.cloud.yandex.net/v1/files"

TOKEN_MULTIPLIER = 2

API_KEY    = ""
PROJECT_ID = ""


# ─────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────

class AI_API:
    """
    Клиент Yandex AI API.

    api_key    — IAM или API-ключ Yandex Cloud
    project_id — folder_id / project_id
    """

    def __init__(self, api_key: str = None, project_id: str = None):
        self.api_key    = api_key    or API_KEY
        self.project_id = project_id or PROJECT_ID
        self._client    = None

    # ─────────────────────────────────────────
    # CLIENT
    # ─────────────────────────────────────────

    def create_client(self) -> openai.OpenAI:
        self._client = openai.OpenAI(
            api_key=self.api_key,
            base_url=YANDEX_API_BASE,
            project=self.project_id,
        )
        return self._client

    @property
    def client(self) -> openai.OpenAI:
        if self._client is None:
            self.create_client()
        return self._client


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
    # TOKENIZER
    # ─────────────────────────────────────────

    def yandex_tokenize(self, text: str) -> list:
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type":  "application/json",
        }
        data = {
            "modelUri": f"gpt://{self.project_id}/yandexgpt/latest",
            "text": text,
        }
        r = requests.post(TOKENIZER_URL, headers=headers, json=data)
        r.raise_for_status()
        return r.json()["tokens"]

    def count_tokens(self, tokens: list) -> int:
        return len(tokens)

    def estimate_tokens_from_text(self, text: str) -> int:
        """Подсчитывает количество токенов через Yandex Tokenizer."""
        tokens = self.yandex_tokenize(text)
        return self.count_tokens(tokens)


    # ─────────────────────────────────────────
    # TOKENS (billing)
    # ─────────────────────────────────────────

    def yandex_tokens_from_usage(self, usage) -> int:
        """Возвращает фактическое количество токенов из объекта usage."""
        return getattr(usage, "total_tokens", 0)

    def charged_tokens(self, yandex_tokens: int) -> int:
        """
        Токены к списанию: 1 токен пользователя = 100 токенов Yandex × множитель.
        Минимум 1 токен за запрос.
        """
        return max(1, (yandex_tokens // 100) * TOKEN_MULTIPLIER)


    # ─────────────────────────────────────────
    # GENERATION
    # ─────────────────────────────────────────

    def create_generation_request(
            self,
            prompt_id: str,
            input_text: str,
            max_tokens: int = 800,
            temperature: float = 0) -> str:
        """Создаёт фоновый (background) запрос генерации. Возвращает task_id."""
        resp = self.client.responses.create(
            prompt={"id": prompt_id},
            input=input_text,
            background=True,
            max_output_tokens=max_tokens,
            temperature=temperature,
            extra_body={"reasoningOptions": {"mode": "DISABLED"}},
        )
        return resp.id

    def create_generation_request_sync(
            self,
            prompt_id: str,
            input_text: str,
            max_tokens: int = 800,
            temperature: float = 0):
        """Создаёт синхронный запрос генерации (background=False). Возвращает response."""
        return self.client.responses.create(
            prompt={"id": prompt_id},
            input=input_text,
            background=False,
            max_output_tokens=max_tokens,
            temperature=temperature,
            extra_body={"reasoningOptions": {"mode": "DISABLED"}},
        )


    # ─────────────────────────────────────────
    # STATUS
    # ─────────────────────────────────────────

    def retrieve_generation_status(self, task_id: str):
        return self.client.responses.retrieve(task_id)

    def wait_until_complete(self, task_id: str, delay: float = 1):
        while True:
            status = self.retrieve_generation_status(task_id)
            if status.status in ("completed", "failed", "cancelled"):
                return status
            time.sleep(delay)


    # ─────────────────────────────────────────
    # OUTPUT
    # ─────────────────────────────────────────

    def extract_output_text(self, status) -> str:
        return (status.output_text or "").strip()

    def clean_markdown_json(self, text: str) -> str:
        text = re.sub(r'^```[a-zA-Z]*\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return text.strip()


    # ─────────────────────────────────────────
    # FILE UPLOAD (Yandex Files API)
    # ─────────────────────────────────────────

    def upload_file(self, file_path: str, purpose: str = "assistants") -> dict:
        """
        Загружает файл блок-схемы в Yandex Files API.

        file_path — путь к файлу (XML, JSON и др.)
        purpose   — назначение файла (assistants / fine-tune)

        Возвращает dict с id файла и метаданными.
        """
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
        }
        with open(file_path, "rb") as f:
            files = {
                "file":    (os.path.basename(file_path), f, "application/octet-stream"),
                "purpose": (None, purpose),
            }
            r = requests.post(FILES_URL, headers=headers, files=files)
        r.raise_for_status()
        return r.json()

    def list_files(self) -> list:
        """Возвращает список загруженных файлов из Yandex Files API."""
        headers = {"Authorization": f"Api-Key {self.api_key}"}
        r = requests.get(FILES_URL, headers=headers)
        r.raise_for_status()
        return r.json().get("data", [])

    def delete_file(self, file_id: str) -> bool:
        """Удаляет файл из Yandex Files API."""
        headers = {"Authorization": f"Api-Key {self.api_key}"}
        r = requests.delete(f"{FILES_URL}/{file_id}", headers=headers)
        r.raise_for_status()
        return True

    def upload_schemes_from_dir(self, schemes_dir: str, extensions: tuple = (".xml",)) -> list:
        """
        Загружает все файлы блок-схем из указанной папки в Yandex Files API.
        Возвращает список результатов: [{"file": str, "status": "ok"|"error", ...}].
        """
        results = []
        if not os.path.isdir(schemes_dir):
            return results
        for fname in os.listdir(schemes_dir):
            if fname.lower().endswith(extensions):
                fpath = os.path.join(schemes_dir, fname)
                try:
                    data = self.upload_file(fpath)
                    results.append({"file": fname, "status": "ok", "data": data})
                except Exception as exc:
                    results.append({"file": fname, "status": "error", "error": str(exc)})
        return results


    # ─────────────────────────────────────────
    # CACHE
    # ─────────────────────────────────────────

    def cache_lookup(self, cache: dict, key: str):
        return cache.get(key)

    def cache_store(self, cache: dict, key: str, value):
        cache[key] = value


    # ─────────────────────────────────────────
    # QUEUE
    # ─────────────────────────────────────────

    def create_task_queue(self) -> queue.Queue:
        return queue.Queue()

    def queue_add(self, task_queue: queue.Queue, item):
        task_queue.put(item)

    def queue_get(self, task_queue: queue.Queue):
        return task_queue.get()

    def queue_task_done(self, task_queue: queue.Queue):
        task_queue.task_done()

    def queue_empty(self, task_queue: queue.Queue) -> bool:
        return task_queue.empty()


    # ─────────────────────────────────────────
    # WORKER
    # ─────────────────────────────────────────

    def queue_worker(self, task_queue: queue.Queue, handler, delay: float = 1):
        while True:
            if self.queue_empty(task_queue):
                time.sleep(delay)
                continue
            task = self.queue_get(task_queue)
            try:
                handler(task)
            finally:
                self.queue_task_done(task_queue)

    def start_worker(self, task_queue: queue.Queue, handler) -> threading.Thread:
        t = threading.Thread(
            target=self.queue_worker,
            args=(task_queue, handler),
            daemon=True,
        )
        t.start()
        return t


# ─────────────────────────────────────────
# STANDALONE REQUEST FUNCTION
# (для совместимости с pipeline.py)
# ─────────────────────────────────────────

def request(
        code_path: str,
        model_id: str = None,
        api_key: str = None,
        project_id: str = None) -> tuple:
    """
    Отправляет код в Yandex AI и возвращает (json_text, charged_tokens).
    charged_tokens = yandex_tokens × TOKEN_MULTIPLIER.
    """
    api  = AI_API(api_key=api_key, project_id=project_id)
    code = api.read_file(code_path)

    if model_id is None:
        raise ValueError("model_id обязателен")

    task_id = api.create_generation_request(prompt_id=model_id, input_text=code)
    status  = api.wait_until_complete(task_id)

    if status.status != "completed":
        raise RuntimeError(f"Генерация завершилась со статусом: {status.status}")

    raw_text    = api.extract_output_text(status)
    json_text   = api.clean_markdown_json(raw_text)
    yandex_tok  = api.yandex_tokens_from_usage(status.usage)
    charge_tok  = api.charged_tokens(yandex_tok)

    return json_text, charge_tok
