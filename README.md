# Recursive Yak Shaver (RYS)

**Recursive Yak Shaver (RYS)** is an autonomous multi-agent pipeline designed to transform ambiguous natural language instructions into safe, atomic, and executable shell operations. Powered by Gemma-3N, it handles translation, planning, implementation, and verification through a rigorous 6-phase process.

## 🚀 Key Architectural Pillars

- **Mono-Role Responsibility**: Each phase is governed by a single, specialized role (Engineer for planning, Coder for implementation) to ensure focused reasoning and prevent logic leakage.
- **Golden Pattern Adherence**: Standardized file operations follow a strict "Golden Pattern": `find` -> `du` -> `sort` -> `head` -> `cut` -> `cat`.
- **Atomic Command Fragments**: The system enforces "One Command per Step" logic. Snippets are treated as pure pipe segments, stripped of redundant prefixes or nested pipe chains.
- **Affirmative Control**: All role directives and cheatsheets use purely affirmative language ("Do this") to maximize LLM instruction-following and stability.

## 🛠 The 5-Phase Pipeline

### Phase 1: Translation (Translater)
Normalizes ambiguous, multi-lingual user input into clear, standardized English tasks.

### Phase 2: Dispatch (Dispatcher)
Categorizes tasks into specific domains and assigns the appropriate **Skill** (e.g., `shell_exec`, `python_math`).

### Phase 3: Strategic Planning (Planner & Titler)
Designs a structured roadmap using the **TOON (YAML) format**. The Planner maps the topic to atomic API-like operations based on the skill cheat sheet, ensuring "current directory" is correctly interpreted as `./`.

### Phase 4: Step-by-Step Coding (Coder)
Implements the roadmap milestones. The Coder generates atomic command fragments based on the skill cheatsheet patterns.

### Phase 5: Execution Loop
Aggregates snippets into a native shell or Python orchestrator and executes the sequence.

## 🕹 Usage & Phase Control (`--from`)

You can control the pipeline execution and caching behavior using the `--from` parameter.

| Command Pattern | Mode | Description |
| :--- | :--- | :--- |
| `./rys/main.bash "..."` | **Default** | Runs from Phase 4 to 6 (using caches for Phase 1-3 if available). |
| `--from=N` | **Resume** | Re-runs from Phase N to 6, clearing caches for Phase N and beyond. |
| `--from=N,M` | **Selective** | Runs only the specified phases (e.g., `3,3` to only re-run Planning). |
| `--from=,N` | **Cache-Only** | Runs from Phase 1 to N using **existing caches only** (no re-generation). |

### Examples:
- **Debug Planning**: `./rys/main.bash "..." --from=3,3` (Re-runs only Phase 3)
- **Review up to Code**: `./rys/main.bash "..." --from=,4` (Shows the plan and code using cached results, then stops)
- **Full Reset from Dispatch**: `./rys/main.bash "..." --from=2` (Re-generates everything starting from Phase 2)

## 📖 Skills & Cheatsheets

Skills are not just tool labels; they are the **Knowledge Anchors** of the system.
- **Planning**: In Phase 4, skills provide the Engineer with the "vocabulary" of available tools.
- **Implementation**: In Phase 5, skills provide the Coder with "best-practice patterns," forcing the model to mirror the exact syntax defined in `config/skills/*.json`.

## 🛡 Security & Reliability

- **Auditor Role**: Plans are checked against a Risk Knowledge Base before execution.
- **Granular Caching**: Every step is cached. Use `RYS_FORCE_CACHE=1` to debug specific milestones and verify granular logic without re-running stable phases.

## ⚖️ License
MIT License
