# pyproject.toml 記法マニュアル

## 開発依存関係の管理

### 推奨: [dependency-groups] を使用

`uv` を主に使用するプロジェクトでは、開発依存関係は `[dependency-groups]` セクションで管理します。

```toml
[dependency-groups]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.0.0",
]
```

### 利点

1. **`uv` コマンドとの直接統合**
   - `uv sync --dev` で開発依存関係をインストール
   - `uv add --dev <package>` で開発依存関係を追加
   - `uv run --dev <command>` で開発依存関係を含めて実行

2. **PEP 735 準拠**
   - 開発依存関係管理の標準的な方法

3. **明確な分離**
   - 開発時にのみ必要な依存関係を明確に分離
   - 本番環境に不要なパッケージが含まれることを防止

### 使用方法

```bash
# 開発依存関係をインストール
uv sync --dev

# 開発依存関係を追加
uv add --dev pytest

# 開発依存関係を含めてコマンド実行
uv run --dev mypy othello_core
```

## [project.optional-dependencies] との違い

### [dependency-groups]
- **目的**: 開発時にのみ必要な依存関係（テスト、リント、型チェックなど）
- **対象**: 開発者
- **インストール**: `uv sync --dev` または `uv pip install -e ".[dev]"`（非推奨）

### [project.optional-dependencies]
- **目的**: エンドユーザーが選択的にインストールする追加機能の依存関係
- **対象**: エンドユーザー
- **インストール**: `uv pip install -e ".[feature-name]"`

### 使い分けの例

```toml
# 開発依存関係（開発者のみ）
[dependency-groups]
dev = [
    "pytest>=7.4.0",
    "mypy>=1.0.0",
]

# オプション機能（エンドユーザーが選択）
[project.optional-dependencies]
redis = [
    "redis>=5.0.0",
]
postgres = [
    "psycopg2>=2.9.0",
]
```

## まとめ

- **開発依存関係** → `[dependency-groups]` を使用
- **オプション機能** → `[project.optional-dependencies]` を使用
- `uv` を主に使用する場合は `[dependency-groups]` が推奨
