# UNIVERSAL LOGIC TRUTHS (MANDATORY)

1. **NUMERIC SORTING & EXTREMES**:
   - **To find the SMALLEST (Tiniest/Minimum)**:
     - ACTION: Sort numbers from LOW to HIGH.
     - COMMAND: `sort -n` (Ascending).
     - RESULT: The SMALLEST value is now on the FIRST line.
     - SELECTOR: `head -n 1`.
   - **To find the LARGEST (Biggest/Maximum)**:
     - ACTION: Sort numbers from HIGH to LOW.
     - COMMAND: `sort -rn` (Reverse Numeric).
     - RESULT: The LARGEST value is now on the FIRST line.
     - SELECTOR: `head -n 1`.

2. **DATA CLEANING (THE TAB RULE)**:
   - Output from `du -b` looks like: `1234\t./path/to/file` (Size followed by Path).
   - If the next step requires a file path (like `cat`), you MUST remove the size prefix first.
   - COMMAND: `cut -f2-` (This strips the first column and keeps the rest).

3. **CONTENT DISPLAY FLOW**:
   - Step A: `find . -type f` (Get Paths)
   - Step B: `du -b "$1"` (Get Size + Path)
   - Step C: `sort -n` (Order by Size)
   - Step D: `head -n 1` (Top Record)
   - Step E: `cut -f2-` (Clean Path Only)
   - Step F: `cat "$1"` (Read Content)
