#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI-compatible Embedding API Client. (v0.1)

History:
1. 2026-02-16 Initial version
"""
# pylint: disable=useless-return,broad-exception-caught

import sys
import argparse
import json
import hashlib
import os
from typing import Optional

from chat_ui import TerminalColors
from chat_api import verify_connection, call_embedding_api, build_base_url

def run_embedding(args: argparse.Namespace) -> None:
    """Initializes and runs the embedding request."""
    colors = TerminalColors(enable_color=not args.no_color)
    base_url = build_base_url(args.host, args.port)
    insecure_flag = getattr(args, "insecure", False)

    input_text = args.input
    if input_text is None and not sys.stdin.isatty():
        input_text = sys.stdin.read().strip()
    
    if not input_text:
        print(colors.wrap_error("[Error] No input text provided."))
        sys.exit(1)

    # Cache logic
    cache_dir = "tmp"
    cache_key = hashlib.sha256(f"{args.model}:{input_text}".encode("utf-8")).hexdigest()
    cache_path = os.path.join(cache_dir, f"embed_{cache_key}.json")

    response = None
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                response = json.load(f)
            if not args.quiet:
                print(colors.colorize(f"--- Cache Hit: {cache_path} ---", colors.sys_color))
        except Exception:
            response = None

    if response is None:
        # verify_connection checks /v1/models by default, which is usually fine for these APIs
        verify_connection(base_url, insecure=insecure_flag)

        api_url = f"{base_url.rstrip('/')}/v1/embeddings"
        
        if not args.quiet:
            print(colors.colorize(f"--- Embedding: {api_url} ({args.model}) ---", colors.sys_color))

        response = call_embedding_api(
            api_url, args.model, input_text, insecure=insecure_flag
        )

        if "error" not in response:
            os.makedirs(cache_dir, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(response, f, ensure_ascii=False, indent=2)

    if "error" in response:
        print(colors.wrap_error(f"[Error] {response['error']}"))
        sys.exit(1)

    if args.raw:
        print(json.dumps(response, indent=2, ensure_ascii=False))
    else:
        # Default behavior: print the embedding vector (first one)
        if "data" in response and response["data"]:
            embedding = response["data"][0].get("embedding", [])
            print(json.dumps(embedding))
        else:
            print(colors.wrap_error(f"[Error] Unexpected response format: {response}"))
            sys.exit(1)

    return None

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Embedding Client v0.1 - OpenAI Compatible"
    )
    parser.add_argument("input", nargs="?", help="Input text to embed")
    parser.add_argument("--host", default="localhost", help="Target Host IP")
    parser.add_argument("--port", "-p", help="Target Port")
    parser.add_argument("--model", "-m", default="nomic-embed-text", help="Model name")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON response")
    parser.add_argument("--no-color", "-n", action="store_true", help="Disable color")
    parser.add_argument(
        "--insecure", "-k", action="store_true",
        help="Skip SSL certificate verification"
    )

    args = parser.parse_args()
    run_embedding(args)
    return None

if __name__ == "__main__":
    main()
