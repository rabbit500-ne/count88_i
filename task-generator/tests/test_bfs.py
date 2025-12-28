"""BFSアルゴリズムのテスト"""

import pytest
from othello_core import Position

from src.algorithms.bfs import bfs


def test_bfs_basic():
    """BFSの基本動作テスト"""
    # TODO: Phase 1では最小限のテスト
    # Phase 2以降で、詳細なテストを実装
    start_position = Position.initial()
    result = bfs(start_position, target_depth=1)
    assert isinstance(result, dict)
