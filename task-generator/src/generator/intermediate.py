"""中間タスク生成（完了したBFSタスクから次のタスクを生成）"""

from __future__ import annotations

import logging
from typing import Optional

from src.database.client import DatabaseClient, TaskRow
from src.valkey.client import ValkeyClient

logger = logging.getLogger(__name__)

# 設定（暫定値、ベンチマーク後に調整）
SEGMENT_WIDTH = 6  # セグメント幅（手番数、パスも1手として数える）
DFS_START_DEPTH = 48  # DFSを開始する局面深さ（D48 から）


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


def _get_all_bfs_phases() -> list[str]:
    """
    全BFS層のフェーズ名を取得（D00-06からD42-48まで）

    Returns:
        フェーズ名のリスト
    """
    phases = []
    for start_depth in range(0, 48, SEGMENT_WIDTH):
        end_depth = start_depth + SEGMENT_WIDTH
        phase = f"bfs_d{start_depth:02d}_{end_depth:02d}"
        phases.append(phase)
    return phases


def _get_parent_phase(child_phase: str) -> Optional[str]:
    """
    子フェーズから親フェーズを取得

    Args:
        child_phase: 子フェーズ名（例: "bfs_d06_12"）

    Returns:
        親フェーズ名（例: "bfs_d00_06"）、存在しない場合はNone
    """
    if not child_phase.startswith("bfs_d"):
        return None
    
    parts = child_phase.replace("bfs_d", "").split("_")
    if len(parts) != 2:
        return None
    
    child_start = int(parts[0])
    if child_start == 0:
        return None  # D00-06層には親がない（初期タスク）
    
    parent_start = child_start - SEGMENT_WIDTH
    parent_end = child_start
    return f"bfs_d{parent_start:02d}_{parent_end:02d}"


