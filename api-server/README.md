# api-server

オセロ棋譜数カウントシステムのAPIサーバ（UI + API統合）です。

## セットアップ

```bash
# 仮想環境の作成
uv venv

# 依存関係のインストール
uv pip install -e ".[dev]"

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してDB接続情報を設定
```

## 開発

```bash
# APIサーバ起動
uv run uvicorn src.main:app --reload

# テスト実行
uv run pytest

# 型チェック
uv run mypy src
```

## データベース

```bash
# マイグレーション作成
uv run alembic revision -m "create tasks table"

# マイグレーション実行
uv run alembic upgrade head

# マイグレーションロールバック
uv run alembic downgrade -1
```
