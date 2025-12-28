"""局面ドメインモデル"""

from dataclasses import dataclass
from typing import Literal

from othello_core import Bitboard


@dataclass
class Position:
    """局面ドメインモデル"""

    black: int  # 黒石ビットボード
    white: int  # 白石ビットボード
    turn: Literal["B", "W"]  # 手番

    def to_bitboard(self) -> Bitboard:
        """Bitboardオブジェクトに変換"""
        return Bitboard(black=self.black, white=self.white)

    @classmethod
    def from_bitboard(cls, bitboard: Bitboard, turn: bool) -> "Position":
        """Bitboardオブジェクトから作成"""
        return cls(
            black=bitboard.black,
            white=bitboard.white,
            turn="B" if turn else "W",
        )
