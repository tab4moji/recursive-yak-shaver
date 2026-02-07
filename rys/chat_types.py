#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat Types and Constants (v0.1)

History:
  1. 2026-02-07 Initial version (split from chat_core.py)
"""
# pylint: disable=useless-return

from dataclasses import dataclass

@dataclass
class ChatConfig:
    """Holds configuration for the chat session."""
    api_url: str
    model: str
    quiet_mode: bool
    stream_output: bool
    insecure: bool = False

    def __post_init__(self) -> None:
        """Validation after initialization."""
        return None
