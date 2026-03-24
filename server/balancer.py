"""
Koritsu Task Balancer
---------------------
In-memory task queue with priority scheduling.
Sits between the web frontend and processing modules.

Priority: 0 (lowest) → 3 (highest)
TTL: priority >= 1 → 5 min, priority 0 → 1 min
"""

from __future__ import annotations

import asyncio
import uuid as uuid_mod
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

from fastapi import APIRouter

from pydantic import BaseModel


# ── Models ───────────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class Task:
    task_uuid: str
    priority: int              # 0-3, 3 = highest
    task_dest: str             # module name, e.g. "fragmos"
    answ_to: str               # user uuid — who gets the result
    username: str              # display name for admin panel
    payload: dict              # arbitrary data for the module
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    result: Any = None
    error: str | None = None

    @property
    def ttl_seconds(self) -> float:
        """Priority >= 1 → 5 min, priority 0 → 1 min."""
        return 300.0 if self.priority >= 1 else 60.0

    @property
    def is_expired(self) -> bool:
        if self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED,
                           TaskStatus.EXPIRED, TaskStatus.CANCELLED):
            return False
        elapsed = time.time() - self.created_at
        return elapsed > self.ttl_seconds

    def to_dict(self) -> dict:
        return {
            "task_uuid": self.task_uuid,
            "priority": self.priority,
            "task_dest": self.task_dest,
            "answ_to": self.answ_to,
            "username": self.username,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "result": self.result,
            "error": self.error,
        }


# ── Balancer Core ────────────────────────────────────────────────────────────

# Handler type: async function(payload) -> result
ModuleHandler = Callable[[dict], Awaitable[Any]]


class Balancer:
    """In-memory priority task queue with background worker."""

    def __init__(self, max_concurrent: int = 3):
        self._tasks: dict[str, Task] = {}           # uuid → Task
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._handlers: dict[str, ModuleHandler] = {}
        self._max_concurrent = max_concurrent
        self._semaphore: asyncio.Semaphore | None = None
        self._worker_task: asyncio.Task | None = None
        self._ttl_task: asyncio.Task | None = None

    # ── Handler registration ─────────────────────────────────────────────

    def register_handler(self, dest: str, handler: ModuleHandler):
        """Register an async handler for a task_dest (e.g. 'fragmos')."""
        self._handlers[dest] = handler

    # ── Lifecycle ────────────────────────────────────────────────────────

    def start(self):
        """Start background workers. Call once after event loop is running."""
        self._semaphore = asyncio.Semaphore(self._max_concurrent)
        self._worker_task = asyncio.create_task(self._worker_loop())
        self._ttl_task = asyncio.create_task(self._ttl_checker())

    def stop(self):
        if self._worker_task:
            self._worker_task.cancel()
        if self._ttl_task:
            self._ttl_task.cancel()

    # ── Submit ───────────────────────────────────────────────────────────

    async def submit(
        self,
        priority: int,
        task_dest: str,
        answ_to: str,
        username: str,
        payload: dict,
        task_uuid: str | None = None,
    ) -> Task:
        if priority < 0 or priority > 3:
            raise ValueError("Priority must be 0-3")

        if task_uuid is None:
            task_uuid = str(uuid_mod.uuid4())

        task = Task(
            task_uuid=task_uuid,
            priority=priority,
            task_dest=task_dest,
            answ_to=answ_to,
            username=username,
            payload=payload,
        )
        self._tasks[task_uuid] = task

        # PriorityQueue is min-heap → negate priority so 3 is processed first
        await self._queue.put((-priority, task.created_at, task_uuid))
        return task

    # ── Query ────────────────────────────────────────────────────────────

    def get_task(self, task_uuid: str) -> Task | None:
        return self._tasks.get(task_uuid)

    def get_all_tasks(self) -> list[dict]:
        """Return all tasks sorted by creation time (newest first)."""
        tasks = sorted(self._tasks.values(), key=lambda t: t.created_at, reverse=True)
        return [t.to_dict() for t in tasks]

    def get_tasks_for_user(self, user_uuid: str) -> list[dict]:
        tasks = [t for t in self._tasks.values() if t.answ_to == user_uuid]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return [t.to_dict() for t in tasks]

    # ── Background workers ───────────────────────────────────────────────

    async def _worker_loop(self):
        """Pull tasks from queue by priority and execute them."""
        while True:
            neg_prio, created_at, task_uuid = await self._queue.get()
            task = self._tasks.get(task_uuid)

            if task is None or task.status != TaskStatus.PENDING:
                self._queue.task_done()
                continue

            # Check TTL before starting
            if task.is_expired:
                task.status = TaskStatus.EXPIRED
                task.finished_at = time.time()
                task.error = "Wait too much, server might be dead"
                self._queue.task_done()
                continue

            # Run with concurrency limit
            asyncio.create_task(self._execute_task(task))
            self._queue.task_done()

    async def _execute_task(self, task: Task):
        await self._semaphore.acquire()
        try:
            handler = self._handlers.get(task.task_dest)
            if handler is None:
                task.status = TaskStatus.FAILED
                task.finished_at = time.time()
                task.error = f"No handler registered for '{task.task_dest}'"
                return

            task.status = TaskStatus.RUNNING
            task.started_at = time.time()

            # Run handler with TTL timeout
            remaining_ttl = task.ttl_seconds - (time.time() - task.created_at)
            if remaining_ttl <= 0:
                task.status = TaskStatus.EXPIRED
                task.finished_at = time.time()
                task.error = "Wait too much, server might be dead"
                return

            result = await asyncio.wait_for(handler(task.payload), timeout=remaining_ttl)

            task.status = TaskStatus.COMPLETED
            task.finished_at = time.time()
            task.result = result

            # Логируем стоимость в консоль для администратора
            cost = result.get("cost_rub") if isinstance(result, dict) else None
            charged = result.get("charged_tokens") if isinstance(result, dict) else None
            elapsed = task.finished_at - (task.started_at or task.created_at)
            print(f"[balancer] DONE {task.task_uuid[:8]} | "
                  f"user={task.username} | "
                  f"{charged or '?'} tok | "
                  f"{cost or '?'} ₽ | "
                  f"{elapsed:.1f}s")

        except asyncio.TimeoutError:
            task.status = TaskStatus.EXPIRED
            task.finished_at = time.time()
            task.error = "Wait too much, server might be dead"
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.finished_at = time.time()
            task.error = str(e)
        finally:
            self._semaphore.release()

    async def _ttl_checker(self):
        """Periodically expire tasks that exceeded their TTL."""
        while True:
            await asyncio.sleep(5)
            for task in self._tasks.values():
                if task.status == TaskStatus.PENDING and task.is_expired:
                    task.status = TaskStatus.EXPIRED
                    task.finished_at = time.time()
                    task.error = "Wait too much, server might be dead"


