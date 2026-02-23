# Recursive Yak Shaver: アーキテクチャ概要
# プロジェクト目的: 複雑なユーザー要求を分解し、スキルベースで実行可能なコードを生成・実行するエージェント・パイプライン。
# 更新履歴: 1.0 (2026-02-17)

## 概要
Recursive Yak Shaver (RYS) は、LLMを活用した「段階的分解・実行」型のパイプラインシステムである。
一度の推論で全てを解決しようとせず、複数のフェーズ (Phases) に分割することで、確実かつ安全なタスク実行を目指している。

## パイプライン・フェーズ
RYS は、タスクの実行を 6 つの独立したフェーズに分割して処理する。各フェーズの詳細は [shaving_phases.md](./shaving_phases.md) にて定義・詳説されている。
また、Bash スクリプトの自動生成に関する設計思想は [bash_framework_design.md](./bash_framework_design.md) を参照。
1. **Phase 1: Translation** (翻訳・正規化)
2. **Phase 2: Dispatch** (タスク分解・スキル割り当て)
3. **Phase 3: Grouping** (グループ化・依存関係解決)
4. **Phase 4: Processing** (入出力要件の分析)
5. **Phase 5: Generation** (実行可能コード生成)
6. **Phase 6: Execution** (実行・結果報告)

## 主要コンセプト
1. **Affirmative Control (肯定説明)**: 全てのロール指示およびチートシートにおいて、否定的な表現を排除し、肯定的な指示（「～せよ」「～を維持せよ」等）のみを用いる。これにより、LLMの指示追従性と実行の安定性を最大化する。
2. **Pipeline Architecture**: 入力から実行までを 6 つのフェーズに分ける。
2. **Role-Based Reasoning**: 各フェーズは、特定の役割 (`roles/*.md`) を持ったエージェントが担当する。
3. **Skill-Oriented Dispatching**: 実行可能な操作を「スキル」(`skills/skills.json`) として定義し、動的にプロンプトへ注入する。
4. **TOON (Token-Oriented Object Notation)**: トークン効率を重視した独自の構造化データ表現を用い、LLMとのやり取りを最適化する。

## コンポーネント構造
- `rys/main.bash`: 各フェーズを順次実行するオーケストレーター。
- `rys/phase*.py`: 各フェーズのロジック。
- `roles/*.md`: 各エージェントのシステムプロンプト。
- `skills/*.json`: スキル、リスク管理、設定情報。
- `~/.cache/rys/`: フェーズ間のキャッシュ（JSON形式）。XDG Base Directory 規格に準拠。
