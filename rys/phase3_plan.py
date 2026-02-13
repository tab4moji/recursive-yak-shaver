#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: Strategic Planning (v2.1)
Replaces old Phase 3 (Visualization) and Phase 4 (Planning).
Includes Titler for better UX and fixes cache naming.
"""

import sys
import os
import argparse
import json
import hashlib
import yaml
from chat_types import ChatConfig
from chat_ui import TerminalColors
from chat_api import build_base_url, verify_connection
from phase_utils import call_role
import group_requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

def parse_toon(raw_response: str):
    """Parses and cleans TOON (YAML) output from LLM."""
    clean_response = raw_response.replace("```TOON", "").replace("```yaml", "").replace("```", "").strip()
    try:
        return yaml.safe_load(clean_response)
    except Exception:
        return None

def cached_call(role: str, prompt: str, cache_path: str, config, colors, 
                skills=None, include_skills=False, risks=None) -> str:
    """Wrapper for role calls with local caching."""
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

def plan_job(job, data, config, colors, tmp_dir, prompt_hash):
    """Processes a single task through the Planner role."""
    req_idx, current_skill, topic, req_title = job["req_idx"], job["skill"], job["topic"], job["title"]
    t_hash = hashlib.md5(topic.encode()).hexdigest()[:8]
    topic_hash = f"{prompt_hash}.req_{req_idx}_{t_hash}"
    
    print(f"\nPlanning {req_title}")
    
    # Using the suggested format: TOPIC: ... | SKILLS: ...
    goal_prompt = f"TOPIC: {topic} | SKILLS: {current_skill}"

    # Use p3.planner as the role and update cache naming
    e_cache = f"{tmp_dir}/.rys.{topic_hash}.p3.planner.json"
    raw_out = cached_call(
        "planner", goal_prompt, e_cache, config, colors, 
        skills=[current_skill], include_skills=True, risks="./config/risks.json"
    )
    
    # Parse TOON/YAML
    toon_data = parse_toon(raw_out)
    if toon_data and isinstance(toon_data, dict):
        op = toon_data.get("operation", "Execute task")
        val = toon_data.get("input", {}).get("value", "")
        # Convert back to a Milestone format that Phase 4 understands
        refined_out = f"Milestone 1: {op}"
        if val:
            refined_out += f" (Input: {val})"
    else:
        # Fallback if parsing fails
        refined_out = raw_out
    
    # Print raw output (YAML) then compact Roadmap
    print(raw_out)
    plan_display = refined_out.replace("\n", " ")
    print(f"Topic: {topic} [Strategic Roadmap] {plan_display}")

    if not refined_out.strip():
        print("Plan generation failed. Skipping.")
        return None

    return {
        "req_idx": req_idx, 
        "skill": current_skill, 
        "title": req_title, 
        "topic": topic, 
        "refined_out": refined_out,
        "content": raw_out
    }

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
        print(f">>> Skipping Phase 3: Input file {args.in_json} not found.")
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return

    with open(args.in_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Perform Grouping (Use 'content' if available)
    dispatch_out = data.get("content", data.get("dispatch_out", ""))
    groups = group_requests.parse_input(dispatch_out)
    data["groups"] = groups

    # Generate Titles for Visualization (UX Restoration)
    visual_input = ""
    req_index = 1
    for key, descriptions in groups.items():
        status = f"[Skill: {key}]"
        if key.startswith("IDONTKNOW__"):
            reason = key.split("__", 2)[2]
            status = f"[Status: Unable to Process ({reason})]"
        visual_input += f"REQUEST {req_index} {status}:\n"
        for desc in descriptions:
            visual_input += f"- TOPIC: {desc}\n"
        visual_input += "\n"
        req_index += 1

    base_url = build_base_url(args.host, args.port)
    verify_connection(base_url)
    config = ChatConfig(api_url=f"{base_url.rstrip('/')}/v1/chat/completions", model=args.model, quiet_mode=True, stream_output=True, insecure=False, silent_mode=True)
    colors = TerminalColors(enable_color=True)

    print("\n>>> Generating Task Titles...")
    titles_out = call_role(SCRIPT_DIR, "titler", visual_input, config, colors)
    data["titles_out"] = titles_out
    titles_lines = titles_out.splitlines()

    exec_plan = []
    req_idx = 1
    for key, descriptions in groups.items():
        if not (key.startswith("IDONTKNOW__") or key == "UNKNOWN"):
            for desc in descriptions:
                # Find the specific title for this request
                req_title = next((l for l in titles_lines if l.startswith(f"REQUEST {req_idx}:")), f"REQUEST {req_idx}: [Skill: {key}]")
                exec_plan.append({"req_idx": req_idx, "skill": key, "topic": desc, "title": req_title})
        req_idx += 1

    if not exec_plan:
        print("No valid tasks to plan.")
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return

    tmp_dir = "./tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    data["planned_topics"] = []

    for job in exec_plan:
        res = plan_job(job, data, config, colors, tmp_dir, args.uuid)
        if res:
            data["planned_topics"].append(res)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
