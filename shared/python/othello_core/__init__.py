"""オセロ（リバーシ）のビットボード基本操作、局面表現、定数を提供する共通ライブラリ"""

from othello_core.bitboard import Bitboard
from othello_core.position import Position
from othello_core.constants import BLACK, WHITE, BOARD_SIZE, INITIAL_BLACK, INITIAL_WHITE

__all__ = [
    "Bitboard",
    "Position",
    "BLACK",
    "WHITE",
    "BOARD_SIZE",
    "INITIAL_BLACK",
    "INITIAL_WHITE",
]
