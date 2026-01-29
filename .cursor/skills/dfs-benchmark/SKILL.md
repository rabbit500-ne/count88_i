---
name: dfs-benchmark
description: DFSアルゴリズムのパフォーマンスを計測するベンチマークを実行する。パフォーマンス計測、DFS処理時間、ベンチマーク実行を依頼された時に使用する。
---

# DFSベンチマーク

DFSアルゴリズムの処理時間を計測するスクリプトを実行します。

## 前提条件

- Node.js 18+

## 実行手順

作業ディレクトリを移動してから実行:

```bash
cd api-server/src/static/js/benchmark
```

### 基本実行（D50相当のサンプル局面）

```bash
node dfs-benchmark.mjs
```

### 詳細出力（盤面表示あり）

```bash
node dfs-benchmark.mjs --verbose
```

### 局面をファイルから読み込み（推奨）

```bash
# resource/kifuフォルダのJSONファイルを指定
node dfs-benchmark.mjs --file ../../../../../resource/kifu/D01_F5.json

# D49の終局間近の局面
node dfs-benchmark.mjs --file ../../../../../resource/kifu/D49_F5D6C3D3C4F4F6F3E6E7D7C5B5B4C6G5G4G3H4H3H5E3D2C2E2F2B3A3A4A5B6A6C7D8E8C8B7A8F7G6H6H7G8F8H8G7E1D1F1.json
```

### 局面を直接指定

JSON形式:
```bash
node dfs-benchmark.mjs --json '{"black":"0x007E7E3E1E0E0600","white":"0xFF81817D61717938","turn":"black"}'
```

個別指定:
```bash
node dfs-benchmark.mjs --black 0x007E7E3E1E0E0600 --white 0xFF81817D61717938 --turn black
```

### 統計取得（複数回実行）

```bash
node dfs-benchmark.mjs --iterations 5 --verbose
```

### 指定深さの局面でテスト

```bash
node dfs-benchmark.mjs --depth 10
```

> **注意**: `--depth` は深い値では非常に時間がかかります。D48等の深い局面は `resource/kifu/` フォルダのJSONファイルを `--file` で指定してください。

## オプション一覧

| オプション | 説明 |
|-----------|------|
| `--file PATH` | 局面をJSONファイルから読み込み（推奨） |
| `--json JSON` | 局面をJSON形式で指定 |
| `--black HEX` | 黒石のビットボード（16進数） |
| `--white HEX` | 白石のビットボード（16進数） |
| `--turn TURN` | 手番 (`black` または `white`) |
| `--depth N` | 初期局面からBFSでN手進めた局面でDFSを実行 |
| `--iterations N` | 繰り返し回数（デフォルト: 1） |
| `--verbose, -v` | 詳細出力（盤面表示など） |
| `--help, -h` | ヘルプを表示 |

## 関連ファイル

```
api-server/src/static/js/
├── othello-core.js       # 共通コアロジック（DFS/BFS）
├── client.js             # ブラウザクライアント
└── benchmark/
    ├── README.md
    └── dfs-benchmark.mjs # ベンチマークスクリプト
```
