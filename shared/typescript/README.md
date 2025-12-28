# @count88/shared

オセロ（リバーシ）の型定義、定数、ユーティリティを提供する共通ライブラリです。

## インストール

```bash
npm install @count88/shared
```

または、ローカル開発時：

```bash
npm install ../shared/typescript
```

## 使用方法

```typescript
import { Position, Task, BLACK, WHITE, createInitialPosition } from "@count88/shared";

// 初期局面の作成
const position = createInitialPosition();

// 型定義の使用
const task: Task = {
  task_id: "1234567890",
  task_type: "BFS",
  position: position,
  depth: 7,
  parent_task_id: null,
  estimated_time: 5.0,
  timestamp: new Date().toISOString(),
};
```

## ビルド

```bash
npm run build
```

## 開発

```bash
# TypeScriptの型チェック
npx tsc --noEmit
```
