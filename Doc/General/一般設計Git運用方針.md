一般設計Git管理戦略

## 1. Git管理戦略

### 1.1 リポジトリ構成：モノレポアプローチ

#### 採用理由
- **密結合なシステム**: フロント、API、タスク生成サーバが同じデータ構造・プロトコルを共有
- **アトミックな変更**: API仕様変更時に全コンポーネントを同時更新可能
- **共通コードの管理**: ビットボード操作、型定義などを一元管理
- **開発初期の柔軟性**: プロトタイプフェーズでは頻繁なリファクタリングが必要
- **CI/CDの効率化**: 統合テスト・デプロイを一元管理

### 1.2 ブランチ戦略

#### ブランチモデル: Git Flow（簡易版）

```
main (本番環境)
  │
  ├─ develop (開発統合ブランチ)
  │   │
  │   ├─ feature/frontend-* (フロント機能開発)
  │   ├─ feature/api-*      (API機能開発)
  │   ├─ feature/task-*     (タスク生成機能)
  │   └─ feature/shared-*   (共通ライブラリ)
  │
  ├─ release/v1.0 (リリース準備)
  │
  └─ hotfix/*      (緊急修正)
```

#### ブランチルール

| ブランチ種別 | 命名規則 | マージ先 | 用途 |
|------------|---------|---------|------|
| `main` | - | - | 本番環境（自動デプロイ） |
| `develop` | - | `main` | 開発統合、QA環境 |
| `feature/*` | `feature/{component}-{description}` | `develop` | 機能開発 |
| `release/*` | `release/v{major}.{minor}` | `main`, `develop` | リリース準備 |
| `hotfix/*` | `hotfix/{issue-number}` | `main`, `develop` | 緊急バグ修正 |

#### 例
```bash
feature/frontend-worker-implementation
feature/api-task-endpoint
feature/task-bfs-algorithm
feature/shared-bitboard-lib
```

### 1.3 コミット規約

#### コミットメッセージフォーマット（Conventional Commits）

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type（必須）
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント変更
- `style`: コードスタイル（フォーマット等）
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド・設定変更

#### Scope（推奨）
- `frontend`: フロントエンド
- `api`: APIサーバ
- `task`: タスク生成サーバ
- `shared`: 共通コード
- `db`: データベース
- `infra`: インフラ

#### 例
```
feat(frontend): Web Workerによる並列計算実装

- BFSアルゴリムをWorkerに分離
- 進捗表示UIの追加
- タスク取得ポーリング実装

Closes #123
```

```
fix(api): タスクタイムアウト処理の修正

60秒でタイムアウトしていなかった問題を修正

Fixes #456
```

### 1.4 プルリクエスト戦略

#### PRテンプレート

```markdown
## 修正背景・動機
<!-- なぜこの修正が必要か。 -->

## 設計考察
<!-- その動機を実現するため何故この実装にするのか。この実装の良い点、悪い点など。 -->

## 変更内容
- [ ] 変更項目1
- [ ] 変更項目2

## 影響範囲
- [ ] フロントエンド
- [ ] APIサーバ
- [ ] タスク生成サーバ
- [ ] データベース

## テスト
- [ ] 単体テスト追加・更新
- [ ] 統合テスト実施
- [ ] 手動テスト完了

## レビュー観点
<!-- レビュアーに確認してほしい点(あれば) -->

## そのほか

```

