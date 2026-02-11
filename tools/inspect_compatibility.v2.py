#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inspects the compatibility level of a custom OpenAI-compatible API.
Version: 4.0 (Agent Diagnostic Edition)
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import socket

# Configuration
DEFAULT_PORT = "11434"
TIMEOUT_SEC = 10  # Short timeout to detect hangs quickly

# Colors
C_RESET = "\033[0m"
C_GREEN = "\033[32m"
C_RED = "\033[31m"
C_YELLOW = "\033[33m"
C_CYAN = "\033[36m"
C_GRAY = "\033[90m"

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
    url_str = url_str.strip()
    if "://" not in url_str:
        url_str = f"http://{url_str}"
    
    parsed = urllib.parse.urlparse(url_str)
    if ":" not in parsed.netloc:
        parsed = parsed._replace(netloc=f"{parsed.netloc}:{DEFAULT_PORT}")
    
    path = parsed.path
    if not path.endswith("/v1"):
        path = path.rstrip("/") + "/v1"
        parsed = parsed._replace(path=path)
        
    return urllib.parse.urlunparse(parsed)

def _send_request(url: str, payload: dict, stream: bool = False, timeout=TIMEOUT_SEC):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    return urllib.request.urlopen(req, timeout=timeout)

def check_system_instruction(base_url: str, model: str) -> None:
    print(f"\n{C_CYAN}[System Role] Character Consistency{C_RESET}")
    # Instruct model to be a cat ending sentences with 'nyan'
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a cat. End every sentence with 'nyan'."},
            {"role": "user", "content": "Hello!"}
        ],
        "temperature": 0.0,
        "max_tokens": 50
    }
    try:
        with _send_request(f"{base_url}/chat/completions", payload) as response:
            resp = json.loads(response.read().decode('utf-8'))
            content = resp['choices'][0]['message']['content'].lower()
            
            print(f"{C_GRAY}  Response: {content}{C_RESET}")
            if "nyan" in content or "meow" in content:
                _print_status("PASS", "System instruction respected (Cat persona detected).")
            else:
                _print_status("WARN", "System instruction might be ignored (No cat-like behavior).")
    except Exception as e:
        _print_status("FAIL", f"Error: {e}")

def check_stop_sequence_robust(base_url: str, model: str) -> None:
    print(f"\n{C_CYAN}[Control] Stop Sequence & Max Tokens{C_RESET}")
    
    # Test 1: Stop Sequence
    # We add max_tokens=20 to prevent infinite hanging if stop fails
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Count numbers: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10."}],
        "stop": ["3"], 
        "max_tokens": 20, 
        "temperature": 0.0
    }
    
    print(f"  Testing stop=['3']...")
    try:
        with _send_request(f"{base_url}/chat/completions", payload) as response:
            resp = json.loads(response.read().decode('utf-8'))
            content = resp['choices'][0]['message']['content']
            
            # If it contains "4", the stop sequence was ignored
            if "4" in content:
                _print_status("FAIL", f"Stop sequence IGNORED. Output continued: '{content.strip()}'")
            elif "3" in content: 
                # Some APIs include the stop token, some exclude it. Both are okay-ish, but ideally exclude.
                _print_status("WARN", f"Stopped but included the token. Output: '{content.strip()}'")
            else:
                _print_status("PASS", f"Stopped perfectly. Output: '{content.strip()}'")
                
            # Check Finish Reason
            reason = resp['choices'][0].get('finish_reason')
            if reason == 'stop':
                _print_status("PASS", f"finish_reason is correctly set to 'stop'.")
            else:
                _print_status("INFO", f"finish_reason is '{reason}' (Expected 'stop').")

    except Exception as e:
        _print_status("FAIL", f"Request failed: {e}")

def check_max_tokens(base_url: str, model: str) -> None:
    # Test 2: Max Tokens
    print(f"  Testing max_tokens=5...")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Write a very long poem about the universe."}],
        "max_tokens": 5,
        "temperature": 0.0
    }
    try:
        with _send_request(f"{base_url}/chat/completions", payload) as response:
            resp = json.loads(response.read().decode('utf-8'))
            content = resp['choices'][0]['message']['content']
            
            # Simple heuristic: is it short?
            if len(content.split()) > 10: 
                _print_status("FAIL", f"max_tokens ignored. Generated long text.")
            else:
                _print_status("PASS", f"max_tokens respected. Output length: {len(content)} chars.")
                
            # Check Usage
            if 'usage' in resp:
                u = resp['usage']
                _print_status("PASS", f"Usage metrics returned: {u}")
            else:
                _print_status("WARN", "No 'usage' metrics returned. Context management will be hard.")

    except Exception as e:
        _print_status("FAIL", f"Request failed: {e}")

def check_stream_cancellation(base_url: str, model: str) -> None:
    print(f"\n{C_CYAN}[Resilience] Stream Cancellation & Recovery{C_RESET}")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Repeat 'A' forever."}],
        "stream": True,
    }
    
    print("  1. Starting infinite stream and cutting connection mid-way...")
    try:
        # Open connection
        req = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req, timeout=5)
        
        # Read a few bytes then aggressively close
        response.read(100) 
        response.close() 
        _print_status("PASS", "Connection closed by client without error.")
        
    except Exception as e:
        _print_status("FAIL", f"Failed during stream close: {e}")

    # Immediately try a new request to see if server is alive
    print("  2. Checking if server is still alive (Zombie check)...")
    time.sleep(1) # Give server a moment to release socket
    
    try:
        payload_ping = {"model": model, "messages": [{"role": "user", "content": "Hi"}]}
        with _send_request(f"{base_url}/chat/completions", payload_ping, timeout=5) as resp:
            if resp.status == 200:
                _print_status("PASS", "Server survived cancellation and accepted new request.")
            else:
                _print_status("FAIL", f"Server responded with {resp.status} after cancellation.")
    except Exception as e:
         _print_status("FAIL", f"Server appears dead/hung after cancellation: {e}")


if __name__ == "__main__":
    _HOST = os.getenv("RYS_LLM_HOST", "http://172.20.0.1")
    _MODEL = os.getenv("RYS_LLM_MODEL", "gemma3n:e4b")
    _TARGET_URL = _normalize_url(_HOST)

    print(f"Target: {_TARGET_URL}")
    print(f"Model:  {_MODEL}")
    
    try:
        # Skip connectivity check, assume user knows IP by now or it will fail in first test
        check_system_instruction(_TARGET_URL, _MODEL)
        check_stop_sequence_robust(_TARGET_URL, _MODEL)
        check_max_tokens(_TARGET_URL, _MODEL)
        check_stream_cancellation(_TARGET_URL, _MODEL)
        
    except KeyboardInterrupt:
        print("\nAborted.")
