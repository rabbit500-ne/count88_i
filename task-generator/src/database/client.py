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
    segment_role: Optional[str] = None  # "current" | "next" | None


class DatabaseClient:
    """DBクライアント"""

    def __init__(self) -> None:
        self._dsn = settings.database_url

    def count_unaggregated_bfs_tasks_by_phase(self, phase: str) -> int:
        """
        指定phaseのBFSタスクのうち、task-generator による集約(game_count)が未作成の件数を返す。

        用途:
          - D42-48層の current/next (=2セグメント) 制御
        """
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM tasks t
                    WHERE t.task_type = 'BFS'
                      AND t.phase = %s
                      AND NOT EXISTS (
                        SELECT 1
                        FROM results r
                        WHERE r.task_id = t.task_id
                          AND r.result_type = 'BFS'
                          AND r.client_id = 'task-generator'
                          AND r.game_count IS NOT NULL
                      )
                    """,
                    (phase,),
                )
                return int(cur.fetchone()[0])

    def get_completed_bfs_task_headers_with_children(
        self,
        processed_task_ids: Optional[set[int]] = None,
        *,
        limit: int = 200,
        phase_filter: Optional[str] = None,
    ) -> list[tuple[int, str, int]]:
        """
        child_positions を持つ完了BFSタスクのヘッダ情報を取得（child_positions本体は取得しない）

        Args:
            processed_task_ids: 処理済みタスクIDセット
            limit: 取得上限
            phase_filter: フェーズでフィルタリング（例: "bfs_d36_42"）

        Returns:
            (task_id, phase, depth) のリスト（task_id昇順）
        """
        if processed_task_ids is None:
            processed_task_ids = set()

        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT DISTINCT ON (t.task_id) t.task_id, t.phase, t.depth
                    FROM tasks t
                    JOIN results r ON t.task_id = r.task_id
                    WHERE t.status = 'completed'
                      AND t.task_type = 'BFS'
                      AND r.result_type = 'BFS'
                      AND r.child_positions IS NOT NULL
                """
                params = []
                if phase_filter:
                    query += " AND t.phase = %s"
                    params.append(phase_filter)
                query += " ORDER BY t.task_id, r.result_id DESC LIMIT %s"
                params.append(limit)

                cur.execute(query, tuple(params))
                rows = cur.fetchall()

        headers: list[tuple[int, str, int]] = []
        for task_id, phase, depth in rows:
            if int(task_id) not in processed_task_ids:
                headers.append((int(task_id), str(phase), int(depth)))
        return headers

    def get_d42_48_candidates(self, processed_task_ids: Optional[set[int]] = None) -> list[int]:
        """
        D42-48層を生成する候補（D36-42層の完了したBFSタスク）をtask_id昇順で取得

        仕様（Doc/内部仕様書.md:596-599）に基づく:
        - D42-48層の候補からtask_id昇順で選ぶ
        - current: 最小task_id
        - next: 次点のtask_id

        Args:
            processed_task_ids: 処理済みタスクIDセット

        Returns:
            task_idのリスト（task_id昇順）
        """
        if processed_task_ids is None:
            processed_task_ids = set()

        headers = self.get_completed_bfs_task_headers_with_children(
            processed_task_ids=processed_task_ids,
            phase_filter="bfs_d36_42",
            limit=200,
        )
        return [task_id for task_id, _, _ in headers]

    def get_current_next_tasks_by_phase(self, phase: str) -> tuple[Optional[int], Optional[int]]:
        """
        指定phaseのcurrent/nextタスクを取得

        Args:
            phase: フェーズ名（例: "bfs_d00_06"）

        Returns:
            (current_task_id, next_task_id) のタプル
        """
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                # currentタスクを取得
                cur.execute(
                    """
                    SELECT task_id
                    FROM tasks
                    WHERE phase = %s
                      AND task_type = 'BFS'
                      AND segment_role = 'current'
                    ORDER BY task_id
                    LIMIT 1
                    """,
                    (phase,),
                )
                current_row = cur.fetchone()
                current_task_id = int(current_row[0]) if current_row else None
                
                # nextタスクを取得
                cur.execute(
                    """
                    SELECT task_id
                    FROM tasks
                    WHERE phase = %s
                      AND task_type = 'BFS'
                      AND segment_role = 'next'
                    ORDER BY task_id
                    LIMIT 1
                    """,
                    (phase,),
                )
                next_row = cur.fetchone()
                next_task_id = int(next_row[0]) if next_row else None
        
        return (current_task_id, next_task_id)

    def set_current_next_tasks_by_phase(
        self, phase: str, current_task_id: Optional[int], next_task_id: Optional[int]
    ) -> None:
        """
        指定phaseのcurrent/nextタスクを設定

        Args:
            phase: フェーズ名（例: "bfs_d00_06"）
            current_task_id: currentタスクのID（Noneの場合はクリア）
            next_task_id: nextタスクのID（Noneの場合はクリア）
        """
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                # 既存のcurrent/nextをクリア
                cur.execute(
                    """
                    UPDATE tasks
                    SET segment_role = NULL
                    WHERE phase = %s
                      AND segment_role IN ('current', 'next')
                    """,
                    (phase,),
                )
                
                # 新しいcurrent/nextを設定
                if current_task_id is not None:
                    cur.execute(
                        """
                        UPDATE tasks
                        SET segment_role = 'current'
                        WHERE task_id = %s AND phase = %s
                        """,
                        (current_task_id, phase),
                    )
                
                if next_task_id is not None:
                    cur.execute(
                        """
                        UPDATE tasks
                        SET segment_role = 'next'
                        WHERE task_id = %s AND phase = %s
                        """,
                        (next_task_id, phase),
                    )
                
                conn.commit()

    def get_candidates_for_phase(self, phase: str, processed_task_ids: Optional[set[int]] = None) -> list[int]:
        """
        指定phaseの候補（完了したBFSタスク）をtask_id昇順で取得

        Args:
            phase: フェーズ名（例: "bfs_d00_06"）
            processed_task_ids: 処理済みタスクIDセット

        Returns:
            task_idのリスト（task_id昇順）
        """
        if processed_task_ids is None:
            processed_task_ids = set()

        headers = self.get_completed_bfs_task_headers_with_children(
            processed_task_ids=processed_task_ids,
            phase_filter=phase,
            limit=200,
        )
        return [task_id for task_id, _, _ in headers]

    def is_task_current(self, task_id: int) -> bool:
        """
        タスクがcurrentかどうかを判定

        Args:
            task_id: タスクID

        Returns:
            currentの場合True
        """
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT segment_role
                    FROM tasks
                    WHERE task_id = %s
                    """,
                    (task_id,),
                )
                row = cur.fetchone()
                return row is not None and row[0] == 'current'

    def get_latest_bfs_child_positions(self, task_id: int) -> Optional[list]:
        """指定task_idの最新のBFS child_positions（NULLならNone）"""
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT child_positions
                    FROM results
                    WHERE task_id = %s
                      AND result_type = 'BFS'
                      AND child_positions IS NOT NULL
                    ORDER BY result_id DESC
                    LIMIT 1
                    """,
                    (task_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return row[0]

    def take_latest_bfs_child_positions(
        self, task_id: int, take: int
    ) -> tuple[list, bool]:
        """
        最新のBFS child_positions から先頭take件を取り出し、残りをDBへ書き戻す（段階的消費）。

        Returns:
            (taken_children, consumed_all)
        """
        if take <= 0:
            return ([], False)

        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                # 最新のchild_positionsをロックして取り出す
                cur.execute(
                    """
                    SELECT result_id, child_positions
                    FROM results
                    WHERE task_id = %s
                      AND result_type = 'BFS'
                      AND child_positions IS NOT NULL
                    ORDER BY result_id DESC
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (task_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return ([], True)

                result_id, child_positions = row
                children = list(child_positions or [])

                taken = children[:take]
                remaining = children[take:]
                consumed_all = len(remaining) == 0

                cur.execute(
                    """
                    UPDATE results
                    SET child_positions = %s
                    WHERE result_id = %s
                    """,
                    (
                        None if consumed_all else psycopg2.extras.Json(remaining),
                        int(result_id),
                    ),
                )
                # 同一task_idに複数のBFS結果が残っている場合は、最新(result_id)以外を無効化して重複処理を防ぐ
                cur.execute(
                    """
                    UPDATE results
                    SET child_positions = NULL
                    WHERE task_id = %s
                      AND result_type = 'BFS'
                      AND result_id <> %s
                      AND child_positions IS NOT NULL
                    """,
                    (task_id, int(result_id)),
                )

        return (taken, consumed_all)

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
                        created_at, started_at, completed_at, segment_role
                    )
                    VALUES (
                        %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s, %s
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
                        task.segment_role,
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

    def get_existing_bfs_phases(self) -> list[str]:
        """
        DBに存在するBFSフェーズ名を取得（動的フェーズ対応用）

        Returns:
            フェーズ名のリスト（重複なし、ソート済み）
        """
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT phase
                    FROM tasks
                    WHERE task_type = 'BFS'
                      AND phase LIKE 'bfs_d%'
                    ORDER BY phase
                    """
                )
                rows = cur.fetchall()
        return [str(r[0]) for r in rows]