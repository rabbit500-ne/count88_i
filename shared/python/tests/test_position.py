"""局面のテスト"""

from othello_core import Position, Bitboard, BLACK, WHITE


def test_position_initial():
    """初期局面の作成テスト"""
    pos = Position.initial()
    assert pos.bitboard.black == 0x0000000810000000
    assert pos.bitboard.white == 0x0000001008000000
    assert pos.turn == BLACK


def test_position_equality():
    """局面の等価性テスト"""
    pos1 = Position.initial()
    pos2 = Position.initial()
    assert pos1 == pos2
