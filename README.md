# Recursive Yak Shaver (RYS)

**Recursive Yak Shaver (RYS)** is an autonomous multi-agent pipeline designed to transform ambiguous natural language instructions into safe, atomic, and executable shell operations. Powered by Gemma-3N, it handles translation, planning, implementation, and verification through a rigorous 6-phase process.

## 🚀 Key Architectural Pillars

- **Mono-Role Responsibility**: Each phase is governed by a single, specialized role (Engineer for planning, Coder for implementation) to ensure focused reasoning and prevent logic leakage.
- **Discovery-Action Pairing**: Complex tasks are split into "Discovery" (Locating target) and "Action" (Executing operation) milestones to ensure reliability.
- **Affirmative Control**: All role directives and cheatsheets use purely affirmative language ("Do this") to maximize LLM instruction-following and stability.
- **MANDATORY HEREDOC**: Every Python execution is wrapped in a heredoc (`python3 << 'EOF'`) to prevent syntax errors and quote escaping issues.

## 🕹 Usage & Phase Control (`--from`)

You can control the pipeline execution and caching behavior using the `--from` parameter. **By default, RYS prioritizes cache for stable early phases (1-3).**

| Command Pattern | Mode | Description |
| :--- | :--- | :--- |
| `./rys/main.bash "..."` | **Default** | Runs from Phase 4 to 6 (uses caches for Phase 1-3 if available). Equivalent to `--from=4,6`. |
| `--from=N` | **Resume** | Re-runs from Phase N to 6, clearing caches for Phase N and beyond. |
| `--from=5,6` | **Implementation** | **Recommended.** Re-runs only Coding and Execution using the existing strategic plan (Phase 4). |
| `--from=,N` | **Cache-Only** | Runs from Phase 1 to N using **existing caches only** (no re-generation). |

### Examples:
- **Default Run**: `./rys/main.bash "Find prime numbers" --auto`
- **Re-generate Code**: `./rys/main.bash "..." --from=5,6 --auto` (Fixes implementation issues without changing the plan)
- **Full Reset**: `./rys/main.bash "..." --from=1 --auto` (Clears all caches and starts over)

## 🛠 The 6-Phase Pipeline

1. **Translation**: Normalizes ambiguous input into standardized English tasks.
2. **Dispatch**: Categorizes tasks and assigns the appropriate **Skill**.
3. **Grouping**: Intelligently groups related tasks into executable requests.
4. **Strategic Planning (Architect)**: Designs a roadmap. Splits file operations into Discovery and Action steps.
5. **Step-by-Step Coding (Coder)**: Implements the roadmap. **Strictly uses provided variables** and avoids re-calculation.
6. **Execution**: Aggregates and executes the generated shell scripts.

## 🛡 Development Directives (The Coder Rules)

To maintain stability, the following rules are enforced during Phase 5:
- **NO RE-CALCULATION**: If a variable `$path` is provided as input, it MUST be used directly. Never run `find` again.
- **STRICT BINDING**: Results MUST be assigned to the variable name defined in the plan (e.g., `content=$(...)`).
- **SELF-CONTAINED PYTHON**: Every Python block must include all necessary `import` and function definitions.

## ⚖️ License
MIT License
