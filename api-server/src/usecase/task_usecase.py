"""タスク管理ユースケース"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime
from typing import Callable, Optional

from src.domain.task import Task as DomainTask
from src.usecase.repositories.task_repository import ITaskRepository
from src.infra.queue.client import ValkeyClient


class TaskUsecase:
    """タスク取得ユースケース"""

    def __init__(
        self,
        task_repo: ITaskRepository,
        valkey: ValkeyClient,
        *,
        commit: Callable[[], None],
        now: Callable[[], datetime] = datetime.utcnow,
        lock_ttl: int = 60,
        queue_names: tuple[str, ...] = (
            "task_queue:bfs:phase1",
            "task_queue:bfs:phase2",
            "task_queue:dfs:phase3",
        ),
        max_pop_attempts: int = 20,
    ):
        self.task_repo = task_repo
        self.valkey = valkey
        self.commit = commit
        self.now = now
        self.lock_ttl = lock_ttl
        self.queue_names = queue_names
        self.max_pop_attempts = max_pop_attempts

    def get_task(self, client_id: Optional[str]) -> Optional[DomainTask]:
        """ValkeyからタスクIDを取り、DBから詳細を返す（なければNone）"""
        cid = client_id or "unknown"

        for _ in range(self.max_pop_attempts):
            task_id = None
            for q in self.queue_names:
                task_id = self.valkey.pop_task(q)
                if task_id is not None:
                    break
            if task_id is None:
                return None

            lock_key = f"task_lock:{task_id}"
            lock_value = json.dumps({"client_id": cid, "started_at": self.now().isoformat()})
            if not self.valkey.set_lock(lock_key, lock_value, ttl=self.lock_ttl):
                continue

            task = self.task_repo.get_by_id(task_id)
            if task is None:
                # DB不整合: ロックだけ残るのは避ける
                self.valkey.delete_lock(lock_key)
                continue

            now_dt = self.now()
            task = replace(
                task,
                status="processing",
                assigned_to=cid,
                assigned_at=now_dt,
                started_at=now_dt,
            )
            self.task_repo.update(task)
            self.commit()
            return task

        return None

