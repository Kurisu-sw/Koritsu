"""
engrafo_state.py — Reflex State для модуля Engrafo.

Управляет:
  - выбором шаблона и кэшированием тегов
  - списком отчётов пользователя
  - текущим отчётом (редактор): значения тегов, preview
  - профилями значений тегов
  - историей версий
"""

import asyncio
import base64
import os
import re as _re
import sys
import time
from html import unescape as _unescape
from typing import Any

import reflex as rx

# ── Импорт модулей Engrafo ─────────────────────────────────────────────────────

_ENGRAFO_MODULE = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../modules/engrafo")
)
if _ENGRAFO_MODULE not in sys.path:
    sys.path.insert(0, _ENGRAFO_MODULE)

_MODULES_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../modules")
)
if _MODULES_DIR not in sys.path:
    sys.path.insert(0, _MODULES_DIR)

import template_manager as _tm   # type: ignore
import docx_processor  as _dp   # type: ignore
import pdf_converter   as _pc   # type: ignore
import report_manager  as _rm   # type: ignore
import profile_manager as _pm   # type: ignore

# ── Конвертеры: list[dict] → list[dict[str, str]] для Reflex foreach ──────────

def _str_dicts(items: list[dict]) -> list[dict[str, str]]:
    """Оставить только str-поля верхнего уровня."""
    return [{k: str(v) for k, v in d.items() if not isinstance(v, dict)} for d in items]


def _report_dicts(items: list[dict]) -> list[dict[str, str]]:
    return [
        {
            "id":            str(r.get("id", "")),
            "title":         str(r.get("title", "")),
            "template_name": str(r.get("template_name", "")),
            "updated_at":    str(r.get("updated_at", ""))[:10],
        }
        for r in items
    ]


def _profile_dicts(items: list[dict]) -> list[dict[str, str]]:
    return [
        {
            "id":         str(p.get("id", "")),
            "name":       str(p.get("name", "")),
            "created_at": str(p.get("created_at", ""))[:10],
        }
        for p in items
    ]


def _version_dicts(items: list[dict]) -> list[dict[str, str]]:
    return [
        {
            "id":       str(v.get("id", "")),
            # Форматируем дату здесь, чтобы в UI не нужны были Var-операции
            "saved_at": str(v.get("saved_at", ""))[:16].replace("T", " "),
        }
        for v in items
    ]


# ── Вспомогательные функции (синхронные, запускаются в потоке) ────────────────

def _sync_generate_preview(user_uuid: str, report_id: str,
                            template_id: str, tag_values: dict) -> str:
    """Рендер docx + конвертация в PDF. Возвращает URL для iframe."""
    tpl_path = _tm.get_template_path(user_uuid, template_id)
    if not tpl_path:
        raise ValueError("Шаблон не найден")

    docx_path = _rm.get_current_docx_path(user_uuid, report_id)
    pdf_path  = _rm.get_current_pdf_path(user_uuid, report_id)

    _dp.render_docx(tpl_path, docx_path, tag_values)
    _pc.docx_to_pdf(docx_path, pdf_path)
    _rm.update_tag_values(user_uuid, report_id, tag_values)

    # PDF раздаётся через FastAPI StaticFiles (нет проблем с CORS для iframe)
    api_url = os.getenv("FASTAPI_URL", "http://localhost:8001")
    ts      = int(time.time())
    return f"{api_url}/files/users/{user_uuid}/engrafo/reports/{report_id}/current.pdf?t={ts}"


def _clean_value(v: str) -> str:
    """Strip leftover HTML from old contenteditable data."""
    if not v or v.startswith("data:image/"):
        return v
    if "<" not in v:
        return v
    # Extract first bare data URL from HTML img tags if present
    m = _re.search(r'<img[^>]+src=["\']?(data:image/[^"\'>\s]+)', v)
    if m:
        return m.group(1)
    # Strip all HTML tags
    text = _re.sub(r'<br\s*/?>', '\n', v, flags=_re.IGNORECASE)
    text = _re.sub(r'<[^>]+>', '', text)
    return _unescape(text).strip()


def _parse_tag_value(value: str) -> tuple[str, str]:
    """Parse tag value → (text_part, image_src).

    Handles: plain text, plain data:image/... URL, HTML with <img>.
    Returns (text, image_src) where both can be empty.
    """
    if not value:
        return "", ""
    if value.startswith("data:image/"):
        return "", value
    if "<img" not in value:
        text = _re.sub(r'<br\s*/?>', '\n', value, flags=_re.IGNORECASE)
        text = _re.sub(r'<[^>]+>', '', text)
        return _unescape(text).strip(), ""
    # HTML with embedded image — extract first <img src>
    m = _re.search(r'<img[^>]+src=["\']([^"\']+)["\']', value)
    image_src = m.group(1) if m else ""
    text = _re.sub(r'<img[^>]+/?>', '', value)
    text = _re.sub(r'<br\s*/?>', '\n', text, flags=_re.IGNORECASE)
    text = _re.sub(r'<[^>]+>', '', text)
    return _unescape(text).strip(), image_src


def _build_tag_value(text: str, image_src: str) -> str:
    """Combine text and image_src into a value string for docx rendering."""
    t = (text or "").strip()
    i = (image_src or "").strip()
    if not t and not i:
        return ""
    if not i:
        return t
    if not t:
        return i  # plain data URL — backward compat for image-only tags
    return t.replace('\n', '<br>') + '<br><img src="' + i + '">'


def _make_tag_entry(key: str, label: str, value: str) -> dict[str, str]:
    """Create a full tag entry dict with text/image_src split from value."""
    text, image_src = _parse_tag_value(value)
    # Normalize value to valid HTML for contenteditable (data-init-html).
    # __ctx__: values are JSON payloads for docx_processor — leave unchanged.
    if value and not value.startswith("__ctx__:"):
        if value.startswith("data:image/"):
            # Raw data URL stored without wrapper — reconstruct <img>
            html_value = '<img src="' + value + '" class="tag-inline-img">'
        elif "<" not in value:
            # Plain text (e.g. from AI generation) — convert \n to <br>
            html_value = value.replace("\n", "<br>")
        else:
            html_value = value
    else:
        html_value = value
    return {"key": key, "label": label, "value": html_value,
            "text": text, "image_src": image_src,
            "type": _tm._detect_tag_type(key)}


# ── State ──────────────────────────────────────────────────────────────────────

