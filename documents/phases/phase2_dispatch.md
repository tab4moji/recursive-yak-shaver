# Phase 2: Dispatch (Task Decomposition)
# Goal: To explain the dispatch phase of the RYS pipeline.
# History: 1.0 (2026-02-23)

## Objective
The **Dispatch Phase** breaks down the normalized prompt into "atomic tasks" called **Topics**. Each topic is assigned a **Skill** (e.g., `web_access`, `shell_exec`, `python_math`) that will be used to handle it.

## Key Components
- **Script**: `rys/phase2_dispatch.py`
- **LLM Role**: `dispatcher` (Role defined in `roles/role_dispatcher.md`)
- **Input**: Normalized text from Phase 1.
- **Output**: JSON file mapping topics to skills.

## Features: Embedding Cache
This phase includes an **Embedding Cache** mechanism.
1. It calculates the embedding vector of the input prompt.
2. It compares it against previously successful dispatch results (stored in `tmp/`).
3. If a high similarity (determined by `--similarity`) is found, it reuses the previous dispatch result, saving time and API costs.

## Operation
1. The script first checks the cache if `--similarity > 0`.
2. If no cache hit, it calls the `dispatcher` role with a list of available skills.
3. The LLM decomposes the prompt into discrete tasks and identifies which skill is best suited for each task.
4. The result is saved to a JSON file in the cache directory.

## Importance
This phase acts as a router, deciding *what* needs to be done and *how* (which skill) it should be executed.
