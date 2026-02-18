#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 1.3: Grouping Phase Core Logic
# リポジトリ規約に基づき pylint の指摘事項を修正
"""
Grouping Phase Core Logic (v1.3)
Step 1: ID Assignment + Title Extraction
Step 2: Skill-based grouping
Step 3: LLM-based intelligent grouping
Final: Sequence numbering with titles
"""

import sys
import os
import re
import subprocess
from typing import List, Dict, Any

def parse_input(dispatch_text: str) -> Dict[str, List[str]]:
    """
    Parses dispatch output and groups topics by skill.
    Returns: Dict[skill, List[topic_description]]
    """
    lines = [line.strip() for line in dispatch_text.strip().split('\n') if line.strip()]
    groups = {}

    for line in lines:
        skill = "UNKNOWN"
        topic = line

        if "| SKILLS: " in line:
            parts = line.split("| SKILLS: ")
            skill = parts[-1].strip()
            topic = parts[0].replace("TOPIC:", "").strip()
        elif "| IDONTKNOW: " in line:
            parts = line.split("| IDONTKNOW: ")
            skill = "IDONTKNOW"
            topic = parts[0].replace("TOPIC:", "").strip()

        groups.setdefault(skill, []).append(topic)
    return groups


def run_grouper_llm(skill: str, topics: List[Dict[str, str]],
                   host: str, port: str, model: str) -> List[str]:
    """Step 3 (Gemma-3N): Intelligent grouping."""
    print("Phase3-Step3(gemma-3n):")

    input_text = f"  {skill}: {', '.join([t['id'] for t in topics])}\n"
    for t in topics:
        input_text += f"    {t['id']}: {t['raw']}\n"

    print("Input for LLM:")
    print(input_text.rstrip())

    cmd = [
        "python3", "./rys/invoke_role.py",
        f"--host={host}",
        "--role=grouper",
        f"--prompt={input_text}",
        f"--model={model}"
    ]
    if port:
        cmd.append(f"--port={port}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        output_lines = []
        print("\nRaw LLM Output:")
        print(f"---START---\n{result.stdout.strip()}\n---END---")

        print("\nParsed Grouping:")
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if line.startswith("REQUEST:"):
                print(f"  {line}")
                output_lines.append(line)
        res = output_lines
    except Exception as e:  # pylint: disable=broad-exception-caught
        sys.stderr.write(f"Error calling grouper LLM: {e}\n")
        res = [f"REQUEST: {t['id']}" for t in topics]

    return res

def _assign_topic_ids(dispatch_text: str) -> List[Dict[str, str]]:
    """Step 1: Assign TOPIC<N> IDs + Extract Titles."""
    print("Phase3-Step1(python):")
    lines = [line.strip() for line in dispatch_text.strip().split('\n') if line.strip()]
    all_topics = []

    for i, line in enumerate(lines, 1):
        topic_id = f"TOPIC{i}"
        title = "Unknown"
        title_match = re.match(r"^TOPIC:\s*(.*?)\s*\|", line)
        if title_match:
            title = title_match.group(1)

        skill = "IDONTKNOW"
        if "| SKILLS: " in line:
            skill = line.split("| SKILLS: ")[-1].strip()
        elif "| IDONTKNOW: " in line:
            skill = "IDONTKNOW"
        elif " | " in line:
            last_part = line.split(" | ")[-1].strip()
            if ":" in last_part:
                pot_skill = last_part.split(":")[0].strip()
                if pot_skill in ["shell_exec", "python_math", "python_script", "web_access"]:
                    skill = pot_skill

        t_data = {"id": topic_id, "title": title, "raw": line, "skill": skill}
        all_topics.append(t_data)
        print(f"  {topic_id}: {line}")

    return all_topics

def _group_by_skill(all_topics: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """Step 2: Group by Skill."""
    print("\nPhase3-Step2(python): Grouping by skill...")
    skill_groups = {}
    for t in all_topics:
        if t["skill"] != "IDONTKNOW":
            skill_groups.setdefault(t["skill"], []).append(t)
    return skill_groups

def _llm_intelligent_grouping(skill_groups: Dict[str, List[Dict[str, str]]],
                             idontknow_topics: List[Dict[str, str]],
                             host: str, port: str, model: str) -> List[Dict[str, Any]]:
    """Step 3: Intelligent Grouping."""
    print("")
    raw_requests = []

    for t in idontknow_topics:
        raw_requests.append({"skill": "IDONTKNOW", "topic_ids": [t["id"]]})

    for skill, topics in skill_groups.items():
        if len(topics) == 1:
            raw_requests.append({"skill": skill, "topic_ids": [topics[0]["id"]]})
        else:
            llm_results = run_grouper_llm(skill, topics, host, port, model)
            if not llm_results:
                print(f"  Warning: No valid REQUEST lines found for {skill}.")
                llm_results = [f"REQUEST: {t['id']}" for t in topics]

            for req_str in llm_results:
                ids = [id_str.strip() for id_str in req_str.replace("REQUEST:", "").split(",")]
                if ids:
                    raw_requests.append({"skill": skill, "topic_ids": ids})
    return raw_requests

def _format_final_requests(raw_requests: List[Dict[str, Any]],
                           topic_map: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    """Final Step: Sort and Number Requests with Titles."""
    def get_min_topic_idx(req):
        return min(int(tid.replace("TOPIC", "")) for tid in req["topic_ids"])

    raw_requests.sort(key=get_min_topic_idx)

    final_requests = []
    print("\nFinal Grouped Requests:")
    for i, req in enumerate(raw_requests, 1):
        req_id = f"REQUEST{i}"
        topic_parts = []
        for tid in req["topic_ids"]:
            t_info = topic_map.get(tid, {})
            title = t_info.get("title", "Unknown")
            topic_parts.append(f"{tid}({title})")

        topic_str = ", ".join(topic_parts)
        display_str = f"{req_id}: {topic_str}"
        print(display_str)

        final_requests.append({
            "id": req_id, "skill": req["skill"],
            "topics": req["topic_ids"], "display": display_str
        })
    return final_requests

def process_grouping(dispatch_text: str, host: str, port: str, model: str) -> Dict[str, Any]:
    """Processes grouping workflow."""
    all_topics = _assign_topic_ids(dispatch_text)
    topic_map = {t["id"]: t for t in all_topics}

    skill_groups = _group_by_skill(all_topics)
    idontknow_topics = [t for t in all_topics if t["skill"] == "IDONTKNOW"]

    raw_reqs = _llm_intelligent_grouping(skill_groups, idontknow_topics, host, port, model)
    final_reqs = _format_final_requests(raw_reqs, topic_map)

    return {
        "all_topics": all_topics,
        "grouped_requests": final_reqs
    }

def main():
    """Main function to handle stdin input."""
    input_text = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not input_text:
        sys.exit(0)

    host_env = os.environ.get("RYS_LLM_HOST", "localhost")
    port_env = os.environ.get("RYS_LLM_PORT", "")
    model_env = os.environ.get("RYS_LLM_MODEL", "gemma3n:e4b")

    process_grouping(input_text, host_env, port_env, model_env)

if __name__ == "__main__":
    main()
