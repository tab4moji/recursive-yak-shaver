# Recursive Yak Shaver (RYS) Pipeline: Shaving Phases
# 概要: RYS タスク実行パイプラインの 6 つのフェーズ解説。
# 更新履歴: 1.1 (2026-02-24)

## Overview
The Recursive Yak Shaver (RYS) は、ユーザーの自然言語プロンプトを実行可能なスクリプトと最終結果に変換する 6 フェーズのパイプラインで構成されている。

| Phase | 名称 | 説明 | 担当スクリプト / ロール |
| :--- | :--- | :--- | :--- |
| **Phase 1** | [Translation](./phases/phase1_translation.md) | プロンプトの翻訳と正規化。 | `phase1_translate.py` / `translater` |
| **Phase 2** | [Dispatch](./phases/phase2_dispatch.md) | 最小単位のタスク (Task) への分解。 | `phase2_dispatch.py` / `dispatcher` |
| **Phase 3** | [Grouping](./phases/phase3_grouping.md) | スキルごとのジョブ (Job) の統合。 | `phase3_group.py` / `grouper` |
| **Phase 4** | [Processing](./phases/phase4_processing.md) | 詳細な I/O 型、ループ構造の計画。 | `phase4_request_loop.py` / `analyzer` |
| **Phase 5** | [Generation](./phases/phase5_generation.md) | フレームワーク設計に基づくコード生成。 | `phase5_generate.py` / `coder` |
| **Phase 6** | [Execution](./phases/phase6_execution.md) | 生成されたスクリプトの実行と報告。 | `phase6_execute.py` / `(Shell/Python)` |

## パイプライン・フロー
1. **入力 (Input)**: 自然言語プロンプト (例: "今の時間を調べて")
2. **分析 (P1-P2)**: プロンプトの翻訳、およびスキル割り当てを伴うタスク分解。
3. **戦略 (P3-P4)**: ジョブ単位への統合と、具体的な I/O マッピング、チートシートからの「ヒント」選択。
4. **構築 (P5)**: 言語（Bash または Python）に応じた「フレームワーク」へのコード片の統合。
5. **完了 (P6)**: 安全な環境での実行と結果表示。

---
各フェーズの詳細ドキュメントは、上記のリンクを参照。
各フェーズの技術仕様は [data_flow.md](../data_flow.md) にて詳説されている。
