# RYS Design Principle: Automated Python Script Building Framework
# Goal: To define the architecture for automated Python script generation using a robust framework and skill-based cheatsheets.
# History: 1.0 (2026-02-24)

## Overview
Recursive Yak Shaver (RYS) provides a "Python Code Framework" to ensure that LLM-generated Python snippets are integrated into a reliable, maintainable, and standardized execution environment. This mirrors the Bash framework but leverages Python's strengths in structured data handling and exception management.

## The Code Framework (The Glue)
The framework acts as the "harness" for snippets. It follows the project's global coding standards.

### Key Elements:
- **Setup & Safety**:
    - Standard header: `#!/usr/bin/env python3`, encoding declaration.
    - Imports: Automatically includes `sys`, `os`, and `json` as base utilities.
    - Error Output: All error messages must be directed to `sys.stderr`.
- **Variable Standardization**:
    - `input_val`: The current scalar input (string, int, or object).
    - `output_val`: The result of the current task snippet.
    - `input_list`: A list containing multiple items for loop operations.
- **Control Flow Architecture**:
    - **Single Return Rule**: Functions within the framework must have only one `return` statement at the very end.
    - **Exception-Based Logic**: Uses `try-except-finally` blocks for error handling instead of early returns or guard clauses.
- **Loop Architecture**: When a task is identified as an "array-producer" or "loop-processor", the framework wraps the snippet in:
    ```python
    output_val = []
    for input_val in input_list:
        # Snippet Start
        ...
        output_val.append(item_result)
        # Snippet End
    ```

## Skill-Driven Construction (Python Hints)
The construction is driven by Python-specific Cheatsheets (`skills/cheatsheets/python_*.json`).

### Mechanism:
1. **Context Mapping**: The LLM identifies the appropriate Python "hint" that matches the task intent.
2. **Variable Binding**: The Generator ensures that the output of Task N (stored in `output_val`) is correctly assigned to the input of Task N+1 (as `input_val`).
3. **Snippet Purity**: Snippets remain focused on logic; they do not include imports or boilerplate, as the Build Engine provides these.

## Implementation Strategy (Global Context Compliance)
- **Error Handling**:
    ```python
    def execute_task(input_val):
        result = None
        try:
            # LLM Snippet logic here
            result = processed_data
        except Exception as e:
            sys.stderr.write(f"Error: {str(e)}
")
            raise
        return result
    ```
- **PEP 8**: All generated code must adhere to PEP 8 naming and formatting conventions.
- **File Size**: Generated scripts are kept modular to respect the 6KiB limit where possible.

## Data Flow Diagram
```
[Phase 4: Plan] -> (Python Task, Skill, I/O Mode)
                      |
                      v
[Phase 5: Build] -> [Python Boilerplate & Imports]
                      |
                      +-- [Task 1: Setup input_val]
                      |
                      +-- [Task 2: Snippet Integration] -- (bind: input_val -> output_val)
                      |
                      +-- [Task 3: List Processing]
                      |     +-- [Exception/Error Wrapper]
                      |
                      +-- [Result Output (JSON/Stdout)]
```

---
This framework ensures that AI-generated Python code is not just "loose code" but part of a predictable and robust execution pipeline.
