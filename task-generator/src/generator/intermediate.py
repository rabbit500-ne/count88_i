"""中間タスク生成（完了したBFSタスクから次のタスクを生成）"""

from __future__ import annotations

import logging
from typing import Optional

from src.database.client import DatabaseClient, TaskRow
from src.valkey.client import ValkeyClient

logger = logging.getLogger(__name__)

# 設定（暫定値、ベンチマーク後に調整）
BFS_DEPTH = 6  # 各BFSステップの探索深さ
DFS_START_DEPTH = 12  # この累積深さに達したらDFSに切り替え


def determine_next_task_type(current_accumulated_depth: int) -> tuple[str, str, str]:
    """
    次のタスクタイプとフェーズを決定

    Args:
        current_accumulated_depth: 現在の累積深さ（親タスクの開始深さ + BFS_DEPTH）

    Returns:
        (task_type, phase, queue_name)
    """
    next_depth = current_accumulated_depth + BFS_DEPTH

    if next_depth >= DFS_START_DEPTH:
        return ("DFS", "dfs_final", "task_queue:dfs:phase3")
    else:
        phase = f"bfs_d{current_accumulated_depth:02d}_{next_depth:02d}"
        return ("BFS", phase, "task_queue:bfs:phase2")


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
        phase: "bfs_d00_06", "bfs_d06_12", "phase1_initial" など

    Returns:
        累積深さ（フェーズの終了深さ）
    """
    if phase == "phase1_initial":
        # 初期フェーズは D0 から D6 まで
        return 6
    elif phase.startswith("bfs_d"):
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

        # 累積深さを計算
        accumulated_depth = _get_accumulated_depth_from_phase(phase)

        # 次のタスクタイプとフェーズを決定
        next_task_type, next_phase, queue_name = determine_next_task_type(accumulated_depth)

        # 次のタスクの探索深さを決定
        if next_task_type == "BFS":
            next_depth = BFS_DEPTH
        else:
            # DFSは終局まで（十分大きな値を設定）
            next_depth = 100

        # child_positionsから各子タスクを生成
        generated_count = 0
        for child in child_positions:
            position = child["position"]
            path_count = str(child.get("path_count", 1))

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

        # 処理済みとしてマーク
        processed_task_ids.add(task_id)
        total_generated += generated_count

    return total_generated
