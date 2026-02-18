#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: Strategic Planning (v2.1)
Replaces old Phase 3 (Visualization) and Phase 4 (Planning).
Includes Titler for better UX and fixes cache naming.
"""

import sys
import os
import json
import hashlib
import yaml
from phase_utils import call_role, get_common_parser, init_llm_config, load_phase_json
import group_requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

def parse_toon(raw_response: str):
    """Parses and cleans TOON (YAML) output from LLM."""
    clean_response = raw_response.replace("```TOON", "").replace("```yaml", "").replace(
        "```", "").strip()
    try:
        return yaml.safe_load(clean_response)
    except (yaml.YAMLError, AttributeError, TypeError):
        return None


# pylint: disable=too-many-arguments,too-many-positional-arguments
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

def _extract_op_from_toon(toon_data):
    """Refines operation from TOON data."""
    op = toon_data.get("operation", "Execute task")
    val = toon_data.get("input", {}).get("value", "")
    out_type = toon_data.get("output", {}).get("type", "")

    # Refine operation if it lacks display/show intent but output type suggests it
    display_keywords = ["display", "show", "print", "read", "content"]
    if out_type in ["display_content", "file_content"] and \
       not any(k in op.lower() for k in display_keywords):
        op = f"{op} and show the content of the file"

    # Convert back to a Milestone format that Phase 4 understands
    refined_out = f"Milestone 1: {op}"
    if val:
        refined_out += f" (Input: {val})"
    return refined_out


# pylint: disable=too-many-arguments,too-many-positional-arguments
def plan_job(job, config, colors, tmp_dir, prompt_hash):
    """Processes a single task through the Planner role."""
    t_hash = hashlib.md5(job["topic"].encode()).hexdigest()[:8]
    topic_hash = f"{prompt_hash}.req_{job['req_idx']}_{t_hash}"

    print(f"\nPlanning {job['title']}")

    # Using the suggested format: TOPIC: ... | SKILLS: ...
    goal_prompt = f"TOPIC: {job['topic']} | SKILLS: {job['skill']}"

    # Use p3.planner as the role and update cache naming
    e_cache = f"{tmp_dir}/.rys.{topic_hash}.p3.planner.json"
    raw_out = cached_call(
        "planner", goal_prompt, e_cache, config, colors,
        skills=[job["skill"]], include_skills=True, risks="./config/risks.json"
    )

    # Parse TOON/YAML
    toon_data = parse_toon(raw_out)
    if toon_data and isinstance(toon_data, dict):
        refined_out = _extract_op_from_toon(toon_data)
    else:
        refined_out = raw_out

    # Print raw output (YAML) then compact Roadmap
    print(raw_out)
    print(f"Topic: {job['topic']} [Strategic Roadmap] {refined_out.replace('\n', ' ')}")

    if not refined_out.strip():
        print("Plan generation failed. Skipping.")
        return None

    return {
        "req_idx": job["req_idx"],
        "skill": job["skill"],
        "title": job["title"],
        "topic": job["topic"],
        "refined_out": refined_out,
        "content": raw_out
    }

def _build_visual_input(groups):
    """Builds visual input string for the titler."""
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
    return visual_input


def _build_exec_plan(groups, titles_out):
    """Builds the execution plan list."""
    titles_lines = titles_out.splitlines()
    exec_plan = []
    req_idx = 1
    for key, descriptions in groups.items():
        if not (key.startswith("IDONTKNOW__") or key == "UNKNOWN"):
            for desc in descriptions:
                # Find the specific title for this request
                req_title = next(
                    (l for l in titles_lines if l.startswith(f"REQUEST {req_idx}:")),
                    f"REQUEST {req_idx}: [Skill: {key}]"
                )
                exec_plan.append({
                    "req_idx": req_idx, "skill": key, "topic": desc, "title": req_title
                })
        req_idx += 1
    return exec_plan


def main():
    """Main execution function for Strategic Planning."""
    parser = get_common_parser("Phase 3: Strategic Planning")
    args = parser.parse_args()

    data = load_phase_json(args.in_json)

    # Perform Grouping (Use 'content' if available)
    dispatch_out = data.get("content", data.get("dispatch_out", ""))
    groups = group_requests.parse_input(dispatch_out)
    data["groups"] = groups

    visual_input = _build_visual_input(groups)

    config, colors = init_llm_config(args)

    print("\n>>> Generating Task Titles...")
    titles_out = call_role(SCRIPT_DIR, "titler", visual_input, config, colors)
    data["titles_out"] = titles_out

    exec_plan = _build_exec_plan(groups, titles_out)

    if not exec_plan:
        print("No valid tasks to plan.")
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return

    tmp_dir = "./tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    data["planned_topics"] = []

    for job in exec_plan:
        res = plan_job(job, config, colors, tmp_dir, args.uuid)
        if res:
            data["planned_topics"].append(res)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
