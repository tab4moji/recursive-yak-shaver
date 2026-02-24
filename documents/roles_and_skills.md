# Recursive Yak Shaver: ロールとスキルの管理
# 目的: プロンプト構築とスキル定義、および TOON 形式の仕様。
# 更新履歴: 1.1 (2026-02-24)

## ロール・システム (Roles)
`roles/` 配下のファイルは、LLMに対する「役割の定義（システムプロンプト）」である。
これらは `rys/role_utils.py` によって読み込まれ、以下の要素と組み合わされる。

1. **Base Role**: 基本的な性格設定と指示。
2. **Skills Definition**: `skills/skills.json` から抽出されたスキルのリスト。
3. **Cheatsheets (Skill-Driven Hints)**: 各スキルの具体的なコード断片（ヒント）。
4. **Risk Knowledge Base**: `skills/risks.json` に基づく禁止事項。

## スキル定義 (Skills)
スキルは JSON 形式で定義され、以下の 2 段階で管理される。
- `skills/skills.json`: 主要なスキルのメタデータ（ID、ツール、概要）。
- `skills/cheatsheets/*.json`: 各スキルの具体的なコードパターン（チートシート）。

### チートシート・スキーマ (Cheatsheet Schema)
各チートシートの `patterns` は以下の情報を保持し、LLM の判断を強力に支援する。
- **`task_name`**: タスクの短い名称。
- **`description`**: 英語による機能説明。
- **`syntax`**: 推奨されるコードスニペット（Bash または Python）。
- **`input`**: 引数の配列。各要素は `name`, `description`, `type` を持つ。
- **`output_description`**: 出力内容の説明。
- **`output_type`**: 出力データ型（List, Value, Path, Content 等）。

### ロール固有のコンテキスト注入 (Role-Specific Context Filtering)
`rys/role_utils.py` は、呼び出されるロール（フェーズ）に応じて、チートシートから抽出する情報を動的に制限する。
- **Dispatcher (Phase 2)**: `task` と `description` のみ。実装詳細（syntax）を隠蔽し、高レベルなマッピングに集中させる。
- **Analyzer (Phase 4)**: `syntax` を除くすべての情報。詳細な I/O 計画を立てるために必要なメタデータを提供する。
- **Coder (Phase 5)**: `syntax` を含むすべての情報。具体的なコード生成のための「完成見本」を提供する。

## TOON (Token-Oriented Object Notation)
LLM に対して情報を効率的に伝えるため、RYS は独自のデータ形式「TOON」を採用している。
- **特徴**: YAML 形式をベースにし、トークン効率を最大化した構造化表現。
- **利点**: JSON と比較してトークンを削減しつつ、モデルが構造を確実に理解できるようにする。
- **引数の平坦化**: チートシート内の `input` 配列は、TOON 変換時に `name(description:type)` 形式の平坦な文字列へ自動的に変換され、モデルの可読性を高める。

例:
```yaml
# TOON example
skills:
  - id: shell_exec
    description: Standard tools for file processing...
```

## 標準バインディング (Standardized Bindings)
フェーズ間でのデータの受け渡しを確実にするため、出力バインディング名は以下に制限される。
- **`path`**: ファイルやディレクトリの場所。
- **`content`**: テキスト、計算結果、汎用データ。
- **`value`**: 数値や特定の結果。
