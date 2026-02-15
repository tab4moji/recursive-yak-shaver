#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grouping Phase Core Logic (v1.2)
Step 1: ID Assignment
Step 2: Skill-based grouping
Step 3: LLM-based intelligent grouping
Final: Sequence numbering
"""

import sys
import os
import json
import re
import subprocess
from typing import List, Dict, Any

def run_grouper_llm(skill: str, topics: List[Dict[str, str]], host: str, port: str, model: str) -> List[str]:
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
        f"--role=grouper",
        f"--prompt={input_text}",
        f"--model={model}"
    ]
    if port:
        cmd.append(f"--port={port}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        output_lines = []
        print("\nOutput from LLM:")
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if line.startswith("REQUEST:"):
                print(f"  {line}")
                output_lines.append(line)
        
        return output_lines
    except Exception as e:
        sys.stderr.write(f"Error calling grouper LLM: {e}\n")
        return [f"REQUEST: {t['id']}" for t in topics]

def process_grouping(dispatch_text: str, host: str, port: str, model: str) -> Dict[str, Any]:
    # Step 1: Assign TOPIC<N> IDs (Python)
    print("Phase3-Step1(python):")
    lines = [line.strip() for line in dispatch_text.strip().split('\n') if line.strip()]
    all_topics = []
    for i, line in enumerate(lines, 1):
        topic_id = f"TOPIC{i}"
        skill = "IDONTKNOW"
        if "| SKILLS: " in line:
            skill = line.split("| SKILLS: ")[-1].strip()
        elif "| IDONTKNOW: " in line:
            skill = "IDONTKNOW"
            
        t_data = {"id": topic_id, "raw": line, "skill": skill}
        all_topics.append(t_data)
        print(f"  {topic_id}: {line}")

    # Step 2: Group by Skill (Python)
    print("\nPhase3-Step2(python):")
    skill_groups = {}
    for t in all_topics:
        s = t["skill"]
        if s not in skill_groups:
            skill_groups[s] = []
        skill_groups[s].append(t)
    
    for skill, topics in skill_groups.items():
        print(f"  {skill}: {', '.join([t['id'] for t in topics])}")

    # Step 3: LLM Grouping (Gemma-3N)
    print("")
    raw_requests = []
    for skill, topics in skill_groups.items():
        if skill == "IDONTKNOW" or len(topics) <= 1:
            for t in topics:
                raw_requests.append({"skill": skill, "topic_ids": [t["id"]]})
        else:
            llm_results = run_grouper_llm(skill, topics, host, port, model)
            for req_str in llm_results:
                ids = [id_str.strip() for id_str in req_str.replace("REQUEST:", "").split(",")]
                raw_requests.append({"skill": skill, "topic_ids": ids})

    # Final Step: Sort and Number Requests
    # Sort by the minimum TOPIC index in each request to preserve original order
    def get_min_topic_idx(req):
        return min([int(tid.replace("TOPIC", "")) for tid in req["topic_ids"]])

    raw_requests.sort(key=get_min_topic_idx)
    
    final_requests = []
    print("\nFinal Grouped Requests:")
    for i, req in enumerate(raw_requests, 1):
        req_id = f"REQUEST{i}"
        topic_str = ", ".join(req["topic_ids"])
        display_str = f"{req_id}: {topic_str}"
        print(display_str)
        final_requests.append({
            "id": req_id,
            "skill": req["skill"],
            "topics": req["topic_ids"],
            "display": display_str
        })

    return {
        "all_topics": all_topics,
        "grouped_requests": final_requests
    }

if __name__ == "__main__":
    import os
    dispatch_text = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not dispatch_text:
        sys.exit(0)
        
    host = os.environ.get("RYS_LLM_HOST", "localhost")
    port = os.environ.get("RYS_LLM_PORT", "")
    model = os.environ.get("RYS_LLM_MODEL", "gemma3n:e4b")
    
    process_grouping(dispatch_text, host, port, model)
