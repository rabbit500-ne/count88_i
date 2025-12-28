"""幅優先探索（BFS）実装"""

from typing import Dict, List, Tuple
from collections import deque

from othello_core import Position, Bitboard
from src.algorithms.bitboard import Bitboard as TaskBitboard


def bfs(start_position: Position, target_depth: int) -> Dict[Position, int]:
    """
    幅優先探索を実行

    Args:
        start_position: 開始局面
        target_depth: 探索する深さ

    Returns:
        到達可能局面とその到達パス数の辞書
    """
    # TODO: Phase 1では最小限の実装
    # 詳細な実装はPhase 2以降で行う

    result_positions: Dict[Position, int] = {}
    queue: deque[Tuple[Position, int]] = deque([(start_position, 0)])

    while queue:
        position, depth = queue.popleft()

        if depth >= target_depth:
            # 目標深さに到達
            if position not in result_positions:
                result_positions[position] = 0
            result_positions[position] += 1
            continue

        # TODO: 合法手の生成と次の局面への展開を実装
        # Phase 1では、基本的な構造のみを定義

    return result_positions
