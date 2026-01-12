"""中間タスク生成（完了したBFSタスクから次のタスクを生成）"""

from __future__ import annotations

import logging
from typing import Optional

from src.database.client import DatabaseClient, TaskRow
from src.valkey.client import ValkeyClient

logger = logging.getLogger(__name__)

# 設定（暫定値、ベンチマーク後に調整）
SEGMENT_WIDTH = 6  # セグメント幅（手番数、パスも1手として数える）
DFS_START_DEPTH = 54  # DFSを開始する局面深さ（D48-54 の終端=54 から）


def determine_child_task_spec(child_start_depth: int) -> tuple[str, str, str, int]:
    """
    子タスク（= 現BFS結果の child_positions から生成するタスク）の仕様を決定

    Args:
        child_start_depth: 子タスクが開始する深さ（= 親BFSセグメントの終端深さ）

    Returns:
        (task_type, phase, queue_name, depth)
    """
    if child_start_depth >= DFS_START_DEPTH:
        # DFSは終局まで
        return ("DFS", f"dfs_from_d{child_start_depth:02d}", "task_queue:dfs:phase3", 100)

    end_depth = child_start_depth + SEGMENT_WIDTH
    phase = f"bfs_d{child_start_depth:02d}_{end_depth:02d}"
    return ("BFS", phase, "task_queue:bfs:phase2", SEGMENT_WIDTH)


def _parse_position(position: dict) -> tuple[bytes, bytes, str]:
    """
    child_positionsのposition形式からバイト列に変換

    Args:
        position: {"black": "0x...", "white": "0x...", "turn": "black"|"white"}

    Returns:
        (position_black, position_white, turn)
    """
    black_hex = position["black"]
    white_hex = position["white"]
    turn_str = position["turn"]

    # "0x..." 形式の16進数文字列をバイト列に変換
    black_int = int(black_hex, 16)
    white_int = int(white_hex, 16)

    position_black = black_int.to_bytes(8, byteorder="big")
    position_white = white_int.to_bytes(8, byteorder="big")

    # "black"/"white" を "B"/"W" に変換
    turn = "B" if turn_str == "black" else "W"

    return position_black, position_white, turn


def _get_accumulated_depth_from_phase(phase: str) -> int:
    """
    フェーズ名から累積深さを取得

    Args:
        phase: "bfs_d00_06", "bfs_d06_12" など

    Returns:
        累積深さ（フェーズの終了深さ）
    """
    if phase.startswith("bfs_d"):
        # "bfs_d06_12" のような形式から終了深さを取得
        parts = phase.replace("bfs_d", "").split("_")
        if len(parts) == 2:
            return int(parts[1])
    # 不明なフェーズの場合はデフォルト値
    logger.warning(f"Unknown phase format: {phase}, using default depth 6")
    return 6


def generate_intermediate_tasks(
    *,
    db: DatabaseClient,
    valkey: ValkeyClient,
    processed_task_ids: set[int],
) -> int:
    """
    完了したBFSタスクの結果から次のタスクを生成

    Args:
        db: DatabaseClient
        valkey: ValkeyClient
        processed_task_ids: 処理済みタスクIDセット（この関数内で更新される）

    Returns:
        生成したタスク数
    """
    results = db.get_completed_bfs_results_with_children(processed_task_ids)

    if not results:
        return 0

    total_generated = 0

    for task_id, phase, depth, child_positions in results:
        logger.info(f"Processing completed BFS task: task_id={task_id}, phase={phase}, depth={depth}")

        # 子タスクの開始深さ（= このBFSセグメントの終端）
        child_start_depth = _get_accumulated_depth_from_phase(phase)
        # 子タスク仕様（タスクタイプ/フェーズ/キュー/探索深さ）
        next_task_type, next_phase, queue_name, next_depth = determine_child_task_spec(
            child_start_depth
        )

        # child_positionsから各子タスクを生成
        generated_count = 0
        for child in child_positions:
            position = child["position"]
            path_count = str(child.get("path_count", "1"))

            position_black, position_white, turn = _parse_position(position)

            task = TaskRow(
                task_type=next_task_type,
                phase=next_phase,
                parent_task_id=task_id,
                position_black=position_black,
                position_white=position_white,
                turn=turn,
                depth=next_depth,
                path_count=path_count,
                status="pending",
                priority=100,
                retry_count=0,
            )

            new_task_id = db.create_task(task)
            valkey.push_task(queue_name, new_task_id)
            generated_count += 1

        logger.info(
            f"Generated {generated_count} {next_task_type} tasks from task_id={task_id} "
            f"(phase={next_phase}, queue={queue_name})"
        )

        # このBFS結果（child_positions）は、子タスク生成が済んだので破棄（保持し続けない）
        db.consume_bfs_child_positions(task_id)

        # 処理済みとしてマーク
        processed_task_ids.add(task_id)
        total_generated += generated_count

    return total_generated
