#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Invoke Role Wrapper (v0.6)
Update: Added --risks support for the Auditor role.

History:
  2. 2026-02-07 Refactored and split for Pylint compliance
"""
# pylint: disable=duplicate-code,useless-return,broad-exception-caught

import sys
import os
import argparse
import json
from typing import List, Optional

from chat_core import run_chat_session
from role_utils import construct_system_prompt

# Setup path to import chat_core
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)


def parse_skills_arg(value: Optional[str]) -> Optional[List[str]]:
    """Parses the --skills argument value."""
    if value is None:
        return None

    val = value.strip()
    if val.startswith("[") and val.endswith("]"):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return [str(p) for p in parsed]
        except json.JSONDecodeError:
            pass

    return [s.strip() for s in val.split(',') if s.strip()]


def main() -> None:
    """Main execution routine."""
    parser = argparse.ArgumentParser(description="Invoke Role Wrapper")
    parser.add_argument("--role", required=True, help="Role name")
    parser.add_argument("--prompt", help="User prompt text")
    parser.add_argument(
        "--skills", nargs='?', const='__ALL__', default=argparse.SUPPRESS,
        help="Include skills."
    )
    parser.add_argument("--risks", help="Path to risks.json file")
    parser.add_argument("--host", default="localhost", help="Target Host IP")
    parser.add_argument("--port", "-p", help="Target Port")
    parser.add_argument("--model", "-m", default="gemma3n:e4b", help="Model name")
    parser.add_argument(
        "--insecure", "-k", action="store_true",
        help="Skip SSL certificate verification"
    )

    # Internal / Fixed args
    parser.add_argument(
        "--interactive", action="store_false", dest="quit",
        default=True, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--no-stream", action="store_false", dest="stream",
        default=True, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--no-color", action="store_true", default=True, help=argparse.SUPPRESS
    )
    parser.add_argument("--system", help=argparse.SUPPRESS)
    parser.add_argument("--session-file", help=argparse.SUPPRESS)
    parser.add_argument("--session-json", help=argparse.SUPPRESS)

    try:
        args = parser.parse_args()
        if args.prompt is None and not sys.stdin.isatty():
            args.prompt = sys.stdin.read().strip()
        if not args.prompt:
            parser.error("the following arguments are required: --prompt (or provide via stdin)")

        include_skills = 'skills' in args
        skill_filter = None
        if include_skills:
            if args.skills == '__ALL__':
                skill_filter = None
            else:
                skill_filter = parse_skills_arg(args.skills)

        base_dir = os.path.dirname(SCRIPT_DIR)
        args.system = construct_system_prompt(
            base_dir, args.role, skill_filter, include_skills, args.risks
        )
        run_chat_session(args)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)

    return None


if __name__ == "__main__":
    main()
