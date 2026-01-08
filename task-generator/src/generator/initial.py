"""初期タスク生成（最小実装）"""

from __future__ import annotations

from src.database.client import DatabaseClient, TaskRow
from src.valkey.client import ValkeyClient


# エンドユーザ仕様書の初期配置例
INITIAL_BLACK = 0x0000000810000000
INITIAL_WHITE = 0x0000001008000000


def generate_initial_tasks(
    *,
    db: DatabaseClient,
    valkey: ValkeyClient,
    depth: int = 6,
    queue_name: str = "task_queue:bfs:phase1",
    phase: str = "bfs_d00_06",
) -> int:
    """初期局面1件のBFSタスクをDBへ作成し、Valkeyへ投入する"""
    task = TaskRow(
        task_type="BFS",
        phase=phase,
        parent_task_id=None,
        position_black=int(INITIAL_BLACK).to_bytes(8, byteorder="big"),
        position_white=int(INITIAL_WHITE).to_bytes(8, byteorder="big"),
        turn="B",
        depth=depth,
        status="pending",
        priority=100,
        retry_count=0,
    )
    task_id = db.create_task(task)
    valkey.push_task(queue_name, task_id)
    return task_id

