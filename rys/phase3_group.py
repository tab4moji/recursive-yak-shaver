#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: Grouping Phase (Entry Point)
"""

import sys
import os
import json
import argparse
from group_requests import process_grouping

def main():
    parser = argparse.ArgumentParser(description="Phase 3: Grouping Phase")
    parser.add_argument("--in-json", required=True, help="Path to Phase 2 output JSON")
    parser.add_argument("--out-json", required=True, help="Path to save Phase 3 output JSON")
    parser.add_argument("--host", default="localhost", help="LLM Host")
    parser.add_argument("--port", help="LLM Port")
    parser.add_argument("--model", default="gemma3n:e4b", help="LLM Model")
    parser.add_argument("--uuid", help="Session UUID")
    
    args = parser.parse_args()

    if not os.path.exists(args.in_json):
        sys.exit(1)

    with open(args.in_json, 'r', encoding='utf-8') as f:
        p2_data = json.load(f)

    dispatch_text = p2_data.get("content", p2_data.get("dispatch_out", ""))
    if not dispatch_text:
        sys.exit(1)

    print(f"Grouping Phase starting for: {args.uuid}\n")
    
    result = process_grouping(dispatch_text, args.host, args.port, args.model)
    
    # Save the result
    with open(args.out_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
