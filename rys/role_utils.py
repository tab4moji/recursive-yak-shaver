#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Role Loading and Prompt Construction Utilities (v0.1)

History:
  1. 2026-02-07 Initial version (split from invoke_role.py)
"""
# pylint: disable=useless-return

import os
import json
from typing import List, Optional, Any


def load_file_content(filepath: str) -> str:
    """Reads and returns content from a file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f_in:
        content = f_in.read().strip()

    return content


def _get_skills_data(config_dir: str) -> str:
    """Locates and reads skills.json or default_skills.json."""
    skills_path = os.path.join(config_dir, "skills.json")
    if not os.path.exists(skills_path):
        skills_path = os.path.join(config_dir, "default_skills.json")
    return load_file_content(skills_path)


def _filter_skills(data: Any, filter_ids: List[str]) -> Any:
    """Filters skills data by ID."""
    available_ids = set()
    result = data

    if isinstance(data, list):
        available_ids = {
            item.get("id") for item in data
            if isinstance(item, dict) and "id" in item
        }
    elif isinstance(data, dict):
        available_ids = set(data.keys())
    else:
        raise ValueError("skills.json has an unknown structure. Cannot filter.")

    missing = [s for s in filter_ids if s not in available_ids]
    if missing:
        raise ValueError(f"Requested skills not found: {', '.join(missing)}")

    if isinstance(data, list):
        result = [item for item in data if isinstance(item, dict) and item.get("id") in filter_ids]
    elif isinstance(data, dict):
        result = {k: v for k, v in data.items() if k in filter_ids}

    return result


def load_skills_content(config_dir: str, filter_skills: Optional[List[str]]) -> str:
    """Loads skills and filters them if requested."""
    content = _get_skills_data(config_dir)
    try:
        data = json.loads(content)
        if filter_skills is not None:
            data = _filter_skills(data, filter_skills)
        formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
    except json.JSONDecodeError as exc:
        if filter_skills is not None:
            raise ValueError("skills.json is invalid JSON. Cannot apply filter.") from exc
        formatted_json = content
    return formatted_json


def load_risks_content(risks_path: str) -> str:
    """Loads content from the risks JSON file."""
    content = load_file_content(risks_path)
    try:
        json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Risk definition file is invalid JSON: {risks_path}") from exc
    return content


def construct_system_prompt(
    base_dir: str,
    role_name: str,
    skill_filter: Optional[List[str]],
    include_skills: bool,
    risks_file: Optional[str]
) -> str:
    """Combines role, constraints, skills, and risks into a system prompt."""
    roles_dir = os.path.join(base_dir, "roles")
    config_dir = os.path.join(base_dir, "config")
    parts = []

    parts.append(load_file_content(os.path.join(roles_dir, f"role_{role_name}.md")))

    common_file = os.path.join(roles_dir, "role_common_constraints.md")
    if os.path.exists(common_file):
        parts.append("\n# Common Constraints\n" + load_file_content(common_file))

    if include_skills:
        skills_text = load_skills_content(config_dir, skill_filter)
        parts.append(f"\n# Available Skills definition\n```json\n{skills_text}\n```")

    if risks_file:
        r_path = risks_file if os.path.exists(risks_file) else os.path.join(config_dir, risks_file)
        if not os.path.exists(r_path):
            r_path = os.path.join(config_dir, "risks.json")
        if os.path.exists(r_path):
            r_text = load_risks_content(r_path)
            parts.append(f"\n# Risk Knowledge Base\n```json\n{r_text}\n```")

    return "\n".join(parts)
