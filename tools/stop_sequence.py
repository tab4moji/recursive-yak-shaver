#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inspects the compatibility level of a custom OpenAI-compatible API.
Version: 3.0 (Fixed URL parsing)
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error

# Configuration
DEFAULT_PORT = "11434"
TIMEOUT_SEC = 20

# Colors
C_RESET = "\033[0m"
C_GREEN = "\033[32m"
C_RED = "\033[31m"
C_YELLOW = "\033[33m"
C_CYAN = "\033[36m"

def _print_status(status: str, message: str) -> None:
    if status == "PASS":
        print(f"  [{C_GREEN}PASS{C_RESET}] {message}")
    elif status == "FAIL":
        print(f"  [{C_RED}FAIL{C_RESET}] {message}")
    elif status == "WARN":
        print(f"  [{C_YELLOW}WARN{C_RESET}] {message}")
    else:
        print(f"  [{C_CYAN}INFO{C_RESET}] {message}")

def _normalize_url(url_str: str) -> str:
    """
    Robustly adds default port 11434 if missing.
    Matches the behavior of chat_core.py
    """
    url_str = url_str.strip()
    if "://" not in url_str:
        url_str = f"http://{url_str}"
    
    parsed = urllib.parse.urlparse(url_str)
    
    # If no port is specified in netloc (e.g. "172.20.0.1" vs "172.20.0.1:11434")
    if ":" not in parsed.netloc:
        new_netloc = f"{parsed.netloc}:{DEFAULT_PORT}"
        parsed = parsed._replace(netloc=new_netloc)
        _print_status("INFO", f"Port missing. Target adjusted to: {parsed.netloc}")
    
    # Ensure path ends with /v1
    path = parsed.path
    if not path.endswith("/v1"):
        path = path.rstrip("/") + "/v1"
        parsed = parsed._replace(path=path)
        
    return urllib.parse.urlunparse(parsed)

def _send_request(url: str, payload: dict, stream: bool = False):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    return urllib.request.urlopen(req, timeout=TIMEOUT_SEC)

def check_connectivity(base_url: str) -> bool:
    print(f"\n{C_CYAN}[1/4] Connectivity Check...{C_RESET}")
    # Try a lightweight endpoint first
    try:
        # Some servers don't support GET /models, so we fallback to a simple chat
        url = f"{base_url}/models"
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status == 200:
                _print_status("PASS", "Server is reachable (/models).")
                return True
    except Exception:
        # Fallback: Try a dry-run chat
        try:
            payload = {"model": "dummy", "messages": []} # Invalid but checks connection
            _send_request(f"{base_url}/chat/completions", payload)
        except urllib.error.HTTPError as e:
            # 400 Bad Request means we connected successfully!
            _print_status("PASS", f"Server is reachable (Got HTTP {e.code}).")
            return True
        except Exception as e:
            _print_status("FAIL", f"Connection failed to {base_url}")
            _print_status("FAIL", f"Error: {e}")
            return False
            
    return True

def check_basic_chat(base_url: str, model: str) -> None:
    print(f"\n{C_CYAN}[2/4] Basic Chat (Non-streaming)...{C_RESET}")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hi"}],
        "temperature": 0.0,
        "max_tokens": 5
    }
    try:
        with _send_request(f"{base_url}/chat/completions", payload) as response:
            resp = json.loads(response.read().decode('utf-8'))
            content = resp['choices'][0]['message']['content']
            _print_status("PASS", f"Response: '{content.strip()}'")
    except Exception as e: # pylint: disable=broad-exception-caught
        _print_status("FAIL", f"{e}")

def check_stop_sequence(base_url: str, model: str) -> None:
    print(f"\n{C_CYAN}[3/4] Stop Sequence Compatibility...{C_RESET}")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Count 1, 2, 3, 4, 5"}],
        "stop": ["3"],
        "temperature": 0.0
    }
    try:
        with _send_request(f"{base_url}/chat/completions", payload) as response:
            resp = json.loads(response.read().decode('utf-8'))
            content = resp['choices'][0]['message']['content']
            if "3" in content or "4" in content:
                _print_status("FAIL", f"Stop ignored. Output: '{content.strip()}'")
                print(f"{C_YELLOW}  -> Warning: Agent might hallucinate extra steps.{C_RESET}")
            else:
                _print_status("PASS", f"Stopped correctly. Output: '{content.strip()}'")
    except Exception as e: # pylint: disable=broad-exception-caught
        _print_status("FAIL", f"{e}")

def check_streaming(base_url: str, model: str) -> None:
    print(f"\n{C_CYAN}[4/4] Streaming & Delta Check...{C_RESET}")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "A, B, C"}],
        "stream": True,
        "temperature": 0.0
    }
    try:
        response = _send_request(f"{base_url}/chat/completions", payload, stream=True)
        chunk_count = 0
        sys.stdout.write("  Stream output: ")
        sys.stdout.flush()
        
        for line in response:
            line = line.decode('utf-8').strip()
            if not line.startswith("data: "):
                continue
            if line == "data: [DONE]":
                break
            try:
                chunk = json.loads(line[6:])
                # Critical check: Some non-standard APIs send 'message' instead of 'delta' in stream
                delta = chunk['choices'][0].get('delta')
                if delta is None:
                     _print_status("WARN", "Received chunk without 'delta' field.")
                     continue
                
                if 'content' in delta:
                    sys.stdout.write(delta['content'])
                    sys.stdout.flush()
                chunk_count += 1
            except json.JSONDecodeError:
                pass
        
        print("")
        if chunk_count > 0:
            _print_status("PASS", f"Stream OK ({chunk_count} chunks).")
        else:
            _print_status("FAIL", "No chunks received.")
            
    except Exception as e: # pylint: disable=broad-exception-caught
        print("")
        _print_status("FAIL", f"{e}")

if __name__ == "__main__":
    _HOST = os.getenv("RYS_LLM_HOST", "http://172.20.0.1")
    _MODEL = os.getenv("RYS_LLM_MODEL", "gemma3n:e4b")
    
    _TARGET_URL = _normalize_url(_HOST)

    print(f"Target: {_TARGET_URL}")
    print(f"Model:  {_MODEL}")
    
    try:
        if check_connectivity(_TARGET_URL):
            check_basic_chat(_TARGET_URL, _MODEL)
            check_stop_sequence(_TARGET_URL, _MODEL)
            check_streaming(_TARGET_URL, _MODEL)
        else:
            print(f"\n{C_RED}Connectivity check failed.{C_RESET}")
            
    except KeyboardInterrupt:
        print("\nAborted.")
