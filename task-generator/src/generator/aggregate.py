"""集約（圧縮）処理: 子タスクの棋譜数から親BFSタスクの棋譜数（スカラー）を確定する

仕様（Doc/内部仕様書.md 分散計算フロー）に基づき、
  parent_game_count = Σ( child.path_count × child.game_count )
を計算し、親タスクに対する results（result_type='BFS', client_id='task-generator'）として保存する。
"""

from __future__ import annotations

import logging

from src.database.client import DatabaseClient

logger = logging.getLogger(__name__)


def aggregate_parent_game_counts(*, db: DatabaseClient, limit: int = 200) -> int:
    """
    集約できる親BFSタスクを探し、可能なものを集約する

    Returns:
        今回新たに集約できたタスク数
    """
    parents = db.get_bfs_tasks_ready_for_aggregation(limit=limit)
    if not parents:
        return 0

    aggregated = 0

    for parent_task_id in parents:
        if db.has_aggregated_game_count(parent_task_id):
            continue

        children = db.get_children_tasks(parent_task_id)
        if not children:
            continue

        total = 0
        all_ready = True

        for child_task_id, path_count_str in children:
            gc = db.get_latest_game_count(child_task_id)
            if gc is None:
                all_ready = False
                break

            try:
                path_count = int(path_count_str)
            except ValueError:
                logger.warning(
                    f"Invalid path_count: parent={parent_task_id} child={child_task_id} value={path_count_str}"
                )
                all_ready = False
                break

            total += path_count * int(gc)

        if not all_ready:
            continue

        db.create_aggregated_result(parent_task_id, str(total))
        aggregated += 1

    return aggregated

