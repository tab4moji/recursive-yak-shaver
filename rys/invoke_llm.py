#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Invoke LLM Wrapper v1.3

Purpose:
  Wraps the existing chat_core to execute with some options hidden from help.
  Fixes argument parsing for boolean flags.

History:
  2. 2026-02-07 Refactored for Pylint compliance
"""
# pylint: disable=duplicate-code,useless-return,broad-exception-caught

import argparse
import sys
import os

# Import from chat_core in the actual environment
# Adjust path if necessary to find chat_core
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

try:
    from chat_core import run_chat_session
except ImportError:
    # Fallback if running from a different CWD
    sys.path.append(os.path.join(SCRIPT_DIR, "../rys"))
    from chat_core import run_chat_session


def main() -> None:
    """
    Main execution routine.
    """
    parser = argparse.ArgumentParser(
        description="Chat Tester v7 - OpenAI Compatible Client"
    )

    # Connection (Visible)
    parser.add_argument("--host", default="localhost", help="Target Host IP")
    parser.add_argument("--port", "-p", help="Target Port")
    parser.add_argument(
        "--model", "-m", default="gemma3n:e4b", help="Model name"
    )
    parser.add_argument(
        "--insecure", "-k", action="store_true",
        help="Skip SSL certificate verification"
    )

    # Context (Visible)
    parser.add_argument(
        "--system", "-s",
        default="You are a helpful assistant.",
        help="System prompt"
    )
    parser.add_argument("--prompt", help="Initial prompt (reads from stdin if omitted)")

    # ---------------------------------------------------------
    # Internal Options (Hidden / Controlled)
    # ---------------------------------------------------------
    # Default is Quiet Mode (quit=True).
    # Use --interactive to turn off quiet mode.
    parser.add_argument(
        "--interactive", action="store_false", dest="quit",
        default=True, help=argparse.SUPPRESS
    )

    # Default is Streaming (stream=True).
    parser.add_argument(
        "--no-stream", action="store_false", dest="stream",
        default=True, help=argparse.SUPPRESS
    )

    # Default is Color enabled (no_color=False).
    parser.add_argument(
        "--no-color", action="store_true", default=False, help=argparse.SUPPRESS
    )

    parser.add_argument("--session-file", help=argparse.SUPPRESS)
    parser.add_argument("--session-json", help=argparse.SUPPRESS)

    try:
        args = parser.parse_args()

        # Handle stdin if prompt is missing
        if args.prompt is None and not sys.stdin.isatty():
            args.prompt = sys.stdin.read().strip()

        if not args.prompt and args.quit:
            # If still no prompt and in quiet mode, we have nothing to do
            parser.error("the following arguments are required: --prompt (or provide via stdin)")

        run_chat_session(args)

    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)

    return None


if __name__ == "__main__":
    main()
