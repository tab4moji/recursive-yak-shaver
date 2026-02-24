# Recursive Yak Shaver: アーキテクチャ概要
# プロジェクト目的: 複雑なユーザー要求を分解し、スキルベースで実行可能なコードを生成・実行するエージェント・パイプライン。
# 更新履歴: 1.2 (2026-02-24) 現状の実装（6フェーズ・キャッシュ機構・Bash/Pythonフレームワーク）に合わせて刷新

## 概要
Recursive Yak Shaver (RYS) は、LLMを活用した「段階的分解・実行」型のパイプラインシステムである。
一度の推論で全てを解決しようとせず、複数のフェーズ (Phases) に分割することで、確実かつ安全なタスク実行を目指している。

## パイプライン・フェーズ (Standard Pipeline)
RYS は、タスクの実行を 6 つの独立したフェーズに分割して処理する。各フェーズの詳細は [shaving_phases.md](./shaving_phases.md) を参照。

1. **Phase 1: Translation** (翻訳・正規化) - ユーザープロンプトの翻訳と構造化。
2. **Phase 2: Dispatch** (タスク分解・スキル割り当て) - 最小単位のタスク (Task) へ分解し、スキルを紐付ける。
3. **Phase 3: Grouping** (グループ化・依存関係解決) - タスクをジョブ (Job) としてまとめ、実行順序を決定する。
4. **Phase 4: Processing** (ジョブ分析・I/O計画) - ジョブごとの入出力要件、ループ構造を詳細分析する。
5. **Phase 5: Generation** (スクリプト生成) - 解析結果を元に、実行可能な Bash または Python スクリプトを生成する。
6. **Phase 6: Execution** (実行・結果報告) - 生成されたスクリプトを安全に実行し、結果を表示する。

## 主要コンセプト (Key Concepts)
1. **Affirmative Control (肯定説明)**: 全てのロール指示およびチートシートにおいて、肯定的な指示（「～せよ」「～を維持せよ」等）のみを用いる。
2. **Cache-Driven Execution**: 各フェーズの出力をハッシュに基づきキャッシュし、入力や設定に変更がない限り再実行をスキップする。
3. **Role-Based Reasoning**: 各フェーズは、特定の役割 (`roles/*.md`) を持ったエージェントが担当する。
4. **Framework-Driven Generation**: 生成されるコードは「生コード」ではなく、Bash または Python の「フレームワーク（糊）」に統合される。詳細は [bash_framework_design.md](./bash_framework_design.md) および [python_framework_design.md](./python_framework_design.md) を参照。
5. **Skill-Oriented Dispatching**: 実行可能な操作を「スキル」(`skills/skills.json`) として定義し、動的にプロンプトへ注入する。
6. **Knowledge Base (Cheatsheets)**: 各スキルの具体的なコード断片（ヒント）定義。

## コンポーネント構造
- `rys/main.bash`: 各フェーズを順次実行するオーケストレーター。キャッシュ管理とフェーズ制御を担当。
- `rys/phase*.py`: 各フェーズの実行ロジック。
- `roles/*.md`: 各エージェントのシステムプロンプト。
- `skills/*.json`: スキル、リスク管理、設定情報。
- `~/.cache/rys/`: フェーズ間の中間データ（JSON形式）。XDG Base Directory 規格に準拠。
