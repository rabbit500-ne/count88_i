オセロ棋譜数カウントシステム api-server設計書

# 技術スタック
## UI層（htmx + Jinja2）
フレームワーク・ライブラリ:
- Jinja2 - テンプレートエンジン
- htmx (v1.9+) - HTMLフラグメントによる動的UI更新
- FastAPI - HTMLレスポンス提供（UIルーター）

UI/UX:
- Tailwind CSS - スタイリング
- Chart.js - グラフ表示（JavaScript）

計算ロジック（ブラウザ内実行）:
- JavaScript - 計算エンジン
- Web Workers - 非同期計算処理
- WebAssembly - 高速計算（Rust + wasm-pack）

テスト:
- pytest - HTMLフラグメントのレスポンステスト
- Playwright - E2Eテスト（オプション）

設計原則:
- `/ui/*` パスでHTMLフラグメントを返す
- htmxの`hx-swap`で部分更新
- CSRF保護はUI層で完結

## API層（JSON API）
フレームワーク:
- FastAPI - JSON API提供（APIルーター）
- Pydantic v2 - リクエスト/レスポンスバリデーション

設計原則:
- `/api/*` パスでJSONを返す
- 将来のReact等への移行を見据えた設計
- OpenAPI仕様書を自動生成

## APIサーバ（統合）
フレームワーク:
- Python 3.12+
- FastAPI (v0.109+) - Webフレームワーク
- Uvicorn - ASGIサーバ
- uv - パッケージ管理

ORM・バリデーション:
- SQLAlchemy 2.0 - ORM
- Alembic - マイグレーション
- Pydantic v2 - バリデーション

キャッシュ・キュー:
- redis-py - Valkeyクライアント

テスト:
- pytest - テストフレームワーク
- pytest-asyncio - 非同期テスト
- httpx - APIテスト

# トラブルシューティング
## よくある問題
### 問題: Jinja2テンプレートが読み込めない
```bash
# テンプレートディレクトリの確認
cd api-server
ls -la src/ui/views/

# FastAPIのテンプレート設定を確認
# src/main.py で Jinja2Templates のパスが正しいか確認
```

# 参考コマンド集
```bash
# Python開発
cd api-server
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
uv run pytest

# APIサーバ起動（UI + API統合）
cd api-server
uv run uvicorn src.main:app --reload

# データベース
uv run alembic revision -m "create tasks table"
uv run alembic upgrade head
uv run alembic downgrade -1
```

