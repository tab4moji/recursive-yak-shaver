#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grouping Phase Core Logic (v1.3)
Step 1: ID Assignment + Title Extraction
Step 2: Skill-based grouping
Step 3: LLM-based intelligent grouping
Final: Sequence numbering with titles
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
    # Step 1: Assign TOPIC<N> IDs + Extract Titles (Python)
    print("Phase3-Step1(python):")
    lines = [line.strip() for line in dispatch_text.strip().split('\n') if line.strip()]
    all_topics = []
    topic_map = {}
    
    for i, line in enumerate(lines, 1):
        topic_id = f"TOPIC{i}"
        
        # Extract title from "TOPIC: <Title> |"
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
            # Fallback: check if the last part looks like a skill (not containing common sentences)
            last_part = line.split(" | ")[-1].strip()
            if ":" in last_part:
                potential_skill = last_part.split(":")[0].strip()
                if potential_skill in ["shell_exec", "python_math", "python_script", "web_access"]:
                    skill = potential_skill
            
        t_data = {"id": topic_id, "title": title, "raw": line, "skill": skill}
        all_topics.append(t_data)
        topic_map[topic_id] = t_data
        print(f"  {topic_id}: {line}")

    # Step 2: Group by Skill (Python) - REPLACED by Logical Grouping
    # We now group all non-IDONTKNOW topics into one "executable" pool
    # and let the LLM decide the logical sub-groups.
    print("\nPhase3-Step2(python): Preparing for intelligent grouping...")
    executable_topics = [t for t in all_topics if t["skill"] != "IDONTKNOW"]
    idontknow_topics = [t for t in all_topics if t["skill"] == "IDONTKNOW"]

    # Step 3: LLM Grouping (Gemma-3N)
    print("")
    raw_requests = []
    
    # Handle IDONTKNOW separately (one request per topic)
    for t in idontknow_topics:
        raw_requests.append({"skill": "IDONTKNOW", "topic_ids": [t["id"]]})
    
    # Intelligent grouping for executable topics
    if executable_topics:
        if len(executable_topics) == 1:
            t = executable_topics[0]
            raw_requests.append({"skill": t["skill"], "topic_ids": [t["id"]]})
        else:
            # We pass all executable topics to the LLM
            llm_results = run_grouper_llm("executable", executable_topics, host, port, model)
            for req_str in llm_results:
                ids = [id_str.strip() for id_str in req_str.replace("REQUEST:", "").split(",")]
                # Determine the skill of the request (using the first topic's skill)
                first_topic_id = ids[0] if ids else None
                skill = topic_map.get(first_topic_id, {}).get("skill", "shell_exec")
                raw_requests.append({"skill": skill, "topic_ids": ids})

    # Final Step: Sort and Number Requests with Titles
    def get_min_topic_idx(req):
        return min([int(tid.replace("TOPIC", "")) for tid in req["topic_ids"]])

    raw_requests.sort(key=get_min_topic_idx)
    
    final_requests = []
    print("\nFinal Grouped Requests:")
    for i, req in enumerate(raw_requests, 1):
        req_id = f"REQUEST{i}"
        
        # Build topic string like "TOPIC3(Find smallest file), TOPIC4(Display smallest file)"
        topic_parts = []
        for tid in req["topic_ids"]:
            t_info = topic_map.get(tid, {})
            title = t_info.get("title", "Unknown")
            topic_parts.append(f"{tid}({title})")
            
        topic_str = ", ".join(topic_parts)
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
