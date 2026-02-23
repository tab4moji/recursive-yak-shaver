# Phase 4: REQUEST Processing (Detailed Analysis)
# Goal: To explain the request processing phase of the RYS pipeline.
# History: 1.0 (2026-02-23)

## Objective
The **REQUEST Processing Phase** performs a deep analysis of each request. It defines the specific inputs and outputs for each topic within the request, creating a concrete execution plan for the coder role in Phase 5.

## Key Components
- **Script**: `rys/phase4_request_loop.py`
- **LLM Role**: `analyzer` (Role defined in `roles/role_analyzer.md`)
- **Input**: Grouped requests from Phase 3.
- **Output**: JSON file with detailed I/O specifications (inputs, outputs, and variable bindings).

## Detailed Steps
- **Phase 4-A: LLM Analysis**: The `analyzer` role examines each topic to determine:
    - What specific input it needs (e.g., a URL, a search query).
    - What output it will produce.
    - How that output should be bound to a variable for subsequent topics.
- **Phase 4-B: Information Integration**: The analysis results are merged with the raw data from previous phases to create an "integrated request" package.

## Data Structure: TOON
The analyzer often produces output in a structured format (TOON: Topic Output-Object Notation) that explicitly defines:
- **ID**: Unique topic ID.
- **Input**: Arguments or data needed.
- **Output**: Result format and binding names.

## Importance
This phase fills the gap between "what to do" and "how to code it" by providing a precise specification that the code generator can follow.
