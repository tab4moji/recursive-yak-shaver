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
from role_utils import load_skill_detail

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

def code_job(topic_data, config, colors, tmp_dir, uuid, prompt_hash):
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
    is_shell = not current_skill.startswith("python_")
    steps = parse_steps(refined_out)

    for i, step_desc in enumerate(steps):
        step_json = f"{tmp_dir}/.rys.{topic_hash}.p5.step_{i+1}.json"
        print(f"    - Step {i+1}/{len(steps)}: {step_desc}")

        if os.path.exists(step_json):
            with open(step_json, "r", encoding="utf-8") as f:
                cached_step = json.load(f)
                clean_snippet = cached_step["snippet"]
                output_type = cached_step.get("output_type", "Single")
                processing = cached_step.get("processing", "Whole")
                print(f"      [SKIP] Using cached result:")
        else:
            # Context Building
            completed_steps = "\n".join([f"- Step {j+1}: {steps_metadata[j]['description']}" for j in range(i)])
            
            skill_cheat_sheet = load_skill_detail(f"{SCRIPT_DIR}/config", current_skill)

            input_type = "Initial" if i == 0 else steps_metadata[i-1]["output_type"]
            input_info = "Initial input" if i == 0 else f"{input_type} data from pipe (Step {i})"

            # Input/Output Context Injection
            io_hint = "None (You are the Generator)"
            if i > 0:
                prev_meta = steps_metadata[i-1]
                prev_cmd = prev_meta['snippet'].split()[0] if prev_meta['snippet'] else "unknown"
                io_hint = f"{prev_meta['output_type']} from Step {i} (Command: `{prev_cmd}`)"

            step_prompt = (
                f"### Original Goal (TOPIC)\n{topic_data['topic']}\n\n"
                f"### Current Task (Step {i+1})\n{step_desc}\n\n"
                f"{skill_cheat_sheet}\n\n"
                f"### Data Flow Context (CRITICAL)\n"
                f"- **INPUT Data**: {io_hint}\n"
                f"- **OUTPUT Goal**: Specify the type of data intended for the next step (e.g. List of files, Single number).\n"
                f"- **DATA FORMAT HINT**: Commands like `du -b` output `[Size]\\t[Path]`. Commands like `cat` only accept a clean `[Path]`. Use `cut -f2-` when transitioning from a size-list to a file-reader.\n\n"
                f"### Total Plan Reference\n{refined_out}\n\n"
                f"### Completed Steps\n{completed_steps}\n\n"
                "### INTERNAL IDENTITY\n"
                "- You are a SINGLE LINK in a long pipeline chain.\n"
                "- You only handle the transformation from Step [i] to Step [i+1].\n\n"
                "### CORE GUIDELINES\n"
                "- **Scope**: Focus exclusively on implementing the Current Task.\n"
                "- **Pipe Integration**: Provide the core command fragment. The system automatically manages pipe chaining.\n"
            )

            if is_shell:
                step_prompt += (
                    f"- Environment: Shell (Bash).\n"
                    f"- Input Source: {input_info}.\n"
                    "- Item Access: Use \"$1\" for target identification when 'Processing' is 'Per-Item'.\n"
                )
                
                # Positive Reinforcement for Data Flow
                if i > 0:
                    prev_snippet = steps_metadata[i-1]["snippet"]
                    prev_cmd = prev_snippet.split()[0] if prev_snippet else ""
                    if prev_cmd in ["ls", "find", "cat", "du", "grep"]:
                         step_prompt += (
                            f"\n### DATA CONTINUITY (CRITICAL)\n"
                            f"- The required data stream is already provided by Step {i}.\n"
                            f"- **Direct Processing**: Apply filters or transformations directly to the incoming data from the previous stage.\n"
                        )
            else:
                step_prompt += (
                    "- Environment: Python.\n"
                    "- State Management: Read from and write to the `data` variable.\n"
                    "- Result Delivery: Ensure the final transformation is stored in `data` for the next segment.\n"
                )

            snippet_out = call_role(SCRIPT_DIR, "coder", step_prompt, config, colors, skills=[current_skill], include_skills=True)

            # [FIX] Robust code block extraction
            # Try to find content within ```...``` first.
            code_match = re.search(r"```(?:\w+)?\s*\n?(.*?)\n?```", snippet_out, re.DOTALL)
            raw_snippet = code_match.group(1).strip() if code_match else snippet_out.strip()

            # [FIX] Force-remove any remaining backticks or markdown language identifiers
            # especially if the LLM output was messy
            lines = raw_snippet.splitlines()
            clean_lines = []
            for line in lines:
                l_strip = line.strip()
                # Skip markdown code block markers
                if l_strip.startswith("```"):
                    continue
                # Skip metadata lines
                if re.search(r"#\s*(Processing|Output Type):", l_strip, re.IGNORECASE):
                    # But extract metadata if not already found
                    if "Processing:" not in line: # actually we already parsed it above
                         pass
                    continue
                clean_lines.append(line)
            
            clean_snippet = "\n".join(clean_lines).strip()

            # [FIX] Simple Quote Closer for common gemma3n errors
            if clean_snippet.count('"') % 2 != 0:
                if clean_snippet.endswith('$1'):
                    clean_snippet += '"'
                elif '"$1' in clean_snippet:
                    clean_snippet += '"'

            # --- Parse Metadata FIRST ---
            proc_match = re.search(r"# Processing:\s*(Per-Item|Whole)", raw_snippet, re.IGNORECASE)
            processing = proc_match.group(1).capitalize() if proc_match else "Whole"

            type_match = re.search(r"# Output Type:\s*(List|Single)", raw_snippet, re.IGNORECASE)
            output_type = type_match.group(1).capitalize() if type_match else "Single"

            # --- Apply Smart-Fixes SECOND (to override LLM if needed) ---
            if clean_snippet.startswith("cut") and ("$1" in clean_snippet or processing == "Per-Item"):
                clean_snippet = clean_snippet.replace(' "$1"', '').replace(' "$item"', '').strip()
                print(f"      [AUTO-FIX] Detected 'cut' misuse, converting to stream filter.")
                processing = "Whole"

            # ==========================================
            # [FIX] Anti-Repetition Logic (Smart-Strip)
            # ==========================================
            if is_shell and i > 0:
                prev_snippet = steps_metadata[i-1]["snippet"].strip()
                curr_snippet = clean_snippet.strip()
                
                # 1. 類似コマンドの繰り返し検知 (find ... | grep ... のようなパターン)
                if "|" in curr_snippet:
                    parts = [p.strip() for p in curr_snippet.split("|")]
                    first_part = parts[0]
                    
                    # 前のステップの最初の単語（コマンド名）を取得
                    prev_cmd = prev_snippet.split()[0] if prev_snippet else ""
                    curr_cmd = first_part.split()[0] if first_part else ""
                    
                    # コマンド名が一致、または前のスニペットそのもので始まっている場合
                    if (prev_cmd and curr_cmd == prev_cmd) or curr_snippet.startswith(prev_snippet):
                        clean_snippet = " | ".join(parts[1:]).strip()
                        print(f"      [AUTO-FIX] Stripped redundant command prefix '{first_part}'.")
                
                # 2. 保険: NO PIPES ルール遵守のため、依然としてパイプがある場合は最後の1つに絞るか警告
                # (ここではユーザーの意図を汲み、先頭の繰り返しを消すことを優先)
                if "|" in clean_snippet and len(clean_snippet.split("|")) > 1:
                    # 前のステップと酷似している部分があればさらに削る
                    if any(cmd in clean_snippet.split("|")[0] for cmd in ["ls", "find", "cat", "du"]):
                         parts = [p.strip() for p in clean_snippet.split("|")]
                         clean_snippet = parts[-1]
                         print(f"      [AUTO-FIX] Multiple pipes detected. Kept last segment: '{clean_snippet}'")
            # ==========================================

            # [FIX] Auto-Correction for $1 and mandatory Per-Item tools
            # Ensure standalone commands get their operands
            for cmd in ["du", "cat", "rm", "mv", "cp", "ls"]:
                if clean_snippet.strip() == cmd:
                    clean_snippet += ' "$1"'
                    print(f"      [AUTO-FIX] Appended operand to standalone '{cmd}'.")
                elif clean_snippet.startswith(f"{cmd} ") and "$1" not in clean_snippet and "-" not in clean_snippet.split()[-1]:
                    # If it has flags but no operand, and doesn't end with a flag
                    if cmd in ["du", "cat", "rm"]:
                        clean_snippet += ' "$1"'
                        print(f"      [AUTO-FIX] Appended operand to flag-only '{cmd}'.")

            if "$1" in clean_snippet and processing == "Whole":
                print(f"      [AUTO-FIX] Detected '$1' in snippet, forcing Processing: Per-Item")
                processing = "Per-Item"

            with open(step_json, "w", encoding="utf-8") as f:
                json.dump({"step": i+1, "description": step_desc, "snippet": clean_snippet, "output_type": output_type, "processing": processing}, f, ensure_ascii=False, indent=2)

        print(f"      Processing: {processing}, Output Type: {output_type}")
        print(f"      ```\n      {clean_snippet.replace(chr(10), chr(10)+'      ')}\n      ```")

        steps_metadata.append({"snippet": clean_snippet, "output_type": output_type, "processing": processing, "description": step_desc})

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
