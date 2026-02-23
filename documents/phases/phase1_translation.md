# Phase 1: Translation (Normalization)
# Goal: To explain the translation phase of the RYS pipeline.
# History: 1.0 (2026-02-23)

## Objective
The **Translation Phase** is the entry point of the pipeline. It reads the raw user prompt and normalizes it into a standard format (often English) that the subsequent phases can easily process.

## Key Components
- **Script**: `rys/phase1_translate.py`
- **LLM Role**: `translater` (Role defined in `roles/role_translater.md`)
- **Input**: Raw user prompt (stdin or command-line argument)
- **Output**: JSON file containing the normalized (translated) text.

## Operation
1. The script calls the `translater` role, providing the raw prompt.
2. The LLM processes the prompt to create a normalized version, removing ambiguity and converting it to a standard language.
3. The result is saved to a JSON file in the cache directory (e.g., `.cache.p1.[hash].json`).

## Why it's needed
Normalizing the input ensures that the `dispatcher` role (Phase 2) can consistently identify tasks regardless of the original language or style of the user prompt.
