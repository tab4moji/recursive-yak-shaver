#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Role Loading and Prompt Construction Utilities (v0.2)

History:
  1. 2026-02-07 Initial version
  2. 2026-02-08 Added dynamic generation_policy injection (Code as Policy)
"""
# pylint: disable=useless-return

import os
import json
from typing import List, Optional, Any, Dict


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


def _filter_skills_list(data: List[Dict[str, Any]], filter_ids: List[str]) -> List[Dict[str, Any]]:
    """Helper to filter list of skill dicts."""
    available_ids = {
        item.get("id") for item in data
        if isinstance(item, dict) and "id" in item
    }
    missing = [s for s in filter_ids if s not in available_ids]
    if missing:
        raise ValueError(f"Requested skills not found: {', '.join(missing)}")

    return [item for item in data if isinstance(item, dict) and item.get("id") in filter_ids]


def _filter_skills(data: Any, filter_ids: List[str]) -> Any:
    """Filters skills data by ID."""
    result = data

    if isinstance(data, list):
        result = _filter_skills_list(data, filter_ids)
    elif isinstance(data, dict):
        available_ids = set(data.keys())
        missing = [s for s in filter_ids if s not in available_ids]
        if missing:
            raise ValueError(f"Requested skills not found: {', '.join(missing)}")
        result = {k: v for k, v in data.items() if k in filter_ids}
    else:
        raise ValueError("skills.json has an unknown structure. Cannot filter.")

    return result


def load_skills_data(config_dir: str, filter_skills: Optional[List[str]]) -> Any:
    """Loads skills as a Python object (List or Dict), filtering if requested."""
    content = _get_skills_data(config_dir)
    try:
        data = json.loads(content)
        if filter_skills is not None:
            data = _filter_skills(data, filter_skills)
    except json.JSONDecodeError as exc:
        if filter_skills is not None:
            raise ValueError("skills.json is invalid JSON. Cannot apply filter.") from exc
        # Fallback to empty list or raise is better.
        raise ValueError(f"skills.json is invalid JSON: {exc}") from exc
    return data


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

    # 1. Base Role Definition
    parts.append(load_file_content(os.path.join(roles_dir, f"role_{role_name}.md")))

    # 2. Common Constraints
    common_file = os.path.join(roles_dir, "role_common_constraints.md")
    if os.path.exists(common_file):
        parts.append("\n# Common Constraints\n" + load_file_content(common_file))

    # 3. Skills & Policies
    if include_skills:
        # Load the data object to extract policies
        skills_data = load_skills_data(config_dir, skill_filter)

        # Dump for the main skills block
        skills_text = json.dumps(skills_data, indent=2, ensure_ascii=False)
        parts.append(f"\n# Available Skills definition\n```json\n{skills_text}\n```")

        # Dynamic Policy Injection
        # Normalize to list for iteration
        skill_list = []
        if isinstance(skills_data, list):
            skill_list = skills_data
        elif isinstance(skills_data, dict):
            # If dict-based skills (id -> content), just take values
            skill_list = list(skills_data.values())

        for skill in skill_list:
            if isinstance(skill, dict):
                policy = skill.get("generation_policy")
                if policy:
                    # Inject specific instructions for this skill
                    parts.append(f"\n# Specific Instructions for [{skill.get('id', 'Unknown')}]\n{policy}")

    # 4. Risks
    if risks_file:
        r_path = risks_file if os.path.exists(risks_file) else os.path.join(config_dir, risks_file)
        if not os.path.exists(r_path):
            r_path = os.path.join(config_dir, "risks.json")
        if os.path.exists(r_path):
            r_text = load_risks_content(r_path)
            parts.append(f"\n# Risk Knowledge Base\n```json\n{r_text}\n```")

    return "\n".join(parts)
