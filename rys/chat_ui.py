#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 0.2: Terminal UI Utilities
# リポジトリ規約に基づき pylint の指摘事項を修正
"""
Terminal UI Utilities (v0.2)

History:
  1. 2026-02-07 Initial version
  2. 2026-02-07 Added output handlers from chat_core.py
"""
# pylint: disable=useless-return

import sys
import unicodedata
from typing import Iterator

# Attempt to import readline for input handling side-effects
try:
    import readline  # pylint: disable=unused-import
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False


class TerminalColors:
    """Manages ANSI color codes and readline escape sequences."""
    # pylint: disable=too-many-instance-attributes

    def __init__(self, enable_color: bool = True):
        self.reset_code = ""
        self.user_color = ""
        self.ai_color = ""
        self.sys_color = ""
        self.err_color = ""
        self.skill_color = ""
        self.prompt_prefix = ""
        self.prompt_suffix = ""

        if enable_color:
            self.reset_code = "\033[0m"
            self.user_color = "\033[36m"  # Cyan
            self.ai_color = "\033[32m"    # Green
            self.sys_color = "\033[33m"   # Yellow
            self.err_color = "\033[31m"   # Red
            self.skill_color = "\033[92m" # Bright Green

            if HAS_READLINE:
                self.prompt_prefix = f"\001{self.user_color}\002"
                self.prompt_suffix = f"\001{self.reset_code}\002"
            else:
                self.prompt_prefix = self.user_color
                self.prompt_suffix = self.reset_code

    def colorize(self, text: str, color_code: str) -> str:
        """Wraps text with the specified color code and reset code."""
        res = text
        if self.reset_code:
            res = f"{color_code}{text}{self.reset_code}"
        return res

    def wrap_error(self, text: str) -> str:
        """Wraps text specifically in the error color."""
        return self.colorize(text, self.err_color)


def get_char_width(char: str) -> int:
    """Returns the visual width of a character."""
    width = 1
    if unicodedata.east_asian_width(char) in ('W', 'F'):
        width = 2
    return width


def get_str_width(text: str) -> int:
    """Returns the total visual width of a string."""
    return sum(get_char_width(c) for c in text)


def clear_console_line(text_width: int) -> None:
    """Clears the current line based on text width."""
    sys.stdout.write("\r" + " " * text_width + "\r")
    sys.stdout.flush()
    return None


def handle_interactive_output(
    stream_gen: Iterator[str],
    colors: TerminalColors,
    status_msg: str,
    silent: bool = False
) -> str:
    """Handles output for interactive mode with UI updates."""
    ai_prefix = f"{colors.ai_color}AI  > {colors.reset_code}"
    full_response = ""
    time_to_wait = True

    for chunk in stream_gen:
        if not silent and time_to_wait:
            clear_console_line(get_str_width(status_msg))
            sys.stdout.write(ai_prefix)
            sys.stdout.flush()
            time_to_wait = False

        if not silent:
            sys.stdout.write(chunk)
            sys.stdout.flush()
        full_response += chunk

    if not silent and time_to_wait:
        clear_console_line(get_str_width(status_msg))

    if not silent:
        sys.stdout.write("\n")
        sys.stdout.flush()
    return full_response


def handle_quiet_output(
    stream_gen: Iterator[str],
    stream_output: bool,
    silent: bool = False
) -> str:
    """Handles output for quiet mode (pipes/scripts)."""
    full_response = ""

    for chunk in stream_gen:
        if stream_output and not silent:
            sys.stdout.write(chunk)
            sys.stdout.flush()
        full_response += chunk

    if not stream_output and not silent:
        sys.stdout.write(full_response)
        sys.stdout.flush()

    if not silent and full_response and not full_response.endswith("\n"):
        sys.stdout.write("\n")
        sys.stdout.flush()

    return full_response
