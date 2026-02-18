#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 0.5: Role Loading and Prompt Construction Utilities
# リポジトリ規約に基づき pylint の指摘事項を修正
"""
Role Loading and Prompt Construction Utilities (v0.5)
Adds 'Cheatsheet' injection from skills. Supports authentic TOON.
"""
# pylint: disable=useless-return,broad-exception-caught

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


def _load_main_skills(config_dir: str, all_skills: List[Dict[str, Any]],
                      seen_ids: set):
    """Internal: Loads skills from main registry."""
    path = os.path.join(config_dir, "skills.json")
    if os.path.exists(path):
        try:
            data = json.loads(load_file_content(path))
            if isinstance(data, list):
                for s in data:
                    if isinstance(s, dict) and "id" in s:
                        all_skills.append(s)
                        seen_ids.add(s["id"])
        except Exception as exc:
            print(f"Warning: Failed to parse skills.json: {exc}")


def _scan_skill_files(config_dir: str, all_skills: List[Dict[str, Any]],
                      seen_ids: set):
    """Internal: Scans individual skill JSON files."""
    subdir = os.path.join(config_dir, "skills")
    if os.path.exists(subdir):
        for filename in os.listdir(subdir):
            if filename.endswith(".json"):
                s_id = filename[:-5]
                if s_id not in seen_ids:
                    try:
                        with open(os.path.join(subdir, filename), 'r',
                                  encoding='utf-8') as f_in:
                            detail = json.load(f_in)
                            all_skills.append({
                                "id": s_id,
                                "type": "primitive",
                                "description": detail.get("description", f"Auto: {s_id}"),
                                "tools": detail.get("tools", [])
                            })
                            seen_ids.add(s_id)
                    except Exception:
                        pass


def _get_all_skills(config_dir: str) -> List[Dict[str, Any]]:
    """Scans skills.json and config/skills/*.json to build a complete list."""
    all_skills = []
    seen_ids = set()
    _load_main_skills(config_dir, all_skills, seen_ids)
    _scan_skill_files(config_dir, all_skills, seen_ids)
    return all_skills


def load_skills_data(config_dir: str, filter_skills: Optional[List[str]]) -> Any:
    """Loads all discovered skills and filters them if requested."""
    all_skills = _get_all_skills(config_dir)
    res = all_skills
    if filter_skills is not None:
        res = [s for s in all_skills if s.get("id") in filter_skills]
    return res


def format_value(val: Any) -> str:
    """Formats a single value according to TOON rules."""
    if val is None:
        res = ""
    else:
        s_val = str(val)
        needs_quoting = "," in s_val or "\n" in s_val or s_val.strip() != s_val
        if needs_quoting:
            escaped = s_val.replace('"', '\\"').replace("\n", "\\n")
            res = f'"{escaped}"'
        else:
            res = s_val
    return res


def _format_toon_list(key: str, data: list, indent: str) -> str:
    """Internal: Formats list as TOON."""
    if not data:
        return f"{indent}{key}[0]{{}}:"

    if all(isinstance(item, dict) for item in data) and data:
        all_keys = []
        for item in data:
            for k in item.keys():
                if k not in all_keys:
                    all_keys.append(k)

        header = f"{indent}{key}[{len(data)}]{{{','.join(all_keys)}}}:"
        lines = [header]
        for item in data:
            row = [format_value(item.get(k, "")) for k in all_keys]
            lines.append(f"{indent}{','.join(row)}")
        res = "\n".join(lines)
    else:
        header = f"{indent}{key}[{len(data)}]:"
        lines = [header]
        for item in data:
            lines.append(f"{indent}{format_value(item)}")
        res = "\n".join(lines)
    return res


def format_as_toon(key: str, data: Any, indent_level: int = 0) -> str:
    """Converts a Python object to authentic TOON format string."""
    indent = "  " * indent_level
    if isinstance(data, list):
        res = _format_toon_list(key, data, indent)
    elif isinstance(data, dict):
        lines = []
        c_ind = indent_level
        if key:
            lines.append(f"{indent}{key}:")
            c_ind += 1
        for k, v in data.items():
            if isinstance(v, (list, dict)):
                lines.append(format_as_toon(k, v, c_ind))
            else:
                lines.append(f"{'  ' * c_ind}{k}: {format_value(v)}")
        res = "\n".join(lines)
    else:
        res = f"{indent}{key}: {format_value(data)}"
    return res


def load_skill_detail(config_dir: str, skill_id: str) -> str:
    """Loads detailed skill definition from config/skills/<id>.json as TOON."""
    path = os.path.join(config_dir, "skills", f"{skill_id}.json")
    res = ""
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f_in:
                data = json.load(f_in)
            ops = []
            for p in data.get("patterns", []):
                in_type = p.get('input_type', 'Any')
                in_def = "./" if "path" in in_type.lower() or "dir" in in_type.lower() else ""
                ops.append({
                    "operation": p['task'].lower().replace(" ", "_"),
                    "description": p['task'], "input_type": in_type,
                    "input_default": in_def, "output_type": p.get('output_type', 'Any'),
                    "recommended": p.get('recommended', '')
                })
            t_data = {"skill_id": skill_id, "operations": ops,
                      "description": f"The \"{skill_id}\" skill virtual operations."}
            res = format_as_toon("", t_data)
        except Exception:
            pass
    return res


def load_risks_content(risks_path: str) -> str:
    """Loads content from the risks JSON file."""
    content = load_file_content(risks_path)
    try:
        json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {risks_path}") from exc
    return content


def _add_cheatsheets(config_dir: str, skills_data: list, parts: list):
    """Internal: Adds cheatsheets to parts."""
    cheatsheets = []
    if isinstance(skills_data, list):
        for skill in skills_data:
            s_id = skill.get("id")
            cs = skill.get("cheatsheet") or load_skill_detail(config_dir, s_id)
            if cs:
                cheatsheets.append(f"## Reference for [{s_id}]\n{cs}")
    if cheatsheets:
        parts.append("\n# Tool Reference / Cheatsheets\n" + "\n\n".join(cheatsheets))


def _add_risks(config_dir: str, risks_file: Optional[str], parts: list):
    """Internal: Adds risks to parts."""
    if risks_file:
        r_path = risks_file if os.path.exists(risks_file) else os.path.join(config_dir, risks_file)
        if not os.path.exists(r_path):
            r_path = os.path.join(config_dir, "risks.json")
        if os.path.exists(r_path):
            try:
                r_data = json.loads(load_risks_content(r_path))
                parts.append(f"\n# Risk Knowledge Base\n{format_as_toon('risks', r_data)}")
            except Exception:
                pass


def construct_system_prompt(
    base_dir: str, role_name: str, skill_filter: Optional[List[str]],
    include_skills: bool, risks_file: Optional[str], include_cheatsheet: bool = True
) -> str:
    """Combines role, constraints, skills, and risks into a system prompt."""
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    roles_dir = os.path.join(base_dir, "roles")
    config_dir = os.path.join(base_dir, "config")
    parts = [load_file_content(os.path.join(roles_dir, f"role_{role_name}.md"))]

    if include_skills:
        skills_data = load_skills_data(config_dir, skill_filter)
        if isinstance(skills_data, list) and skills_data:
            clean = [{k: v for k, v in s.items() if k != "cheatsheet"} for s in skills_data]
            parts.append(f"\n# Available Skills definition\n{format_as_toon('skills', clean)}")

        if include_cheatsheet:
            _add_cheatsheets(config_dir, skills_data, parts)

    _add_risks(config_dir, risks_file, parts)
    return "\n".join(parts)
