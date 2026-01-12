"""PostgreSQL クライアント（最小実装）"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import psycopg2
import psycopg2.extras

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

    def consume_bfs_child_positions(self, task_id: int) -> None:
        """
        BFS結果の child_positions を破棄（NULLにする）

        目的:
          - 下位セグメントの探索木データを保持し続けない（仕様どおり）
          - タスク生成済みのBFSを再処理しないためのマーカーにもなる
        """
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE results
                    SET child_positions = NULL
                    WHERE task_id = %s
                      AND result_type = 'BFS'
                      AND child_positions IS NOT NULL
                    """,
                    (task_id,),
                )

    def get_children_tasks(self, parent_task_id: int) -> list[tuple[int, str]]:
        """親タスクに紐づく子タスク一覧を取得: [(task_id, path_count)]"""
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT task_id, path_count
                    FROM tasks
                    WHERE parent_task_id = %s
                    ORDER BY task_id
                    """,
                    (parent_task_id,),
                )
                rows = cur.fetchall()
        return [(int(tid), str(pc)) for tid, pc in rows]

    def get_latest_game_count(self, task_id: int) -> Optional[str]:
        """task_id の最新 game_count（NULLならNone）"""
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT game_count
                    FROM results
                    WHERE task_id = %s
                      AND game_count IS NOT NULL
                    ORDER BY result_id DESC
                    LIMIT 1
                    """,
                    (task_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return str(row[0])

    def has_aggregated_game_count(self, task_id: int) -> bool:
        """task-generator が既に集約結果を作っているか（冪等性確保）"""
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1
                    FROM results
                    WHERE task_id = %s
                      AND result_type = 'BFS'
                      AND client_id = 'task-generator'
                      AND game_count IS NOT NULL
                    LIMIT 1
                    """,
                    (task_id,),
                )
                row = cur.fetchone()
        return row is not None

    def create_aggregated_result(self, task_id: int, game_count: str) -> None:
        """集約済み棋譜数を results として保存（BFSタスクに対するスカラー結果）"""
        task_answer = [{"label": "game_count", "value": str(game_count)}]
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO results (
                        task_id, result_type, task_answer, game_count, child_positions,
                        computation_time, client_id, client_info,
                        verified, verification_count, created_at
                    )
                    VALUES (
                        %s, 'BFS', %s::jsonb, %s, NULL,
                        NULL, 'task-generator', NULL,
                        false, 0, NOW()
                    )
                    """,
                    (task_id, psycopg2.extras.Json(task_answer), game_count),
                )

    def get_bfs_tasks_ready_for_aggregation(self, limit: int = 200) -> list[int]:
        """
        集約候補のBFSタスクIDを取得（子タスクを持ち、まだ集約結果を持たない）
        """
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT t.task_id
                    FROM tasks t
                    WHERE t.task_type = 'BFS'
                      AND t.status = 'completed'
                      AND EXISTS (
                        SELECT 1 FROM tasks c WHERE c.parent_task_id = t.task_id
                      )
                      AND NOT EXISTS (
                        SELECT 1 FROM results r
                        WHERE r.task_id = t.task_id
                          AND r.result_type = 'BFS'
                          AND r.client_id = 'task-generator'
                          AND r.game_count IS NOT NULL
                      )
                    ORDER BY t.task_id
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        return [int(r[0]) for r in rows]