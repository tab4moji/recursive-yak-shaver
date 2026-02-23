#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4: Job Processing Loop (v1.4)
Analyzes I/O types and integrates raw task data for complete information.
"""

import sys
import json
import subprocess
from typing import Dict
from phase_utils import get_common_parser, load_phase_json

def run_analyzer_llm(job: Dict, task_map: Dict, host: str, port: str, model: str) -> Dict:
    """Step 4-A: Structured Analysis using LLM."""
    input_text = f"Job: {', '.join(job['tasks'])}\n"
    for tid in job['tasks']:
        t_info = task_map.get(tid, {})
        input_text += f"  {tid}: {t_info.get('raw', '')}\n"

    cmd = [
        "python3", "./rys/invoke_role.py",
        f"--host={host}",
        "--role=analyzer",
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
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as jde:
                sys.stderr.write(f"JSON Decode Error: {jde}\nRaw snippet: {json_str}\n")
                return {"tasks": []}

        sys.stderr.write(f"No JSON found in LLM output: {out_text[:200]}...\n")
        return {"tasks": []}
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Subprocess Error calling analyzer LLM: {e}\n")
        return {"tasks": []}

def main():
    """Main execution loop for Phase 4 Job processing."""
    parser = get_common_parser("Phase 4: Job Processing Loop")
    args = parser.parse_args()

    p3_data = load_phase_json(args.in_json)

    task_map = {t["id"]: t for t in p3_data.get("all_tasks", [])}

    print(f"Job Processing Phase starting for: {args.uuid}\n")

    final_integrated_jobs = []

    for job in p3_data.get("grouped_jobs", []):
        print(f"--- Handling {job['id']} ({job['skill']}) ---")

        if job['skill'] == "IDONTKNOW":
            print("Skipping analysis for IDONTKNOW skill.")
            structured_job = {
                "job_id": job["id"],
                "skill": job["skill"],
                "tasks": []
            }
        else:
            # Phase 4-A: LLM Analysis
            print("Phase4-A: Analyzing structure...")
            analysis_data = run_analyzer_llm(job, task_map, args.host, args.port, args.model)

            # Phase 4-B: Information Integration
            print("Phase4-B: Integrating raw task data...")
            integrated_tasks = []
            for a_task in analysis_data.get("tasks", []):
                tid = a_task.get("id")
                raw_info = task_map.get(tid, {})

                # Merge: Analysis + Raw Data
                merged_task = {
                    "id": tid,
                    "title": raw_info.get("title", "Unknown"),
                    "raw": raw_info.get("raw", ""),
                    "input": a_task.get("input"),
                    "output": a_task.get("output"),
                    "loop": a_task.get("loop", False)
                }
                # Keep any other fields from analysis (like hints)
                for k, v in a_task.items():
                    if k not in merged_task:
                        merged_task[k] = v
                
                integrated_tasks.append(merged_task)

            structured_job = {
                "job_id": job["id"],
                "skill": job["skill"],
                "tasks": integrated_tasks
            }

        final_integrated_jobs.append(structured_job)

        # Display the final complete information package
        print(json.dumps(structured_job, indent=2))
        print("")

    # Save the complete information for Phase 5
    p3_data["integrated_jobs"] = final_integrated_jobs
    with open(args.out_json, 'w', encoding='utf-8') as f:
        json.dump(p3_data, f, indent=2)

if __name__ == "__main__":
    main()
