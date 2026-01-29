# DFS ベンチマーク

DFSアルゴリズムの処理時間を計測するためのスクリプトです。

## 前提条件

- Node.js 18+（ESモジュールサポート）

## 使い方

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

### 局面をファイルから読み込み

```bash
# resource/kifuフォルダのJSONファイルを指定
node dfs-benchmark.mjs --file ../../../../../resource/kifu/D01_F5.json

# D49の終局間近の局面
node dfs-benchmark.mjs --file ../../../../../resource/kifu/D49_F5D6C3D3C4F4F6F3E6E7D7C5B5B4C6G5G4G3H4H3H5E3D2C2E2F2B3A3A4A5B6A6C7D8E8C8B7A8F7G6H6H7G8F8H8G7E1D1F1.json
```

### 局面を直接指定

```bash
# JSON形式で指定
node dfs-benchmark.mjs --json '{"black":"0x007E7E3E1E0E0600","white":"0xFF81817D61717938","turn":"black"}'

# 個別指定
node dfs-benchmark.mjs --black 0x007E7E3E1E0E0600 --white 0xFF81817D61717938 --turn black
```

### 複数回実行して統計を取得

```bash
node dfs-benchmark.mjs --iterations 5 --verbose
```

### BFSで指定深さまで進めた局面でテスト

```bash
# D10の局面を生成してDFS実行（時間がかかる）
node dfs-benchmark.mjs --depth 10
```

> **注意**: `--depth` オプションはD0からBFSで局面を生成するため、深い深さでは非常に時間がかかります。D48の局面をテストする場合は、`resource/kifu/` フォルダのJSONファイルを `--file` で指定してください。

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

## 出力例

```
============================================================
DFS ベンチマーク
============================================================

【局面】
  a b c d e f g h
1 . . . ○ ○ ○ . . 
2 ○ ● ● ○ ○ ○ ○ . 
3 ○ ● ● ● ○ ○ ○ . 
4 ○ ● ● ● ● ○ ○ . 
5 ○ ● ● ● ● ● ○ . 
6 ○ ● ● ● ● ● ● ○ 
7 ○ ● ● ● ● ● ● ○ 
8 ○ ○ ○ ○ ○ ○ ○ ○ 

Black: 0x007E7E3E1E0E0600
White: 0xFF81817D61717938
Turn: black
合法手数: 6

【実行】 iterations=1
  [1/1] 3928.755 ms (棋譜数: 38704)

【結果】
棋譜数: 38704
処理時間: 3928.755 ms
============================================================
```

## 共通モジュール

このベンチマークは `othello-core.js` の共通モジュールを使用しています。
同じDFSロジックがブラウザクライアント（`client.js`）でも使用されているため、
ベンチマーク結果はブラウザでの実行時間の参考になります。

```
api-server/src/static/js/
├── othello-core.js    # 共通コアロジック（DFS/BFS）
├── client.js          # ブラウザクライアント
└── benchmark/
    ├── README.md      # このファイル
    └── dfs-benchmark.mjs  # 評価スクリプト
```
