オセロ棋譜数カウントシステム infra設計書

# 技術スタック
## データベース
RDBMS:
- PostgreSQL 16+
- Extensions: `pg_bigm` - 高速全文検索（オプション）

## キャッシュ・キュー
- Valkey 7.2+ (Redis互換)

## インフラ
コンテナ:
- Docker (v24+)
- Docker Compose (v2.20+)

オーケストレーション（本番環境）:
- Kubernetes (v1.28+)
- Helm - パッケージ管理

CI/CD:
- GitHub Actions

監視（将来実装）:
- Prometheus - メトリクス収集
- Grafana - 可視化
- Loki - ログ集約

# 開発環境構築
## 必要なツール
共通:
- Git (v2.40+)
- Docker (v24+)
- Docker Compose (v2.20+)

バックエンド（APIサーバ）:
- Python (v3.12+)
- uv (v0.1.0+) - インストール: `pip install uv`

WebAssembly（計算ロジック用、オプション）:
- Rust (v1.75+)
- wasm-pack (v0.12+)

## 初期セットアップスクリプト
### scripts/setup.sh
```bash
#!/bin/bash
set -e

echo "========================================="
echo "  オセロ棋譜数カウントシステム セットアップ"
echo "========================================="

# 1. ルートディレクトリに移動
cd "$(dirname "$0")/.."

# 2. APIサーバのセットアップ
echo "[1/3] APIサーバのセットアップ..."
cd api-server
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .
cd ..

# 3. タスク生成サーバのセットアップ
echo "[2/3] タスク生成サーバのセットアップ..."
cd task-generator
uv venv
source .venv/bin/activate
uv pip install -e .
cd ..

# 4. 共通ライブラリのセットアップ
echo "[3/3] 共通ライブラリのセットアップ..."
cd shared/python
uv pip install -e .
cd ../..

echo ""
echo "✅ セットアップ完了！"
echo ""
echo "次のステップ:"
echo "  1. Docker環境を起動: docker-compose up -d"
echo "  2. 開発サーバー起動: ./scripts/dev-start.sh"
```

## 開発環境起動スクリプト
### scripts/dev-start.sh
```bash
#!/bin/bash
set -e

echo "開発環境を起動しています..."

# Docker Compose で PostgreSQL と Valkey を起動
docker-compose up -d postgres valkey

# データベースマイグレーション
cd api-server
uv run alembic upgrade head
cd ..

# 並列起動（各ターミナルで実行）
echo ""
echo "以下のコマンドを別々のターミナルで実行してください:"
echo ""
echo "  # APIサーバ（UI + API統合）"
echo "  cd api-server && uv run uvicorn src.main:app --reload"
echo ""
echo "  # タスク生成サーバ"
echo "  cd task-generator && uv run python src/main.py"
echo ""
echo "ブラウザで http://localhost:8000/ui にアクセス"
echo ""
```

## docker-compose.yml
```yaml
version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: postgres:16-alpine
    container_name: count88_postgres
    environment:
      POSTGRES_USER: count88
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: count88_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/postgresql/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U count88"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Valkey (Redis互換)
  valkey:
    image: valkey/valkey:7.2
    container_name: count88_valkey
    ports:
      - "6379:6379"
    volumes:
      - valkey_data:/data
      - ./infra/valkey/valkey.conf:/usr/local/etc/valkey/valkey.conf
    command: valkey-server /usr/local/etc/valkey/valkey.conf
    healthcheck:
      test: ["CMD", "valkey-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # API Server (開発用)
  api:
    build:
      context: ./api-server
      dockerfile: Dockerfile
    container_name: count88_api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://count88:dev_password@postgres:5432/count88_db
      VALKEY_URL: redis://valkey:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      valkey:
        condition: service_healthy
    volumes:
      - ./api-server:/app
    command: uvicorn src.main:app --host 0.0.0.0 --reload

  # Task Generator (開発用)
  task-generator:
    build:
      context: ./task-generator
      dockerfile: Dockerfile
    container_name: count88_task_generator
    environment:
      DATABASE_URL: postgresql://count88:dev_password@postgres:5432/count88_db
      VALKEY_URL: redis://valkey:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      valkey:
        condition: service_healthy
    volumes:
      - ./task-generator:/app

volumes:
  postgres_data:
  valkey_data:
```

