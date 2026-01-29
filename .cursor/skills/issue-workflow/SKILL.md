---
name: issue-workflow
description: GitHub issue起点で調査または実装を行うワークフロー。ユーザーがissue番号を指定して作業を依頼した時、「issue #123 を調査して」「issue #45 を実装して」などの指示を受けた時に使用する。
---

# Issue Workflow

GitHub issue起点での調査・実装作業を進めるためのワークフロー。

## ワークフロー概要

```
1. issueの内容把握 (gh issue view)
     ↓
2. 作業フォルダの確認 (workspace/issue_#<issue_number>)
     ↓
3. 初回: TODOテンプレートをコピー / 継続: TODO.mdを読む
     ↓
4. TODO.mdに従って作業を進める
```

## Step 1: issueの内容を把握

```bash
gh issue view <issue_number>
```

**重要**: エラーが発生した場合は直ちに作業を止め、指示者(ユーザー)に確認を求めること。

## Step 2: 作業フォルダの確認

`workspace/issue_#<issue_number>` フォルダと `TODO.md` の存在を確認する。

| 状態 | 次のステップ |
|------|-------------|
| フォルダが存在しない | → Step 3 (初回作業) |
| TODO.mdが存在する | → Step 4 (継続作業) |

## Step 3: 初回作業 - TODOテンプレートのコピー

### フォルダ作成

```bash
mkdir -p workspace/issue_#<issue_number>
```

### テンプレート選択

| 作業種別 | コピー元 |
|---------|---------|
| 調査 | `Doc/General/issue_調査_TODO_template.md` |
| 実装 | `Doc/General/issue_実装_TODO_template.md` |

テンプレートを `workspace/issue_#<issue_number>/TODO.md` としてコピーする。

## Step 4: TODO.mdに従って作業を進める

`workspace/issue_#<issue_number>/TODO.md` を読み、チェックリストに従って作業を進める。

### 作業の流れ（共通）

1. issueの内容把握
2. 質問の生成 → `QA.md` にまとめる
3. 質問への回答を `QA.md` に追記
4. **指示者に確認を求めて一旦停止**
5. 本作業（調査: report.md作成 / 実装: コード修正）
6. **指示者に確認を求めて一旦停止**

## 注意事項

- **調査指示の場合**: 不具合の調査のみ行い、修正は行わない
- **停止ポイント**: TODO.mdで指定された箇所で必ず停止し、ユーザー確認を待つ
- チェック完了した項目は `[x]` でマークする
