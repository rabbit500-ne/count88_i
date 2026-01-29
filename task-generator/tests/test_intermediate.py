"""intermediate.py のユニットテスト"""

import pytest

from src.generator.intermediate import (
    _count_stones_from_hex,
    _should_start_dfs,
    determine_child_task_spec,
    _get_accumulated_depth_from_phase,
    _get_parent_phase,
    DFS_START_DEPTH,
    DFS_START_STONE_COUNT,
    MAX_BFS_DEPTH,
    SEGMENT_WIDTH,
)


class TestCountStonesFromHex:
    """石数計算関数のテスト"""

    def test_initial_position(self):
        """初期配置（黒2白2）"""
        # 初期配置: e4, d5が黒、d4, e5が白
        # 黒: 0x0000000810000000 (e4=bit27, d5=bit36)
        # 白: 0x0000001008000000 (d4=bit28, e5=bit35)
        black_hex = "0x0000000810000000"
        white_hex = "0x0000001008000000"
        assert _count_stones_from_hex(black_hex, white_hex) == 4

    def test_empty_board(self):
        """空盤面"""
        assert _count_stones_from_hex("0x0", "0x0") == 0

    def test_full_board(self):
        """全マス埋まった盤面（64石）"""
        # 黒32石、白32石
        black_hex = "0xFFFFFFFF00000000"
        white_hex = "0x00000000FFFFFFFF"
        assert _count_stones_from_hex(black_hex, white_hex) == 64

    def test_typical_midgame(self):
        """典型的な中盤局面（52石）"""
        # 黒26石、白26石 = 52石
        black_hex = "0x00FFFFFFFFFFFF00"  # 48石（例示用、実際の値は異なる）
        white_hex = "0x000000000000000F"  # 4石
        result = _count_stones_from_hex(black_hex, white_hex)
        assert result == 52  # 48 + 4 = 52


class TestShouldStartDfs:
    """DFS開始条件判定のテスト"""

    def test_depth_less_than_48(self):
        """深さ48未満: 常にBFS継続"""
        assert _should_start_dfs(42, 60) is False
        assert _should_start_dfs(36, 52) is False
        assert _should_start_dfs(0, 64) is False

    def test_depth_48_stone_52_or_more(self):
        """深さ48、石数52以上: DFS開始"""
        assert _should_start_dfs(48, 52) is True
        assert _should_start_dfs(48, 60) is True
        assert _should_start_dfs(48, 64) is True

    def test_depth_48_stone_less_than_52(self):
        """深さ48、石数52未満: BFS継続"""
        assert _should_start_dfs(48, 51) is False
        assert _should_start_dfs(48, 40) is False
        assert _should_start_dfs(48, 4) is False

    def test_depth_54_stone_52_or_more(self):
        """深さ54、石数52以上: DFS開始"""
        assert _should_start_dfs(54, 52) is True
        assert _should_start_dfs(54, 58) is True

    def test_depth_54_stone_less_than_52(self):
        """深さ54、石数52未満: BFS継続"""
        assert _should_start_dfs(54, 51) is False
        assert _should_start_dfs(54, 48) is False

    def test_depth_60_or_more_force_dfs(self):
        """深さ60以上: 石数に関わらず強制DFS"""
        assert _should_start_dfs(60, 52) is True
        assert _should_start_dfs(60, 51) is True  # 石数52未満でもDFS
        assert _should_start_dfs(60, 40) is True
        assert _should_start_dfs(66, 30) is True  # 極端に少ない石数でもDFS


