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
- `skills/skills.json`: 主要なスキルのメタデータ。
- `skills/cheatsheets/*.json`: 各スキルのコード断片（ヒント）定義（チートシート）。

### チートシートによるヒント提供 (Skill-Driven Hints)
各チートシート内の `patterns` は、LLM に対する具体的な実装の「ヒント」として機能する。
1. **パターン選択**: `Phase 4` (Analyzer) が、ユーザーの意図に最も近い `pattern` を選択し、その ID を出力に含める。
2. **自動組み上げ**: `Phase 5` (Generator) は、選択されたパターンの入出力モードに基づき、適切な Bash または Python の「フレームワーク（糊）」を適用してスクリプトを構築する。

これにより、LLM はゼロからコードを考える必要がなくなり、安定したパターンを「選択・適用」することで堅牢な実行を保証する。

## TOON (Token-Oriented Object Notation)
LLM に対して情報を効率的に伝えるため、RYS は独自のデータ形式「TOON」を採用している。
- **特徴**: YAML 形式をベースにし、トークン効率を最大化した構造化表現。
- **利点**: JSON と比較してトークンを削減しつつ、モデルが構造を確実に理解できるようにする。

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
