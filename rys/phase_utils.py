#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase Utilities (v1.0)
Common functions for RYS phase scripts.
"""

import os
import re
from typing import List, Optional
from invoke_role import invoke_role_api

def call_role(script_dir: str, role: str, prompt: str, config, colors, 
              skills=None, include_skills=False, risks=None) -> str:
    """Invokes a specific role through the centralized invoke_role_api."""
    return invoke_role_api(role, prompt, config, colors, 
                           skills=skills, include_skills=include_skills, risks=risks)

def parse_steps(text: str) -> List[str]:
    """Parses various step-list formats into individual steps.
    Includes protection against redundant or hallucinated repetitions.
    """
    steps = []
    # Matches: "1. text", "- Step 1: text", "Step 1: text", "* 1. text"
    pattern = re.compile(r"^(?:[\-\*\s]*)(?:Step\s+)?(\d+)[\.\:]?\s*(.*)", re.IGNORECASE)
    
    seen_descriptions = set()
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if match:
            desc = match.group(2).strip()
            # Ignore empty, exact duplicates, or too many steps (safety)
            if desc and desc not in seen_descriptions:
                steps.append(desc)
                seen_descriptions.add(desc)
        
        if len(steps) >= 20: # Hard limit to prevent loop-de-loop
            break
    return steps
