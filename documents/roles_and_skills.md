# Recursive Yak Shaver: ロールとスキルの管理
# プロジェクト目的: プロンプト構築とスキル定義のメカニズム解説。
# 更新履歴: 1.0 (2026-02-17)

## ロール・システム (Roles)
`roles/` 配下のマークダウンファイルは、LLMに対する「役割の定義」である。
これらは `rys/role_utils.py` によって動的に読み込まれ、以下の要素と組み合わされてシステムプロンプトとして構築される。

1. **Base Role**: 基本的な性格設定と指示。
2. **Skills Definition**: `config/skills.json` から抽出された利用可能なスキルのリスト。
3. **Tool Reference / Cheatsheets**: 各スキルに紐づく具体的なツールの使用例。
4. **Risk Knowledge Base**: `config/risks.json` に基づく禁止事項や注意点。

## スキル定義 (Skills)
スキルは JSON 形式で定義され、以下の 2 段階で管理される。
- `config/skills.json`: 主要なスキルのメタデータ。
- `config/skills/*.json`: 各スキルの具体的な操作、入出力、推奨されるパターンなどの詳細（チートシート）。

## TOON (Token-Oriented Object Notation)
LLM に対して情報を効率的に伝えるため、RYS は独自のデータ形式「TOON」を採用している。
- **特徴**: カンマ区切りの表形式（CSVに似た形式）や、インデントによる階層表現を組み合わせる。
- **利点**: JSON と比較して構文トークンを削減し、コンテキストウィンドウを節約しつつ、モデルが構造を理解しやすくする。

例:
```
skills[3]{id,type,description}:
python_math,primitive,Advanced mathematical calculations...
shell_exec,primitive,Experimental shell execution tools...
```

## 標準バインディング (Standardized Bindings)
フェーズ間でのデータの受け渡しを確実にするため、各スキルの出力バインディング名は以下の 2 種類に制限される。
- **`path`**: ファイルやディレクトリの場所を表す出力に使用。
- **`content`**: テキスト、計算結果、ステータス、またはその他の汎用データ出力に使用。

この標準化により、後続のフェーズ（例: Coder や Executor）がどのバインディングを参照すべきか迷うことがなくなり、パイプライン全体の堅牢性が向上している。
