# 開発用スクリプト

開発環境で使用するユーティリティスクリプト群です。

## 前提条件

- Python 3.11+
- uv（パッケージマネージャ）
- PostgreSQL クライアントツール（`pg_dump`, `psql`）
- Docker で PostgreSQL / Valkey が起動していること

```bash
docker-compose up -d
```

## スクリプト一覧

### db_reset.py - データベースリセット

PostgreSQL と Valkey のデータを全削除し、初期状態に戻します。

```bash
# 確認プロンプトあり
uv run python scripts/db_reset.py

# 確認なしで実行
uv run python scripts/db_reset.py --force

# PostgreSQL のみリセット
uv run python scripts/db_reset.py --postgres-only

# Valkey のみリセット
uv run python scripts/db_reset.py --valkey-only

# 静かに実行（出力抑制）
uv run python scripts/db_reset.py --force --quiet
```

**注意**: `alembic_version` テーブル（マイグレーション履歴）は保持されます。

### db_copy.py - データベースコピー

PostgreSQL のバックアップ/リストア、環境間コピーを行います。

#### バックアップ

```bash
# デフォルトファイル名（backup_YYYYMMDD_HHMMSS.sql）
uv run python scripts/db_copy.py backup

# ファイル名を指定
uv run python scripts/db_copy.py backup -o mybackup.sql

# 別のデータベースを指定
uv run python scripts/db_copy.py backup --database-url "postgresql://user:pass@host:5432/dbname"
```

#### リストア

```bash
# バックアップファイルからリストア
uv run python scripts/db_copy.py restore backup_20250112_123456.sql

# 確認なしでリストア
uv run python scripts/db_copy.py restore backup.sql --force
```

#### 環境間コピー

```bash
# ソースDBからターゲットDBへコピー
uv run python scripts/db_copy.py copy \
  --source-url "postgresql://user:pass@source-host:5432/dbname" \
  --target-url "postgresql://user:pass@target-host:5432/dbname"

# 確認なしでコピー
uv run python scripts/db_copy.py copy --force \
  --source-url "..." \
  --target-url "..."
```

## 環境変数

スクリプトは以下の環境変数を参照します（設定されていない場合は既定値を使用）:

| 環境変数 | 既定値 | 説明 |
|---------|--------|------|
| `DATABASE_URL` | `postgresql://count88:dev_password@localhost:5432/count88_db` | PostgreSQL 接続URL |
| `VALKEY_HOST` | `localhost` | Valkey ホスト |
| `VALKEY_PORT` | `6379` | Valkey ポート |
| `VALKEY_DB` | `0` | Valkey DB番号 |

## 典型的なワークフロー

### 開発を最初からやり直す

```bash
# 1. データベースをリセット
uv run python scripts/db_reset.py --force

# 2. マイグレーション実行（テーブル再作成）
cd api-server
uv run alembic upgrade head

# 3. タスク生成サーバで初期タスクを投入
cd ../task-generator
uv run python -m src.main
```

### 現在の状態を保存して後で復元

```bash
# 保存
uv run python scripts/db_copy.py backup -o checkpoint.sql

# ... 作業 ...

# 復元
uv run python scripts/db_copy.py restore checkpoint.sql --force
```
