# othello-core

オセロ（リバーシ）のビットボード基本操作、局面表現、定数を提供する共通ライブラリです。

## インストール

開発時は、プロジェクトルートから以下のコマンドでローカルインストールします：

```bash
uv pip install -e ../shared/python
```

## 使用方法

```python
from othello_core import Bitboard, Position, BLACK, WHITE

# 初期局面の作成
position = Position.initial()

# ビットボード操作
bitboard = Bitboard(black=0x0000000810000000, white=0x0000001008000000)
```

## 開発

```bash
# 開発依存関係をインストール
uv sync --dev

# テスト実行
uv run pytest

# 型チェック
uv run mypy othello_core
```
