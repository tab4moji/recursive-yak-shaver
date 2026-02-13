#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2: Dispatch (v1.1)
Reads translated prompt, returns dispatch info via JSON.
"""

import sys
import os
import argparse
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

from chat_types import ChatConfig
from chat_ui import TerminalColors
from chat_api import build_base_url, verify_connection
from phase_utils import call_role

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-json", required=True)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default="11434")
    parser.add_argument("--model", default="gemma3n:e4b")
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.in_json):
        print(f">>> Skipping Phase 2: Input file {args.in_json} not found.")
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return

    with open(args.in_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Use 'content' if available, fallback to 'translated_text'
    input_text = data.get("content", data.get("translated_text", ""))

    base_url = build_base_url(args.host, args.port)
    verify_connection(base_url)
    config = ChatConfig(api_url=f"{base_url.rstrip('/')}/v1/chat/completions", model=args.model, quiet_mode=True, stream_output=True, insecure=False)
    colors = TerminalColors(enable_color=True)

    dispatch_out = call_role(SCRIPT_DIR, "dispatcher", input_text, config, colors, include_skills=True)
    
    data["content"] = dispatch_out
    data["dispatch_out"] = dispatch_out
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
