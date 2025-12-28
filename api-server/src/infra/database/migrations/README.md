# Alembicマイグレーション

このディレクトリにはAlembicのマイグレーションファイルが格納されます。

## 使用方法

```bash
# マイグレーション作成
uv run alembic revision -m "create tasks table"

# マイグレーション実行
uv run alembic upgrade head

# マイグレーションロールバック
uv run alembic downgrade -1

# 現在のリビジョン確認
uv run alembic current
```
