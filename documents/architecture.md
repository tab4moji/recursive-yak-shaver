# Recursive Yak Shaver: アーキテクチャ概要
# プロジェクト目的: 複雑なユーザー要求を分解し、スキルベースで実行可能なコードを生成・実行するエージェント・パイプライン。
# 更新履歴: 1.0 (2026-02-17)

## 概要
Recursive Yak Shaver (RYS) は、LLMを活用した「段階的分解・実行」型のパイプラインシステムである。
一度の推論で全てを解決しようとせず、複数のフェーズ (Phases) に分割することで、確実かつ安全なタスク実行を目指している。

## 主要コンセプト
1. **Pipeline Architecture**: 入力から実行までを 6 つのフェーズに分ける。
2. **Role-Based Reasoning**: 各フェーズは、特定の役割 (`roles/*.md`) を持ったエージェントが担当する。
3. **Skill-Oriented Dispatching**: 実行可能な操作を「スキル」(`config/skills.json`) として定義し、動的にプロンプトへ注入する。
4. **TOON (Token-Oriented Object Notation)**: トークン効率を重視した独自の構造化データ表現を用い、LLMとのやり取りを最適化する。

## コンポーネント構造
- `rys/main.bash`: 各フェーズを順次実行するオーケストレーター。
- `rys/phase*.py`: 各フェーズのロジック。
- `roles/*.md`: 各エージェントのシステムプロンプト。
- `config/*.json`: スキル、リスク管理、設定情報。
- `~/.cache/rys/`: フェーズ間のキャッシュ（JSON形式）。XDG Base Directory 規格に準拠。
