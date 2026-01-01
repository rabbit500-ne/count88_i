"""PostgreSQL クライアント（最小実装）"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import psycopg2

from src.config import settings


@dataclass(frozen=True)
class TaskRow:
    task_type: str  # "BFS" | "DFS"
    phase: str
    parent_task_id: Optional[int]
    position_black: bytes
    position_white: bytes
    turn: str  # "B" | "W"
    depth: int
    status: str = "pending"
    priority: int = 100
    retry_count: int = 0
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    created_at: datetime = datetime.utcnow()
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DatabaseClient:
    """DBクライアント"""

    def __init__(self) -> None:
        self._dsn = settings.database_url

    def create_task(self, task: TaskRow) -> int:
        """tasks にINSERTして task_id を返す"""
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tasks (
                        task_type, phase, parent_task_id,
                        position_black, position_white, turn, depth,
                        status, priority, retry_count,
                        assigned_to, assigned_at,
                        created_at, started_at, completed_at
                    )
                    VALUES (
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s
                    )
                    RETURNING task_id
                    """,
                    (
                        task.task_type,
                        task.phase,
                        task.parent_task_id,
                        task.position_black,
                        task.position_white,
                        task.turn,
                        task.depth,
                        task.status,
                        task.priority,
                        task.retry_count,
                        task.assigned_to,
                        task.assigned_at,
                        task.created_at,
                        task.started_at,
                        task.completed_at,
                    ),
                )
                task_id = cur.fetchone()[0]
                return int(task_id)

