#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: Visualize (v1.1)
Reads dispatch info, returns titler output and groups via JSON.
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
import group_requests
from phase_utils import call_role

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-json", required=True)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default="11434")
    parser.add_argument("--model", default="gemma3n:e4b")
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

    with open(args.in_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    groups = group_requests.parse_input(data["dispatch_out"])
    
    visual_input = ""
    req_index = 1
    for key, descriptions in groups.items():
        status = f"[Skill: {key}]"
        if key.startswith("IDONTKNOW__"):
            reason = key.split("__", 2)[2]
            status = f"[Status: Unable to Process ({reason})]"
        visual_input += f"REQUEST {req_index} {status}:\n"
        for desc in descriptions:
            visual_input += f"- TOPIC: {desc}\n"
        visual_input += "\n"
        req_index += 1

    base_url = build_base_url(args.host, args.port)
    verify_connection(base_url)
    config = ChatConfig(api_url=f"{base_url.rstrip('/')}/v1/chat/completions", model=args.model, quiet_mode=True, stream_output=True, insecure=False)
    colors = TerminalColors(enable_color=True)

    titles_out = call_role(SCRIPT_DIR, "titler", visual_input, config, colors)
    
    data["groups"] = groups
    data["titles_out"] = titles_out
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
