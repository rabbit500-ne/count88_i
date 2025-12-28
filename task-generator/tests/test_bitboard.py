"""ビットボード操作のテスト"""

import pytest
from othello_core import Bitboard

from src.algorithms.bitboard import Bitboard as TaskBitboard


def test_bitboard_wrapper():
    """ビットボードラッパーのテスト"""
    bb = TaskBitboard(black=0x0000000810000000, white=0x0000001008000000)
    assert bb.black == 0x0000000810000000
    assert bb.white == 0x0000001008000000
