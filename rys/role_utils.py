#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Role Loading and Prompt Construction Utilities (v0.3)
Adds 'Cheatsheet' injection from skills.
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
    if not os.path.exists(skills_path):
        return "[]" # Return empty list json if no file found
    return load_file_content(skills_path)


def _filter_skills_list(data: List[Dict[str, Any]], filter_ids: List[str]) -> List[Dict[str, Any]]:
    """Helper to filter list of skill dicts."""
    available_ids = {
        item.get("id") for item in data
        if isinstance(item, dict) and "id" in item
    }
    # Relaxed check: Don't raise error if skill is missing, just ignore (fallback to general)
    return [item for item in data if isinstance(item, dict) and item.get("id") in filter_ids]


def load_skills_data(config_dir: str, filter_skills: Optional[List[str]]) -> Any:
    """Loads skills as a Python object (List or Dict), filtering if requested."""
    content = _get_skills_data(config_dir)
    try:
        data = json.loads(content)
        if filter_skills is not None and isinstance(data, list):
            data = _filter_skills_list(data, filter_skills)
    except json.JSONDecodeError as exc:
        print(f"Warning: skills.json is invalid. {exc}")
        data = []
    return data


def load_skill_detail(config_dir: str, skill_id: str) -> str:
    """Loads detailed skill definition from config/skills/<id>.json"""
    path = os.path.join(config_dir, "skills", f"{skill_id}.json")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # チートシートをMarkdown形式に変換してプロンプト用に整形
            lines = [f"### Skill Cheat Sheet: {data.get('name', skill_id)}"]

            if "guidelines" in data:
                lines.append("#### Guidelines")
                for g in data["guidelines"]:
                    lines.append(f"- {g}")

            if "patterns" in data:
                lines.append("#### Recommended Patterns (Few-Shot)")
                for p in data["patterns"]:
                    lines.append(f"- Task: {p['task']}")
                    lines.append(f"  - Recommended: `{p['recommended']}`")
                    lines.append(f"  - Input: {p.get('input_type', 'Any')} -> Output: {p.get('output_type', 'Any')}")

            return "\n".join(lines)
        except Exception:
            return ""
    return ""


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

    # 1. Base Role
    parts.append(load_file_content(os.path.join(roles_dir, f"role_{role_name}.md")))

    # 2. Common Constraints
    common_file = os.path.join(roles_dir, "role_common_constraints.md")
    if os.path.exists(common_file):
        parts.append("\n# Common Constraints\n" + load_file_content(common_file))

    # 3. Skills & Cheatsheets
    if include_skills:
        skills_data = load_skills_data(config_dir, skill_filter)
        
        # Add Cheatsheets (The "Context" for ICL)
        cheatsheets = []
        if isinstance(skills_data, list):
            for skill in skills_data:
                cs = skill.get("cheatsheet")
                if cs:
                    cheatsheets.append(f"## Reference for [{skill.get('id')}]\n{cs}")
        
        if cheatsheets:
            parts.append("\n# Tool Reference / Cheatsheets (USE THESE PATTERNS)\n" + "\n\n".join(cheatsheets))
        
        # Add Policy if exists
        for skill in (skills_data if isinstance(skills_data, list) else []):
            policy = skill.get("generation_policy")
            if policy:
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
