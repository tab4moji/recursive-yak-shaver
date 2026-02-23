# Phase 6: Execution (Result Delivery)
# Goal: To explain the execution phase of the RYS pipeline.
# History: 1.0 (2026-02-23)

## Objective
The **Execution Phase** is the final step where the generated bash scripts are actually run. It handles the safe execution of the scripts and displays the results to the user.

## Key Components
- **Script**: `rys/phase6_execute.py`
- **Input**: List of generated scripts from Phase 5.
- **Output**: Final results of the tasks (printed to terminal or saved to files).

## Operation
1. The script reads the generation results from the Phase 5 output JSON.
2. It iterates through the list of generated script paths.
3. For each script:
    - It displays the script content to the user (unless `--auto` is used).
    - It asks for confirmation: `Execute? [y/N]`.
    - If confirmed, it executes the script using `subprocess.run`.
4. The script also handles path correction if it's running in a different environment than where the cache was created.

## Safety and Control
By default, this phase requires human interaction to confirm each execution. The `--auto` flag can bypass this for automated workflows.

## Importance
This phase bridges the gap between the virtual planning/coding and the real-world impact of the task. It provides a final checkpoint for the user to review the generated code before it runs.