def generate_intermediate_tasks(
    *,
    db: DatabaseClient,
    valkey: ValkeyClient,
    processed_task_ids: set[int],
) -> int:
    """
    完了したBFSタスクの結果から次のタスクを生成

    仕様（Doc/内部仕様書.md:597-608）に基づく:
    - BFS層（D00-06～D42-48）: 各層に最大2つのタスク（current/next）のみが存在
    - 親セグメントのみからcurrentセグメントタスク、nextセグメントタスクを生成する（容量削減のため）
    - currentセグメントが完了したら、nextセグメントをcurrentに昇格させ、新しいnextセグメントを生成する
    - DFS層（D48-54）: 親セグメント（D42-48層）のnext,current両方の全ノードからDFSタスクを生成する
    - D48-54層にはcurrent/nextの概念はなく、各ノードから終局まで1タスクで処理する

    Args:
        db: DatabaseClient
        valkey: ValkeyClient
        processed_task_ids: 処理済みタスクIDセット（この関数内で更新される）

    Returns:
        生成したタスク数
    """
    total_generated = 0

    # 全BFS層（D06-12からD42-48まで）について子タスクを生成
    # D00-06は初期タスクなので親からの生成対象外
    bfs_phases = _get_all_bfs_phases()

    for child_phase in bfs_phases:
        # 親フェーズを取得（D00-06の場合はNone）
        parent_phase = _get_parent_phase(child_phase)
        if parent_phase is None:
            continue  # D00-06層は親がないのでスキップ

        # 現在のcurrent/nextを取得
        existing_current, existing_next = db.get_current_next_tasks_by_phase(child_phase)
        
        # 生成が必要な数を決定
        need_current = existing_current is None
        need_next = existing_next is None
        tasks_to_generate = (1 if need_current else 0) + (1 if need_next else 0)
        
        if tasks_to_generate == 0:
            logger.debug(f"Phase {child_phase}: current/next already exist, skipping")
            continue

        logger.info(
            f"Phase {child_phase}: need_current={need_current}, need_next={need_next}, "
            f"existing_current={existing_current}, existing_next={existing_next}"
        )

        # 親フェーズの完了タスクからchild_positionsを取得
        parent_candidates = db.get_candidates_for_phase(parent_phase, processed_task_ids)
        
        if not parent_candidates:
            logger.debug(f"Phase {child_phase}: no parent candidates from {parent_phase}")
            continue

        # 親タスク（task_id最小）から局面を取得
        parent_task_id = parent_candidates[0]
        
        # 必要な数だけ局面を取り出す
        child_positions, consumed_all = db.take_latest_bfs_child_positions(
            parent_task_id, tasks_to_generate
        )

        if not child_positions:
            logger.debug(f"Phase {child_phase}: no child_positions from parent {parent_task_id}")
            # child_positionsが空の場合、この親タスクは処理済み扱い
            processed_task_ids.add(parent_task_id)
            continue

        # 子タスク仕様を決定
        child_start_depth = _get_accumulated_depth_from_phase(parent_phase)
        next_task_type, next_phase, queue_name, next_depth = determine_child_task_spec(
            child_start_depth
        )

        # D42-48層（child_start_depth=48）の場合はDFSタスクなのでここでは処理しない
        if child_start_depth >= DFS_START_DEPTH:
            continue

        # 子タスクを生成
        generated_count = 0
        for idx, child in enumerate(child_positions):
            position = child["position"]
            path_count = str(child.get("path_count", "1"))

            position_black, position_white, turn = _parse_position(position)

            # segment_roleを決定
            if need_current and need_next:
                # 両方必要な場合: 1つ目がcurrent, 2つ目がnext
                segment_role = "current" if idx == 0 else "next"
            elif need_current:
                # currentのみ必要
                segment_role = "current"
            else:
                # nextのみ必要
                segment_role = "next"

            task = TaskRow(
                task_type=next_task_type,
                phase=next_phase,
                parent_task_id=parent_task_id,
                position_black=position_black,
                position_white=position_white,
                turn=turn,
                depth=next_depth,
                path_count=path_count,
                status="pending",
                priority=100,
                retry_count=0,
                segment_role=segment_role,
            )

            new_task_id = db.create_task(task)
            valkey.push_task(queue_name, new_task_id)
            generated_count += 1

            logger.info(
                f"Generated {next_task_type} task {new_task_id} with segment_role={segment_role} "
                f"from parent {parent_task_id} (phase={next_phase})"
            )

        # child_positionsが全消費された場合のみ processed 扱いにする
        if consumed_all:
            processed_task_ids.add(parent_task_id)
        total_generated += generated_count

    # D42-48層のBFSタスク（current/next両方）からDFSタスクを生成
    # 仕様: 親セグメント（D42-48層）のnext,current両方の全ノードからDFSタスクを生成する
    d42_48_phase = "bfs_d42_48"
    d42_48_headers = db.get_completed_bfs_task_headers_with_children(
        processed_task_ids=processed_task_ids,
        phase_filter=d42_48_phase,
        limit=200,
    )

    for task_id, phase, depth in d42_48_headers:
        logger.info(
            f"Processing D42-48 BFS task for DFS generation: task_id={task_id}, phase={phase}, depth={depth}"
        )

        # 子タスクの開始深さ（= D42-48の終端=48）
        child_start_depth = _get_accumulated_depth_from_phase(phase)
        # 子タスク仕様（DFSタスク）
        next_task_type, next_phase, queue_name, next_depth = determine_child_task_spec(
            child_start_depth
        )

        # 全件をDFSタスク化（current/nextの概念なし）
        child_positions = db.get_latest_bfs_child_positions(task_id) or []

        if not child_positions:
            processed_task_ids.add(task_id)
            continue

        # child_positionsから各DFSタスクを生成
        generated_count = 0
        for child in child_positions:
            position = child["position"]
            path_count = str(child.get("path_count", "1"))

            position_black, position_white, turn = _parse_position(position)

            # D48-54層のDFSタスクにはsegment_roleは設定しない
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
                segment_role=None,
            )

            new_task_id = db.create_task(task)
            valkey.push_task(queue_name, new_task_id)
            generated_count += 1

        logger.info(
            f"Generated {generated_count} {next_task_type} tasks from D42-48 task_id={task_id} "
            f"(phase={next_phase}, queue={queue_name})"
        )

        # このBFS結果（child_positions）は、子タスク生成が済んだので破棄
        db.consume_bfs_child_positions(task_id)

        # 処理済みとしてマーク
        processed_task_ids.add(task_id)
        total_generated += generated_count

    return total_generated
