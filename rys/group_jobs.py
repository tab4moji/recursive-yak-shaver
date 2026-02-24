#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 1.4: Grouping Phase Core Logic
# Updated: Renamed TOPIC to Task and REQUEST to Job (v1.4)
"""
Grouping Phase Core Logic (v1.4)
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
    Parses dispatch output and groups tasks by skill.
    Returns: Dict[skill, List[task_description]]
    """
    lines = [line.strip() for line in dispatch_text.strip().split('\n') if line.strip()]
    groups = {}

    for line in lines:
        skill = "UNKNOWN"
        task = line

        if "| SKILLS: " in line:
            parts = line.split("| SKILLS: ")
            skill = parts[-1].strip()
            task = parts[0].replace("Task:", "").strip()
        elif "| IDONTKNOW: " in line:
            parts = line.split("| IDONTKNOW: ")
            skill = "IDONTKNOW"
            task = parts[0].replace("Task:", "").strip()

        groups.setdefault(skill, []).append(task)
    return groups


def run_grouper_llm(skill: str, tasks: List[Dict[str, str]],
                   host: str, port: str, model: str,
                   translated_text: str = None) -> List[str]:
    """Step 3 (Gemma-3N): Intelligent grouping."""
    print("Phase3-Step3(gemma-3n):")

    input_text = ""
    if translated_text:
        input_text += f"Context (Original Request):\n{translated_text}\n\n"

    input_text += f"  {skill}: {', '.join([t['id'] for t in tasks])}\n"
    for t in tasks:
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
            # Accept both "Job:" and "REQUEST:" (flexible format)
            if re.match(r"^(Job|REQUEST|TaskGroup)\s*:", line, re.IGNORECASE):
                print(f"  {line}")
                output_lines.append(line)
        res = output_lines
    except Exception as e:  # pylint: disable=broad-exception-caught
        sys.stderr.write(f"Error calling grouper LLM: {e}\n")
        res = [f"Job: {t['id']}" for t in tasks]

    return res

def _assign_task_ids(dispatch_text: str) -> List[Dict[str, str]]:
    """Step 1: Assign Task<N> IDs + Extract Titles."""
    print("Phase3-Step1(python):")
    lines = [line.strip() for line in dispatch_text.strip().split('\n') if line.strip()]
    all_tasks = []

    for i, line in enumerate(lines, 1):
        task_id = f"Task{i}"
        title = "Unknown"
        title_match = re.match(r"^Task:\s*(.*?)\s*\|", line)
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

        t_data = {"id": task_id, "title": title, "raw": line, "skill": skill}
        all_tasks.append(t_data)
        print(f"  {task_id}: {line}")

    return all_tasks

def _group_by_skill(all_tasks: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """Step 2: Group by Skill."""
    print("\nPhase3-Step2(python): Grouping by skill...")
    skill_groups = {}
    for t in all_tasks:
        if t["skill"] != "IDONTKNOW":
            skill_groups.setdefault(t["skill"], []).append(t)
    return skill_groups

def _normalize_task_id(tid: str) -> str:
    """Normalizes variations like 'Tas1' or '1' to 'Task1'."""
    match = re.search(r"(\d+)", tid)
    if match:
        return f"Task{match.group(1)}"
    return tid

def _llm_intelligent_grouping(skill_groups: Dict[str, List[Dict[str, str]]],
                             idontknow_tasks: List[Dict[str, str]],
                             host: str, port: str, model: str,
                             translated_text: str = None) -> List[Dict[str, Any]]:
    """Step 3: Intelligent Grouping."""
    print("")
    raw_jobs = []

    for t in idontknow_tasks:
        raw_jobs.append({"skill": "IDONTKNOW", "task_ids": [t["id"]]})

    for skill, tasks in skill_groups.items():
        if len(tasks) == 1:
            raw_jobs.append({"skill": skill, "task_ids": [tasks[0]["id"]]})
        else:
            llm_results = run_grouper_llm(skill, tasks, host, port, model, translated_text)
            if not llm_results:
                print(f"  Warning: No valid Job lines found for {skill}.")
                llm_results = [f"Job: {t['id']}" for t in tasks]

            for job_str in llm_results:
                # Strip prefix (Job:, REQUEST:, etc.) using regex
                ids_part = re.sub(r"^(Job|REQUEST|TaskGroup)\s*:\s*", "", job_str, flags=re.IGNORECASE)
                raw_ids = [id_str.strip() for id_str in ids_part.split(",")]
                ids = [_normalize_task_id(rid) for rid in raw_ids if rid]
                if ids:
                    raw_jobs.append({"skill": skill, "task_ids": ids})
    return raw_jobs

def _format_final_jobs(raw_jobs: List[Dict[str, Any]],
                        task_map: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    """Final Step: Sort and Number Jobs with Titles."""
    def get_min_task_idx(job):
        indices = []
        for tid in job["task_ids"]:
            match = re.search(r"(\d+)", tid)
            if match:
                indices.append(int(match.group(1)))
            else:
                indices.append(9999)
        return min(indices) if indices else 9999

    raw_jobs.sort(key=get_min_task_idx)

    final_jobs = []
    print("\nFinal Grouped Jobs:")
    for i, job in enumerate(raw_jobs, 1):
        job_id = f"Job{i}"
        task_parts = []
        for tid in job["task_ids"]:
            t_info = task_map.get(tid, {})
            title = t_info.get("title", "Unknown")
            task_parts.append(f"{tid}({title})")

        task_str = ", ".join(task_parts)
        display_str = f"{job_id}: {task_str}"
        print(display_str)

        final_jobs.append({
            "id": job_id, "skill": job["skill"],
            "tasks": job["task_ids"], "display": display_str
        })
    return final_jobs

def process_grouping(dispatch_text: str, host: str, port: str, model: str,
                     translated_text: str = None) -> Dict[str, Any]:
    """Processes grouping workflow."""
    all_tasks = _assign_task_ids(dispatch_text)
    task_map = {t["id"]: t for t in all_tasks}

    skill_groups = _group_by_skill(all_tasks)
    idontknow_tasks = [t for t in all_tasks if t["skill"] == "IDONTKNOW"]

    raw_jobs = _llm_intelligent_grouping(skill_groups, idontknow_tasks, host, port, model, translated_text)
    final_jobs = _format_final_jobs(raw_jobs, task_map)

    return {
        "all_tasks": all_tasks,
        "grouped_jobs": final_jobs
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
