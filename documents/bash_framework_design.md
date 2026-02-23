# RYS Design Principle: Automated Bash Script Building Framework
# Goal: To define the architecture for automated script generation using a robust Bash framework and skill-based cheatsheets.
# History: 1.1 (2026-02-23)

## Overview
Recursive Yak Shaver (RYS) generates not just loose script snippets, but a structured and robust Bash script by embedding LLM-generated commands into a predefined "Code Framework." This ensures high reliability, consistent error handling, and standardized data binding between tasks.

## The Code Framework (The Glue)
The framework acts as the "glue" that connects multiple tasks into a single executable pipeline. It follows the pattern established in `tools/etude_test.bash`.

### Key Elements:
- **Setup & Safety**: Uses `set -euo pipefail` to stop on errors and unset variables. `shopt -s lastpipe` allows `mapfile` or `read` to modify variables in the current shell when used at the end of a pipeline.
- **Variable Standardization**:
    - `input`: The current scalar input (string or single path).
    - `script_output`: The result of the current task snippet.
    - `inputs`: An array containing multiple items (e.g., a list of files found by `find`).
- **Loop Architecture**: When Phase 4 identifies a task as a "loop" operation, Phase 5 wraps the snippet in a `for input in "${inputs[@]}"; do ... done` block.
- **Pipe-safe Capturing**:
    ```bash
    # For single results:
    command | read -r script_output
    # For multi-line or large results:
    command | read -r -d '' script_output || true
    ```

## Skill-Driven Construction (The Hints)
The construction of the script is driven by **Cheatsheets** (`skills/cheatsheets/*.json`).

### Mechanism:
1. **Pattern Matching**: Each cheatsheet provides "hints" (example commands) that use the `input`/`script_output` convention.
2. **Context Selection**: The LLM (Analyzer in Phase 4) identifies which pattern matches the intent and determines if the task is an "array-producer" (find) or "item-processor" (du).
3. **Automated Assembly**: Phase 5 (Generator) acts as a **Build Engine**. It assembles the final `.sh` file by:
    - Injecting the Boilerplate (Setup).
    - Wrapping Snippets in Loop/Binding code based on the I/O plan.
    - Finalizing with Result Display.

## Data Flow Diagram
```
[Phase 4: Plan] -> (Task ID, Skill, Hint Selection, I/O Mode)
                      |
                      v
[Phase 5: Build] -> [Setup Boilerplate]
                      |
                      +-- [Task 1 Snippet] -- (bind: input -> script_output)
                      |
                      +-- [Data Transfer] -- (input = script_output)
                      |
                      +-- [Loop Wrapper]
                      |     +-- [Task 2 Snippet]
                      |
                      +-- [Result Reporting]
```

## Implementation Strategy
- **Cheatsheet Enrichment**: Cheatsheets are the primary "Knowledge Base" for the Build Engine.
- **Snippet Purity**: LLM-generated snippets must not contain `set -e` or shell-specific setup; they are "plugins" for the framework.
- **Reliable Transitions**: Transitions between tasks (e.g., converting a multi-line string in `script_output` to an `inputs` array) are handled automatically by the framework.

---
This approach bridges the gap between flexible AI-generated logic and rigid, reliable shell script execution.
