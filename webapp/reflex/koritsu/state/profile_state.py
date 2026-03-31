import asyncio
import os
import re
import reflex as rx
import httpx
from pydantic import BaseModel
from koritsu.state.auth_state import AuthState

API_URL = os.getenv("FASTAPI_URL", "http://localhost:8001")
FILES_URL = os.getenv("PUBLIC_FILES_URL", API_URL)


class FileData(BaseModel):
    name: str
    file_type: str
    size: str
    date: str


class ReferralData(rx.Base):
    name: str = ""
    earnings: str = ""
    date: str = ""
    status: str = "active"


class ProfileState(rx.State):

    # === Аккаунт ===
    editing_password: bool = False
    editing_username: bool = False
    editing_display_name: bool = False

    password: str = "••••••••"
    password_input: str = ""
    old_password_input: str = ""
    username: str = ""
    username_input: str = ""
    display_name: str = ""
    display_name_input: str = ""
    avatar_url: str = ""

    profile_message: str = ""
    profile_message_is_error: bool = False

    # === Файлы ===
    search_query: str = ""
    files: list[FileData] = []

    # === Реферальная программа ===
    copied: bool = False
    is_connected: bool = False
    referral_link: str = ""
    referral_count: int = 0
    ref_uuid: str = ""
    referrals: list[ReferralData] = []

    # === Аватарка ===
    show_avatar_upload: bool = False
    avatar_preview_url: str = ""
    avatar_upload_error: str = ""
    avatar_pending_b64: str = ""
    avatar_pending_filename: str = ""

    # === Computed vars ===

    @rx.var
    def current_page(self) -> str:
        return self.router.url.path

    @rx.var
    def is_account_active(self) -> bool:
        return self.current_page == "/profile"

    @rx.var
    def is_files_active(self) -> bool:
        return self.current_page == "/profile/files"

    @rx.var
    def is_referral_active(self) -> bool:
        return self.current_page == "/profile/referral"

    @rx.var
    def filtered_files(self) -> list[FileData]:
        if not self.search_query:
            return self.files
        query = self.search_query.lower()
        return [f for f in self.files if query in f.name.lower()]

    @rx.var
    def user_initial(self) -> str:
        if self.display_name:
            return self.display_name[0].upper()
        elif self.username:
            return self.username[0].upper()
        return "?"

    @rx.var
    def total_referrals_count(self) -> str:
        return str(self.referral_count)

    @rx.var
    def pw_check_length(self) -> bool:
        return len(self.password_input) >= 12

    @rx.var
    def pw_check_upper(self) -> bool:
        return bool(re.search(r"[A-ZА-ЯЁ]", self.password_input))

    @rx.var
    def pw_check_special(self) -> bool:
        return bool(re.search(r"""[!@#$%^&*()\-_=+\[\]{}|;:'",.<>?/`~]""", self.password_input))

    # === Setters ===

    def set_password_input(self, value: str):
        self.password_input = value

    def set_old_password_input(self, value: str):
        self.old_password_input = value

    def set_username_input(self, value: str):
        self.username_input = value

    def set_display_name_input(self, value: str):
        self.display_name_input = value

    def set_search_query(self, value: str):
        self.search_query = value

    # === Валидация ===

    def _validate_password(self, password: str) -> str | None:
        if len(password) < 12:
            return "Пароль должен быть не менее 12 символов"
        if not re.search(r"[A-ZА-ЯЁ]", password):
            return "Пароль должен содержать хотя бы одну заглавную букву"
        if not re.search(r"""[!@#$%^&*()\-_=+\[\]{}|;:'",.<>?/`~]""", password):
            return "Пароль должен содержать хотя бы один спецсимвол"
        return None

    # === Пароль ===

    def start_edit_password(self):
        self.editing_password = True
        self.password_input = ""
        self.old_password_input = ""
        self.profile_message = ""

    def cancel_edit_password(self):
        self.editing_password = False
        self.password_input = ""
        self.old_password_input = ""
        self.profile_message = ""

    async def save_password(self):
        if not self.password_input or not self.old_password_input:
            self.profile_message = "Заполните оба поля пароля"
            self.profile_message_is_error = True
            return

        err = self._validate_password(self.password_input)
        if err:
            self.profile_message = err
            self.profile_message_is_error = True
            return

        auth_state = await self.get_state(AuthState)
        if not auth_state.user_uuid:
            return

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.patch(
                    f"{API_URL}/user/{auth_state.user_uuid}",
                    json={"item": "password", "newitem": self.password_input, "olditem": self.old_password_input},
                    timeout=10,
                )
                data = resp.json()
        except Exception:
            self.profile_message = "Ошибка подключения к серверу"
            self.profile_message_is_error = True
            return

        if "error" in data:
            self.profile_message = data["error"]
            self.profile_message_is_error = True
        else:
            self.profile_message = "Пароль изменён"
            self.profile_message_is_error = False
            self.editing_password = False
            self.password_input = ""
            self.old_password_input = ""

    # === Имя пользователя ===

    def start_edit_username(self):
        self.editing_username = True
        self.username_input = self.username
        self.profile_message = ""

    def cancel_edit_username(self):
        self.editing_username = False
        self.username_input = ""
        self.profile_message = ""

    async def save_username(self):
        if not self.username_input.strip():
            self.editing_username = False
            return

        auth_state = await self.get_state(AuthState)
        if not auth_state.user_uuid:
            return

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.patch(
                    f"{API_URL}/user/{auth_state.user_uuid}",
                    json={"item": "username", "newitem": self.username_input.strip()},
                    timeout=10,
                )
                data = resp.json()
        except Exception:
            self.profile_message = "Ошибка подключения к серверу"
            self.profile_message_is_error = True
            return

        if "error" in data:
            self.profile_message = data["error"]
            self.profile_message_is_error = True
        else:
            self.username = self.username_input.strip()
            self.profile_message = "Имя пользователя изменено"
            self.profile_message_is_error = False
            self.editing_username = False
            self.username_input = ""

    # === Отображаемое имя ===

    def start_edit_display_name(self):
        self.editing_display_name = True
        self.display_name_input = self.display_name
        self.profile_message = ""

    def cancel_edit_display_name(self):
        self.editing_display_name = False
        self.display_name_input = ""
        self.profile_message = ""

    async def save_display_name(self):
        if not self.display_name_input.strip():
            self.editing_display_name = False
            return

        auth_state = await self.get_state(AuthState)
        if not auth_state.user_uuid:
            return

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.patch(
                    f"{API_URL}/user/{auth_state.user_uuid}",
                    json={"item": "display_name", "newitem": self.display_name_input.strip()},
                    timeout=10,
                )
                data = resp.json()
        except Exception:
            self.profile_message = "Ошибка подключения к серверу"
            self.profile_message_is_error = True
            return

        if "error" in data:
            self.profile_message = data["error"]
            self.profile_message_is_error = True
        else:
            self.display_name = self.display_name_input.strip()
            self.profile_message = "Отображаемое имя изменено"
            self.profile_message_is_error = False
            self.editing_display_name = False
            self.display_name_input = ""

    # === Аватарка ===

    def open_avatar_upload(self):
        self.show_avatar_upload = True
        self.avatar_preview_url = ""
        self.avatar_upload_error = ""
        self.avatar_pending_b64 = ""
        self.avatar_pending_filename = ""

    def close_avatar_upload(self):
        self.show_avatar_upload = False
        self.avatar_preview_url = ""
        self.avatar_upload_error = ""
        self.avatar_pending_b64 = ""
        self.avatar_pending_filename = ""

    async def handle_avatar_select(self, files: list[rx.UploadFile]):
        """Сохраняет файл в state и показывает превью."""
        if not files:
            return
        file = files[0]
        fname_lower = file.filename.lower()
        if not any(fname_lower.endswith(e) for e in (".png", ".jpg", ".jpeg")):
            self.avatar_upload_error = "Разрешены только файлы PNG и JPEG"
            self.avatar_preview_url = ""
            self.avatar_pending_b64 = ""
            return
        self.avatar_upload_error = ""
        import base64
        upload_data = await file.read()
        b64 = base64.b64encode(upload_data).decode("utf-8")
        mime = "image/jpeg" if fname_lower.endswith((".jpg", ".jpeg")) else "image/png"
        self.avatar_preview_url = f"data:{mime};base64,{b64}"
        self.avatar_pending_b64 = b64
        self.avatar_pending_filename = file.filename

    async def upload_avatar(self):
        """Загружает сохранённый файл на сервер."""
        if not self.avatar_pending_b64:
            self.avatar_upload_error = "Сначала выберите файл"
            return

        auth_state = await self.get_state(AuthState)
        if not auth_state.user_uuid:
            self.show_avatar_upload = False
            return

        import base64
        upload_data = base64.b64decode(self.avatar_pending_b64)
        _fname = self.avatar_pending_filename.lower()
        _mime = "image/jpeg" if _fname.endswith((".jpg", ".jpeg")) else "image/png"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/user/{auth_state.user_uuid}/avatar",
                    files={"file": (self.avatar_pending_filename, upload_data, _mime)},
                    timeout=30,
                )
                data = resp.json()
        except Exception:
            self.avatar_upload_error = "Ошибка подключения к серверу"
            return

        if "icon" in data:
            import time
            ts = int(time.time())
            self.avatar_url = f"{FILES_URL}/{data['icon']}?t={ts}"
            # Синхронизируем с AuthState для хедера и home
            auth_state.user_icon = f"{FILES_URL}/{data['icon']}?t={ts}"

        self.show_avatar_upload = False
        self.avatar_preview_url = ""
        self.avatar_upload_error = ""
        self.avatar_pending_b64 = ""
        self.avatar_pending_filename = ""

    # === Реферальная программа ===

    async def copy_referral_link(self):
        yield rx.set_clipboard(self.referral_link)
        self.copied = True
        yield
        await asyncio.sleep(2)
        self.copied = False

    async def connect_referral_program(self):
        auth_state = await self.get_state(AuthState)
        if not auth_state.user_uuid:
            return

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/user/{auth_state.user_uuid}/referral",
                    timeout=10,
                )
                data = resp.json()
        except Exception:
            return

        if "ref_uuid" in data:
            self.ref_uuid = data["ref_uuid"]
            self.referral_link = f"https://koritsu.app/ref/{data['ref_uuid']}"
            self.is_connected = True

    # === Загрузка данных ===

    async def load_user_data(self):
        auth_state = await self.get_state(AuthState)

        if not auth_state.user_uuid:
            return rx.redirect("/")

        user_uuid = auth_state.user_uuid

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API_URL}/user/{user_uuid}", timeout=10)
                data = resp.json()
        except Exception:
            return

        if "user_data" in data:
            ud = data["user_data"]
            self.username = ud.get("username", "")
            self.display_name = ud.get("display_name") or ud.get("username", "")
            icon = ud.get("icon") or ""
            import time as _time
            self.avatar_url = f"{FILES_URL}/{icon}?t={int(_time.time())}" if icon else ""

        # Загружаем реферальные данные
        try:
            async with httpx.AsyncClient() as client:
                ref_resp = await client.get(f"{API_URL}/user/{user_uuid}/referral", timeout=10)
                ref_data = ref_resp.json()
        except Exception:
            return

        if ref_data.get("referral"):
            r = ref_data["referral"]
            self.ref_uuid = r.get("ref_uuid", "")
            self.referral_count = r.get("referral_count", 0)
            self.referral_link = f"https://koritsu.app/ref/{self.ref_uuid}"
            self.is_connected = True
        else:
            self.is_connected = False
            self.referrals = []
            return

        # Загружаем список рефералов
        try:
            async with httpx.AsyncClient() as client:
                det_resp = await client.get(
                    f"{API_URL}/user/{user_uuid}/referral/details", timeout=10
                )
                det_data = det_resp.json()
        except Exception:
            return

        raw = det_data.get("referrals", [])
        self.referrals = [
            ReferralData(
                name=item.get("name", ""),
                earnings=item.get("earnings", "0 бонусов"),
                date=item.get("date", ""),
                status=item.get("status", "active"),
            )
            for item in raw
        ]
