"""結果処理ユースケース"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any, Callable, Optional

from src.domain.result import Result as DomainResult, TaskAnswer
from src.usecase.repositories.result_repository import IResultRepository
from src.usecase.repositories.task_repository import ITaskRepository
from src.infra.queue.client import ValkeyClient


class ResultUsecase:
    """結果受領ユースケース"""

    def __init__(
        self,
        task_repo: ITaskRepository,
        result_repo: IResultRepository,
        valkey: ValkeyClient,
        *,
        commit: Callable[[], None],
        now: Callable[[], datetime] = datetime.utcnow,
        queue_names: tuple[str, ...] = (
            "task_queue:bfs:phase1",
            "task_queue:bfs:phase2",
            "task_queue:dfs:phase3",
        ),
    ):
        self.task_repo = task_repo
        self.result_repo = result_repo
        self.valkey = valkey
        self.commit = commit
        self.now = now
        self.queue_names = queue_names

    def _extract_game_count(self, task_answer: list[dict[str, Any]]) -> Optional[str]:
        for item in task_answer:
            if item.get("label") == "game_count":
                v = item.get("value")
                if v is None:
                    return None
                return str(v)
        return None

    def _extract_child_positions(
        self, task_answer: list[dict[str, Any]]
    ) -> Optional[list[dict[str, Any]]]:
        for item in task_answer:
            if item.get("label") == "child_positions":
                v = item.get("value")
                if v is None:
                    return None
                if isinstance(v, list):
                    return v
                return None
        return None

    def submit_result(
        self,
        *,
        task_id: int,
        task_type: str,
        task_answer: list[dict[str, Any]],
        computation_time: Optional[float],
        client_id: Optional[str],
        client_info: Optional[dict[str, Any]],
    ) -> tuple[DomainResult, bool]:
        """結果を保存し、タスクを完了にし、次タスクの有無を返す"""
        task = self.task_repo.get_by_id(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        # lock解除（設計書どおり）
        self.valkey.delete_lock(f"task_lock:{task_id}")

        domain_task_answer = [TaskAnswer(label=ta["label"], value=ta["value"]) for ta in task_answer]
        result = DomainResult(
            result_id=None,
            task_id=task_id,
            result_type=task_type,  # "BFS" | "DFS"
            task_answer=domain_task_answer,
            game_count=self._extract_game_count(task_answer),
            child_positions=self._extract_child_positions(task_answer),
            computation_time=computation_time,
            client_id=client_id,
            client_info=client_info,
            verified=False,
            verification_count=0,
            created_at=self.now(),
        )
        saved = self.result_repo.create(result)

        task = replace(task, status="completed", completed_at=self.now())
        self.task_repo.update(task)
        self.commit()

        next_available = any(self.valkey.queue_length(q) > 0 for q in self.queue_names)
        return saved, next_available