class EngrafoState(rx.State):

    # ── Auth sync ────────────────────────────────────────────────────────────
    user_uuid: str = ""

    # ── Templates ────────────────────────────────────────────────────────────
    # [{id, name, source}]
    templates: list[dict[str, str]]     = []
    selected_template_id: str = ""
    selected_template_name: str = ""
    # ── Reports list ─────────────────────────────────────────────────────────
    # [{id, title, template_name, updated_at}]
    reports: list[dict[str, str]] = []

    # ── Current report (editor) ───────────────────────────────────────────────
    current_report_id: str   = ""
    current_report_title: str = ""

    # tag_entries: [{key: str, label: str, value: str}]
    tag_entries: list[dict[str, str]] = []
    # Выбранные теги для редактирования (ключи)
    selected_tags: list[str] = []

    # ── Preview ───────────────────────────────────────────────────────────────
    preview_url:    str  = ""
    preview_loading: bool = False
    _preview_in_progress: bool = False

    # ── Profiles ──────────────────────────────────────────────────────────────
    # [{id, name, created_at}]  — tag_values хранятся только на диске
    profiles: list[dict[str, str]] = []
    show_save_profile_dialog: bool = False
    new_profile_name: str = ""
    selected_profile_id: str = ""

    # ── Versions ──────────────────────────────────────────────────────────────
    # [{id, saved_at}]  — tag_values хранятся только на диске
    versions: list[dict[str, str]] = []

    # form_key инкрементируется при загрузке профиля/версии — debounce_input
    # видит новый key и делает ремаунт, показывая обновлённые значения.
    form_key: int = 0

    # ── New report dialog ─────────────────────────────────────────────────────
    show_new_report_dialog: bool = False
    new_report_title: str = ""

    # ── Upload template dialog ────────────────────────────────────────────────
    show_upload_dialog: bool = False

    # ── Tags modal ────────────────────────────────────────────────────────────
    show_tags_modal: bool = False

    # ── Expand editor (модальное окно для длинного текста) ────────────────────
    expand_key: str = ""      # ключ тега, открытого в expand-редакторе
    expand_label: str = ""    # label тега
    expand_value: str = ""    # текущее значение в expand (комбинированное)
    expand_text: str = ""     # текстовая часть в expand
    expand_image_src: str = ""  # картинка в expand (data URL)
    expand_html: str = ""     # raw HTML из contenteditable expand-редактора

    # ── Image picker ──────────────────────────────────────────────────────────
    image_picker_key: str = ""   # ключ тега, в который вставляем картинку

    # ── Clipboard paste proxy ─────────────────────────────────────────────────
    clipboard_paste_data: str = ""   # данные от JS при Ctrl+V (KEY|||data:image/...)

    # ── Context file upload ───────────────────────────────────────────────────
    show_context_upload: bool = False
    context_files: list[dict[str, str]] = []   # [{name, size, ext}]

    # ── AI / Contextualizer ───────────────────────────────────────────────────
    ai_loading: bool = False          # идёт ли AI-операция
    ai_status_msg: str = ""           # последнее сообщение о статусе AI
    needs_prompt_tags: list[str] = [] # теги без промпта — нужен ввод юзера
    show_ai_prompt_dialog: bool = False
    ai_prompt_tag_key: str = ""
    ai_prompt_system: str = ""
    ai_prompt_user_text: str = ""
    ai_prompt_context_level: str = "full"
    ai_prompt_include_ocr: bool = True

    # ── Generate modal ────────────────────────────────────────────────────
    show_generate_modal: bool = False
    generate_mode: str = "ai"  # "ai" | "manual"
    # [{key, label, has_prompt, selected, custom_prompt}]
    generate_tag_rows: list[dict[str, str]] = []
    manual_context_url: str = ""   # URL скачать ai_context.md

    # ── Tag history (последние 3 уникальных значения для chips) ────────────
    tag_history: dict[str, list[str]] = {}

    # ── Autosave ──────────────────────────────────────────────────────────────
    autosave_pending: bool = False
    _last_change_ts:  float = 0.0   # timestamp последнего изменения тега
    _last_save_ts:    float = 0.0   # timestamp последнего автосохранения

    # ── Delete report confirmation ───────────────────────────────────────────
    pending_delete_id: str = ""
    show_delete_confirm: bool = False

    # ── Delete profile confirmation ──────────────────────────────────────────
    pending_delete_profile_id: str = ""
    show_delete_profile_confirm: bool = False

    # ── Restore version confirmation ─────────────────────────────────────────
    show_restore_confirm: bool = False
    pending_restore_version_id: str = ""

    # ── Feedback ──────────────────────────────────────────────────────────────
    error_msg:   str = ""
    success_msg: str = ""
    loading:     bool = False

    # ── Global tags (page /engrafo tabs) ──────────────────────────────────────
    engrafo_tab: str = "reports"        # "reports" | "global_tags"
    # [{key, value}] — user-level default tag values
    global_tags: list[dict[str, str]] = []
    global_tag_new_key: str = ""
    global_tag_new_value: str = ""

    # ── Global tags popup при создании отчёта ────────────────────────────────
    show_global_popup: bool = False
    global_popup_tags: list[str] = []   # ключи global_ тегов найденных в шаблоне

    # =========================================================================
    # Page on_load handlers
    # =========================================================================

    async def on_load_list(self):
        """Вызывается при загрузке страницы /engrafo (список отчётов)."""
        await self._sync_user()
        if self.user_uuid:
            self.templates = _str_dicts(_tm.list_templates(self.user_uuid))
            self.reports   = _report_dicts(_rm.list_reports(self.user_uuid))
            self.profiles  = _profile_dicts(_pm.list_profiles(self.user_uuid))
            self._load_global_tags()

    async def on_load_editor(self):
        """Вызывается при загрузке страницы /engrafo/editor."""
        await self._sync_user()
        if not self.user_uuid:
            return
        self.templates = _str_dicts(_tm.list_templates(self.user_uuid))
        self.profiles  = _profile_dicts(_pm.list_profiles(self.user_uuid))

        if self.current_report_id:
            await self._load_current_report()
        self._load_context_files()
        self.form_key += 1  # trigger contenteditable re-sync after state loads

    async def _sync_user(self):
        """Получить user_uuid из AuthState."""
        from koritsu.state.auth_state import AuthState
        auth = await self.get_state(AuthState)
        self.user_uuid = auth.user_uuid

    # =========================================================================
    # New report dialog
    # =========================================================================

    def open_new_report_dialog(self):
        self.show_new_report_dialog = True
        self.new_report_title = ""
        self.error_msg = ""

    def close_new_report_dialog(self):
        self.show_new_report_dialog = False

    def set_new_report_title(self, v: str):
        self.new_report_title = v

    def set_selected_template_for_new(self, tpl_id: str):
        self.selected_template_id = tpl_id
        # Найти имя
        for t in self.templates:
            if t["id"] == tpl_id:
                self.selected_template_name = t["name"]
                break

    async def create_report(self):
        if not self.selected_template_id:
            self.error_msg = "Выберите шаблон"
            return
        if not self.user_uuid:
            self.error_msg = "Необходима авторизация"
            return

        meta = _rm.create_report(
            self.user_uuid,
            self.selected_template_id,
            self.selected_template_name,
            self.new_report_title,
        )
        self.current_report_id    = meta["id"]
        self.current_report_title = meta["title"]
        self.show_new_report_dialog = False

        # Загружаем теги шаблона (без global_ значений — их применим через popup)
        tpl_path = _tm.get_template_path(self.user_uuid, self.selected_template_id)
        if tpl_path:
            tags = _tm.extract_tags(tpl_path)
            self.tag_entries = [
                _make_tag_entry(t["key"], t["label"], "")
                for t in tags
            ]
            # Проверяем есть ли global_ теги с заполненными значениями
            global_vals = self._load_global_tags_dict()
            global_keys_in_tpl = [t["key"] for t in tags if t["key"].startswith("global_")]
            fillable = [k for k in global_keys_in_tpl if global_vals.get(k)]
            if fillable:
                self.global_popup_tags = fillable
                self.show_global_popup = True

        self.versions    = []
        self.preview_url = ""

        yield rx.redirect("/engrafo/editor")

    def apply_global_tags(self):
        """Применить глобальные теги из профиля пользователя."""
        global_vals = self._load_global_tags_dict()
        self.tag_entries = [
            _make_tag_entry(e["key"], e["label"], global_vals.get(e["key"], e["value"]))
            if e["key"].startswith("global_") and global_vals.get(e["key"])
            else e
            for e in self.tag_entries
        ]
        self.show_global_popup = False
        self.global_popup_tags = []
        self.form_key += 1  # перемонтировать contenteditable с новыми значениями

    def skip_global_tags(self):
        """Закрыть popup без применения глобальных тегов."""
        self.show_global_popup = False
        self.global_popup_tags = []

    # =========================================================================
    # Template selection (in editor)
    # =========================================================================

    def select_template(self, tpl_id: str):
        """Выбрать шаблон в редакторе."""
        self.selected_template_id = tpl_id
        for t in self.templates:
            if t["id"] == tpl_id:
                self.selected_template_name = t["name"]
                break

        tpl_path = _tm.get_template_path(self.user_uuid, tpl_id)
        if tpl_path:
            old_values = {e["key"]: e["value"] for e in self.tag_entries}
            self.tag_entries = [
                _make_tag_entry(t["key"], t["label"], str(old_values.get(t["key"], "")))
                for t in _tm.extract_tags(tpl_path)
            ]
        else:
            self.tag_entries = []

        # Автовыбрать все теги
        self.selected_tags = [e["key"] for e in self.tag_entries]
        self.preview_url = ""

    # =========================================================================
    # Tag values
    # =========================================================================

    def toggle_tag_selection(self, key: str):
        """Выбрать/убрать тег из списка редактируемых."""
        if key in self.selected_tags:
            self.selected_tags = [k for k in self.selected_tags if k != key]
        else:
            self.selected_tags = self.selected_tags + [key]

    def select_all_tags(self):
        """Выбрать все теги."""
        self.selected_tags = [e["key"] for e in self.tag_entries]

    def deselect_all_tags(self):
        """Снять выбор со всех тегов."""
        self.selected_tags = []

    def set_tag_value(self, key: str, value: str):
        """Обновить значение одного тега (backward compat)."""
        self.tag_entries = [
            _make_tag_entry(e["key"], e["label"], value) if e["key"] == key else e
            for e in self.tag_entries
        ]
        self._last_change_ts = time.time()
        self._try_autosave()

    def set_tag_text(self, key: str, text: str):
        """Обновить текстовую часть тега (вызывается на on_blur textarea)."""
        self.tag_entries = [
            _make_tag_entry(e["key"], e["label"],
                            _build_tag_value(text, e.get("image_src", "")))
            if e["key"] == key else e
            for e in self.tag_entries
        ]
        self._last_change_ts = time.time()
        self._try_autosave()

    def set_tag_image(self, key: str, data_url: str):
        """Установить картинку для тега (сохраняет текст)."""
        self.tag_entries = [
            _make_tag_entry(e["key"], e["label"],
                            _build_tag_value(e.get("text", ""), data_url))
            if e["key"] == key else e
            for e in self.tag_entries
        ]
        self._last_change_ts = time.time()
        self._try_autosave()

    def clear_tag_image(self, key: str):
        """Удалить картинку тега, сохранив текст."""
        self.tag_entries = [
            _make_tag_entry(e["key"], e["label"], e.get("text", ""))
            if e["key"] == key else e
            for e in self.tag_entries
        ]
        self._last_change_ts = time.time()
        self._try_autosave()

    def handle_clipboard_paste(self, data: str):
        """Вызывается из JS при Ctrl+V с картинкой.
        Формат data: 'TAG_KEY|||data:image/...' или '__EXPAND__|||data:image/...'
        """
        if not data or "|||" not in data:
            self.clipboard_paste_data = ""
            return
        key, data_url = data.split("|||", 1)
        self.clipboard_paste_data = ""
        if not data_url.startswith("data:image/"):
            return
        if len(data_url) > 10 * 1024 * 1024:
            self.error_msg = "Картинка слишком большая (макс. ~7 MB)"
            return
        if key == "__EXPAND__":
            self.set_expand_image(data_url)
        else:
            self.set_tag_image(key, data_url)

    def set_tag_html(self, key: str, html: str):
        """Сохранить raw HTML из contenteditable для тега (поддерживает несколько картинок)."""
        # Normalize empty contenteditable output
        cleaned = html.strip()
        if cleaned in ("<br>", "<div><br></div>", "<p><br></p>"):
            cleaned = ""
        self.tag_entries = [
            _make_tag_entry(e["key"], e["label"], cleaned) if e["key"] == key else e
            for e in self.tag_entries
        ]
        self._last_change_ts = time.time()
        self._try_autosave()

    def handle_html_update(self, data: str):
        """Вызывается из JS при blur contenteditable.
        Формат data: 'TAG_KEY|||html' или '__EXPAND__|||html'
        """
        if not data or "|||" not in data:
            return
        key, html = data.split("|||", 1)
        if key == "__EXPAND__":
            cleaned = html.strip()
            if cleaned in ("<br>", "<div><br></div>", "<p><br></p>"):
                cleaned = ""
            self.expand_html = cleaned
            self.expand_value = cleaned
            self.expand_text, self.expand_image_src = _parse_tag_value(cleaned)
        else:
            self.set_tag_html(key, html)

    def clear_tag_value(self, key: str):
        """Полностью очистить значение тега (текст и картинку)."""
        self.tag_entries = [
            _make_tag_entry(e["key"], e["label"], "") if e["key"] == key else e
            for e in self.tag_entries
        ]
        self._last_change_ts = time.time()
        self._try_autosave()

    # =========================================================================
    # Image picker
    # =========================================================================

    # ── Expand editor ────────────────────────────────────────────────────────

    def open_expand_editor(self, key: str):
        """Открыть модальный редактор для тега."""
        for e in self.tag_entries:
            if e["key"] == key:
                self.expand_key = key
                self.expand_label = e["label"]
                self.expand_value = e["value"]
                self.expand_html = e["value"]
                self.expand_text = e.get("text", "")
                self.expand_image_src = e.get("image_src", "")
                break

    def set_expand_value(self, value: str):
        """Backward compat: устанавливает expand_value и парсит text/image."""
        self.expand_value = value
        self.expand_text, self.expand_image_src = _parse_tag_value(value)

    def set_expand_text(self, text: str):
        """Обновить текст в expand-редакторе."""
        self.expand_text = text
        self.expand_value = _build_tag_value(text, self.expand_image_src)

    def set_expand_image(self, data_url: str):
        """Установить картинку в expand-редакторе."""
        self.expand_image_src = data_url
        self.expand_value = _build_tag_value(self.expand_text, data_url)

    def clear_expand_image(self):
        """Удалить картинку из expand-редактора."""
        self.expand_image_src = ""
        self.expand_value = _build_tag_value(self.expand_text, "")

    def save_expand_and_close(self):
        """Сохранить HTML из expand-редактора и закрыть."""
        if self.expand_key:
            # Use expand_html (from contenteditable) if available, else fall back
            value = self.expand_html or _build_tag_value(self.expand_text, self.expand_image_src)
            self.tag_entries = [
                _make_tag_entry(e["key"], e["label"], value)
                if e["key"] == self.expand_key else e
                for e in self.tag_entries
            ]
            self._last_change_ts = time.time()
            self._try_autosave()
            self.form_key += 1
        self.expand_key = ""
        self.expand_label = ""
        self.expand_value = ""
        self.expand_html = ""
        self.expand_text = ""
        self.expand_image_src = ""

    def close_expand_editor(self):
        self.expand_key = ""
        self.expand_label = ""
        self.expand_value = ""
        self.expand_html = ""
        self.expand_text = ""
        self.expand_image_src = ""

    # ── Image picker ──────────────────────────────────────────────────────────

    def open_image_picker(self, key: str):
        self.image_picker_key = key

    def close_image_picker(self):
        self.image_picker_key = ""

    async def handle_image_upload(self, files: list[rx.UploadFile]):
        """Читает файл, кодирует в base64, добавляет картинку в тег."""
        if not files or not self.image_picker_key:
            self.image_picker_key = ""
            return
        key = self.image_picker_key
        self.image_picker_key = ""
        try:
            f = files[0]
            data = await f.read()
            if len(data) > 8 * 1024 * 1024:
                self.error_msg = "Файл слишком большой (макс. 8MB)"
                return
            mime = f.content_type or "image/png"
            b64 = base64.b64encode(data).decode("utf-8")
            data_url = f"data:{mime};base64,{b64}"
            if key == "__EXPAND__":
                self.set_expand_image(data_url)
            else:
                self.set_tag_image(key, data_url)
        except Exception as exc:
            self.error_msg = f"Ошибка загрузки: {exc}"

    # =========================================================================
    # Autosave (версия каждые 5 мин после последнего изменения, макс 3 версии)
    # =========================================================================

    def _try_autosave(self):
        """Сохраняет версию, если прошло ≥5 мин с последнего автосохранения.
        Вызывается синхронно из set_tag_value — не блокирует UI."""
        AUTOSAVE_INTERVAL = 300  # 5 минут
        now = time.time()
        if now - self._last_save_ts < AUTOSAVE_INTERVAL:
            return
        if not self.current_report_id or not self.user_uuid:
            return
        vmeta = _rm.save_version(self.user_uuid, self.current_report_id)
        if vmeta:
            all_versions = _rm.list_versions(self.user_uuid, self.current_report_id)
            while len(all_versions) > 3:
                oldest = all_versions[-1]
                _rm._delete_version(self.user_uuid, self.current_report_id, oldest["id"])
                all_versions = _rm.list_versions(self.user_uuid, self.current_report_id)
            self.versions = _version_dicts(all_versions)
        self._last_save_ts = now

    # =========================================================================
    # Preview generation (async generator — yield отправляет state во frontend)
    # =========================================================================

    async def generate_preview(self):
        if self._preview_in_progress:
            return
        if not self.user_uuid or not self.current_report_id or not self.selected_template_id:
            return

        self._preview_in_progress = True
        self.preview_loading      = True
        self.error_msg            = ""
        yield  # → frontend получает spinner

        user_uuid   = self.user_uuid
        report_id   = self.current_report_id
        template_id = self.selected_template_id
        tag_values  = {e["key"]: e["value"] for e in self.tag_entries}

        try:
            url = await asyncio.to_thread(
                _sync_generate_preview,
                user_uuid, report_id, template_id, tag_values,
            )
            self.preview_url = url
        except Exception as exc:
            self.error_msg = f"Ошибка генерации: {exc}"
        finally:
            self.preview_loading      = False
            self._preview_in_progress = False

    # =========================================================================
    # Versions
    # =========================================================================

    def save_version(self):
        if not self.current_report_id or not self.user_uuid:
            return
        vmeta = _rm.save_version(self.user_uuid, self.current_report_id)
        if vmeta:
            self.versions  = _version_dicts(_rm.list_versions(self.user_uuid, self.current_report_id))
            self.success_msg = "Версия сохранена"

    def confirm_restore_version(self, version_id: str):
        """Open restore-version confirmation dialog."""
        self.pending_restore_version_id = version_id
        self.show_restore_confirm = True

    def cancel_restore_version(self):
        self.pending_restore_version_id = ""
        self.show_restore_confirm = False

    async def do_restore_version(self):
        """Actually restore the version after confirmation."""
        version_id = self.pending_restore_version_id
        self.pending_restore_version_id = ""
        self.show_restore_confirm = False
        if not version_id or not self.current_report_id or not self.user_uuid:
            return
        ok = _rm.restore_version(self.user_uuid, self.current_report_id, version_id)
        if ok:
            await self._load_current_report()
            self.form_key   += 1
            self.success_msg = "Версия восстановлена"
            yield EngrafoState.generate_preview

    async def restore_version(self, version_id: str):
        if not self.current_report_id or not self.user_uuid:
            return
        ok = _rm.restore_version(self.user_uuid, self.current_report_id, version_id)
        if ok:
            await self._load_current_report()
            self.form_key   += 1  # ремаунт debounce_input'ов
            self.success_msg = "Версия восстановлена"
            yield EngrafoState.generate_preview

    def load_versions(self):
        if self.current_report_id and self.user_uuid:
            self.versions = _version_dicts(_rm.list_versions(self.user_uuid, self.current_report_id))

    # =========================================================================
    # Profiles
    # =========================================================================

    def open_save_profile_dialog(self):
        self.show_save_profile_dialog = True
        self.new_profile_name = ""

    def close_save_profile_dialog(self):
        self.show_save_profile_dialog = False

    def set_new_profile_name(self, v: str):
        self.new_profile_name = v

    def save_profile(self):
        if not self.user_uuid:
            return
        tag_values = {e["key"]: e["value"] for e in self.tag_entries}
        _pm.create_profile(self.user_uuid, self.new_profile_name, tag_values)
        self.profiles                = _profile_dicts(_pm.list_profiles(self.user_uuid))
        self.show_save_profile_dialog = False
        self.success_msg             = "Профиль сохранён"

    async def load_profile(self, profile_id: str):
        profile = _pm.get_profile(self.user_uuid, profile_id)
        if not profile:
            return
        stored = profile.get("tag_values", {})
        self.tag_entries = [
            _make_tag_entry(e["key"], e["label"], stored.get(e["key"], ""))
            for e in self.tag_entries
        ]
        self.form_key += 1  # ремаунт textarea'ов (uncontrolled)
        yield EngrafoState.generate_preview

    def confirm_delete_profile(self, profile_id: str):
        """Open delete-profile confirmation dialog."""
        self.pending_delete_profile_id = profile_id
        self.show_delete_profile_confirm = True

    def cancel_delete_profile(self):
        self.pending_delete_profile_id = ""
        self.show_delete_profile_confirm = False

    def do_delete_profile(self):
        """Actually delete the profile after confirmation."""
        if self.pending_delete_profile_id and self.user_uuid:
            _pm.delete_profile(self.user_uuid, self.pending_delete_profile_id)
            self.profiles = _profile_dicts(_pm.list_profiles(self.user_uuid))
        self.pending_delete_profile_id = ""
        self.show_delete_profile_confirm = False

    def delete_profile(self, profile_id: str):
        _pm.delete_profile(self.user_uuid, profile_id)
        self.profiles = _profile_dicts(_pm.list_profiles(self.user_uuid))

    # =========================================================================
    # Export / Finalize
    # =========================================================================

    def download_pdf(self):
        api_url = os.getenv("FASTAPI_URL", "http://localhost:8001")
        ts      = int(time.time())
        url     = f"{api_url}/files/users/{self.user_uuid}/engrafo/reports/{self.current_report_id}/current.pdf?t={ts}"
        return rx.call_script(f"window.open('{url}', '_blank')")

    def download_docx(self):
        api_url = os.getenv("FASTAPI_URL", "http://localhost:8001")
        ts      = int(time.time())
        url     = f"{api_url}/files/users/{self.user_uuid}/engrafo/reports/{self.current_report_id}/current.docx?t={ts}"
        return rx.call_script(f"window.open('{url}', '_blank')")

    def finalize_report(self):
        if self.current_report_id and self.user_uuid:
            _rm.finalize_report(self.user_uuid, self.current_report_id)
            self.versions    = []
            self.success_msg = "Отчёт завершён. Версии очищены."

    # =========================================================================
    # Reports list actions
    # =========================================================================

    def open_report(self, report_id: str):
        self.current_report_id = report_id
        return rx.redirect("/engrafo/editor")

    def confirm_delete(self, report_id: str):
        """Open delete-report confirmation dialog."""
        self.pending_delete_id = report_id
        self.show_delete_confirm = True

    def cancel_delete(self):
        self.pending_delete_id = ""
        self.show_delete_confirm = False

    def do_delete(self):
        """Actually delete the report after confirmation."""
        if self.pending_delete_id and self.user_uuid:
            _rm.delete_report(self.user_uuid, self.pending_delete_id)
            self.reports = _report_dicts(_rm.list_reports(self.user_uuid))
        self.pending_delete_id = ""
        self.show_delete_confirm = False

    def delete_report(self, report_id: str):
        _rm.delete_report(self.user_uuid, report_id)
        self.reports = _report_dicts(_rm.list_reports(self.user_uuid))

    # =========================================================================
    # Template upload
    # =========================================================================

    def open_upload_dialog(self):
        self.show_upload_dialog = True

    def close_upload_dialog(self):
        self.show_upload_dialog = False

    # =========================================================================
    # Context file upload (для будущего AI-агента)
    # =========================================================================

    # Базовый путь к files/ FastAPI-сервера (относительно корня проекта)
    _FILES_BASE: str = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../server/files")
    )

    _CONTEXT_ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".zip", ".txt", ".docx"}
    _CONTEXT_MAX_SIZE    = 20 * 1024 * 1024  # 20MB

    def open_context_upload(self):
        self.show_context_upload = True

    def close_context_upload(self):
        self.show_context_upload = False

    def _context_dir(self) -> str:
        """Папка files конкретного отчёта — туда же куда и фото."""
        if self.current_report_id:
            return os.path.join(
                self._FILES_BASE, "users", self.user_uuid,
                "engrafo", "reports", self.current_report_id, "files",
            )
        # fallback — глобальная папка если отчёт ещё не создан
        return os.path.join(self._FILES_BASE, "users", self.user_uuid, "engrafo", "context")

    def _load_context_files(self):
        ctx = self._context_dir()
        if not os.path.exists(ctx):
            self.context_files = []
            return
        files = []
        for name in sorted(os.listdir(ctx)):
            path = os.path.join(ctx, name)
            if not os.path.isfile(path):
                continue
            size = os.path.getsize(path)
            if size >= 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.1f} MB"
            elif size >= 1024:
                size_str = f"{size // 1024} KB"
            else:
                size_str = f"{size} B"
            ext = os.path.splitext(name)[1].lower()
            files.append({"name": name, "size": size_str, "ext": ext})
        self.context_files = files

    async def upload_context_files(self, files: list[rx.UploadFile]):
        self.loading = True
        self.error_msg = ""
        yield

        try:
            from contextualizer.file_processor import process_upload  # type: ignore
            from contextualizer.context_builder import build_context   # type: ignore

            # Все файлы (включая изображения) сохраняем в папку files/ отчёта.
            ctx = self._context_dir()
            os.makedirs(ctx, exist_ok=True)

            saved = 0
            all_warnings = []

            for file in files:
                ext = os.path.splitext(file.filename or "")[1].lower()
                if ext not in self._CONTEXT_ALLOWED_EXT:
                    continue
                content = await file.read()
                if len(content) > self._CONTEXT_MAX_SIZE:
                    self.error_msg = f"{file.filename}: файл слишком большой (макс. 20MB)"
                    continue

                safe = "".join(c for c in (file.filename or "file") if c.isalnum() or c in ".-_ ")[:120]
                with open(os.path.join(ctx, safe), "wb") as fh:
                    fh.write(content)

                # Обрабатываем через contextualizer если есть активный отчёт
                if self.current_report_id and self.user_uuid:
                    try:
                        processed, warns = process_upload(file.filename or safe, content)
                        all_warnings.extend(warns)
                        if processed:
                            result = build_context(self.user_uuid, self.current_report_id, processed)
                            all_warnings.extend(result.get("warnings", []))
                    except Exception as ctx_exc:
                        all_warnings.append(f"Contextualizer: {ctx_exc}")

                saved += 1

            self._load_context_files()
            if saved:
                self.success_msg = f"Загружено файлов: {saved}"
                if all_warnings:
                    self.ai_status_msg = "Предупреждения: " + "; ".join(all_warnings[:3])
        except Exception as exc:
            self.error_msg = f"Ошибка загрузки: {exc}"
        finally:
            self.loading = False

    def delete_context_file(self, filename: str):
        if "/" in filename or "\\" in filename or ".." in filename:
            return
        path = os.path.join(self._context_dir(), filename)
        if os.path.isfile(path):
            os.remove(path)
        self._load_context_files()

    # =========================================================================
    # AI / Contextualizer
    # =========================================================================

    async def run_ai_sequencer(self):
        """Запустить LLM-агент для генерации контента тегов."""
        if not self.current_report_id or not self.user_uuid:
            self.error_msg = "Сначала создайте или откройте отчёт"
            return
        if self.ai_loading:
            return

        self.ai_loading = True
        self.ai_status_msg = "Генерация контента..."
        self.error_msg = ""
        yield

        try:
            from contextualizer.sequencer import run_sequencer as _run_seq  # type: ignore

            # Собираем список тегов из текущего отчёта
            tags = [e["key"] for e in self.tag_entries] if self.tag_entries else None

            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: _run_seq(
                    self.user_uuid,
                    self.current_report_id,
                    tags=tags,
                    custom_prompts={},
                )
            )

            if "error" in result:
                self.error_msg = result["error"]
            else:
                processed = result.get("processed", [])
                self.needs_prompt_tags = result.get("needs_prompt", [])
                self.ai_status_msg = f"Сгенерировано: {len(processed)} тег(ов)"
                if self.needs_prompt_tags:
                    self.ai_status_msg += f" | Нужен промпт: {len(self.needs_prompt_tags)}"
                    # Открываем диалог для первого тега без промпта
                    self.ai_prompt_tag_key = self.needs_prompt_tags[0]
                    self.show_ai_prompt_dialog = True
                if processed:
                    self.success_msg = f"AI сгенерировал контент для: {', '.join(processed)}"
        except Exception as exc:
            self.error_msg = f"Ошибка AI: {exc}"
            self.ai_status_msg = ""
        finally:
            self.ai_loading = False

    async def apply_ai_steps(self):
        """Применить steps.md → tag_values.json и обновить отображение тегов."""
        if not self.current_report_id or not self.user_uuid:
            self.error_msg = "Нет активного отчёта"
            return

        self.ai_loading = True
        self.ai_status_msg = "Применение..."
        yield

        try:
            from contextualizer.steps_applier import apply_steps as _apply  # type: ignore

            tag_order = [e["key"] for e in self.tag_entries] if self.tag_entries else None
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: _apply(self.user_uuid, self.current_report_id, tag_order=tag_order),
            )

            if "error" in result:
                self.error_msg = result["error"]
            else:
                applied = result.get("applied_tags", [])
                # Перезагружаем tag_entries из обновлённого tag_values.json
                await self._load_current_report()
                self.form_key += 1
                self.success_msg = f"Применено: {', '.join(applied)}" if applied else "Нечего применять"
                self.ai_status_msg = ""
        except Exception as exc:
            self.error_msg = f"Ошибка применения: {exc}"
        finally:
            self.ai_loading = False

    def open_ai_prompt_dialog(self, tag_key: str):
        self.ai_prompt_tag_key = tag_key
        self.ai_prompt_system = ""
        self.ai_prompt_user_text = ""
        self.ai_prompt_context_level = "full"
        self.ai_prompt_include_ocr = True
        self.show_ai_prompt_dialog = True

    def close_ai_prompt_dialog(self):
        self.show_ai_prompt_dialog = False

    async def save_ai_prompt_and_run(self):
        """Сохранить кастомный промпт и запустить sequencer для этого тега."""
        if not self.ai_prompt_tag_key:
            self.show_ai_prompt_dialog = False
            return

        self.show_ai_prompt_dialog = False
        self.ai_loading = True
        self.ai_status_msg = f"Генерация '{self.ai_prompt_tag_key}'..."
        yield

        try:
            from contextualizer.sequencer import run_sequencer as _run_seq  # type: ignore

            custom = {
                self.ai_prompt_tag_key: {
                    "system": self.ai_prompt_system or "Ты технический писатель.",
                    "user": self.ai_prompt_user_text,
                    "context_level": self.ai_prompt_context_level,
                    "include_ocr": self.ai_prompt_include_ocr,
                }
            }

            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: _run_seq(
                    self.user_uuid,
                    self.current_report_id,
                    tags=[self.ai_prompt_tag_key],
                    custom_prompts=custom,
                )
            )

            if "error" in result:
                self.error_msg = result["error"]
            else:
                # Убираем тег из списка needs_prompt
                self.needs_prompt_tags = [
                    t for t in self.needs_prompt_tags if t != self.ai_prompt_tag_key
                ]
                if result.get("processed"):
                    self.success_msg = f"Тег '{self.ai_prompt_tag_key}' сгенерирован"
                # Если ещё есть теги без промпта — открываем следующий
                if self.needs_prompt_tags:
                    self.ai_prompt_tag_key = self.needs_prompt_tags[0]
                    self.ai_prompt_system = ""
                    self.ai_prompt_user_text = ""
                    self.show_ai_prompt_dialog = True
        except Exception as exc:
            self.error_msg = f"Ошибка AI: {exc}"
        finally:
            self.ai_loading = False

    # =========================================================================
    # Generate modal
    # =========================================================================

    def open_generate_modal(self):
        """Открыть модальное окно выбора тегов для генерации."""
        import yaml as _yaml

        prompts_path = os.path.join(_MODULES_DIR, "contextualizer", "prompts.yaml")
        try:
            with open(prompts_path, encoding="utf-8") as _f:
                _pcfg = _yaml.safe_load(_f)
            system_tag_prompts = (_pcfg or {}).get("tag_prompts", {})
            system_keys = set(system_tag_prompts.keys())
            never_generate = set((_pcfg or {}).get("never_generate", []))
        except Exception:
            system_tag_prompts = {}
            system_keys = set()
            never_generate = set()

        user_prompts = self._load_user_custom_prompts()

        # Только теги, выбранные пользователем (visible в редакторе)
        active_keys = set(self.selected_tags) if self.selected_tags else {e["key"] for e in self.tag_entries}
        rows = []
        for e in self.tag_entries:
            key = e["key"]
            # Пропускаем теги не выбранные пользователем
            if key not in active_keys:
                continue
            # Пропускаем теги из never_generate
            if key in never_generate:
                continue
            # Показываем только ai_ теги и теги без известного префикса.
            # global_, doc_, raw_ — не для AI-генерации.
            if any(key.startswith(p) for p in ("global_", "doc_", "raw_")):
                continue
            has_sys = key in system_keys
            has_user = key in user_prompts
            saved_prompt = ""
            if not has_sys and has_user:
                saved_prompt = user_prompts[key].get("user", "")
            # Используем label из prompts.yaml если есть
            label = (system_tag_prompts.get(key) or {}).get("label", "") or e["label"]
            rows.append({
                "key": key,
                "label": label,
                "has_prompt": "true" if (has_sys or has_user) else "false",
                "selected": "true",   # все выбраны по умолчанию
                "custom_prompt": saved_prompt,
            })

        self.generate_tag_rows = rows
        self.generate_mode = "ai"
        self.manual_context_url = ""
        self.show_generate_modal = True

    def close_generate_modal(self):
        self.show_generate_modal = False
        self.manual_context_url = ""

    def set_generate_mode(self, mode: str):
        self.generate_mode = mode
        self.manual_context_url = ""

    def toggle_generate_key(self, key: str):
        self.generate_tag_rows = [
            {**r, "selected": "false" if r["selected"] == "true" else "true"}
            if r["key"] == key else r
            for r in self.generate_tag_rows
        ]

    def set_generate_custom_prompt(self, key: str, value: str):
        self.generate_tag_rows = [
            {**r, "custom_prompt": value} if r["key"] == key else r
            for r in self.generate_tag_rows
        ]

    def _load_user_custom_prompts(self) -> dict:
        path = os.path.join(
            self._FILES_BASE, "users", self.user_uuid, "engrafo", "prompts_custom.json"
        )
        if not os.path.isfile(path):
            return {}
        try:
            import json as _json
            with open(path, encoding="utf-8") as _f:
                return _json.load(_f)
        except Exception:
            return {}

    def _save_user_custom_prompts(self, new_prompts: dict):
        import json as _json
        path = os.path.join(
            self._FILES_BASE, "users", self.user_uuid, "engrafo", "prompts_custom.json"
        )
        os.makedirs(os.path.dirname(path), exist_ok=True)
        existing = self._load_user_custom_prompts()
        existing.update(new_prompts)
        with open(path, "w", encoding="utf-8") as _f:
            _json.dump(existing, _f, ensure_ascii=False, indent=2)

    async def run_generate(self):
        """Запустить AI-генерацию для выбранных в модале тегов."""
        selected = [r["key"] for r in self.generate_tag_rows if r["selected"] == "true"]
        if not selected:
            self.error_msg = "Выберите хотя бы один тег"
            return
        if not self.current_report_id or not self.user_uuid:
            self.error_msg = "Сначала создайте или откройте отчёт"
            return

        # Собираем кастомные промпты для тегов без системного промпта
        custom_to_save = {}
        custom_for_run = {}
        for r in self.generate_tag_rows:
            if r["selected"] == "true" and r["has_prompt"] == "false" and r["custom_prompt"].strip():
                entry = {
                    "system": "Ты — технический писатель академических отчётов.",
                    "user": r["custom_prompt"].strip(),
                    "context_level": "full",
                    "include_ocr": "false",
                }
                custom_to_save[r["key"]] = entry
                custom_for_run[r["key"]] = entry

        if custom_to_save:
            self._save_user_custom_prompts(custom_to_save)

        self.show_generate_modal = False
        self.ai_loading = True
        self.ai_status_msg = "Генерация контента..."
        self.error_msg = ""
        yield

        try:
            from contextualizer.sequencer import run_sequencer as _run_seq  # type: ignore

            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: _run_seq(
                    self.user_uuid,
                    self.current_report_id,
                    tags=selected,
                    custom_prompts=custom_for_run,
                ),
            )
            if "error" in result:
                self.error_msg = result["error"]
            else:
                processed = result.get("processed", [])
                self.needs_prompt_tags = result.get("needs_prompt", [])
                self.ai_status_msg = f"Сгенерировано: {len(processed)} тег(ов)"
                if self.needs_prompt_tags:
                    self.ai_status_msg += f" | Нужен промпт: {len(self.needs_prompt_tags)}"
                    self.ai_prompt_tag_key = self.needs_prompt_tags[0]
                    self.show_ai_prompt_dialog = True
                if processed:
                    self.success_msg = f"AI сгенерировал контент для: {', '.join(processed)}"
        except Exception as exc:
            self.error_msg = f"Ошибка AI: {exc}"
            self.ai_status_msg = ""
        finally:
            self.ai_loading = False

    # =========================================================================
    # Manual AI mode
    # =========================================================================

    async def build_ai_context_file(self):
        """Создать ai_context.md для отправки в стороннюю нейросеть."""
        if not self.current_report_id or not self.user_uuid:
            self.error_msg = "Нет активного отчёта"
            return

        selected_keys = [r["key"] for r in self.generate_tag_rows if r["selected"] == "true"]
        if not selected_keys:
            self.error_msg = "Выберите хотя бы один тег"
            return

        import yaml as _yaml

        prompts_path = os.path.join(_MODULES_DIR, "contextualizer", "prompts.yaml")
        try:
            with open(prompts_path, encoding="utf-8") as _f:
                _pcfg = _yaml.safe_load(_f)
            system_prompts = (_pcfg or {}).get("tag_prompts", {})
        except Exception:
            system_prompts = {}

        user_prompts = self._load_user_custom_prompts()

        rdir = os.path.join(
            self._FILES_BASE, "users", self.user_uuid,
            "engrafo", "reports", self.current_report_id,
        )
        ctx_path = os.path.join(rdir, "context.md")
        context_text = ""
        if os.path.isfile(ctx_path):
            with open(ctx_path, encoding="utf-8") as _f:
                context_text = _f.read()

        ocr_path = os.path.join(rdir, "OCR.md")
        ocr_text = ""
        if os.path.isfile(ocr_path):
            with open(ocr_path, encoding="utf-8") as _f:
                ocr_text = _f.read()

        lines = [
            "# AI Context",
            "",
            "Заполни каждую секцию. **Строго соблюдай формат** — каждый ответ должен начинаться с:",
            "",
            "```",
            "## Tag: ключ_тега",
            "Текст ответа",
            "```",
            "",
        ]

        if context_text:
            lines += [
                "---",
                "",
                "## Контекст документа",
                "",
                context_text.strip(),
                "",
            ]

        if ocr_text:
            lines += [
                "---",
                "",
                "## OCR изображений",
                "",
                ocr_text.strip(),
                "",
            ]

        lines += ["---", "", "## Секции для заполнения", ""]

        row_map = {r["key"]: r for r in self.generate_tag_rows}
        for key in selected_keys:
            row = row_map.get(key, {})
            label = row.get("label", key)
            custom_prompt = row.get("custom_prompt", "").strip()

            if key in system_prompts:
                prompt_text = system_prompts[key].get("user", "").strip()
            elif key in user_prompts:
                prompt_text = user_prompts[key].get("user", custom_prompt).strip()
            else:
                prompt_text = custom_prompt or f"Напиши раздел «{label}»."

            lines += [
                f"## Tag: {key}",
                f"Метка: {label}",
                f"Задание: {prompt_text}",
                "",
            ]

        content = "\n".join(lines)
        os.makedirs(rdir, exist_ok=True)
        with open(os.path.join(rdir, "ai_context.md"), "w", encoding="utf-8") as _f:
            _f.write(content)

        api_url = os.getenv("FASTAPI_URL", "http://localhost:8001")
        self.manual_context_url = (
            f"{api_url}/files/users/{self.user_uuid}"
            f"/engrafo/reports/{self.current_report_id}/ai_context.md"
        )

    async def upload_ans_md(self, files: list[rx.UploadFile]):
        """Загрузить ans.md с ответами нейросети и применить к тегам."""
        if not files:
            return
        try:
            raw = await files[0].read()
            text = raw.decode("utf-8", errors="replace")
        except Exception as exc:
            self.error_msg = f"Ошибка чтения файла: {exc}"
            return

        sections = _re.split(r'\n(?=## Tag: )', text)
        parsed: dict[str, str] = {}
        for section in sections:
            m = _re.match(r'^## Tag: ([^\n]+)\n(.*)', section, _re.DOTALL)
            if m:
                parsed[m.group(1).strip()] = m.group(2).strip()

        if not parsed:
            self.error_msg = "В файле не найдено разделов «## Tag: ...»"
            return

        applied = []
        self.tag_entries = [
            (_make_tag_entry(e["key"], e["label"], parsed[e["key"]])
             if e["key"] in parsed else e)
            for e in self.tag_entries
        ]
        applied = [k for k in parsed if any(e["key"] == k for e in self.tag_entries)]

        self.form_key += 1
        self.show_generate_modal = False
        self.success_msg = f"Применено из ans.md: {', '.join(applied)}" if applied else "Ничего не применено"
        self._last_change_ts = time.time()
        self._try_autosave()

    def open_tags_modal(self):
        self.show_tags_modal = True

    def close_tags_modal(self):
        self.show_tags_modal = False

    async def upload_template(self, files: list[rx.UploadFile]):
        self.loading = True
        self.error_msg = ""
        yield  # → frontend получает spinner

        try:
            for file in files:
                content = await file.read()
                _tm.save_personal_template(self.user_uuid, file.filename or "template.docx", content)
            self.templates = _str_dicts(_tm.list_templates(self.user_uuid))
            self.success_msg = f"✓ Загружено {len(files)} шаблон{'ов' if len(files) != 1 else ''}"
            await asyncio.sleep(2)  # показать сообщение 2 сек перед закрытием
            self.show_upload_dialog = False
            self.success_msg = ""
        except Exception as exc:
            self.error_msg = f"Ошибка загрузки: {exc}"
        finally:
            self.loading = False

    # =========================================================================
    # Feedback helpers
    # =========================================================================

    def noop(self):
        """Пустой обработчик для условных on_click."""

    def clear_messages(self):
        self.error_msg   = ""
        self.success_msg = ""

    # =========================================================================
    # Computed vars
    # =========================================================================

    @rx.var
    def has_tags(self) -> bool:
        return len(self.tag_entries) > 0

    @rx.var
    def visible_tag_entries(self) -> list[dict[str, str]]:
        """Только выбранные теги для отображения в редакторе."""
        if not self.selected_tags:
            return []
        return [e for e in self.tag_entries if e["key"] in self.selected_tags]

    @rx.var
    def all_tags_selected(self) -> bool:
        return len(self.selected_tags) >= len(self.tag_entries) and len(self.tag_entries) > 0

    @rx.var
    def has_preview(self) -> bool:
        return self.preview_url != ""

    @rx.var
    def has_reports(self) -> bool:
        return len(self.reports) > 0

    @rx.var
    def has_templates(self) -> bool:
        return len(self.templates) > 0

    @rx.var
    def has_profiles(self) -> bool:
        return len(self.profiles) > 0

    @rx.var
    def has_versions(self) -> bool:
        return len(self.versions) > 0

    # =========================================================================
    # Global tags (user-level defaults)
    # =========================================================================

    def set_engrafo_tab(self, tab: str):
        self.engrafo_tab = tab

    def set_global_tag_new_key(self, v: str):
        self.global_tag_new_key = v

    def set_global_tag_new_value(self, v: str):
        self.global_tag_new_value = v

    def _global_tags_path(self) -> str:
        return os.path.join(
            self._FILES_BASE, "users", self.user_uuid, "engrafo", "global_tags.json"
        )

    def _load_global_tags_dict(self) -> dict:
        import json as _json
        path = self._global_tags_path()
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                return _json.load(f)
        except Exception:
            return {}

    @staticmethod
    def _get_admin_global_tag_keys() -> list[dict]:
        """Читает global_tag_keys из prompts.yaml (определяются администратором)."""
        import yaml as _yaml
        prompts_path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../../../../modules/contextualizer/prompts.yaml"
        ))
        try:
            with open(prompts_path, encoding="utf-8") as f:
                pcfg = _yaml.safe_load(f) or {}
            return pcfg.get("global_tag_keys", [])
        except Exception:
            return []

    def _load_global_tags(self):
        d = self._load_global_tags_dict()
        # Добавляем admin-defined ключи если их нет у пользователя
        for entry in self._get_admin_global_tag_keys():
            key = str(entry.get("key", ""))
            if key and key not in d:
                d[key] = ""
        self.global_tags = [{"key": k, "value": v} for k, v in d.items()]

    def _save_global_tags_from_list(self):
        import json as _json
        path = self._global_tags_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        d = {e["key"]: e["value"] for e in self.global_tags}
        with open(path, "w", encoding="utf-8") as f:
            _json.dump(d, f, ensure_ascii=False, indent=2)

    def set_global_tag_value(self, key: str, value: str):
        self.global_tags = [
            {"key": e["key"], "value": value} if e["key"] == key else e
            for e in self.global_tags
        ]
        self._save_global_tags_from_list()

    def add_global_tag(self):
        key = self.global_tag_new_key.strip()
        if not key:
            return
        # Update existing or add new
        for e in self.global_tags:
            if e["key"] == key:
                self.global_tags = [
                    {"key": e2["key"], "value": self.global_tag_new_value}
                    if e2["key"] == key else e2
                    for e2 in self.global_tags
                ]
                self._save_global_tags_from_list()
                self.global_tag_new_key = ""
                self.global_tag_new_value = ""
                return
        self.global_tags = self.global_tags + [
            {"key": key, "value": self.global_tag_new_value}
        ]
        self._save_global_tags_from_list()
        self.global_tag_new_key = ""
        self.global_tag_new_value = ""

    def delete_global_tag(self, key: str):
        self.global_tags = [e for e in self.global_tags if e["key"] != key]
        self._save_global_tags_from_list()

    # =========================================================================
    # Internal helpers
    # =========================================================================

    async def _load_current_report(self):
        report = _rm.get_report(self.user_uuid, self.current_report_id)
        if not report:
            return

        self.current_report_title = report.get("title", "")
        self.selected_template_id   = report.get("template_id", "")
        self.selected_template_name = report.get("template_name", "")

        stored = report.get("tag_values", {})
        tpl_path = _tm.get_template_path(self.user_uuid, self.selected_template_id)
        if tpl_path:
            self.tag_entries = [
                _make_tag_entry(t["key"], t["label"],
                                str(stored.get(t["key"], "")))
                for t in _tm.extract_tags(tpl_path)
            ]
        else:
            self.tag_entries = [
                _make_tag_entry(k, k, str(v))
                for k, v in stored.items()
            ]

        self.selected_tags = [e["key"] for e in self.tag_entries]
        self.versions = _version_dicts(_rm.list_versions(self.user_uuid, self.current_report_id))

        # Проверить наличие pdf
        pdf_path = _rm.get_current_pdf_path(self.user_uuid, self.current_report_id)
        if os.path.isfile(pdf_path):
            api_url = os.getenv("FASTAPI_URL", "http://localhost:8001")
            ts      = int(os.path.getmtime(pdf_path))
            self.preview_url = (
                f"{api_url}/files/users/{self.user_uuid}/engrafo"
                f"/reports/{self.current_report_id}/current.pdf?t={ts}"
            )
        else:
            self.preview_url = ""
