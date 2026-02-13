#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5: Step-by-Step Coding (v1.4)
Generates code segments with strict "Anti-Repetition" prompting.
Includes "Smart-Strip" logic to remove regurgitated previous steps.
"""

import sys
import os
import argparse
import json
import re
from chat_types import ChatConfig
from chat_ui import TerminalColors
from chat_api import build_base_url, verify_connection
from phase_utils import call_role, parse_steps

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

def code_job(topic_data, config, colors, tmp_dir, uuid, prompt_hash):
    """Processes a single task through the Coder role for each milestone."""
    import hashlib
    req_idx = topic_data["req_idx"]
    current_skill = topic_data["skill"]
    req_title = topic_data["title"]
    refined_out = topic_data["refined_out"]
    topic = topic_data.get("topic", "")
    t_hash = hashlib.md5(topic.encode()).hexdigest()[:8]
    topic_hash = f"{prompt_hash}.req_{req_idx}_{t_hash}"

    print(f"\nCoding {req_title}")
    print(f"Topic: {topic}")
    print(f"  [Step-by-Step Coding]")

    steps_metadata = []
    is_shell = True # All current skills are shell-compatible fragments
    steps = parse_steps(refined_out)

    for i, step_desc in enumerate(steps):
        step_json = f"{tmp_dir}/.rys.{topic_hash}.p5.step_{i+1}.json"
        
        # Check if step cache exists
        if os.path.exists(step_json):
            try:
                with open(step_json, "r", encoding="utf-8") as f:
                    cached_step = json.load(f)
                    # Metadata must be preserved for subsequent context
                    steps_metadata.append({
                        "snippet": cached_step["snippet"],
                        "output_type": cached_step["output_type"],
                        "processing": cached_step["processing"],
                        "description": cached_step["description"]
                    })
                    print(f"    - Step {i+1}/{len(steps)}: [SKIP] Using cached step: {step_json}")
                    continue
            except Exception as e:
                print(f"    - Step {i+1}/{len(steps)}: Cache error ({e}), re-generating...")
        elif os.environ.get("RYS_FORCE_CACHE") == "1":
            print(f"\n[FATAL CACHE MISS] Step {i+1} cache not found!")
            print(f"Expected path: {step_json}")
            sys.exit(1)

        print(f"    - Step {i+1}/{len(steps)}: {step_desc}")

        # Context Building
        completed_steps = "\n".join([f"- Step {j+1}: {steps_metadata[j]['description']}" for j in range(i)])
        
        # Input/Output Context Injection
        io_hint = "Standard Input" if i == 0 else f"Output from Step {i}"

        step_prompt = (
            f"### Task\n{step_desc}\n\n"
            f"### Context\n"
            f"- Input: {io_hint}\n"
        )

        snippet_out = call_role(SCRIPT_DIR, "coder", step_prompt, config, colors, 
                                skills=[current_skill], include_skills=True, risks="./config/risks.json")

        # Code block extraction
        code_match = re.search(r"```(?:\w+)?\s*\n?(.*?)\n?```", snippet_out, re.DOTALL)
        raw_snippet = code_match.group(1).strip() if code_match else snippet_out.strip()

        clean_lines = []
        for line in raw_snippet.splitlines():
            l_strip = line.strip()
            if l_strip.startswith("```"): continue
            if re.search(r"#\s*(Processing|Output Type):", l_strip, re.IGNORECASE):
                # Metadata is parsed from raw_snippet anyway
                continue
            clean_lines.append(line)
        
        clean_snippet = "\n".join(clean_lines).strip()

        # --- MANDATORY PIPE STRIPPER (Keep Last Segment) ---
        if "|" in clean_snippet:
            last_cmd = clean_snippet.split("|")[-1].strip()
            print(f"      [STRIP] Multiple segments detected. Keeping last: '{last_cmd}'")
            clean_snippet = last_cmd
        # ---------------------------------------------------

        # Metadata Parsing
        proc_match = re.search(r"# Processing:\s*(Per-Item|Whole)", raw_snippet, re.IGNORECASE)
        processing = proc_match.group(1).capitalize() if proc_match else "Whole"

        type_match = re.search(r"# Output Type:\s*(List|Single)", raw_snippet, re.IGNORECASE)
        output_type = type_match.group(1).capitalize() if type_match else "Single"

        # Aggressive Auto-Fixes
        # 1. Stream tools must NOT have $1
        stream_tools = ["sort", "head", "tail", "grep", "cut", "awk", "sed", "uniq"]
        first_word = clean_snippet.split()[0] if clean_snippet else ""
        if first_word in stream_tools:
            if "$1" in clean_snippet:
                clean_snippet = clean_snippet.replace(' "$1"', '').replace('"$1"', '').strip()
                print(f"      [AUTO-FIX] Removed '$1' from stream tool '{first_word}'.")
            processing = "Whole"

        # 2. General $1 presence vs Processing mode
        if "$1" in clean_snippet and processing == "Whole":
            # Only switch if NOT a stream tool (which we handled above)
            if first_word not in stream_tools:
                processing = "Per-Item"
                print(f"      [AUTO-FIX] Detected '$1', forcing Per-Item.")

        with open(step_json, "w", encoding="utf-8") as f:
            json.dump({
                "step": i+1, 
                "description": step_desc, 
                "snippet": clean_snippet, 
                "output_type": output_type, 
                "processing": processing
            }, f, ensure_ascii=False, indent=2)

        print(f"      Processing: {processing}, Output Type: {output_type}")
        print(f"      ```\n      {clean_snippet.replace(chr(10), chr(10)+'      ')}\n      ```")

        steps_metadata.append({
            "snippet": clean_snippet, 
            "output_type": output_type, 
            "processing": processing, 
            "description": step_desc
        })

    if is_shell:
        # Generate Native Shell Script (.sh)
        sh_lines = ["#!/bin/bash", "set -e", ""]

        step_blocks = []
        for i, meta in enumerate(steps_metadata):
            snippet = meta["snippet"].strip()
            if not snippet:
                continue
            proc = meta["processing"].lower() if i > 0 else "whole"

            # Assembly-Time Correction
            if "$1" in snippet and proc != "per-item":
                print(f"      [ASSEMBLY FIX] Step {i+1}: Detected '$1', forcing Per-Item loop.")
                proc = "per-item"

            block = ["{"]
            if proc == "per-item":
                block.append("  while read -r item; do")
                block.append("    set -- \"$item\"")
                for line in snippet.splitlines():
                    block.append(f"    {line}")
                block.append("  done")
            else:
                for line in snippet.splitlines():
                    block.append(f"  {line}")
            block.append("}")

            step_blocks.append("\n".join(block))

        sh_lines.append(" | \\\n".join(step_blocks))

        path = f"{tmp_dir}/.rys.{uuid}.req_{req_idx}.sh"
        with open(path, "w", encoding="utf-8") as fs:
            fs.write("\n".join(sh_lines))
    else:
        # Generate Orchestrator Python Script (.py)
        orchestrator = [
            "import subprocess, sys, os",
            "def run_shell(cmd, args=None, stdin_data=None):",
            "    full_cmd = cmd",
            "    if args: full_cmd += ' ' + ' '.join(f'\"{a}\"' for a in args)",
            "    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, input=stdin_data)",
            "    return res.stdout.strip()",
            "",
            "data = []",
            "try:"
        ]

        for i, meta in enumerate(steps_metadata):
            snippet = meta["snippet"]
            if not snippet.strip():
                continue
            desc = meta["description"]
            proc = meta["processing"].lower()
            prev_type = steps_metadata[i-1]["output_type"] if i > 0 else "Initial"

            orchestrator.append(f"    # Step {i+1}: {desc}")
            if prev_type == "List" and proc == "per-item":
                orchestrator.append(f"    new_data = []")
                orchestrator.append(f"    for item in data:")
                orchestrator.append(f"        data = item # Current item context")
                for line in snippet.splitlines():
                    if line.strip():
                        orchestrator.append("            " + line)
                orchestrator.append(f"        new_data.append(data)")
                orchestrator.append(f"    data = new_data")
            else:
                for line in snippet.splitlines():
                    if line.strip():
                        orchestrator.append("    " + line)

        orchestrator.append("    if data is not None:")
        orchestrator.append("        pass # Final output is handled by snippets")
        orchestrator.append("except Exception as e:")
        orchestrator.append("    print(f'Error at Step: {e}', file=sys.stderr)")
        orchestrator.append("    sys.exit(1)")

        path = f"{tmp_dir}/.rys.{uuid}.req_{req_idx}.py"
        with open(path, "w", encoding="utf-8") as fs:
            fs.write("\n".join(orchestrator))

    return {"req_idx": req_idx, "path": path, "title": req_title}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-json", required=True)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default="11434")
    parser.add_argument("--model", default="gemma3n:e4b")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--uuid", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.in_json):
        print(f">>> Skipping Phase 5: Input file {args.in_json} not found.")
        # Create an empty or minimal output JSON to satisfy the pipeline if needed
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return

    with open(args.in_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "planned_topics" not in data or not data["planned_topics"]:
        print("No planned topics to code.")
        return

    base_url = build_base_url(args.host, args.port)
    verify_connection(base_url)
    config = ChatConfig(api_url=f"{base_url.rstrip('/')}/v1/chat/completions", model=args.model, quiet_mode=True, stream_output=True, insecure=False, silent_mode=True)
    colors = TerminalColors(enable_color=True)
    tmp_dir = "./tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    data["scripts"] = []

    for topic_data in data["planned_topics"]:
        res = code_job(topic_data, config, colors, tmp_dir, args.uuid, args.uuid)
        if res:
            data["scripts"].append(res)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
