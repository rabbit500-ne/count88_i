# UI画面分離設計書

## 概要
管理画面と公開画面を分離し、管理画面を保護しつつ公開画面を外部公開する。

## 要件

### 機能要件
1. **公開画面**: 認証なしでアクセス可能な一般ユーザー向けページ
2. **管理画面**: 認証が必要な管理者向けページ（進捗監視、タスク管理等）
3. 管理画面のURLパスは`.env`から動的に設定可能とする

### セキュリティ要件
- 管理画面のパスは推測されにくい文字列を使用
- nginxレベルでBasic認証を適用（本番環境）
- パス名に`admin`や`management`等の推測しやすい名前を使用しない

## URL設計

### 公開画面（認証不要）

| パス | 説明 | 実装 |
|------|------|------|
| `/` | 公開用トップページ | public_router |
| `/progress` | 進捗表示（公開用、簡易版） | public_router |
| `/participate` | 分散計算参加ページ | public_router |
| `/api/v1/*` | 公開API（タスク取得・結果送信等） | 既存api_router |

### 管理画面（認証必要）

| パス | 説明 | 実装 |
|------|------|------|
| `/${ADMIN_PATH}/` | 管理画面トップ | admin_router |
| `/${ADMIN_PATH}/progress` | 詳細進捗（BFS/DFS別） | admin_router |
| `/${ADMIN_PATH}/statistics` | 統計情報 | admin_router |
| `/${ADMIN_PATH}/tasks` | タスク一覧 | admin_router |

※ `ADMIN_PATH`は`.env`で設定（例: `ctrl-x7k9m2p4`）

## アーキテクチャ

```
[インターネット]
      │
      ▼
┌─────────────────────────────────────┐
│              nginx                   │
│  ┌───────────────────────────────┐  │
│  │ /${ADMIN_PATH}/* → Basic認証  │  │
│  │ /* → proxy（認証なし）        │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│          FastAPI (api-server)       │
│  ┌─────────────┐  ┌──────────────┐  │
│  │ AdminRouter │  │ PublicRouter │  │
│  │ /{ADMIN}/*  │  │ /*           │  │
│  └─────────────┘  └──────────────┘  │
└─────────────────────────────────────┘
```

## ディレクトリ構成

### 変更前
```
api-server/src/ui/
├── router.py           # UIルーター（単一）
└── views/
    ├── base.html
    ├── index.html
    ├── _progress.html
    ├── _statistics.html
    └── _tasks.html
```

### 変更後
```
api-server/src/ui/
├── admin_router.py     # 管理画面ルーター
├── public_router.py    # 公開画面ルーター
└── views/
    ├── base.html           # 共通ベーステンプレート
    ├── admin/              # 管理画面用テンプレート
    │   ├── index.html
    │   ├── _progress.html
    │   ├── _statistics.html
    │   └── _tasks.html
    └── public/             # 公開画面用テンプレート
        ├── index.html
        ├── _progress.html
        └── participate.html
```

## 設定

### .env
```env
# 管理画面のパス（推測されにくい文字列を設定）
# デフォルト: ctrl-panel（開発用）
# 本番では必ずランダムな文字列に変更すること
ADMIN_PATH=ctrl-x7k9m2p4
```

### config.py の追加項目
```python
class Settings(BaseSettings):
    # ... 既存設定 ...
    
    # 管理画面パス設定
    admin_path: str = "ctrl-panel"  # デフォルト（開発用）
```

## nginx設定例（本番用）

```nginx
# 管理画面 - Basic認証で保護
location ~ ^/${ADMIN_PATH}(/|$) {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

# 公開画面・API - 認証なし
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

## 実装詳細

### 公開画面の機能
1. **トップページ (`/`)**
   - プロジェクト概要
   - 参加方法の説明
   - 現在の進捗（簡易表示）

2. **進捗ページ (`/progress`)**
   - 全体の進捗率
   - 棋譜数カウント（現在値）
   - シンプルな表示（詳細は管理画面）

3. **参加ページ (`/participate`)**
   - 計算クライアント機能（現在の管理画面のクライアント機能を移植）
   - 開始/停止ボタン
   - 計算ログ表示

### 管理画面の機能
1. **トップページ (`/${ADMIN_PATH}/`)**
   - ダッシュボード（進捗、統計、タスク一覧の統合表示）

2. **詳細進捗 (`/${ADMIN_PATH}/progress`)**
   - BFS/DFS別の進捗
   - 詳細なステータス表示

3. **統計 (`/${ADMIN_PATH}/statistics`)**
   - 計算時間統計
   - キュー状態
   - クライアント情報

4. **タスク一覧 (`/${ADMIN_PATH}/tasks`)**
   - 最近のタスク（デバッグ用）
   - ステータス詳細

## 移行手順

1. `config.py`に`admin_path`設定を追加
2. `ui/admin_router.py`を作成（既存router.pyをベースに）
3. `ui/public_router.py`を新規作成
4. テンプレートを`admin/`と`public/`に分離
5. `main.py`を更新してルーターを統合
6. 動作確認
7. nginx設定を更新（本番デプロイ時）

## 注意事項

- **ADMIN_PATH**は本番環境では必ずランダムな文字列に変更すること
- Basic認証はHTTPS環境でのみ使用すること（HTTPでは平文送信される）
- ログに管理画面パスが出力されないよう注意
