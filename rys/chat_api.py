#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Communication and Data Loading (v0.2)

History:
1. 2026-02-07 Initial version (split from chat_core.py)
2. 2026-02-15 Added image encoding and list content support for Vision API
"""
# pylint: disable=useless-return,broad-exception-caught

import sys
import json
import os
import ssl
import base64
import mimetypes
import urllib.request
import urllib.error
from typing import Iterator, Dict, Any, List, Optional
from chat_ui import TerminalColors

def get_ssl_context(insecure: bool) -> Optional[ssl.SSLContext]:
    """Returns an SSL context, possibly unverified."""
    ctx = None
    if insecure:
        # pylint: disable=protected-access
        ctx = ssl._create_unverified_context()
    return ctx

def build_base_url(host: str, port: Optional[str]) -> str:
    """Constructs the base URL from host and port."""
    host_input = host.strip()
    port_arg = str(port).strip() if port else ""
    if "://" in host_input:
        protocol, host_part = host_input.split("://", 1)
        protocol = protocol.lower()
    else:
        is_local = any(h in host_input.lower() for h in ["localhost", "127.0.0.1"])
        protocol = "http" if is_local else "https"
        host_part = host_input

    default_port = "11434" if protocol == "http" else "443"
    if ":" in host_part:
        final_host_part = host_part
    else:
        final_port = port_arg if port_arg else default_port
        final_host_part = f"{host_part}:{final_port}"
    
    return f"{protocol}://{final_host_part}"

def verify_connection(base_url: str, timeout: int = 2, insecure: bool = False) -> None:
    """Checks if the API endpoint is reachable."""
    target_url = f"{base_url}/v1/models"
    headers = {"Authorization": "Bearer not-needed"}
    ctx = get_ssl_context(insecure)
    try:
        req = urllib.request.Request(target_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx):
            pass
    except (urllib.error.URLError, OSError) as exc:
        sys.stderr.write(f"\033[31m[Fatal Error] Could not connect to {target_url}\n")
        sys.stderr.write(f"Reason: {exc}\033[0m\n")
        sys.exit(1)
    return None

def encode_image(file_path: str) -> Optional[str]:
    """Encodes an image file to a base64 string with data URI scheme."""
    if not os.path.exists(file_path):
        return None
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"
    try:
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:{mime_type};base64,{encoded_string}"
    except Exception:
        return None

def normalize_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures message has standard 'role' and 'content' keys."""
    # Allow content to be list (for multimodal) or string
    result = {"role": "user", "content": msg.get("content", "")}
    if "role" in msg and "content" in msg:
        result = msg
    else:
        for role_key in ["user", "system", "assistant", "agent"]:
            if role_key in msg:
                norm_role = "assistant" if role_key == "agent" else role_key
                result = {"role": norm_role, "content": msg[role_key]}
                break
    
    # Ensure content is string only if it's not a list (to keep objects for vision)
    if not isinstance(result["content"], list) and not isinstance(result["content"], str):
         result["content"] = str(result["content"])

    return result

def load_session_data(
    file_path: Optional[str],
    json_str: Optional[str]
) -> List[Dict[str, Any]]:
    """Loads session history from a file or JSON string."""
    raw_data = []
    try:
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f_in:
                raw_data = json.load(f_in)
        elif json_str:
            raw_data = json.loads(json_str)
    except (json.JSONDecodeError, OSError):
        sys.exit(1)

    if not raw_data:
        return []

    if not isinstance(raw_data, list):
        raw_data = [raw_data]

    return [normalize_message(m) for m in raw_data]

def _parse_stream_line(line_str: str) -> Optional[str]:
    """Parses a single line from the SSE stream."""
    content = None
    if line_str.startswith("data: "):
        json_str = line_str[6:]
        if json_str != "[DONE]":
            try:
                chunk = json.loads(json_str)
                if "choices" in chunk and chunk["choices"]:
                    content = chunk["choices"][0].get("delta", {}).get("content", "")
            except (json.JSONDecodeError, KeyError):
                pass
    return content

def stream_chat_completion(
    url: str,
    model: str,
    messages: List[Dict[str, Any]],
    colors: TerminalColors,
    insecure: bool = False
) -> Iterator[str]:
    """Generates streaming response from the API."""
    headers = {"Content-Type": "application/json", "Authorization": "Bearer not-needed"}
    payload = {"model": model, "messages": messages, "stream": True}
    ctx = get_ssl_context(insecure)

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, context=ctx) as response:
            for line in response:
                content = _parse_stream_line(line.decode("utf-8").strip())
                if content:
                    # Clean up special tokens
                    for token in ["<end_of_turn>", "<start_of_turn>", "<|file_separator|>", "<|end_of_text|>", "<|im_end|>"]:
                        content = content.replace(token, "")
                    yield content
                elif line.decode("utf-8").strip() == "data: [DONE]":
                    break
    except urllib.error.URLError as exc:
        yield f"\n{colors.wrap_error(f'[Connection Error] {exc}')}"
    except Exception as exc: # pylint: disable=broad-exception-caught
        yield f"\n{colors.wrap_error(f'[Error] {exc}')}"
    return None

def call_embedding_api(
    url: str,
    model: str,
    input_text: str,
    insecure: bool = False,
    dimensions: Optional[int] = None
) -> Dict[str, Any]:
    """Calls the embedding API and returns the response."""
    headers = {"Content-Type": "application/json", "Authorization": "Bearer not-needed"}
    payload = {"model": model, "input": input_text}
    if dimensions:
        payload["dimensions"] = dimensions
    ctx = get_ssl_context(insecure)

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, context=ctx) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc: # pylint: disable=broad-exception-caught
        return {"error": str(exc)}
    