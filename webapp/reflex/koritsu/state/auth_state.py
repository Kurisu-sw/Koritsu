import re
import time
import reflex as rx
import httpx

API_URL = "http://localhost:8001"


class AuthState(rx.State):
    # ── User data ──────────────────────────────────────────────────────────────
    user_uuid: str = ""
    username: str = ""
    user_icon: str = ""
    sub_level: str = "free"
    sub_expire_date: str = ""
    tokens_left: int = 0

    # ── Persistent session (localStorage) ────────────────────────────────────
    stored_uuid: str = rx.LocalStorage(name="koritsu_uuid", sync=True)

    # ── Modal ──────────────────────────────────────────────────────────────────
    show_auth_modal: bool = False
    auth_tab: str = "login"
    show_avatar_upload: bool = False
    avatar_file: str = ""

    # ── Form fields ────────────────────────────────────────────────────────────
    login_username: str = ""
    login_password: str = ""
    register_username: str = ""
    register_password: str = ""
    register_password_confirm: str = ""
    register_ref_code: str = ""

    # ── Feedback ───────────────────────────────────────────────────────────────
    auth_error: str = ""
    auth_success: str = ""

    # ── Rate limiting (backend-only: underscore prefix) ────────────────────────
    _login_attempts: int = 0
    _login_cooldown_until: float = 0.0
    _register_attempts: int = 0
    _register_cooldown_until: float = 0.0

    # ── Computed vars ──────────────────────────────────────────────────────────

    @rx.var
    def is_logged_in(self) -> bool:
        return self.user_uuid != ""

    @rx.var
    def sub_label(self) -> str:
        m = {"free": "Free", "pro": "Pro", "enterprise": "Enterprise"}
        return m.get(self.sub_level, self.sub_level.capitalize())

    @rx.var
    def user_initial(self) -> str:
        if self.username:
            return self.username[0].upper()
        return "?"

    @rx.var
    def sub_expire_display(self) -> str:
        if self.sub_expire_date:
            return self.sub_expire_date
        return "Бессрочно"

    # ── Modal controls ─────────────────────────────────────────────────────────

    async def check_auth_query(self):
        """Restore session from localStorage + handle ?auth= query param."""
        # Restore session if we have a stored UUID but no active session
        if not self.user_uuid and self.stored_uuid:
            self.user_uuid = self.stored_uuid
            await self._load_user_data()
            # If load failed (user deleted, etc.), clear everything
            if not self.username:
                self.user_uuid = ""
                self.stored_uuid = ""

        params = self.router.page.params
        auth = params.get("auth", "")
        if auth == "login":
            self.open_login()
        elif auth == "register":
            self.open_register()

    def open_login(self):
        self.auth_tab = "login"
        self.auth_error = ""
        self.auth_success = ""
        self.show_auth_modal = True

    def open_register(self):
        self.auth_tab = "register"
        self.auth_error = ""
        self.auth_success = ""
        self.show_auth_modal = True

    def close_auth_modal(self):
        self.show_auth_modal = False
        self.auth_error = ""
        self.auth_success = ""
        self.login_password = ""
        self.register_password = ""
        self.register_password_confirm = ""
        self.register_ref_code = ""

    def set_register_ref_code(self, value: str):
        self.register_ref_code = value

    def switch_to_login(self):
        self.auth_tab = "login"
        self.auth_error = ""

    def switch_to_register(self):
        self.auth_tab = "register"
        self.auth_error = ""

    # ── Avatar upload ──────────────────────────────────────────────────────────

    def open_avatar_upload(self):
        self.show_avatar_upload = True

    def close_avatar_upload(self):
        self.show_avatar_upload = False

    async def upload_avatar(self, files: list[rx.UploadFile]):
        """Загрузка аватарки пользователя."""
        if not files or not self.user_uuid:
            return
        
        try:
            file = files[0]
            upload_data = await file.read()
            
            # Отправляем файл на сервер
            async with httpx.AsyncClient() as client:
                # Создаём multipart/form-data запрос
                files_dict = {"avatar": (file.filename, upload_data, file.content_type)}
                resp = await client.post(
                    f"{API_URL}/user/{self.user_uuid}/avatar",
                    files=files_dict,
                    timeout=30,
                )
                data = resp.json()
            
            if "icon" in data:
                self.user_icon = data["icon"]
                # Обновляем avatar_url в ProfileState
                profile_state = await self.get_state("koritsu.state.profile_state.ProfileState")
                profile_state.avatar_url = f"{API_URL}/{data['icon']}"
            
            self.show_avatar_upload = False
        except Exception:
            self.show_avatar_upload = False

    # ── Validation ─────────────────────────────────────────────────────────────

    def _validate_password(self, password: str) -> str | None:
        if len(password) < 12:
            return "Пароль должен быть не менее 12 символов"
        if not re.search(r"[A-ZА-ЯЁ]", password):
            return "Пароль должен содержать хотя бы одну заглавную букву"
        if not re.search(r"""[!@#$%^&*()\-_=+\[\]{}|;:'",.<>?/`~]""", password):
            return "Пароль должен содержать хотя бы один спецсимвол"
        return None

    # ── Login ──────────────────────────────────────────────────────────────────

    async def do_login(self):
        now = time.time()
        if now < self._login_cooldown_until:
            remaining = int(self._login_cooldown_until - now)
            self.auth_error = f"Подождите {remaining} сек. перед повторной попыткой"
            return

        if not self.login_username.strip() or not self.login_password:
            self.auth_error = "Заполните все поля"
            return

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/login",
                    json={
                        "username": self.login_username.strip(),
                        "password": self.login_password,
                    },
                    timeout=10,
                )
                data = resp.json()
        except Exception:
            self.auth_error = "Ошибка подключения к серверу"
            return

        if "error" in data:
            self._login_attempts += 1
            if self._login_attempts >= 5:
                self._login_cooldown_until = time.time() + 180
                self._login_attempts = 0
                self.auth_error = "Слишком много попыток. Подождите 3 минуты"
            else:
                self.auth_error = data["error"]
            return

        # Success
        self.user_uuid = data.get("uuid", "")
        self.stored_uuid = self.user_uuid  # persist to localStorage
        self._login_attempts = 0
        self.auth_error = ""
        await self._load_user_data()
        self.show_auth_modal = False
        self.login_password = ""

    # ── Logout ─────────────────────────────────────────────────────────────────

    async def do_logout(self):
        self.user_uuid = ""
        self.stored_uuid = ""  # clear localStorage
        self.username = ""
        self.user_icon = ""
        self.sub_level = "free"
        self.sub_expire_date = ""
        self.tokens_left = 0

    async def do_refresh_user(self):
        """Restore session from localStorage if needed, then refresh user data."""
        if not self.user_uuid and self.stored_uuid:
            self.user_uuid = self.stored_uuid
        if self.user_uuid:
            await self._load_user_data()
            if not self.username:
                self.user_uuid = ""
                self.stored_uuid = ""

    # ── Register ───────────────────────────────────────────────────────────────

    async def do_register(self):
        now = time.time()
        if now < self._register_cooldown_until:
            remaining = int(self._register_cooldown_until - now)
            self.auth_error = f"Подождите {remaining} сек. перед повторной попыткой"
            return

        if not self.register_username.strip() or not self.register_password:
            self.auth_error = "Заполните все поля"
            return

        if self.register_password != self.register_password_confirm:
            self.auth_error = "Пароли не совпадают"
            return

        err = self._validate_password(self.register_password)
        if err:
            self.auth_error = err
            return

        try:
            ref_code = self.register_ref_code.strip()
            if ref_code:
                url = f"{API_URL}/register/ref/{ref_code}"
            else:
                url = f"{API_URL}/register"
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    json={
                        "username": self.register_username.strip(),
                        "password": self.register_password,
                    },
                    timeout=10,
                )
                data = resp.json()
        except Exception:
            self.auth_error = "Ошибка подключения к серверу"
            return

        if "error" in data:
            self._register_attempts += 1
            if self._register_attempts >= 5:
                self._register_cooldown_until = time.time() + 300
                self._register_attempts = 0
                self.auth_error = "Слишком много попыток. Подождите 5 минут"
            else:
                self.auth_error = data["error"]
            return

        # Success — switch to login tab
        self._register_attempts = 0
        self.auth_success = "Аккаунт создан! Войдите в систему"
        self.auth_tab = "login"
        self.login_username = self.register_username
        self.register_password = ""
        self.register_password_confirm = ""
        self.register_ref_code = ""

    # ── Load user data ─────────────────────────────────────────────────────────

    async def _load_user_data(self):
        if not self.user_uuid:
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_URL}/user/{self.user_uuid}", timeout=10,
                )
                data = resp.json()
        except Exception:
            return

        if "user_data" in data:
            ud = data["user_data"]
            self.username = ud.get("username", "")
            icon = ud.get("icon") or ""
            # превращаем серверный путь в URL
            if icon:
                self.user_icon = f"{API_URL}/{icon}"
            else:
                self.user_icon = ""
            self.sub_level = ud.get("sub_level", "free")
            self.sub_expire_date = ud.get("sub_expire_date") or ""
            self.tokens_left = ud.get("tokens_left", 0)
