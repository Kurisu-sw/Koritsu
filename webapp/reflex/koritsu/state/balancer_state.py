"""State for the Balancer admin/test page."""

import json
import reflex as rx
import httpx
import uuid as uuid_mod

API = "http://localhost:8001"


class BalancerState(rx.State):
    # ── Task list ────────────────────────────────────────────────────────
    tasks: list[dict] = []
    is_loading: bool = False

    # ── Search & filter ──────────────────────────────────────────────────
    search_query: str = ""
    status_filter: str = "all"  # "all", "pending", "running", "completed", "failed", "expired", "cancelled"

    # ── Detail view ──────────────────────────────────────────────────────
    selected_task: dict = {}
    show_detail: bool = False

    async def load_tasks(self):
        self.is_loading = True
        yield
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API}/balancer/tasks", timeout=5)
                data = resp.json()
                self.tasks = data.get("tasks", [])
        except Exception:
            self.tasks = []
        self.is_loading = False

    async def cancel_task(self, task_uuid: str):
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"{API}/balancer/task/{task_uuid}", timeout=5
                )
        except Exception:
            pass
        yield BalancerState.load_tasks

    def select_task(self, task: dict):
        self.selected_task = task
        self.show_detail = True

    def close_detail(self):
        self.show_detail = False

    def set_search(self, value: str):
        self.search_query = value

    def set_filter(self, status: str):
        self.status_filter = status

    @rx.var
    def filtered_tasks(self) -> list[dict]:
        result = self.tasks
        # Filter by status
        if self.status_filter != "all":
            result = [t for t in result if t.get("status") == self.status_filter]
        # Filter by search query (uuid, username, task_dest)
        if self.search_query.strip():
            q = self.search_query.strip().lower()
            result = [
                t for t in result
                if q in t.get("task_uuid", "").lower()
                or q in t.get("username", "").lower()
                or q in t.get("task_dest", "").lower()
                or q in t.get("answ_to", "").lower()
            ]
        return result

    @rx.var
    def total_count(self) -> int:
        return len(self.tasks)

    @rx.var
    def pending_count(self) -> int:
        return sum(1 for t in self.tasks if t.get("status") == "pending")

    @rx.var
    def running_count(self) -> int:
        return sum(1 for t in self.tasks if t.get("status") == "running")

    @rx.var
    def done_count(self) -> int:
        return sum(1 for t in self.tasks if t.get("status") == "completed")

    @rx.var
    def failed_count(self) -> int:
        return sum(1 for t in self.tasks if t.get("status") == "failed")

    @rx.var
    def selected_task_result_str(self) -> str:
        """Serialize selected_task['result'] to a JSON string for safe rendering."""
        result = self.selected_task.get("result")
        if result is None:
            return ""
        if isinstance(result, dict):
            return json.dumps(result, ensure_ascii=False, indent=2)
        return str(result)
