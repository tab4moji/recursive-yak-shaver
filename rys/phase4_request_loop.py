#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4: REQUEST Processing Loop (v1.3)
Analyzes I/O types and integrates raw topic data for complete information.
"""

import sys
import os
import json
import argparse
import subprocess
import re
from typing import Dict, List, Any

def run_analyzer_llm(req: Dict, topic_map: Dict, host: str, port: str, model: str) -> Dict:
    """Step 4-A: Structured Analysis using LLM."""
    input_text = f"REQUEST: {', '.join(req['topics'])}\n"
    for tid in req['topics']:
        t_info = topic_map.get(tid, {})
        input_text += f"  {tid}: {t_info.get('raw', '')}\n"

    cmd = [
        "python3", "./rys/invoke_role.py",
        f"--host={host}",
        f"--role=analyzer",
        f"--prompt={input_text}",
        f"--model={model}",
        "--no-skills"
    ]
    if port:
        cmd.append(f"--port={port}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        out_text = result.stdout.strip()
        
        # Robustly find the JSON part
        start_idx = out_text.find('{')
        end_idx = out_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = out_text[start_idx:end_idx+1]
            return json.loads(json_str)
        
        return {"topics": []}
    except Exception as e:
        sys.stderr.write(f"Error calling analyzer LLM: {e}\n")
        return {"topics": []}

def main():
    parser = argparse.ArgumentParser(description="Phase 4: REQUEST Processing Loop")
    parser.add_argument("--in-json", required=True, help="Path to Phase 3 output JSON")
    parser.add_argument("--out-json", required=True, help="Path to save Phase 4 output JSON")
    parser.add_argument("--host", default="localhost", help="LLM Host")
    parser.add_argument("--port", help="LLM Port")
    parser.add_argument("--model", default="gemma3n:e4b", help="LLM Model")
    parser.add_argument("--uuid", help="Session UUID")
    
    args = parser.parse_args()

    if not os.path.exists(args.in_json):
        sys.exit(1)

    with open(args.in_json, 'r', encoding='utf-8') as f:
        p3_data = json.load(f)

    grouped_requests = p3_data.get("grouped_requests", [])
    topic_map = {t["id"]: t for t in p3_data.get("all_topics", [])}

    print(f"REQUEST Processing Phase starting for: {args.uuid}\n")

    final_integrated_requests = []

    for req in grouped_requests:
        print(f"--- Handling {req['id']} ({req['skill']}) ---")
        
        if req['skill'] == "IDONTKNOW":
            print(f"Skipping analysis for IDONTKNOW skill.")
            structured_req = {
                "request_id": req["id"],
                "skill": req["skill"],
                "topics": []
            }
        else:
            # Phase 4-A: LLM Analysis
            print(f"Phase4-A: Analyzing structure...")
            analysis_data = run_analyzer_llm(req, topic_map, args.host, args.port, args.model)
            analyzed_topics = analysis_data.get("topics", [])
            
            # Phase 4-B: Information Integration
            print(f"Phase4-B: Integrating raw topic data...")
            integrated_topics = []
            for a_topic in analyzed_topics:
                tid = a_topic.get("id")
                raw_info = topic_map.get(tid, {})
                
                # Merge: Analysis + Raw Data
                full_topic = {
                    "id": tid,
                    "title": raw_info.get("title", "Unknown"),
                    "raw": raw_info.get("raw", ""),
                    "input": a_topic.get("input"),
                    "output": a_topic.get("output")
                }
                integrated_topics.append(full_topic)
            
            structured_req = {
                "request_id": req["id"],
                "skill": req["skill"],
                "topics": integrated_topics
            }
        
        final_integrated_requests.append(structured_req)
        
        # Display the final complete information package
        print(json.dumps(structured_req, indent=2))
        print("")

    # Save the complete information for Phase 5
    p3_data["integrated_requests"] = final_integrated_requests
    with open(args.out_json, 'w', encoding='utf-8') as f:
        json.dump(p3_data, f, indent=2)

if __name__ == "__main__":
    main()
