#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5: Script Generation (v2.10)
Generates bash scripts for requests based on the I/O plan in TOON format.
Supports partial regeneration via --request=ID.
"""

import sys
import os
import json
import argparse
import subprocess
import re

# Add project root to path for role_utils
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

from role_utils import format_as_toon

def resolve_refs(data):
    """Recursively replaces ref:TOPIC<N>.<binding> with $<binding>."""
    if isinstance(data, dict):
        return {k: resolve_refs(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_refs(i) for i in data]
    elif isinstance(data, str):
        return re.sub(r'ref:TOPIC\d+\.([a-zA-Z_0-9]+)', r'$\1', data)
    return data

def call_coder(topic, skill, host, port, model):
    """Calls the Coder role to get a code snippet."""
    clean_input = resolve_refs(topic['input'])
    clean_output = resolve_refs(topic['output'])
    
    analysis_toon = format_as_toon("analysis", {
        "input": clean_input,
        "output": clean_output
    })
    
    # Inject affirmative hint into the task description
    task_title = topic['title']
    prompt_suffix = ""
    
    # Extract the actual value string for checking
    input_val = ""
    if isinstance(clean_input, str):
        input_val = clean_input
    elif isinstance(clean_input, dict) and "value" in clean_input:
        input_val = clean_input["value"]

    if isinstance(input_val, str) and input_val.startswith('$'):
        task_title = f"Perform action on {input_val} for: {task_title}"
        prompt_suffix = f"\n### TIP\nUse the variable {input_val} directly to complete this action in a single command.\n"
    elif isinstance(clean_input, dict) and "value" in clean_input:
        val = clean_input["value"]
        if isinstance(val, dict):
            # Map input case (e.g., min/max)
            val_str = ", ".join([f"{k}={v}" for k, v in val.items()])
            if "min" in val and "max" in val:
                prompt_suffix = f"\n### INSTRUCTION\nUse range({val['min']}, {val['max']}+1) for this task.\n"
            else:
                prompt_suffix = f"\n### TIP\nEmbed these literal values directly: {val_str}\n"

    prompt = f"### TASK\n{task_title}\n\n"
    prompt += f"### ANALYSIS\n{analysis_toon}\n"
    prompt += prompt_suffix
    
    cmd = [
        "python3", os.path.join(SCRIPT_DIR, "invoke_role.py"),
        "--role=coder",
        f"--prompt={prompt}",
        f"--skills={skill}",
        f"--host={host}",
        f"--model={model}",
        "--no-stream"
    ]
    if port: cmd.append(f"--port={port}")
        
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        out = result.stdout.strip()
        code_match = re.search(r"```(?:\w+)?\s*\n?(.*?)\n?```", out, re.DOTALL)
        snippet = code_match.group(1).strip() if code_match else out.strip()
        
        clean_lines = [l for l in snippet.splitlines() if not (l.startswith("# Processing:") or l.startswith("# Output Type:"))]
        return "\n".join(clean_lines).strip()
    except Exception as e:
        return f"# Error calling coder LLM: {e}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-json", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--uuid", required=True)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port")
    parser.add_argument("--model", default="gemma3n:e4b")
    parser.add_argument("--request", help="Specific Request ID to regenerate")
    args = parser.parse_args()
    
    if not os.path.exists(args.in_json): sys.exit(1)
    with open(args.in_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load existing P5 data if it exists to preserve other scripts
    existing_scripts = {}
    if os.path.exists(args.out_json):
        try:
            with open(args.out_json, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                for s in old_data.get("generated_scripts", []):
                    existing_scripts[s["request_id"]] = s
        except: pass

    integrated_requests = data.get("integrated_requests", [])
    script_list = []

    print(f">>> Phase 5: Generating Scripts (Session: {args.uuid})")

    for req in integrated_requests:
        req_id = req["request_id"]
        skill = req["skill"]
        if skill == "IDONTKNOW": continue

        # Skip if filter is set and doesn't match
        if args.request and req_id != args.request:
            if req_id in existing_scripts:
                print(f"Skipping {req_id} (Keeping existing script)")
                script_list.append(existing_scripts[req_id])
                continue
            else:
                print(f"Skipping {req_id} (No existing script to keep)")
                continue

        print(f"Handling {req_id} ({skill})...")
        script_lines = ["#!/bin/bash", "# Generated by RYS Phase 5", ""]
        final_binding = None

        for topic in req["topics"]:
            print(f"  Coding {topic['id']}...")
            snippet = call_coder(topic, skill, args.host, args.port, args.model)
            script_lines.append(f"# --- {topic['id']}: {topic['title']} ---")
            script_lines.append(snippet)
            script_lines.append("")
            if topic.get('output', {}).get('binding'):
                final_binding = topic['output']['binding']

        if final_binding:
            script_lines.append(f"# --- Final Result Display ---\necho \"\"\necho \"[RESULT: {req_id}]\"\necho \"${final_binding}\"\necho \"\"\n")

        script_path = f"./tmp/.rys.{args.uuid}.{req_id}.sh"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write("\n".join(script_lines))
        os.chmod(script_path, 0o755)
        
        script_list.append({"request_id": req_id, "path": script_path, "skill": skill})

    data["generated_scripts"] = script_list
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print(f"Phase 5 Complete. {len(script_list)} scripts tracked.\n")

if __name__ == "__main__":
    main()
