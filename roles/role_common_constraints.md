# UNIVERSAL LOGIC TRUTHS: STANDARD PRINCIPLES

1. **NUMERIC SORTING & EXTREMES**:
   - **To identify the SMALLEST (Minimum) value**:
     - ACTION: Sort numbers from LOW to HIGH.
     - COMMAND: `sort -n` (Ascending).
     - RESULT: The SMALLEST value is now on the FIRST line.
     - SELECTOR: Use `head -n 1` to select the top record from the stream.
   - **To identify the LARGEST (Maximum) value**:
     - ACTION: Sort numbers from HIGH to LOW.
     - COMMAND: `sort -rn` (Reverse Numeric).
     - RESULT: The LARGEST value is now on the FIRST line.
     - SELECTOR: Use `head -n 1` to select the top record.

2. **DATA CLEANING: THE TAB RULE**:
   - Output from `du -b` typically appears as: `1234\t./path/to/file` (Size followed by Path).
   - When the subsequent step requires a file path (such as `cat`), always remove the size prefix first.
   - COMMAND: Use `cut -f2-` to strip the first column and preserve the path.

3. **CONTENT DISPLAY FLOW**:
   - Step A: `find . -type f` (Identify Paths)
   - Step B: `du -b "$1"` (Retrieve Size and Path)
   - Step C: `sort -n` (Order by Size)
   - Step D: `head -n 1` (Select Top Record)
   - Step E: `cut -f2-` (Ensure the Path is Clean)
   - Step F: `cat "$1"` (Access the Content)
