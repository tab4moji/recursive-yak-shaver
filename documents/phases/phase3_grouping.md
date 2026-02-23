# Phase 3: Grouping (Job Planning)
# Goal: To explain the grouping phase of the RYS pipeline.
# History: 1.0 (2026-02-23)

## Objective
The **Grouping Phase** (also known as the Planning Phase) organizes the atomic tasks identified in Phase 2 into executable units called **Jobs**. It also determines the order of execution based on dependencies.

## Key Components
- **Script**: `rys/phase3_group.py` (which calls `rys/group_jobs.py`)
- **LLM Role**: `planner` or `grouper` (depending on implementation, often uses the `planner` role)
- **Input**: List of tasks and skills from Phase 2.
- **Output**: JSON file with grouped jobs and a dependency-sorted execution plan.

## Operation
1. Tasks that share the same skill and are logically related are grouped together into a single "Job."
2. The planner identifies if a task depends on the output of another task (e.g., "Find the price" before "Calculate the total").
3. The jobs are ordered such that all dependencies are met before execution.
4. The final plan is saved as a JSON structure (e.g., `.cache.p3.[hash].json`).

## Importance
Without this phase, the system might try to execute tasks out of order or handle related tasks inefficiently. Grouping ensures a logical flow of information between tasks.
