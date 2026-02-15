#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grouping Phase Core Logic (v1.1)
Strictly follows the 3-step decomposition requested by the user.
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
    
    # Format Input for LLM
    input_text = f"  {skill}: {', '.join([t['id'] for t in topics])}\n"
    for t in topics:
        input_text += f"    {t['id']}: {t['raw']}\n"
    
    print("Input for LLM:")
    print(input_text.rstrip())

    # Call invoke_role.py
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
        # Capture the result
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse output (only REQUEST lines)
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
        
        # Simple skill extraction
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
    final_requests = []
    sorted_skills = sorted(skill_groups.keys(), key=lambda x: (x == "IDONTKNOW", x))

    for skill in sorted_skills:
        topics = skill_groups[skill]
        if skill == "IDONTKNOW" or len(topics) <= 1:
            # Simple bypass for non-complex groups
            for t in topics:
                final_requests.append({"skill": skill, "request": f"REQUEST: {t['id']}", "topics": [t]})
        else:
            # Multi-topic group
            llm_results = run_grouper_llm(skill, topics, host, port, model)
            for req_str in llm_results:
                ids = [id_str.strip() for id_str in req_str.replace("REQUEST:", "").split(",")]
                req_topics = [t for t in topics if t["id"] in ids]
                final_requests.append({"skill": skill, "request": req_str, "topics": req_topics})

    return {
        "all_topics": all_topics,
        "skill_groups": skill_groups,
        "grouped_requests": final_requests
    }

if __name__ == "__main__":
    # Same as before
    dispatch_file = sys.argv[1] if len(sys.argv) > 1 else None
    if dispatch_file and os.path.exists(dispatch_file):
        with open(dispatch_file, 'r') as f:
            dispatch_text = f.read()
    else:
        sys.exit(1)
        
    host = os.environ.get("RYS_LLM_HOST", "localhost")
    port = os.environ.get("RYS_LLM_PORT", "")
    model = os.environ.get("RYS_LLM_MODEL", "gemma3n:e4b")
    
    process_grouping(dispatch_text, host, port, model)
