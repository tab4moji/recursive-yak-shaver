#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase Utilities (v1.3)
Common functions for RYS phase scripts.
1. 2026-02-17: Optimized call_role signature and fixed line lengths.
"""

import os
import re
import subprocess
from typing import List, Optional, Any, Dict
from invoke_role import invoke_role_api
from role_utils import format_as_toon

# pylint: disable=useless-return

def resolve_refs(data: Any) -> Any:
    """Recursively replaces ref:TOPIC<N>.<binding> with $<binding>."""
    result = data
    if isinstance(data, dict):
        result = {k: resolve_refs(v) for k, v in data.items()}
    elif isinstance(data, list):
        result = [resolve_refs(i) for i in data]
    elif isinstance(data, str):
        result = re.sub(r'ref:TOPIC\d+\.([a-zA-Z_0-9]+)', r'$\1', data)
    return result


def prepare_coder_prompt(topic: Dict[str, Any]) -> str:
    """Prepares a standardized prompt for the Coder role."""
    clean_in = resolve_refs(topic.get('input', ""))
    clean_out = resolve_refs(topic.get('output', ""))

    analysis_toon = format_as_toon("analysis", {"input": clean_in, "output": clean_out})
    task_title = topic.get('title', 'Generate code')
    prompt_suffix = ""

    input_val = clean_in
    if isinstance(clean_in, dict) and "value" in clean_in:
        input_val = clean_in["value"]

    if isinstance(input_val, str) and input_val.startswith('$'):
        task_title = f"Perform action on {input_val} for: {task_title}"
        prompt_suffix = f"\n### TIP\nUse the variable {input_val} directly.\n"
    elif isinstance(clean_in, dict) and "value" in clean_in:
        val = clean_in["value"]
        if isinstance(val, dict):
            if "min" in val and "max" in val:
                prompt_suffix = f"\n### INSTRUCTION\nUse range({val['min']}, {val['max']}+1).\n"
            else:
                v_str = ", ".join([f"{k}={v}" for k, v in val.items()])
                prompt_suffix = f"\n### TIP\nEmbed literal values directly: {v_str}\n"

    prompt = f"### TASK\n{task_title}\n\n### ANALYSIS\n{analysis_toon}\n{prompt_suffix}"
    return prompt


def invoke_coder(script_dir: str, prompt: str, skill: str, llm_config: Dict[str, Any]) -> str:
    """Invokes the Coder role and extracts the code snippet."""
    snippet = ""
    host = llm_config.get("host", "localhost")
    port = llm_config.get("port")
    model = llm_config.get("model", "gemma3n:e4b")

    cmd = [
        "python3", os.path.join(script_dir, "invoke_role.py"),
        "--role=coder", f"--prompt={prompt}", f"--skills={skill}",
        f"--host={host}", f"--model={model}", "--no-stream"
    ]
    if port:
        cmd.append(f"--port={port}")

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        out = res.stdout.strip()
        code_match = re.search(r"```(?:\w+)?\s*\n?(.*?)\n?```", out, re.DOTALL)
        snippet = code_match.group(1).strip() if code_match else out.strip()
        if not code_match and out and ("Error" in out or "Connection" in out):
            snippet = f"# Error: {out[:100]}..."

        clean_lines = [l for l in snippet.splitlines()
                       if not (l.startswith("# Processing:") or l.startswith("# Output Type:"))]
        snippet = "\n".join(clean_lines).strip()
    except Exception as exc: # pylint: disable=broad-exception-caught
        snippet = f"# Error calling coder LLM: {exc}"

    return snippet


def append_result_display(lines: List[str], req_id: str, binding: Optional[str]):
    """Appends a result display section to script lines."""
    if binding:
        lines.append("# --- Final Result Display ---")
        lines.append('echo ""')
        lines.append(f'echo "[RESULT: {req_id}]"')
        lines.append(f'echo "${binding}"')
        lines.append('echo ""')
    return


def call_role(script_dir: str, role: str, prompt: str, config: Any, colors: Any, **kwargs) -> str:
    """Invokes a specific role through the centralized invoke_role_api."""
    # pylint: disable=unused-argument
    return invoke_role_api(role, prompt, config, colors,
                           skills=kwargs.get("skills"),
                           include_skills=kwargs.get("include_skills", False),
                           risks=kwargs.get("risks"))


def parse_steps(text: str) -> List[str]:
    """Parses various step-list formats into individual steps."""
    steps = []
    # Matches: "1. text", "- Step 1: text", "Milestone 1: text", etc.
    reg_str = r"^(?:[\-\*\s]*)(?:(?:Step|Milestone)\s+)?(\d+)[\.\:]?\s*(.*)"
    pattern = re.compile(reg_str, re.IGNORECASE)
    seen_descriptions = set()
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if match:
            desc = match.group(2).strip()
            if desc and desc not in seen_descriptions:
                steps.append(desc)
                seen_descriptions.add(desc)
        if len(steps) >= 20:
            break
    return steps
