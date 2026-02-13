#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5: Execution Loop (v2.0)
Iterates through generated scripts and asks for execution.
Renamed from Phase 6 to Phase 5.
"""

import sys
import os
import argparse
import json
import subprocess
from chat_ui import TerminalColors

def main():
    colors = TerminalColors(enable_color=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-json", required=True)
    parser.add_argument("--auto", action="store_true", help="Execute without prompting")
    args = parser.parse_args()

    if not os.path.exists(args.in_json):
        print(f">>> Skipping Phase 5: Input file {args.in_json} not found.")
        return

    with open(args.in_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    scripts = data.get("scripts", [])
    if not scripts:
        print("No scripts to execute.")
        return

    for script in scripts:
        target_file = script["path"]
        req_title = script["title"]
        
        if not os.path.exists(target_file):
            continue

        print("\n---------------------------------------------------")
        print(req_title)
        print(f"File: {target_file}")
        print("---------------------------------------------------")

        interpreter = "bash" if target_file.endswith(".sh") else "python3"
        
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)
                if len(content.strip().splitlines()) <= 2 and "#!" in content:
                    print(f"{colors.err_color}[WARNING] This script looks incomplete (too short).{colors.reset_code}")
        except OSError:
            print("  (Could not read file)")

        if args.auto:
            choice = 'y'
            print(">> Auto-executing...")
        else:
            choice = input(">> Execute this script? [y/N]: ").strip().lower()

        if choice == 'y':
            print(">> Running...")
            subprocess.run([interpreter, target_file], check=False)
            print(">> Done.")
        else:
            print(">> Skipped.")

if __name__ == "__main__":
    main()
