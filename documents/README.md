# Recursive Yak Shaver (RYS) ドキュメント
# 概要: RYS プロジェクトの全体設計、コード生成フレームワーク、各フェーズの技術仕様。
# 更新履歴: 1.0 (2026-02-24) 新規作成

## ドキュメント構成 (Index)
RYS プロジェクトの設計と運用に関する情報は、以下のドキュメントに分割されている。

### 1. 全体設計 (Master Design)
- **[architecture.md](./architecture.md)**: システム全体のアーキテクチャ、6 フェーズ・パイプライン、主要コンセプトの概要。
- **[shaving_phases.md](./shaving_phases.md)**: 翻訳から実行までの 6 つのフェーズの解説。
- **[data_flow.md](./data_flow.md)**: キャッシュ機構（XDG）と各フェーズ間のデータ受け渡し。
- **[roles_and_skills.md](./roles_and_skills.md)**: ロール（エージェント）の役割、スキル定義、TOON 形式。

### 2. コード生成フレームワーク (Framework Design)
- **[bash_framework_design.md](./bash_framework_design.md)**: Bash スクリプト自動生成の「糊（Glue）」となる設計指針。
- **[python_framework_design.md](./python_framework_design.md)**: Python スクリプト自動生成の「糊（Glue）」となる設計指針。

### 3. フェーズ詳細 (Phase Details)
各フェーズの入出力、使用するロール、スクリプトの技術仕様。
- [Phase 1: Translation](./phases/phase1_translation.md)
- [Phase 2: Dispatch](./phases/phase2_dispatch.md)
- [Phase 3: Grouping](./phases/phase3_grouping.md)
- [Phase 4: Processing](./phases/phase4_processing.md)
- [Phase 5: Generation](./phases/phase5_generation.md)
- [Phase 6: Execution](./phases/phase6_execution.md)

---
これらのドキュメントは、LLM が生成する不安定なコードを「安全で堅牢なフレームワーク」へ統合するための、プロジェクトの「憲法」である。
各ファイルは 6KiB 以内のサイズを維持し、常に最新の実装状況を反映する。
