#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Role Loading and Prompt Construction Utilities (v0.5)
Adds 'Cheatsheet' injection from skills. Supports authentic TOON (Token-Oriented Object Notation).
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


def _get_all_skills(config_dir: str) -> List[Dict[str, Any]]:
    """Scans skills.json and config/skills/*.json to build a complete list."""
    all_skills = []
    seen_ids = set()

    # 1. Load from skills.json (Main Registry)
    skills_json_path = os.path.join(config_dir, "skills.json")
    if os.path.exists(skills_json_path):
        try:
            data = json.loads(load_file_content(skills_json_path))
            if isinstance(data, list):
                for s in data:
                    if isinstance(s, dict) and "id" in s:
                        all_skills.append(s)
                        seen_ids.add(s["id"])
        except Exception as exc:
            print(f"Warning: Failed to parse skills.json: {exc}")

    # 2. Scan config/skills/*.json for additional/missing skills
    skills_subdir = os.path.join(config_dir, "skills")
    if os.path.exists(skills_subdir):
        for filename in os.listdir(skills_subdir):
            if filename.endswith(".json"):
                s_id = filename[:-5]
                if s_id not in seen_ids:
                    # Load minimal info from the skill file itself
                    try:
                        with open(os.path.join(skills_subdir, filename), 'r', encoding='utf-8') as f:
                            detail = json.load(f)
                            all_skills.append({
                                "id": s_id,
                                "type": "primitive",
                                "description": detail.get("description", f"Auto-discovered skill: {s_id}"),
                                "tools": detail.get("tools", [])
                            })
                            seen_ids.add(s_id)
                    except Exception:
                        pass
    
    return all_skills


def load_skills_data(config_dir: str, filter_skills: Optional[List[str]]) -> Any:
    """Loads all discovered skills and filters them if requested."""
    all_skills = _get_all_skills(config_dir)
    
    if filter_skills is None: # Represents 'all'
        return all_skills
        
    return [s for s in all_skills if s.get("id") in filter_skills]


def format_value(val: Any) -> str:
    """Formats a single value according to TOON rules (quoting/escaping)."""
    if val is None:
        return ""
    
    s_val = str(val)
    # Check if quoting is needed: contains comma, newline, or wrapping spaces
    needs_quoting = "," in s_val or "\n" in s_val or s_val.strip() != s_val
    
    if needs_quoting:
        # JSON-style escaping for quotes and newlines
        escaped = s_val.replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    
    return s_val


def format_as_toon(key: str, data: Any, indent_level: int = 0) -> str:
    """Converts a Python object to authentic TOON format string."""
    indent = "  " * indent_level
    
    if isinstance(data, list):
        if not data:
            return f"{indent}{key}[0]{{}}:"
        
        # Determine common fields for tabular format if it's a list of dicts
        if all(isinstance(item, dict) for item in data) and data:
            # Collect all unique keys present in the items to form columns
            all_keys = []
            for item in data:
                for k in item.keys():
                    if k not in all_keys:
                        all_keys.append(k)
            
            header = f"{indent}{key}[{len(data)}]{{{','.join(all_keys)}}}:"
            lines = [header]
            for item in data:
                row = []
                for k in all_keys:
                    row.append(format_value(item.get(k, "")))
                lines.append(f"{indent}{','.join(row)}")
            return "\n".join(lines)
        else:
            # Simple list
            header = f"{indent}{key}[{len(data)}]:"
            lines = [header]
            for item in data:
                lines.append(f"{indent}{format_value(item)}")
            return "\n".join(lines)
            
    elif isinstance(data, dict):
        lines = []
        if key:
            lines.append(f"{indent}{key}:")
            child_indent = indent_level + 1
        else:
            child_indent = indent_level
            
        for k, v in data.items():
            if isinstance(v, (list, dict)):
                lines.append(format_as_toon(k, v, child_indent))
            else:
                lines.append(f"{'  ' * child_indent}{k}: {format_value(v)}")
        return "\n".join(lines)
    
    else:
        return f"{indent}{key}: {format_value(data)}"


def load_skill_detail(config_dir: str, skill_id: str) -> str:
    """Loads detailed skill definition from config/skills/<id>.json as TOON."""
    path = os.path.join(config_dir, "skills", f"{skill_id}.json")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            ops = []
            if "patterns" in data:
                for p in data["patterns"]:
                    in_type = p.get('input_type', 'Any')
                    in_def = ""
                    if "path" in in_type.lower() or "directory" in in_type.lower():
                        in_def = "./"
                        
                    ops.append({
                        "operation": p['task'].lower().replace(" ", "_"),
                        "description": p['task'],
                        "input_type": in_type,
                        "input_default": in_def,
                        "output_type": p.get('output_type', 'Any'),
                        "recommended": p.get('recommended', '')
                    })

            toon_data = {
                "skill_id": skill_id,
                "description": f"The \"{skill_id}\" skill supports the following virtual operations.",
                "operations": ops
            }

            content = format_as_toon("", toon_data)
            return content
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
    risks_file: Optional[str],
    include_cheatsheet: bool = True
) -> str:
    """Combines role, constraints, skills, and risks into a system prompt using TOON."""
    roles_dir = os.path.join(base_dir, "roles")
    config_dir = os.path.join(base_dir, "config")
    parts = []

    # 1. Base Role
    parts.append(load_file_content(os.path.join(roles_dir, f"role_{role_name}.md")))

    # 3. Skills & Cheatsheets
    if include_skills:
        skills_data = load_skills_data(config_dir, skill_filter)
        
        # Add Skill Definitions (Formal IDs and descriptions)
        if isinstance(skills_data, list) and skills_data:
            # We omit 'cheatsheet' field in the tabular view to keep it clean
            clean_skills = []
            for s in skills_data:
                item = {k: v for k, v in s.items() if k != "cheatsheet"}
                clean_skills.append(item)
            
            skills_toon = format_as_toon("skills", clean_skills)
            parts.append(f"\n# Available Skills definition\n{skills_toon}")

        # Add Cheatsheets (The "Context" for ICL)
        if include_cheatsheet:
            cheatsheets = []
            if isinstance(skills_data, list):
                for skill in skills_data:
                    s_id = skill.get("id")
                    cs = skill.get("cheatsheet")
                    if not cs and s_id:
                        # Fallback to loading from skills/<id>.json
                        cs = load_skill_detail(config_dir, s_id)
                    
                    if cs:
                        cheatsheets.append(f"## Reference for [{s_id}]\n{cs}")
            
            if cheatsheets:
                parts.append("\n# Tool Reference / Cheatsheets (USE THESE PATTERNS)\n" + "\n\n".join(cheatsheets))
        
    # 4. Risks
    if risks_file:
        r_path = risks_file if os.path.exists(risks_file) else os.path.join(config_dir, risks_file)
        if not os.path.exists(r_path):
            r_path = os.path.join(config_dir, "risks.json")
        if os.path.exists(r_path):
            try:
                r_data = json.loads(load_risks_content(r_path))
                risks_toon = format_as_toon("risks", r_data)
                parts.append(f"\n# Risk Knowledge Base\n{risks_toon}")
            except Exception:
                pass

    return "\n".join(parts)
