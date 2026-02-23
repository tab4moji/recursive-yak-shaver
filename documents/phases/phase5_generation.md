# Phase 5: Script Generation (Coding)
# Goal: To explain the script generation phase of the RYS pipeline.
# History: 1.0 (2026-02-23)

## Objective
The **Script Generation Phase** transforms the detailed job plans from Phase 4 into actual executable Bash scripts. It uses an LLM specialized in coding to write small, focused snippets for each task.

## Key Components
- **Script**: `rys/phase5_generate.py`
- **LLM Role**: `coder` (Role defined in `roles/role_coder.md`)
- **Input**: Detailed I/O specifications from Phase 4.
- **Output**: Executable `.sh` script files in the cache directory.

## Operation
1. For each task in a job, the script prepares a prompt for the `coder` role based on its skill and I/O plan.
2. The `coder` generates a bash script snippet that performs the task and handles its inputs/outputs.
3. These snippets are assembled into a single bash script for the job.
4. The script includes logic to display final results if a binding is specified.
5. Files are saved (e.g., `.rys.[uuid].[job_id].sh`) and marked as executable.

## Features: Selective Regeneration
Using the `--job` flag, users can choose to regenerate a script for a specific job ID without re-running the entire generation process for other jobs.

## Importance
This is where the actual logic to perform the task is created. By breaking it into tasks and jobs, the coder can focus on simple, robust snippets.
