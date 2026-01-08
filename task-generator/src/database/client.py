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
    path_count: str = "1"  # 到達パス数（多倍長整数文字列）
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
                        position_black, position_white, turn, depth, path_count,
                        status, priority, retry_count,
                        assigned_to, assigned_at,
                        created_at, started_at, completed_at
                    )
                    VALUES (
                        %s, %s, %s,
                        %s, %s, %s, %s, %s,
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
                        task.path_count,
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

    def get_completed_bfs_results_with_children(
        self,
        processed_task_ids: Optional[set[int]] = None,
    ) -> list[tuple[int, str, int, list]]:
        """
        完了したBFSタスクの結果を取得

        Args:
            processed_task_ids: 既に処理済みのタスクIDセット（重複処理を防ぐため）

        Returns:
            (task_id, phase, depth, child_positions) のタプルのリスト
        """
        if processed_task_ids is None:
            processed_task_ids = set()

        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT t.task_id, t.phase, t.depth, r.child_positions
                    FROM tasks t
                    JOIN results r ON t.task_id = r.task_id
                    WHERE t.status = 'completed'
                      AND t.task_type = 'BFS'
                      AND r.child_positions IS NOT NULL
                    ORDER BY t.task_id
                    """
                )
                rows = cur.fetchall()

        results = []
        for task_id, phase, depth, child_positions in rows:
            if task_id not in processed_task_ids:
                results.append((task_id, phase, depth, child_positions))
        return results
