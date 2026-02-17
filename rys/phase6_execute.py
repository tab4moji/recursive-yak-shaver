#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6: Final Execution (v1.2)
Executes scripts generated in Phase 5.

History:
1. 2026-02-17 Initial version (v1.1).
2. 2026-02-17 v1.2: Fixed Pylint issues (trailing whitespace, docstrings,
   f-strings, broad exception handling, subprocess check).
"""

import sys
import os
import json
import argparse
import subprocess

def main():
    """Main execution entry point for Phase 6."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-json", required=True)
    parser.add_argument("--auto", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.in_json):
        sys.exit(1)
    with open(args.in_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scripts = data.get("generated_scripts", [])
    if not scripts:
        print("No scripts to execute.")
        return

    print(">>> Phase 6: Execution Phase")
    cache_dir = os.environ.get("RYS_CACHE_DIR", "")

    for s in scripts:
        path = s['path']

        # Path Correction Logic:
        # If the path in JSON is missing, try looking for the filename in the current RYS_CACHE_DIR
        if not os.path.exists(path) and cache_dir:
            filename = os.path.basename(path)
            alt_path = os.path.join(cache_dir, filename)
            if os.path.exists(alt_path):
                path = alt_path

        print("==================================================")
        print(f"Executing {s['request_id']} ({s['skill']})")
        print(f"Path: {path}")
        print("--------------------------------------------------")

        # Display script content
        try:
            with open(path, 'r', encoding='utf-8') as f:
                print(f.read())
        except OSError as e:
            print(f"(Error reading script: {e})")

        print("--------------------------------------------------")

        if not args.auto:
            choice = input("Execute? [y/N]: ").strip().lower()
            if choice != 'y':
                print("Skipped.")
                continue

        subprocess.run(path, shell=True, check=False)
        print("--------------------------------------------------\n")

if __name__ == "__main__":
    main()
