"""ビットボード操作（sharedモジュールのラッパー）"""

from othello_core import Bitboard as CoreBitboard


class Bitboard(CoreBitboard):
    """ビットボード操作（sharedモジュールのラッパー）"""

    # Phase 1では、sharedモジュールの機能をそのまま使用
    # Phase 2以降で、task-generator固有の拡張を追加する可能性がある
