"""局面表現"""

from othello_core.bitboard import Bitboard
from othello_core.constants import BLACK, WHITE, INITIAL_BLACK, INITIAL_WHITE


class Position:
    """オセロの局面を表現するクラス"""

    def __init__(self, bitboard: Bitboard, turn: bool = BLACK):
        """
        局面を初期化

        Args:
            bitboard: ビットボード
            turn: 手番（Trueなら黒、Falseなら白）
        """
        self.bitboard = bitboard
        self.turn = turn

    @classmethod
    def initial(cls) -> "Position":
        """初期局面を作成"""
        bitboard = Bitboard(black=INITIAL_BLACK, white=INITIAL_WHITE)
        return cls(bitboard=bitboard, turn=BLACK)

    def __eq__(self, other: object) -> bool:
        """等価性チェック"""
        if not isinstance(other, Position):
            return False
        return (
            self.bitboard == other.bitboard
            and self.turn == other.turn
        )

    def __repr__(self) -> str:
        """文字列表現"""
        turn_str = "BLACK" if self.turn else "WHITE"
        return f"Position(bitboard={self.bitboard}, turn={turn_str})"

    def get_legal_moves(self) -> int:
        """
        合法手を取得（ビットボード形式）

        Returns:
            合法手を表すビットボード
        """
        # TODO: Phase 1では最小限の実装
        # 詳細な実装はPhase 2以降で行う
        raise NotImplementedError("get_legal_moves is not implemented yet")

    def make_move(self, move: int) -> "Position":
        """
        手を打つ

        Args:
            move: 打つ位置を表すビット（1つのビットのみが立っている）

        Returns:
            新しい局面
        """
        # TODO: Phase 1では最小限の実装
        # 詳細な実装はPhase 2以降で行う
        raise NotImplementedError("make_move is not implemented yet")

    def is_game_over(self) -> bool:
        """ゲーム終了判定"""
        # TODO: Phase 1では最小限の実装
        raise NotImplementedError("is_game_over is not implemented yet")
