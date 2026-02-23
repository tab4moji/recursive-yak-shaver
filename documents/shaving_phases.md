# Recursive Yak Shaver (RYS) Pipeline: Shaving Phases
# Goal: To explain the 6 key phases of the RYS task execution pipeline.
# History: 1.0 (2026-02-23)

## Overview
The Recursive Yak Shaver (RYS) operates through a 6-phase pipeline, transforming a natural language user prompt into executable scripts and their final results. Each phase is controlled by `rys/main.bash` and uses specific Python scripts and LLM roles.

| Phase | Name | Description | Role / Script |
| :--- | :--- | :--- | :--- |
| **Phase 1** | [Translation](./phases/phase1_translation.md) | Translates and normalizes user prompt. | `translater` / `phase1_translate.py` |
| **Phase 2** | [Dispatch](./phases/phase2_dispatch.md) | Breaks prompt into atomic tasks (topics) and assigns skills. | `dispatcher` / `phase2_dispatch.py` |
| **Phase 3** | [Grouping](./phases/phase3_grouping.md) | Groups topics into executable requests and sorts by dependency. | `grouper` / `phase3_group.py` |
| **Phase 4** | [Processing](./phases/phase4_processing.md) | Analyzes detailed I/O requirements for each request. | `analyzer` / `phase4_request_loop.py` |
| **Phase 5** | [Generation](./phases/phase5_generation.md) | Generates executable bash scripts for each topic using code snippets. | `coder` / `phase5_generate.py` |
| **Phase 6** | [Execution](./phases/phase6_execution.md) | Safely executes the generated scripts and reports results. | `phase6_execute.py` |

## Pipeline Flow
1. **Input**: User prompt (e.g., "What's the weather in Tokyo and tell me a joke about it.")
2. **Phase 1-2**: Normalization and atomic task identification.
3. **Phase 3-4**: Strategic planning and detailed input/output mapping.
4. **Phase 5**: Code generation tailored for each task.
5. **Phase 6**: Execution and result presentation.

---
See the detailed documentation for each phase linked above.
