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
import sys
import time
from typing import Any

import reflex as rx

# ── Импорт модулей Engrafo ─────────────────────────────────────────────────────

_ENGRAFO_MODULE = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../modules/engrafo")
)
if _ENGRAFO_MODULE not in sys.path:
    sys.path.insert(0, _ENGRAFO_MODULE)

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
    expand_value: str = ""    # текущее значение в expand

    # ── Image picker ──────────────────────────────────────────────────────────
    image_picker_key: str = ""   # ключ тега, в который вставляем картинку

    # ── Autosave ──────────────────────────────────────────────────────────────
    autosave_pending: bool = False
    _last_change_ts:  float = 0.0   # timestamp последнего изменения тега
    _last_save_ts:    float = 0.0   # timestamp последнего автосохранения

    # ── Feedback ──────────────────────────────────────────────────────────────
    error_msg:   str = ""
    success_msg: str = ""
    loading:     bool = False

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

    async def on_load_editor(self):
        """Вызывается при загрузке страницы /engrafo/editor."""
        await self._sync_user()
        if not self.user_uuid:
            return
        self.templates = _str_dicts(_tm.list_templates(self.user_uuid))
        self.profiles  = _profile_dicts(_pm.list_profiles(self.user_uuid))

        if self.current_report_id:
            await self._load_current_report()

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

        # Загружаем теги шаблона
        tpl_path = _tm.get_template_path(self.user_uuid, self.selected_template_id)
        if tpl_path:
            self.tag_entries = [
                {"key": t["key"], "label": t["label"], "value": ""}
                for t in _tm.extract_tags(tpl_path)
            ]

        self.versions    = []
        self.preview_url = ""

        yield rx.redirect("/engrafo/editor")

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
                {"key": t["key"], "label": t["label"], "value": str(old_values.get(t["key"], ""))}
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

    async def set_tag_value(self, key: str, value: str):
        """Обновить значение одного тега."""
        self.tag_entries = [
            {**e, "value": value} if e["key"] == key else e
            for e in self.tag_entries
        ]
        self._last_change_ts = time.time()
        # Автосохранение (если прошло ≥5 мин с последнего)
        self._try_autosave()
        yield EngrafoState.generate_preview

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
                break

    def set_expand_value(self, value: str):
        self.expand_value = value

    def save_expand_and_close(self):
        """Сохранить значение из expand-редактора и закрыть."""
        if self.expand_key:
            self.tag_entries = [
                {**e, "value": self.expand_value} if e["key"] == self.expand_key else e
                for e in self.tag_entries
            ]
            self._last_change_ts = time.time()
            self._try_autosave()
            self.form_key += 1
        self.expand_key = ""
        self.expand_label = ""
        self.expand_value = ""

    def close_expand_editor(self):
        self.expand_key = ""
        self.expand_label = ""
        self.expand_value = ""

    # ── Image picker ──────────────────────────────────────────────────────────

    def open_image_picker(self, key: str):
        self.image_picker_key = key

    def close_image_picker(self):
        self.image_picker_key = ""

    async def handle_image_upload(self, files: list[rx.UploadFile]):
        """Читает первый файл, кодирует в base64, вставляет в значение тега."""
        if not files or not self.image_picker_key:
            self.image_picker_key = ""
            return
        key = self.image_picker_key
        try:
            f = files[0]
            data = await f.read()
            mime = f.content_type or "image/png"
            b64 = base64.b64encode(data).decode("utf-8")
            data_url = f"data:{mime};base64,{b64}"
            self.tag_entries = [
                {**e, "value": data_url} if e["key"] == key else e
                for e in self.tag_entries
            ]
            self.form_key += 1
            self.success_msg = f"Картинка вставлена в «{key}»"
            self._last_change_ts = time.time()
            self._try_autosave()
        except Exception as exc:
            self.error_msg = f"Ошибка загрузки картинки: {exc}"
        finally:
            self.image_picker_key = ""
        # Сохранить значения тегов на диск + обновить preview
        yield EngrafoState.generate_preview

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
            {**e, "value": stored.get(e["key"], "")}
            for e in self.tag_entries
        ]
        self.form_key += 1  # ремаунт debounce_input'ов
        yield EngrafoState.generate_preview

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
            return self.tag_entries
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
                {"key": t["key"], "label": t["label"], "value": str(stored.get(t["key"], ""))}
                for t in _tm.extract_tags(tpl_path)
            ]
        else:
            self.tag_entries = [
                {"key": k, "label": k, "value": str(v)}
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
