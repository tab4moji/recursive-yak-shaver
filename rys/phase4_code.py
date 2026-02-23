#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4: Step-by-Step Coding (v2.0)
Generates code segments for the planned milestones.
Renamed from Phase 5 to Phase 4.
"""

import sys
import os
import json
import re
import hashlib
from phase_utils import call_role, parse_steps, get_common_parser, init_llm_config, load_phase_json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

def _clean_snippet(raw_snippet):
    """Cleans the raw snippet from LLM output."""
    clean_lines = []
    for line in raw_snippet.splitlines():
        l_strip = line.strip()
        if l_strip.startswith("```"):
            continue
        if re.search(r"#\s*(Processing|Output Type):", l_strip, re.IGNORECASE):
            continue
        clean_lines.append(line)

    clean_snippet = "\n".join(clean_lines).strip()

    if "|" in clean_snippet:
        last_cmd = clean_snippet.rsplit("|", maxsplit=1)[-1].strip()
        print(f"      [STRIP] Multiple segments detected. Keeping last: '{last_cmd}'")
        clean_snippet = last_cmd

    return clean_snippet

def _extract_step_metadata(raw_snippet, clean_snippet):
    """Extracts processing and output type from snippet."""
    proc_match = re.search(r"# Processing:\s*(Per-Item|Whole)", raw_snippet, re.IGNORECASE)
    processing = proc_match.group(1).capitalize() if proc_match else "Whole"

    type_match = re.search(r"# Output Type:\s*(List|Single)", raw_snippet, re.IGNORECASE)
    output_type = type_match.group(1).capitalize() if type_match else "Single"

    # Auto-adjust processing for stream tools
    stream_tools = ["sort", "head", "tail", "grep", "cut", "awk", "sed", "uniq"]
    first_word = clean_snippet.split()[0] if clean_snippet else ""
    if first_word in stream_tools:
        if "$1" in clean_snippet:
            clean_snippet = clean_snippet.replace(' "$1"', '').replace('"$1"', '').strip()
        processing = "Whole"

    if "$1" in clean_snippet and processing == "Whole" and first_word not in stream_tools:
        processing = "Per-Item"

    return processing, output_type, clean_snippet

def _handle_step_cache(step_json, step_idx):
    """Checks if step cache exists and is valid."""
    if os.path.exists(step_json):
        try:
            with open(step_json, "r", encoding="utf-8") as f:
                cached = json.load(f)
                print(f"    - Step {step_idx+1}: [SKIP] Using cached step: {step_json}")
                return cached
        except (json.JSONDecodeError, IOError) as e:
            print(f"    - Step {step_idx+1}: Cache error ({e}), re-generating...")
    return None

def _process_single_step(step_idx, step_desc, meta_context, config, colors):
    # pylint: disable=too-many-locals
    """Processes a single step: cache or LLM call."""
    t_hash = meta_context['topic_hash']
    step_json = f"{meta_context['tmp_dir']}/.rys.{t_hash}.p4.step_{step_idx+1}.json"
    cached = _handle_step_cache(step_json, step_idx)
    if cached:
        return cached

    print(f"    - Step {step_idx+1}: {step_desc}")
    input_hint = 'Standard Input' if step_idx == 0 else f'Output from Step {step_idx}'
    snippet_out = call_role(
        SCRIPT_DIR, "coder",
        f"### Task\n{step_desc}\n\n### Context\n"
        f"- Input: {input_hint}\n",
        config, colors, skills=[meta_context["skill"]], include_skills=True,
        risks="./skills/risks.json"
    )

    match = re.search(r"```(?:\w+)?\s*\n?(.*?)\n?```", snippet_out, re.DOTALL)
    raw_snippet = match.group(1).strip() if match else snippet_out.strip()
    proc, o_type, clean = _extract_step_metadata(raw_snippet, _clean_snippet(raw_snippet))

    res = {
        "step": step_idx+1, "description": step_desc, "snippet": clean,
        "output_type": o_type, "processing": proc, "content": snippet_out
    }
    with open(step_json, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    print(f"      Processing: {proc}, Output Type: {o_type}")
    return res

def _generate_shell_content(steps_metadata):
    """Generates the bash script content from steps metadata."""
    sh_lines = ["#!/bin/bash", "set -e", ""]
    step_blocks = []
    for i, meta in enumerate(steps_metadata):
        snippet = meta["snippet"].strip()
        if not snippet:
            continue
        proc = meta["processing"].lower() if i > 0 else "whole"
        if "$1" in snippet and proc != "per-item":
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
    return "\n".join(sh_lines)

def code_job(topic_data, config, colors, tmp_dir, identifiers):
    # pylint: disable=too-many-locals
    """Processes a single task through the Coder role for each milestone."""
    uuid, prompt_hash = identifiers
    req_idx = topic_data["req_idx"]
    req_title = topic_data["title"]
    topic = topic_data.get("topic", "")
    t_hash = hashlib.md5(topic.encode()).hexdigest()[:8]
    topic_hash = f"{prompt_hash}.req_{req_idx}_{t_hash}"

    print(f"\nCoding {req_title}")
    print(f"Topic: {topic}")
    print("  [Step-by-Step Coding]")

    steps = parse_steps(topic_data["refined_out"])
    steps_metadata = []
    meta_ctx = {"tmp_dir": tmp_dir, "topic_hash": topic_hash, "skill": topic_data["skill"]}

    for i, step_desc in enumerate(steps):
        res = _process_single_step(i, step_desc, meta_ctx, config, colors)
        steps_metadata.append(res)
        snippet_disp = res["snippet"].replace(chr(10), chr(10)+'      ')
        print(f"      ```\n      {snippet_disp}\n      ```")

    sh_content = _generate_shell_content(steps_metadata)
    path = f"{tmp_dir}/.rys.{uuid}.req_{req_idx}.sh"
    with open(path, "w", encoding="utf-8") as fs:
        fs.write(sh_content)

    return {"req_idx": req_idx, "path": path, "title": req_title}

def _process_topics(data, config, colors, uuid):
    """Processes all planned topics into scripts."""
    tmp_dir = "./tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    data["scripts"] = []
    for topic_data in data["planned_topics"]:
        res = code_job(topic_data, config, colors, tmp_dir, (uuid, uuid))
        if res:
            data["scripts"].append(res)

def main():
    """Main entry point for Phase 4 coding."""
    parser = get_common_parser("Phase 4: Step-by-Step Coding")
    args = parser.parse_args()

    data = load_phase_json(args.in_json)

    if not data.get("planned_topics"):
        print("No planned topics to code.")
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return

    config, colors = init_llm_config(args)
    _process_topics(data, config, colors, args.uuid)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