class TestDetermineChildTaskSpec:
    """子タスク仕様決定のテスト"""

    def test_depth_less_than_48_returns_bfs(self):
        """深さ48未満: BFSタスクを返す"""
        task_type, phase, queue, depth = determine_child_task_spec(42)
        assert task_type == "BFS"
        assert phase == "bfs_d42_48"
        assert queue == "task_queue:bfs:phase2"
        assert depth == SEGMENT_WIDTH

    def test_depth_48_stone_52_returns_dfs(self):
        """深さ48、石数52以上: DFSタスクを返す"""
        task_type, phase, queue, depth = determine_child_task_spec(48, 52)
        assert task_type == "DFS"
        assert phase == "dfs_from_d48"
        assert queue == "task_queue:dfs:phase3"
        assert depth == 100

    def test_depth_48_stone_51_returns_bfs(self):
        """深さ48、石数52未満: BFSタスクを返す"""
        task_type, phase, queue, depth = determine_child_task_spec(48, 51)
        assert task_type == "BFS"
        assert phase == "bfs_d48_54"
        assert queue == "task_queue:bfs:phase2"
        assert depth == SEGMENT_WIDTH

    def test_depth_54_stone_52_returns_dfs(self):
        """深さ54、石数52以上: DFSタスクを返す"""
        task_type, phase, queue, depth = determine_child_task_spec(54, 52)
        assert task_type == "DFS"
        assert phase == "dfs_from_d54"
        assert queue == "task_queue:dfs:phase3"
        assert depth == 100

    def test_depth_54_stone_51_returns_bfs(self):
        """深さ54、石数52未満: BFSタスクを返す"""
        task_type, phase, queue, depth = determine_child_task_spec(54, 51)
        assert task_type == "BFS"
        assert phase == "bfs_d54_60"
        assert queue == "task_queue:bfs:phase2"
        assert depth == SEGMENT_WIDTH

    def test_depth_60_force_dfs(self):
        """深さ60以上: 石数に関わらずDFSタスクを返す"""
        task_type, phase, queue, depth = determine_child_task_spec(60, 40)
        assert task_type == "DFS"
        assert phase == "dfs_from_d60"
        assert queue == "task_queue:dfs:phase3"
        assert depth == 100

    def test_depth_60_no_stone_count_returns_dfs(self):
        """深さ60以上、石数未指定: DFSタスクを返す"""
        task_type, phase, queue, depth = determine_child_task_spec(60)
        assert task_type == "DFS"
        assert phase == "dfs_from_d60"


class TestGetAccumulatedDepthFromPhase:
    """フェーズ名から累積深さを取得するテスト"""

    def test_standard_phases(self):
        """標準的なフェーズ名"""
        assert _get_accumulated_depth_from_phase("bfs_d00_06") == 6
        assert _get_accumulated_depth_from_phase("bfs_d06_12") == 12
        assert _get_accumulated_depth_from_phase("bfs_d42_48") == 48
        assert _get_accumulated_depth_from_phase("bfs_d48_54") == 54
        assert _get_accumulated_depth_from_phase("bfs_d54_60") == 60


class TestGetParentPhase:
    """親フェーズ取得のテスト"""

    def test_d00_06_has_no_parent(self):
        """D00-06層には親がない"""
        assert _get_parent_phase("bfs_d00_06") is None

    def test_d06_12_parent_is_d00_06(self):
        """D06-12層の親はD00-06層"""
        assert _get_parent_phase("bfs_d06_12") == "bfs_d00_06"

    def test_d48_54_parent_is_d42_48(self):
        """D48-54層の親はD42-48層"""
        assert _get_parent_phase("bfs_d48_54") == "bfs_d42_48"

    def test_d54_60_parent_is_d48_54(self):
        """D54-60層の親はD48-54層"""
        assert _get_parent_phase("bfs_d54_60") == "bfs_d48_54"


class TestConstants:
    """定数のテスト"""

    def test_segment_width(self):
        """セグメント幅"""
        assert SEGMENT_WIDTH == 6

    def test_dfs_start_depth(self):
        """DFS開始深さ"""
        assert DFS_START_DEPTH == 48

    def test_dfs_start_stone_count(self):
        """DFS開始石数"""
        assert DFS_START_STONE_COUNT == 52

    def test_max_bfs_depth(self):
        """最大BFS深さ"""
        assert MAX_BFS_DEPTH == 60
