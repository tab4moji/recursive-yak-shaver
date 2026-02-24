#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase Utilities (v1.3)
Common functions for RYS phase scripts.
"""

import os
import re
import subprocess
import argparse
import json
import sys
from typing import List, Optional, Any, Dict, Tuple
from invoke_role import invoke_role_api
from role_utils import format_as_toon
from chat_api import build_base_url, verify_connection
from chat_types import ChatConfig
from chat_ui import TerminalColors

# pylint: disable=useless-return

def get_common_parser(description: str) -> argparse.ArgumentParser:
    """Returns an ArgumentParser with common RYS phase options."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--in-json", help="Input JSON file path")
    parser.add_argument("--out-json", help="Output JSON file path")
    parser.add_argument("--host", default="localhost", help="LLM Host")
    parser.add_argument("--port", help="LLM Port")
    parser.add_argument("--model", default="gemma3n:e4b", help="LLM Model")
    parser.add_argument("--uuid", help="Session UUID")
    return parser


def init_llm_config(args: argparse.Namespace) -> Tuple[ChatConfig, TerminalColors]:
    """Initializes ChatConfig and TerminalColors based on common arguments."""
    base_url = build_base_url(args.host, args.port)
    verify_connection(base_url)
    config = ChatConfig(
        api_url=f"{base_url.rstrip('/')}/v1/chat/completions",
        model=args.model,
        quiet_mode=True,
        stream_output=True,
        insecure=False
    )
    colors = TerminalColors(enable_color=True)
    return config, colors


def load_phase_json(path: str) -> Dict[str, Any]:
    """Loads a JSON file with existence and error checks."""
    if not path or not os.path.exists(path):
        print(f">>> Error: Input file '{path}' not found.", file=sys.stderr)
        sys.exit(1)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f">>> Error loading '{path}': {e}", file=sys.stderr)
        sys.exit(1)


def resolve_refs(data: Any) -> Any:
    """Recursively replaces ref:Task<N>.<binding> with $<binding>."""
    result = data
    if isinstance(data, dict):
        result = {k: resolve_refs(v) for k, v in data.items()}
    elif isinstance(data, list):
        result = [resolve_refs(i) for i in data]
    elif isinstance(data, str):
        result = re.sub(r'ref:Task\d+\.([a-zA-Z_0-9]+)', r'$\1', data)
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


def invoke_coder(script_dir: str, prompt: str, skill: str, llm_config: Dict[str, Any], task: Dict[str, Any] = None) -> str:
    """Invokes the Coder role with strict hard-coded fallbacks and cheatsheet matching."""
    if task:
        title = task.get("title", "").lower()
        
        # Priority 1: Hard-coded robust snippets for shell_exec
        if skill == "shell_exec":
            if "largest" in title:
                return "echo \"${input}\" | xargs -d '\\n' du -b | sort -nr | head -n 1 | awk '{$1=\"\"; print substr($0,2)}'"
            if "smallest" in title:
                return "echo \"${input}\" | xargs -d '\\n' du -b | sort -n | head -n 1 | awk '{$1=\"\"; print substr($0,2)}'"
            if "python file" in title or "python ファイル" in title:
                return "find \"${input}\" -type f -name \"*.py\""
            if "current path" in title or "フルパス" in title:
                return "pwd"
            if "time" in title or "時間" in title:
                return "date '+%Y-%m-%d %H:%M:%S'"
            if "pylint" in title:
                return "pylint \"${input}\""
            if "cat" in title or "中身" in title or "content" in title:
                return "cat \"${input}\""

        # Priority 2: Cheatsheet matching for all skills
        cs_path = os.path.join(script_dir, "..", "skills", "cheatsheets", f"{skill}.json")
        if os.path.exists(cs_path):
            try:
                with open(cs_path, "r", encoding="utf-8") as f:
                    cs_data = json.load(f)
                
                # Priority 2.1: Exact task_name match
                for pattern in cs_data.get("patterns", []):
                    if pattern["task_name"].lower() == title:
                        return pattern["syntax"]
                
                # Priority 2.2: Title contains task_name
                for pattern in cs_data.get("patterns", []):
                    if pattern["task_name"].lower() in title:
                        return pattern["syntax"]
            except (json.JSONDecodeError, OSError):
                pass

    # Priority 3: LLM Call
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
        
        # Cleaning
        if snippet.endswith("`") and snippet.count("`") % 2 != 0:
            snippet = snippet[:-1].strip()
        if snippet.endswith("'") and snippet.count("'") % 2 != 0:
            snippet = snippet[:-1].strip()
        snippet = re.sub(r"\*\*(.*?)\*\*", r"\1", snippet)
        
        clean_lines = [l for l in snippet.splitlines()
                       if not (l.startswith("# Processing:") or l.startswith("# Output Type:"))]
        return "\n".join(clean_lines).strip()
    except Exception as exc:
        return f"# Error calling coder LLM: {exc}"


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
    return invoke_role_api(role, prompt, config, colors,
                           skills=kwargs.get("skills"),
                           include_skills=kwargs.get("include_skills", False),
                           risks=kwargs.get("risks"))


def parse_steps(text: str) -> List[str]:
    """Parses various step-list formats into individual steps."""
    steps = []
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
    return steps
