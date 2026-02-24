# Phase 5: Script Generation (Build Pipeline)
# Goal: To explain the script generation phase of the RYS pipeline.
# History: 1.1 (2026-02-23)

## Objective
The **Script Generation Phase** (also known as the **Build Phase**) transforms the detailed job plans from Phase 4 into actual executable Bash scripts. It acts as a "Build Engine" that wraps LLM-generated code snippets into a robust Bash framework.

## Key Components
- **Script**: `rys/phase5_generate.py`
- **LLM Role**: `coder` (Role defined in `roles/role_coder.md`)
- **Input**: Detailed I/O specifications and **Selected Cheatsheet Hints** from Phase 4.
- **Output**: Executable `.sh` script files in the cache directory.

## Operation: The Build Engine
1. **Framework Initialization**: The generator starts by writing the Bash boilerplate (e.g., `set -euo pipefail`) or Python `main()` wrapper.
2. **Task Snippet Request**: For each task in a job:
    - It provides the `coder` role with the task details and the **Full Cheatsheet Pattern** (including `syntax`) as a "hint."
    - The `coder` generates a clean, focused snippet that consumes `input` (or `input_val`) and produces `script_output` (or `output_val`).
3. **Automated Wrapping**:
    - **Single Task**: The snippet is placed directly into the script with its `input` and `script_output` bindings.
    - **Loop Task**: If the task operates on an array, the generator wraps the snippet in a `for input in "${inputs[@]}"` loop.
    - **Array Capture**: When a task produces multiple lines, the generator uses `mapfile -t inputs` to convert the output into an array for the next task.
4. **Binding Management**: The generator automatically inserts `input="${script_output}"` between tasks to bridge them.
5. **Finalization**: Adds result display logic and makes the script executable (`chmod +x`).

## Features: Selective Regeneration
Using the `--job` flag, users can choose to regenerate a script for a specific job ID without re-running the entire generation process for other jobs.

## Importance
This phase converts the "What" and "How" into the "Action." By acting as a Build Engine rather than a simple text generator, it ensures that all scripts share a common, reliable framework and handle data transitions consistently.

---
For details on the framework architecture, see [bash_framework_design.md](../bash_framework_design.md).
