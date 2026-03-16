import reflex as rx
import httpx

API_URL = "http://localhost:8001"


class ReferralData(rx.Base):
    """Модель данных для реферала."""
    name: str
    email: str
    status: str  # 'active' или 'pending'
    earnings: str
    date: str


class FileData(rx.Base):
    """Модель данных для файла."""
    name: str
    file_type: str  # 'document', 'image', 'audio', 'video'
    size: str
    date: str


class ProfileState(rx.State):
    """Состояние страницы профиля пользователя."""
    
    # === Аккаунт ===
    editing_password: bool = False
    editing_username: bool = False
    editing_display_name: bool = False
    
    password: str = "••••••••"
    password_input: str = ""
    username: str = ""
    username_input: str = ""
    display_name: str = ""
    display_name_input: str = ""
    email: str = ""
    avatar_url: str = ""
    
    # === Файлы ===
    search_query: str = ""
    
    files: list[FileData] = []
    
    # === Реферальная программа ===
    copied: bool = False
    is_connected: bool = True
    
    referral_link: str = ""
    show_avatar_upload: bool = False
    
    referrals: list[ReferralData] = []
    
    # === Computed vars ===
    
    @rx.var
    def current_page(self) -> str:
        """Текущая страница для подсветки в сайдбаре."""
        return self.router.page.path
    
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
        """Фильтрация файлов по поисковому запросу."""
        if not self.search_query:
            return self.files
        query = self.search_query.lower()
        return [f for f in self.files if query in f.name.lower()]
    
    @rx.var
    def total_earnings(self) -> str:
        """Общая сумма заработка от рефералов."""
        total = 0
        for ref in self.referrals:
            earnings_str = ref.earnings.replace("₽", "").replace(",", "")
            if earnings_str.isdigit():
                total += int(earnings_str)
        return f"₽{total:,}"
    
    @rx.var
    def active_referrals_count(self) -> str:
        """Количество активных рефералов."""
        return str(sum(1 for ref in self.referrals if ref.status == "active"))
    
    @rx.var
    def total_referrals_count(self) -> str:
        """Общее количество рефералов."""
        return str(len(self.referrals))
    
    @rx.var
    def user_initial(self) -> str:
        """Первая буква имени для аватара."""
        if self.display_name:
            return self.display_name[0].upper()
        elif self.username:
            return self.username[0].upper()
        return "?"
    
    # === Методы ===
    
    def set_password_input(self, value: str):
        self.password_input = value
    
    def set_username_input(self, value: str):
        self.username_input = value
    
    def set_display_name_input(self, value: str):
        self.display_name_input = value
    
    def start_edit_password(self):
        self.editing_password = True
        self.password_input = ""
    
    def save_password(self):
        """Сохранение нового пароля."""
        if not self.password_input:
            return
        
        try:
            import httpx
            auth_state = self.get_state("koritsu.state.auth_state.AuthState")
            if auth_state.user_uuid:
                with httpx.Client() as client:
                    resp = client.post(
                        f"{API_URL}/user/{auth_state.user_uuid}/change-password",
                        json={"new_password": self.password_input},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        self.password = "••••••••"
        except Exception:
            pass
        
        self.editing_password = False
        self.password_input = ""
    
    def cancel_edit_password(self):
        self.editing_password = False
        self.password = "••••••••"
        self.password_input = ""
    
    def start_edit_username(self):
        self.editing_username = True
        self.username_input = self.username
    
    def save_username(self):
        """Сохранение нового имени пользователя."""
        if not self.username_input.strip():
            self.editing_username = False
            self.username_input = ""
            return
        
        try:
            import httpx
            auth_state = self.get_state("koritsu.state.auth_state.AuthState")
            if auth_state.user_uuid:
                with httpx.Client() as client:
                    resp = client.post(
                        f"{API_URL}/user/{auth_state.user_uuid}/change-username",
                        json={"new_username": self.username_input.strip()},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        self.username = self.username_input.strip()
                        self.referral_link = f"https://example.com/ref/{self.username}"
        except Exception:
            pass
        
        self.editing_username = False
        self.username_input = ""
    
    def cancel_edit_username(self):
        self.editing_username = False
        self.username_input = ""
    
    def start_edit_display_name(self):
        self.editing_display_name = True
        self.display_name_input = self.display_name
    
    def save_display_name(self):
        """Сохранение нового отображаемого имени."""
        if not self.display_name_input.strip():
            self.editing_display_name = False
            self.display_name_input = ""
            return
        
        try:
            import httpx
            auth_state = self.get_state("koritsu.state.auth_state.AuthState")
            if auth_state.user_uuid:
                with httpx.Client() as client:
                    resp = client.post(
                        f"{API_URL}/user/{auth_state.user_uuid}/change-display-name",
                        json={"new_display_name": self.display_name_input.strip()},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        self.display_name = self.display_name_input.strip()
        except Exception:
            pass
        
        self.editing_display_name = False
        self.display_name_input = ""
    
    def cancel_edit_display_name(self):
        self.editing_display_name = False
        self.display_name_input = ""
    
    async def copy_referral_link(self):
        """Копирование реферальной ссылки."""
        yield rx.set_clipboard(self.referral_link)
        self.copied = True
        yield
        await rx.sleep(2)
        self.copied = False
    
    def connect_referral_program(self):
        """Подключение к реферальной программе."""
        self.is_connected = True
    
    def open_avatar_upload(self):
        """Открыть диалог загрузки аватарки."""
        self.show_avatar_upload = True
    
    def close_avatar_upload(self):
        """Закрыть диалог загрузки аватарки."""
        self.show_avatar_upload = False
    
    async def upload_avatar(self, files: list[rx.UploadFile]):
        """Загрузка аватарки пользователя."""
        if not files:
            return
        
        try:
            auth_state = await self.get_state("koritsu.state.auth_state.AuthState")
            if not auth_state.user_uuid:
                return
                
            file = files[0]
            upload_data = await file.read()
            
            async with httpx.AsyncClient() as client:
                files_dict = {"avatar": (file.filename, upload_data, file.content_type)}
                resp = await client.post(
                    f"{API_URL}/user/{auth_state.user_uuid}/avatar",
                    files=files_dict,
                    timeout=30,
                )
                data = resp.json()
            
            if "icon" in data:
                self.avatar_url = f"{API_URL}/{data['icon']}"
            
            self.show_avatar_upload = False
        except Exception:
            self.show_avatar_upload = False
    
    async def load_user_data(self):
        """Загрузка данных пользователя из API."""
        # Получаем данные из AuthState
        try:
            auth_state = await self.get_state(AuthState)
        except Exception:
            return
        
        if not auth_state.user_uuid:
            # Если не авторизован, перенаправляем на главную
            return
        
        user_uuid = auth_state.user_uuid
        
        # Загружаем данные пользователя
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_URL}/user/{user_uuid}",
                    timeout=10,
                )
                data = resp.json()
        except Exception:
            return
        
        if "user_data" in data:
            ud = data["user_data"]
            self.username = ud.get("username", "")
            self.display_name = ud.get("display_name") or ud.get("username", "")
            self.email = ud.get("email", "")
            
            # Аватар
            icon = ud.get("icon") or ""
            if icon:
                self.avatar_url = f"{API_URL}/{icon}"
            else:
                self.avatar_url = ""
            
            # Реферальная ссылка
            self.referral_link = f"https://example.com/ref/{self.username}"
            
            # Загружаем файлы пользователя
            try:
                async with httpx.AsyncClient() as client:
                    files_resp = await client.get(
                        f"{API_URL}/user/{user_uuid}/fragmos",
                        timeout=10,
                    )
                    files_data = files_resp.json()
                    if "files" in files_data:
                        self.files = [
                            FileData(name=f, file_type="document", size="Неизвестно", date="Неизвестно")
                            for f in files_data["files"]
                        ]
            except Exception:
                pass
            
            # Загружаем рефералов
            try:
                async with httpx.AsyncClient() as client:
                    refs_resp = await client.get(
                        f"{API_URL}/user/{user_uuid}/referrals",
                        timeout=10,
                    )
                    refs_data = refs_resp.json()
                    if "referrals" in refs_data:
                        self.referrals = [
                            ReferralData(
                                name=r.get("name", ""),
                                email=r.get("email", ""),
                                status=r.get("status", "pending"),
                                earnings=r.get("earnings", "₽0"),
                                date=r.get("date", ""),
                            )
                            for r in refs_data["referrals"]
                        ]
            except Exception:
                pass
