#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 0.9: Invoke Role Wrapper
# リポジトリ規約に基づき pylint の指摘事項を修正
"""
Invoke Role Wrapper (v0.9)
Centralized hub for all role-based LLM interactions with analysis capabilities.
"""
# pylint: disable=duplicate-code,useless-return,broad-exception-caught

import sys
import os
import argparse
import json
from typing import List, Optional

# Setup path at the very top to satisfy pylint
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# pylint: disable=wrong-import-position
from chat_core import process_turn
from role_utils import construct_system_prompt
from chat_types import ChatConfig
from chat_ui import TerminalColors
from chat_api import build_base_url


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


def invoke_role_api(role: str, prompt: str, config: ChatConfig, colors: TerminalColors,
                    skills: Optional[List[str]] = None,
                    include_skills: bool = False,
                    include_cheatsheet: bool = True,
                    risks: Optional[str] = None,
                    analyze: bool = False,
                    debug: bool = False) -> str:
    """Centralized API for invoking roles. All LLM calls pass through here."""
    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    base_dir = os.path.dirname(SCRIPT_DIR)

    # 1. System Prompt Construction
    system_prompt = construct_system_prompt(
        base_dir, role, skills, include_skills, risks, include_cheatsheet
    )

    if debug:
        print(f"\n{colors.sys_color}=== [DEBUG: SYSTEM PROMPT] ==={colors.reset_code}")
        display_prompt = system_prompt
        if colors.skill_color:
            sections = ["\n# Available Skills definition", "\n# Tool Reference / Cheatsheets"]
            for section in sections:
                if section in display_prompt:
                    display_prompt = display_prompt.replace(
                        section, f"\n{colors.skill_color}{section.lstrip()}"
                    )
            display_prompt = display_prompt.replace(
                "\n# Risk Knowledge Base",
                f"{colors.reset_code}\n# Risk Knowledge Base"
            )
            # Final safety reset
            if colors.skill_color in display_prompt:
                last_part = display_prompt.rsplit(colors.skill_color, maxsplit=1)[-1]
                if colors.reset_code not in last_part:
                    display_prompt += colors.reset_code
        print(display_prompt)
        print(f"{colors.sys_color}=== [DEBUG: USER PROMPT] ==={colors.reset_code}")
        print(prompt)
        print(f"{colors.sys_color}=============================={colors.reset_code}\n")
    elif analyze:
        print(f"\n{colors.sys_color}=== [ANALYSIS: SYSTEM PROMPT] ==={colors.reset_code}")
        print(system_prompt)
        print(f"{colors.sys_color}==================================={colors.reset_code}\n")

    # 2. Execution
    messages = [{"role": "system", "content": system_prompt}]
    process_turn(config, messages, colors, prompt_text=prompt)
    response = messages[-1]["content"]

    # 3. Post-Process Analysis
    if analyze:
        print(f"\n{colors.sys_color}=== [ANALYSIS: RESPONSE] ==={colors.reset_code}")
        print(f"- Role: {role}\n- Response Length: {len(response)} chars")
        print(f"- Code Blocks Detected: {'Yes' if '```' in response else 'No'}")
        if role == "engineer" and "```" in response:
            print(f"{colors.err_color}[WARNING] Architect leaked code blocks!{colors.reset_code}")
        print(f"{colors.sys_color}============================={colors.reset_code}\n")

    return response


def main() -> None:
    """Main execution routine for CLI usage."""
    parser = argparse.ArgumentParser(description="Invoke Role Wrapper")
    parser.add_argument("--role", default="gemma", help="Role name")
    parser.add_argument("--prompt", help="User prompt text")
    parser.add_argument("--skills", help="Include specific skills or 'all'.")
    parser.add_argument("--no-skills", action="store_true", help="Disable skills.")
    parser.add_argument("--risks", help="Path to risks.json file")
    parser.add_argument("--host", default="localhost", help="Target Host IP")
    parser.add_argument("--port", "-p", help="Target Port")
    parser.add_argument("--model", "-m", default="gemma3n:e4b", help="Model name")
    parser.add_argument("--insecure", "-k", action="store_true", help="Skip SSL")
    parser.add_argument("--analyze", action="store_true", help="Enable analysis")
    parser.add_argument("--debug", "-d", action="store_true", help="Show instruction/prompt")

    # Internal / Fixed args
    parser.add_argument("--interactive", action="store_false", dest="quit",
                        default=True, help=argparse.SUPPRESS)
    parser.add_argument("--no-stream", action="store_false", dest="stream",
                        default=True, help=argparse.SUPPRESS)
    parser.add_argument("--no-color", action="store_true", default=False, help=argparse.SUPPRESS)
    parser.add_argument("--system", help=argparse.SUPPRESS)
    parser.add_argument("--session-file", help=argparse.SUPPRESS)
    parser.add_argument("--session-json", help=argparse.SUPPRESS)

    try:
        args = parser.parse_args()
        if args.prompt is None and not sys.stdin.isatty():
            args.prompt = sys.stdin.read().strip()
        if not args.prompt:
            parser.error("the following arguments are required: --prompt")

        colors = TerminalColors(enable_color=not args.no_color)
        base_url = build_base_url(args.host, args.port)
        config = ChatConfig(
            api_url=f"{base_url.rstrip('/')}/v1/chat/completions",
            model=args.model, quiet_mode=args.quit,
            stream_output=args.stream, insecure=args.insecure
        )

        # Skill Logic
        include_skills = not args.no_skills
        skill_filter = None
        include_cheatsheet = False
        if args.skills and args.skills.lower() != 'all':
            skill_filter = parse_skills_arg(args.skills)
            include_cheatsheet = True

        invoke_role_api(args.role, args.prompt, config, colors,
                        skills=skill_filter, include_skills=include_skills,
                        include_cheatsheet=include_cheatsheet,
                        risks=args.risks, analyze=args.analyze, debug=args.debug)

    except Exception as exc:  # pylint: disable=broad-exception-caught
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)

    return None


if __name__ == "__main__":
    main()
