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
import math
from typing import Optional, List

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from chat_ui import TerminalColors
from chat_api import verify_connection, call_embedding_api, build_base_url

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates cosine similarity between two vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    
    if HAS_NUMPY:
        a = np.array(v1)
        b = np.array(v2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    # Fallback to pure Python
    dot_product = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(a * a for a in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product / (mag1 * mag2)

def get_embedding(
    text: str,
    model: str,
    base_url: str,
    colors: TerminalColors,
    args: argparse.Namespace
) -> List[float]:
    """Gets embedding for a single text, using cache if available."""
    cache_dir = "tmp"
    cache_key = hashlib.sha256(f"{model}:{text}".encode("utf-8")).hexdigest()
    cache_path = os.path.join(cache_dir, f"embed_{cache_key}.json")
    insecure_flag = getattr(args, "insecure", False)

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
        verify_connection(base_url, insecure=insecure_flag)
        api_url = f"{base_url.rstrip('/')}/v1/embeddings"
        if not args.quiet:
            print(colors.colorize(f"--- Embedding: {api_url} ({model}) ---", colors.sys_color))
        
        response = call_embedding_api(api_url, model, text, insecure=insecure_flag)
        if "error" not in response:
            os.makedirs(cache_dir, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
    
    if "error" in response:
        print(colors.wrap_error(f"[Error] {response['error']}"))
        sys.exit(1)
    
    if "data" in response and response["data"]:
        return response["data"][0].get("embedding", [])
    
    print(colors.wrap_error(f"[Error] Unexpected response format: {response}"))
    sys.exit(1)

def run_embedding(args: argparse.Namespace) -> None:
    """Initializes and runs the embedding request."""
    colors = TerminalColors(enable_color=not args.no_color)
    base_url = build_base_url(args.host, args.port)

    # Handle multiple inputs for diff mode
    inputs = args.inputs
    if not inputs and not sys.stdin.isatty():
        inputs = [sys.stdin.read().strip()]
    
    if not inputs:
        print(colors.wrap_error("[Error] No input text provided."))
        sys.exit(1)

    if len(inputs) == 3 and inputs[0] == "diff":
        # Diff mode: ./embedding.py diff "text1" "text2"
        v1 = get_embedding(inputs[1], args.model, base_url, colors, args)
        v2 = get_embedding(inputs[2], args.model, base_url, colors, args)
        similarity = cosine_similarity(v1, v2)
        if args.raw:
            print(json.dumps({"similarity": similarity}))
        else:
            print(f"Cosine Similarity: {similarity:.4f}")
    elif len(inputs) == 2:
        # Implicit diff mode: ./embedding.py "text1" "text2"
        v1 = get_embedding(inputs[0], args.model, base_url, colors, args)
        v2 = get_embedding(inputs[1], args.model, base_url, colors, args)
        similarity = cosine_similarity(v1, v2)
        print(f"Cosine Similarity: {similarity:.4f}")
    else:
        # Single mode
        text = inputs[0]
        embedding = get_embedding(text, args.model, base_url, colors, args)
        # Output the vector
        print(json.dumps(embedding))

    return None

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Embedding Client v0.1 - OpenAI Compatible"
    )
    parser.add_argument("inputs", nargs="*", help="Input text(s) to embed or 'diff text1 text2'")
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
