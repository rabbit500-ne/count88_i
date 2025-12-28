# task-generator

オセロ棋譜数カウントシステムのタスク生成サーバです。

## セットアップ

```bash
# 仮想環境の作成
uv venv

# 依存関係のインストール
uv pip install -e ".[dev]"

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してValkey接続情報を設定
```

## 開発

```bash
# サーバ起動
uv run python src/main.py

# テスト実行
uv run pytest

# 型チェック
uv run mypy src
```
