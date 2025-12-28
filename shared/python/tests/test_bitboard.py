"""ビットボードのテスト"""

import pytest
from othello_core import Bitboard, BLACK, WHITE


def test_bitboard_initialization():
    """ビットボードの初期化テスト"""
    bb = Bitboard(black=0x0000000810000000, white=0x0000001008000000)
    assert bb.black == 0x0000000810000000
    assert bb.white == 0x0000001008000000


def test_bitboard_equality():
    """ビットボードの等価性テスト"""
    bb1 = Bitboard(black=0x0000000810000000, white=0x0000001008000000)
    bb2 = Bitboard(black=0x0000000810000000, white=0x0000001008000000)
    assert bb1 == bb2


def test_color_inversion():
    """色反転テスト"""
    bb = Bitboard(black=0x0000000810000000, white=0x0000001008000000)
    inverted = bb.color_inversion()
    assert inverted.black == 0x0000001008000000
    assert inverted.white == 0x0000000810000000


def test_count_pieces():
    """石の数カウントテスト"""
    bb = Bitboard(black=0x0000000810000000, white=0x0000001008000000)
    assert bb.count_pieces(BLACK) == 2
    assert bb.count_pieces(WHITE) == 2
