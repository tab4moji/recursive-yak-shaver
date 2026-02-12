#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4: Strategic Planning (v1.1)
Processes each topic through Planner, Engineer, Refiner, and Auditor roles.
Outputs a JSON with the refined workflow steps.
"""

import sys
import os
import argparse
import json
from chat_types import ChatConfig
from chat_ui import TerminalColors
from chat_api import build_base_url, verify_connection
from phase_utils import call_role, parse_steps

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

def cached_call(role: str, prompt: str, cache_path: str, config, colors, 
                skills=None, include_skills=False, risks=None) -> str:
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f_in:
            cached_data = json.load(f_in)
            print(f"  [SKIP] Using cached {role} result: {cache_path}")
            return cached_data["content"]

    content = call_role(SCRIPT_DIR, role, prompt, config, colors, 
                        skills=skills, include_skills=include_skills, risks=risks)
    with open(cache_path, "w", encoding="utf-8") as f_out:
        json.dump({"role": role, "content": content}, f_out, ensure_ascii=False, indent=2)
    return content

def plan_job(job, data, config, colors, risks_config, tmp_dir, prompt_hash):
    import hashlib
    req_idx, current_skill, topic = job["req_idx"], job["skill"], job["topic"]
    t_hash = hashlib.md5(topic.encode()).hexdigest()[:8]
    topic_hash = f"{prompt_hash}.req_{req_idx}_{t_hash}"
    titles_lines = data["titles_out"].splitlines()
    req_title = next((l for l in titles_lines if l.startswith(f"REQUEST {req_idx}:")), f"REQUEST {req_idx}:")
    
    print(f"\nPlanning {req_title}")
    print(f"Topic: {topic}")
    goal = f"- TOPIC: {topic}"

    e_cache = f"{tmp_dir}/.rys.{topic_hash}.p4.2_engineer.json"
    eng_out = cached_call("engineer", goal, e_cache, config, colors, skills=[current_skill], include_skills=True)
    
    # Defensive: Strip markdown code blocks and deduplicate lines
    import re
    cleaned = re.sub(r"```.*?```", "", eng_out, flags=re.DOTALL).strip()
    
    unique_lines = []
    seen_lines = set()
    for line in cleaned.splitlines():
        l_strip = line.strip()
        if l_strip and l_strip not in seen_lines:
            unique_lines.append(line)
            seen_lines.add(l_strip)
    
    refined_out = "\n".join(unique_lines)
    if not refined_out:
        refined_out = eng_out

    print(f"\n  [Strategic Roadmap (from Strategic Architect)]")
    for line in refined_out.splitlines():
        print(f"    {line}")
    a_cache = f"{tmp_dir}/.rys.{topic_hash}.p4.4_auditor.json"
    audit_out = cached_call("auditor", refined_out, a_cache, config, colors, risks=risks_config)

    if not refined_out.strip() or "[FAIL]" in audit_out:
        print("Plan failed refinement or audit. Skipping.")
        return None

    return {"req_idx": req_idx, "skill": current_skill, "title": req_title, "topic": topic, "refined_out": refined_out}

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
        print(f">>> Skipping Phase 4: Input file {args.in_json} not found.")
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return

    with open(args.in_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    exec_plan = []
    req_idx = 1
    for key, descriptions in data.get("groups", {}).items():
        if not (key.startswith("IDONTKNOW__") or key == "UNKNOWN"):
            for desc in descriptions:
                exec_plan.append({"req_idx": req_idx, "skill": key, "topic": desc})
        req_idx += 1

    if not exec_plan:
        print("No valid tasks to plan.")
        # Create output JSON even if empty to satisfy pipeline
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return

    base_url = build_base_url(args.host, args.port)
    verify_connection(base_url)
    config = ChatConfig(api_url=f"{base_url.rstrip('/')}/v1/chat/completions", model=args.model, quiet_mode=True, stream_output=True, insecure=False, silent_mode=True)
    colors = TerminalColors(enable_color=True)
    tmp_dir = "./tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    data["planned_topics"] = []

    for job in exec_plan:
        res = plan_job(job, data, config, colors, "./config/risks.json", tmp_dir, args.uuid)
        if res:
            data["planned_topics"].append(res)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
