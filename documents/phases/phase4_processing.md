# Phase 4: Job Processing (Detailed Analysis)
# Goal: To explain the job processing phase of the RYS pipeline.
# History: 1.1 (2026-02-23)

## Objective
The **Job Processing Phase** (also known as the Request Loop) performs a deep analysis of each job. It defines the specific inputs and outputs for each task within the job, creating a concrete execution plan for the Build Phase in Phase 5.

## Key Components
- **Script**: `rys/phase4_request_loop.py`
- **LLM Role**: `analyzer` (Role defined in `roles/role_analyzer.md`)
- **Input**: Grouped jobs from Phase 3.
- **Output**: JSON file with detailed I/O specifications and **Cheatsheet Hints**.

## Detailed Steps
- **Phase 4-A: LLM Analysis**: The `analyzer` role examines each task to determine the detailed I/O plan.
    - **Context Injection**: The analyzer receives rich metadata from the cheatsheets (Task, Description, Input Arguments, Output Details), but the actual implementation `syntax` is excluded to avoid premature code generation.
    - **TOON Flattening**: Input arguments defined as arrays in the JSON schema are flattened into a `name(description:type)` format within the TOON prompt for maximum LLM readability.
    - It determines what specific input it needs (e.g., a URL, a search query).
    - It defines what output it will produce.
    - It specifies how that output should be bound to a variable for subsequent tasks.
- **Phase 4-B: Cheatsheet Hint Selection**: The `analyzer` scans the `skills/cheatsheets/*.json` to find the most relevant "pattern" for each task. It identifies:
    - Is the task a scalar-to-scalar (Item) or a scalar-to-array (Collection) operation?
    - Does it require a loop in Phase 5?
- **Phase 4-C: Information Integration**: The analysis results are merged with the raw data from previous phases to create an "integrated job" package.

## Data Structure: TOON
The analyzer produces output in a structured format (TOON: Task Output-Object Notation) that explicitly defines:
- **ID**: Unique task ID.
- **Input**: Arguments or data needed.
- **Output**: Result format and binding names.
- **Pattern Hint**: The ID of the selected pattern from the cheatsheet.

## Importance
This phase fills the gap between "what to do" and "how to code it" by providing a precise specification that the Build Engine (Phase 5) can follow to assemble the final script using the Bash framework.

---
See [bash_framework_design.md](../bash_framework_design.md) for more details on the automated construction.
