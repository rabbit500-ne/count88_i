"""ビットボード基本操作"""

from typing import Tuple


class Bitboard:
    """64bitビットボードで盤面を表現するクラス"""

    def __init__(self, black: int, white: int):
        """
        ビットボードを初期化

        Args:
            black: 黒石の配置を表す64bit整数
            white: 白石の配置を表す64bit整数
        """
        self.black = black
        self.white = white

    def __eq__(self, other: object) -> bool:
        """等価性チェック"""
        if not isinstance(other, Bitboard):
            return False
        return self.black == other.black and self.white == other.white

    def __repr__(self) -> str:
        """文字列表現"""
        return f"Bitboard(black=0x{self.black:016x}, white=0x{self.white:016x})"

    def get_empty(self) -> int:
        """空きマスを取得"""
        return ~(self.black | self.white) & 0xFFFFFFFFFFFFFFFF

    def get_occupied(self) -> int:
        """占有マスを取得"""
        return self.black | self.white

    def count_pieces(self, color: bool) -> int:
        """
        石の数をカウント

        Args:
            color: Trueなら黒、Falseなら白

        Returns:
            石の数
        """
        board = self.black if color else self.white
        return bin(board).count("1")

    def rotate90(self) -> "Bitboard":
        """90度回転"""
        # TODO: Phase 1では最小限の実装
        # 詳細な実装はPhase 2以降で行う
        raise NotImplementedError("rotate90 is not implemented yet")

    def rotate180(self) -> "Bitboard":
        """180度回転"""
        # TODO: Phase 1では最小限の実装
        raise NotImplementedError("rotate180 is not implemented yet")

    def rotate270(self) -> "Bitboard":
        """270度回転"""
        # TODO: Phase 1では最小限の実装
        raise NotImplementedError("rotate270 is not implemented yet")

    def color_inversion(self) -> "Bitboard":
        """色反転（黒と白を入れ替え）"""
        return Bitboard(black=self.white, white=self.black)
