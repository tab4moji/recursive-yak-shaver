#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Request Grouper v0.4
Description:
  Parses Dispatcher output and groups lines strictly by Skill ID.
  Outputs:
    Stdout: Markdown text for Titler (Visualization).
    File:   /tmp/.rys.tmp.exec_plan.tsv (For main.sh execution).

History:
  1. 2025-12-29 Initial version
  2. 2026-02-07 Refactored for Pylint compliance and modularity
"""
# pylint: disable=useless-return

import sys
import re
import argparse
from collections import defaultdict
from typing import Dict, List


def parse_line(line: str, idontknow_counter: int) -> tuple:
    """
    Parses a single line of dispatcher output.
    Returns (skill_id, desc, updated_counter).
    """
    skill_id = "UNKNOWN"
    desc = ""
    updated_counter = idontknow_counter

    if line.strip():
        parts = line.split('|')
        if len(parts) >= 3:
            # Original Phrase (2nd part) contains more details (e.g., "up to 100")
            desc = parts[1].strip()

            # Status (Last part)
            status_part = parts[-1].strip()

            # Robust ID Extraction
            skill_match = re.search(r'SKILLS:\s*([^\s]+)', status_part)

            if skill_match:
                skill_id = skill_match.group(1).strip()
            elif "IDONTKNOW" in status_part:
                # Create unique key for each failure
                reason = status_part.replace('IDONTKNOW:', '').strip()
                skill_id = f"IDONTKNOW__{idontknow_counter}__{reason}"
                updated_counter += 1
            elif not any(x in status_part for x in ["IDONTKNOW", "UNKNOWN"]):
                # If no SKILLS prefix, but looks like a skill ID (no spaces)
                cleaned_status = status_part.strip()
                if cleaned_status and " " not in cleaned_status:
                    skill_id = cleaned_status

    return skill_id, desc, updated_counter


def parse_input(input_data: str) -> Dict[str, List[str]]:
    """
    Parses the entire input string and groups descriptions by skill ID.
    """
    groups = defaultdict(list)
    idontknow_counter = 1

    lines = input_data.split('\n')
    for line in lines:
        skill_id, desc, idontknow_counter = parse_line(line, idontknow_counter)
        if desc:
            groups[skill_id].append(desc)

    return dict(groups)


def output_visualization(groups: Dict[str, List[str]]) -> None:
    """
    Prints the grouped requests to stdout for visualization.
    """
    req_index = 1
    for key, descriptions in groups.items():
        if key.startswith("IDONTKNOW__"):
            reason = key.split("__", 2)[2]
            print(f"REQUEST {req_index} [Status: Unable to Process ({reason})]:")
        else:
            print(f"REQUEST {req_index} [Skill: {key}]:")

        for desc in descriptions:
            print(f"- TOPIC: {desc}")

        print("")
        req_index += 1

    return None


def output_execution_plan(groups: Dict[str, List[str]], plan_file: str) -> None:
    """
    Writes the execution plan to a TSV file.
    """
    with open(plan_file, 'w', encoding='utf-8') as f:
        req_index = 1
        for key, descriptions in groups.items():
            # Skip IDONTKNOW tasks for execution plan
            if key.startswith("IDONTKNOW__") or key == "UNKNOWN":
                req_index += 1
                continue

            # One line per topic
            for desc in descriptions:
                # Line: index \t skill_id \t topic
                f.write(f"{req_index}\t{key}\t{desc}\n")
            req_index += 1

    return None


def main() -> None:
    """
    Main entry point for Request Grouper.
    """
    parser = argparse.ArgumentParser(description="Request Grouper v0.4")
    parser.add_argument("--plan-file", help="Path to save the execution plan (TSV)")
    args = parser.parse_args()

    # Read stdin
    input_data = sys.stdin.read().strip()
    if input_data:
        groups = parse_input(input_data)

        # 1. Output for Visualization (Stdout -> Titler)
        output_visualization(groups)

        # 2. Output for Execution (File -> main.sh)
        if args.plan_file:
            output_execution_plan(groups, args.plan_file)

    return None


if __name__ == "__main__":
    main()
