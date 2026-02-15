#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6: Final Execution (v1.1)
Executes scripts generated in Phase 5.
"""

import sys
import os
import json
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-json", required=True)
    parser.add_argument("--auto", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.in_json): sys.exit(1)
    with open(args.in_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scripts = data.get("generated_scripts", [])
    if not scripts:
        print("No scripts to execute.")
        return

    print(">>> Phase 6: Execution Phase")
    for s in scripts:
        print(f"==================================================")
        print(f"Executing {s['request_id']} ({s['skill']})")
        print(f"Path: {s['path']}")
        print(f"--------------------------------------------------")
        
        # Display script content
        try:
            with open(s['path'], 'r', encoding='utf-8') as f:
                print(f.read())
        except Exception as e:
            print(f"(Error reading script: {e})")
        
        print(f"--------------------------------------------------")
        
        if not args.auto:
            choice = input("Execute? [y/N]: ").strip().lower()
            if choice != 'y':
                print("Skipped.")
                continue
        
        subprocess.run(s['path'], shell=True)
        print("--------------------------------------------------\n")

if __name__ == "__main__":
    main()