注意: UIはAPIサーバに統合されているため、別のfrontendサービスは不要です。

# デプロイ戦略
## 環境構成
| 環境 | 用途 | ブランチ | URL |
|------|------|---------|-----|
| Development | ローカル開発 | `feature/*` | localhost |
| QA | 統合テスト | `develop` | qa.count88.example.com |
| Production | 本番環境 | `main` | count88.example.com |

## CI/CDパイプライン
注意: UIはAPIサーバに統合されているため、別のfrontend CIは不要です。UI層のテストは`ci-api.yml`に含まれます。

### .github/workflows/ci-api.yml
```yaml
name: API Server CI (UI + API統合)

on:
  push:
    branches: [develop, main]
    paths:
      - 'api-server/**'
      - '.github/workflows/ci-api.yml'
  pull_request:
    paths:
      - 'api-server/**'

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      valkey:
        image: valkey/valkey:7.2
        options: >-
          --health-cmd "valkey-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install uv
        run: pip install uv
      
      - name: Install dependencies
        working-directory: api-server
        run: |
          uv venv
          source .venv/bin/activate
          uv pip install -e ".[dev]"
      
      - name: Lint
        working-directory: api-server
        run: |
          source .venv/bin/activate
          ruff check .
      
      - name: Type check
        working-directory: api-server
        run: |
          source .venv/bin/activate
          mypy src/
      
      - name: Run tests
        working-directory: api-server
        run: |
          source .venv/bin/activate
          pytest
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_db
          VALKEY_URL: redis://localhost:6379/0
      
      - name: Test UI templates
        working-directory: api-server
        run: |
          source .venv/bin/activate
          pytest tests/ui/ -v
```

## デプロイフロー
### 開発 → QA
```bash
# 1. feature ブランチで開発
git checkout -b feature/api-new-endpoint

# 2. コミット
git commit -m "feat(api): 新しいエンドポイント追加"

# 3. develop にマージ
git checkout develop
git merge feature/api-new-endpoint

# 4. プッシュ → 自動デプロイ（QA環境）
git push origin develop
```

### QA → 本番
```bash
# 1. リリースブランチ作成
git checkout -b release/v1.0 develop

# 2. バージョン更新・最終テスト

# 3. main にマージ
git checkout main
git merge release/v1.0

# 4. タグ付け
git tag -a v1.0.0 -m "Release v1.0.0"

# 5. プッシュ → 自動デプロイ（本番環境）
git push origin main --tags
```

# セキュリティ設計
## 環境変数管理
### .env.example
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/count88_db

# Valkey
VALKEY_URL=redis://localhost:6379/0

# API
API_SECRET_KEY=your-secret-key-here
API_CORS_ORIGINS=http://localhost:5173,https://count88.example.com

# Task Generator
TASK_BFS_DEPTH=7
TASK_TIMEOUT_SECONDS=60

# Monitoring (Optional)
SENTRY_DSN=
PROMETHEUS_ENABLED=false
```

# 監視・ログ設計
詳細は内部仕様書を参照。

# トラブルシューティング
## よくある問題
### 問題: Valkeyに接続できない
```bash
# 接続確認
redis-cli -h localhost -p 6379 ping
# → PONG が返れば正常

# Docker コンテナ確認
docker-compose ps valkey
```

### 問題: PostgreSQLマイグレーションエラー
```bash
# マイグレーション履歴確認
cd api-server
uv run alembic history

# 特定バージョンにダウングレード
uv run alembic downgrade -1

# 再度アップグレード
uv run alembic upgrade head
```

# 参考コマンド集
```bash
# Git操作
git checkout -b feature/new-feature
git commit -m "feat(api): 新機能追加"
git push origin feature/new-feature

# Docker操作
docker-compose up -d
docker-compose logs -f api
docker-compose down
```

