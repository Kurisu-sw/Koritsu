"""State for admin panel — user management, topology health checks."""

import reflex as rx
import httpx

API = "http://localhost:8001"


class AdminState(rx.State):
    # ── Active tab ────────────────────────────────────────────────────────
    active_tab: str = "topology"  # "topology", "balancer", "users"

    # ── Search ───────────────────────────────────────────────────────────
    search_query: str = ""
    search_error: str = ""
    search_results: list[dict] = []  # for username search (multiple results)

    # ── Loaded user data ─────────────────────────────────────────────────
    user_loaded: bool = False
    user_uuid: str = ""
    username: str = ""
    display_name: str = ""
    sub_level: str = ""
    sub_expire_date: str = ""
    tokens_left: int = 0
    icon: str = ""
    is_banned: int = 0
    ban_reason: str = ""
    ban_until: str = ""

    # ── Edit fields ──────────────────────────────────────────────────────
    edit_username: str = ""
    edit_display_name: str = ""
    edit_tokens: str = ""
    edit_sub_level: str = ""
    edit_password: str = ""
    ban_reason_input: str = ""
    ban_timeout_minutes: str = ""  # empty = permanent

    # ── Feedback ─────────────────────────────────────────────────────────
    save_success: str = ""
    save_error: str = ""

    # ── Topology health ──────────────────────────────────────────────────
    topo_reflex_status: str = "checking"
    topo_fastapi_status: str = "checking"
    topo_db_status: str = "checking"
    topo_ai_status: str = "checking"
    topo_reflex_latency: str = ""
    topo_fastapi_latency: str = ""
    topo_ai_latency: str = ""

    # ── Confirm delete ───────────────────────────────────────────────────
    show_delete_confirm: bool = False

    def set_active_tab(self, tab: str):
        self.active_tab = tab

    def set_search_query(self, v: str):
        self.search_query = v

    def set_edit_username(self, v: str):
        self.edit_username = v

    def set_edit_display_name(self, v: str):
        self.edit_display_name = v

    def set_edit_tokens(self, v: str):
        self.edit_tokens = v

    def set_edit_sub_level(self, v: str):
        self.edit_sub_level = v

    def set_edit_password(self, v: str):
        self.edit_password = v

    def set_ban_reason_input(self, v: str):
        self.ban_reason_input = v

    def set_ban_timeout_minutes(self, v: str):
        self.ban_timeout_minutes = v

    def toggle_delete_confirm(self):
        self.show_delete_confirm = not self.show_delete_confirm

    # ── Search ───────────────────────────────────────────────────────────

    @staticmethod
    def _looks_like_uuid(s: str) -> bool:
        """Check if string looks like a UUID (contains dashes and hex chars)."""
        import re
        return bool(re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-', s, re.IGNORECASE))

    async def search_user(self):
        self.search_error = ""
        self.user_loaded = False
        self.search_results = []
        self.save_success = ""
        self.save_error = ""

        q = self.search_query.strip()
        if not q:
            self.search_error = "Enter UUID or username"
            return

        # Auto-detect: if it looks like UUID, search by UUID; otherwise by username
        if self._looks_like_uuid(q):
            await self._load_user_by_uuid(q)
        else:
            await self._search_by_username(q)

    async def _load_user_by_uuid(self, uuid: str):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API}/user/{uuid}", timeout=5)
                data = resp.json()
        except Exception as e:
            self.search_error = f"Connection error: {e}"
            return

        if "error" in data:
            self.search_error = data["error"]
            return

        self._fill_user_data(uuid, data.get("user_data", {}))

    async def _search_by_username(self, username: str):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API}/admin/search",
                    params={"username": username},
                    timeout=5,
                )
                data = resp.json()
        except Exception as e:
            self.search_error = f"Connection error: {e}"
            return

        if "error" in data:
            self.search_error = data["error"]
            return

        users = data.get("users", [])
        if len(users) == 0:
            self.search_error = "No users found"
        elif len(users) == 1:
            u = users[0]
            self._fill_user_data(u["uuid"], u)
        else:
            self.search_results = users

    async def select_search_result(self, uuid: str):
        """Pick a user from search results."""
        self.search_results = []
        await self._load_user_by_uuid(uuid)

    def _fill_user_data(self, uuid: str, ud: dict):
        self.user_uuid = uuid
        self.username = ud.get("username", "")
        self.display_name = ud.get("display_name", "") or ""
        self.sub_level = ud.get("sub_level", "free")
        self.sub_expire_date = ud.get("sub_expire_date", "") or ""
        self.tokens_left = ud.get("tokens_left", 0) or 0
        self.icon = ud.get("icon", "") or ""
        self.is_banned = ud.get("is_banned", 0) or 0
        self.ban_reason = ud.get("ban_reason", "") or ""
        self.ban_until = ud.get("ban_until", "") or ""

        self.edit_username = self.username
        self.edit_display_name = self.display_name
        self.edit_tokens = str(self.tokens_left)
        self.edit_sub_level = self.sub_level
        self.edit_password = ""
        self.ban_reason_input = ""
        self.ban_timeout_minutes = ""
        self.show_delete_confirm = False
        self.user_loaded = True

    # ── Save operations ──────────────────────────────────────────────────

    async def save_username(self):
        self.save_error = ""
        self.save_success = ""
        if self.edit_username == self.username:
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.patch(
                    f"{API}/user/{self.user_uuid}",
                    json={"item": "username", "newitem": self.edit_username},
                    timeout=5,
                )
                data = resp.json()
            if "error" in data:
                self.save_error = data["error"]
            else:
                self.username = self.edit_username
                self.save_success = "Username updated"
        except Exception as e:
            self.save_error = str(e)

    async def save_display_name(self):
        self.save_error = ""
        self.save_success = ""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.patch(
                    f"{API}/user/{self.user_uuid}",
                    json={"item": "display_name", "newitem": self.edit_display_name},
                    timeout=5,
                )
                data = resp.json()
            if "error" in data:
                self.save_error = data["error"]
            else:
                self.display_name = self.edit_display_name
                self.save_success = "Display name updated"
        except Exception as e:
            self.save_error = str(e)

    async def save_tokens(self):
        self.save_error = ""
        self.save_success = ""
        try:
            new_tokens = int(self.edit_tokens)
        except ValueError:
            self.save_error = "Tokens must be a number"
            return

        diff = new_tokens - self.tokens_left
        if diff == 0:
            return

        op = "plus" if diff > 0 else "minus"
        amount = abs(diff)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.patch(
                    f"{API}/user/{self.user_uuid}",
                    json={"item": "tokens_left", "olditem": op, "newitem": str(amount)},
                    timeout=5,
                )
                data = resp.json()
            if "error" in data:
                self.save_error = data["error"]
            else:
                self.tokens_left = new_tokens
                self.save_success = f"Tokens set to {new_tokens}"
        except Exception as e:
            self.save_error = str(e)

    async def save_sub_level(self):
        self.save_error = ""
        self.save_success = ""
        if self.edit_sub_level == self.sub_level:
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.patch(
                    f"{API}/admin/user/{self.user_uuid}/sub-level",
                    json={"item": "sub_level", "newitem": self.edit_sub_level},
                    timeout=5,
                )
                data = resp.json()
            if "error" in data:
                self.save_error = data["error"]
            else:
                self.sub_level = self.edit_sub_level
                self.save_success = f"Sub level → {self.edit_sub_level}"
        except Exception as e:
            self.save_error = str(e)

    async def reset_password(self):
        self.save_error = ""
        self.save_success = ""
        if not self.edit_password.strip():
            self.save_error = "Enter new password"
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API}/admin/user/{self.user_uuid}/reset-password",
                    json={"new_password": self.edit_password},
                    timeout=5,
                )
                data = resp.json()
            if "error" in data:
                self.save_error = data["error"]
            else:
                self.edit_password = ""
                self.save_success = "Password reset"
        except Exception as e:
            self.save_error = str(e)

    async def ban_user(self):
        self.save_error = ""
        self.save_success = ""
        timeout = 0
        if self.ban_timeout_minutes.strip():
            try:
                timeout = int(self.ban_timeout_minutes)
            except ValueError:
                self.save_error = "Timeout must be a number (minutes)"
                return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API}/admin/user/{self.user_uuid}/ban",
                    json={"reason": self.ban_reason_input, "timeout_minutes": timeout},
                    timeout=5,
                )
                data = resp.json()
            if "error" in data:
                self.save_error = data["error"]
            else:
                self.is_banned = 1
                self.ban_reason = self.ban_reason_input
                self.ban_until = data.get("ban_until", "") or ""
                self.save_success = "User banned" if timeout == 0 else f"User timed out for {timeout}m"
        except Exception as e:
            self.save_error = str(e)

    async def unban_user(self):
        self.save_error = ""
        self.save_success = ""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API}/admin/user/{self.user_uuid}/unban",
                    timeout=5,
                )
                data = resp.json()
            if "error" in data:
                self.save_error = data["error"]
            else:
                self.is_banned = 0
                self.ban_reason = ""
                self.ban_until = ""
                self.save_success = "User unbanned"
        except Exception as e:
            self.save_error = str(e)

    async def delete_user(self):
        self.save_error = ""
        self.save_success = ""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.delete(
                    f"{API}/admin/user/{self.user_uuid}",
                    timeout=5,
                )
                data = resp.json()
            if "error" in data:
                self.save_error = data["error"]
            else:
                self.save_success = f"User {self.username} deleted"
                self.user_loaded = False
                self.show_delete_confirm = False
        except Exception as e:
            self.save_error = str(e)

    # ── Topology health checks ───────────────────────────────────────────

    async def check_topology(self):
        """Ping all services and update statuses in one go (no yield)."""
        import time

        # FastAPI
        try:
            t0 = time.monotonic()
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API}/", timeout=3)
            latency = int((time.monotonic() - t0) * 1000)
            if resp.status_code == 200:
                self.topo_fastapi_status = "online"
                self.topo_fastapi_latency = f"{latency}ms"
            else:
                self.topo_fastapi_status = "error"
                self.topo_fastapi_latency = ""
        except Exception:
            self.topo_fastapi_status = "offline"
            self.topo_fastapi_latency = ""

        # DB — dedicated health endpoint
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API}/admin/health", timeout=3)
                data = resp.json()
            if data.get("status") == "ok":
                self.topo_db_status = "online"
            else:
                self.topo_db_status = "error"
        except Exception:
            self.topo_db_status = "offline"

        # Reflex frontend
        try:
            t0 = time.monotonic()
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://localhost:3000", timeout=3)
            latency = int((time.monotonic() - t0) * 1000)
            if resp.status_code == 200:
                self.topo_reflex_status = "online"
                self.topo_reflex_latency = f"{latency}ms"
            else:
                self.topo_reflex_status = "error"
                self.topo_reflex_latency = ""
        except Exception:
            self.topo_reflex_status = "offline"
            self.topo_reflex_latency = ""

        # AI Cloud (Yandex AI Studio)
        try:
            t0 = time.monotonic()
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://300.ya.ru", timeout=5)
            latency = int((time.monotonic() - t0) * 1000)
            self.topo_ai_status = "online"
            self.topo_ai_latency = f"{latency}ms"
        except Exception:
            self.topo_ai_status = "offline"
            self.topo_ai_latency = ""
