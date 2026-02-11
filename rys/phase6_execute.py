#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5: Execution (v1.0)
Iterates through generated scripts and asks for execution.
"""

import sys
import os
import argparse
import json
import subprocess

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-json", required=True)
    args = parser.parse_args()

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
                print(f.read())
        except OSError:
            print("  (Could not read file)")

        choice = input(">> Execute this script? [y/N]: ").strip().lower()
        if choice == 'y':
            print(">> Running...")
            subprocess.run([interpreter, target_file], check=False)
            print(">> Done.")
        else:
            print(">> Skipped.")

if __name__ == "__main__":
    main()