# ── Singleton ────────────────────────────────────────────────────────────────

balancer = Balancer()


# ── API Router ───────────────────────────────────────────────────────────────

router = APIRouter(prefix="/balancer", tags=["balancer"])


class TaskSubmitRequest(BaseModel):
    priority: int = 1           # 0-3
    task_dest: str              # e.g. "fragmos"
    answ_to: str                # user uuid
    username: str               # for admin display
    payload: dict = {}
    task_uuid: str | None = None


@router.post("/task")
async def create_task(data: TaskSubmitRequest):
    try:
        task = await balancer.submit(
            priority=data.priority,
            task_dest=data.task_dest,
            answ_to=data.answ_to,
            username=data.username,
            payload=data.payload,
            task_uuid=data.task_uuid,
        )
        return {"success": True, "task": task.to_dict()}
    except ValueError as e:
        return {"error": str(e)}


@router.get("/task/{task_uuid}")
async def get_task(task_uuid: str):
    task = balancer.get_task(task_uuid)
    if task is None:
        return {"error": "Task not found"}
    return {"task": task.to_dict()}


@router.get("/tasks")
async def list_all_tasks():
    """Admin endpoint — returns all tasks."""
    return {"tasks": balancer.get_all_tasks()}


@router.get("/tasks/user/{user_uuid}")
async def list_user_tasks(user_uuid: str):
    """Get tasks for a specific user."""
    return {"tasks": balancer.get_tasks_for_user(user_uuid)}


@router.delete("/task/{task_uuid}")
async def cancel_task(task_uuid: str):
    task = balancer.get_task(task_uuid)
    if task is None:
        return {"error": "Task not found"}
    if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED,
                       TaskStatus.EXPIRED, TaskStatus.CANCELLED):
        return {"error": f"Task already {task.status.value}"}
    task.status = TaskStatus.CANCELLED
    task.finished_at = time.time()
    task.error = "Cancelled by user"
    return {"success": True, "task": task.to_dict()}
