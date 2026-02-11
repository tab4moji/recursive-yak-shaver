#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI-compatible API Connection Command. (v0.3)

History:
  1. 2025-12-29 Initial version
  2. 2026-02-07 Refactored and split into modules for Pylint compliance
  3. 2026-02-07 Further split to reduce file size < 6KiB
"""
# pylint: disable=useless-return,broad-exception-caught

import sys
import argparse
from typing import Dict, List, Optional

from chat_types import ChatConfig
from chat_ui import TerminalColors, handle_interactive_output, handle_quiet_output
from chat_api import verify_connection, load_session_data, stream_chat_completion, build_base_url


def process_turn(
    config: ChatConfig,
    messages: List[Dict[str, str]],
    colors: TerminalColors,
    prompt_text: Optional[str] = None
) -> None:
    """Orchestrates a single turn of conversation."""
    if prompt_text:
        messages.append({"role": "user", "content": prompt_text})
        if not config.quiet_mode:
            print(f"{colors.prompt_prefix}You > {colors.prompt_suffix}{prompt_text}")

    status_msg = "... thinking ..."
    if not config.quiet_mode:
        sys.stdout.write(colors.colorize(status_msg, colors.sys_color))
        sys.stdout.flush()

    stream_gen = stream_chat_completion(
        config.api_url, config.model, messages, colors, insecure=config.insecure
    )

    if not config.quiet_mode:
        full_response = handle_interactive_output(
            stream_gen, colors, status_msg, silent=config.silent_mode
        )
    else:
        full_response = handle_quiet_output(
            stream_gen, config.stream_output, silent=config.silent_mode
        )

    if "[Connection Error]" in full_response:
        if messages and messages[-1]["role"] == "user":
            messages.pop()
    else:
        messages.append({"role": "assistant", "content": full_response})

    return None


def _run_interactive_loop(
    config: ChatConfig,
    messages: List[Dict[str, str]],
    colors: TerminalColors
) -> None:
    """Runs the main interactive REPL loop."""
    print(colors.colorize("Type 'exit' to stop.\n", colors.sys_color))

    while True:
        try:
            prompt_str = f"{colors.prompt_prefix}You > {colors.prompt_suffix}"
            user_input = input(prompt_str)

            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                break

            process_turn(config, messages, colors, prompt_text=user_input)

        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"\n{colors.wrap_error(f'[CRITICAL] {exc}')}")
            break

    return None


def run_chat_session(args: argparse.Namespace) -> None:
    """Initializes and runs the chat loop or one-shot command."""
    colors = TerminalColors(enable_color=not args.no_color)
    base_url = build_base_url(args.host, args.port)
    insecure_flag = getattr(args, "insecure", False)

    verify_connection(base_url, insecure=insecure_flag)

    config = ChatConfig(
        api_url=f"{base_url.rstrip('/')}/v1/chat/completions",
        model=args.model,
        quiet_mode=args.quit,
        stream_output=args.stream,
        insecure=insecure_flag
    )

    messages = [{"role": "system", "content": args.system}]
    loaded_session = load_session_data(args.session_file, args.session_json)
    if loaded_session:
        if loaded_session[0].get("role") == "system":
            messages = loaded_session
        else:
            messages.extend(loaded_session)
        if not args.quit:
            msg = f"[Session Loaded] {len(loaded_session)} messages."
            print(colors.colorize(msg, colors.sys_color))

    initial_prompt = args.prompt
    if initial_prompt is None and not sys.stdin.isatty():
        initial_prompt = sys.stdin.read().strip()

    if args.quit:
        if initial_prompt:
            process_turn(config, messages, colors, prompt_text=initial_prompt)
    else:
        msg = f"--- Streaming Mode: {config.api_url} ({config.model}) ---"
        print(f"{colors.sys_color}{msg}{colors.reset_code}")
        if initial_prompt:
            process_turn(config, messages, colors, prompt_text=initial_prompt)
        _run_interactive_loop(config, messages, colors)

    return None


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Chat Tester v7.3 - OpenAI Compatible Client"
    )
    parser.add_argument("--host", default="localhost", help="Target Host IP")
    parser.add_argument("--port", "-p", help="Target Port")
    parser.add_argument("--model", "-m", default="gemma3n:e4b", help="Model name")
    parser.add_argument(
        "--system", "-s", default="You are a helpful assistant.",
        help="System prompt"
    )
    parser.add_argument("--prompt", help="Initial prompt")
    parser.add_argument("--session-file", help="History file path")
    parser.add_argument("--session-json", help="History JSON string")
    parser.add_argument("--quit", "-q", action="store_true", help="Quiet mode")
    parser.add_argument("--stream", action="store_true", help="Force streaming")
    parser.add_argument("--no-color", "-n", action="store_true", help="Disable color")
    parser.add_argument(
        "--insecure", "-k", action="store_true",
        help="Skip SSL certificate verification"
    )

    args = parser.parse_args()
    run_chat_session(args)
    return None


if __name__ == "__main__":
    main()
