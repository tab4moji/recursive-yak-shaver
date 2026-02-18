#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 0.1: OpenAI-compatible Embedding API Client
# リポジトリ規約に基づき pylint の指摘事項を修正
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
from typing import List

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
        res = 0.0
    elif HAS_NUMPY:
        a = np.array(v1)
        b = np.array(v2)
        res = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    else:
        # Fallback to pure Python
        dot_product = sum(a * b for a, b in zip(v1, v2))
        mag1 = math.sqrt(sum(a * a for a in v1))
        mag2 = math.sqrt(sum(a * a for a in v2))
        if mag1 == 0 or mag2 == 0:
            res = 0.0
        else:
            res = dot_product / (mag1 * mag2)
    return res

def _check_cache(cache_path: str, args: argparse.Namespace,
                 colors: TerminalColors) -> List[float]:
    """Internal: Checks if a valid embedding exists in cache."""
    vec = []
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            if "response" in cache_data:
                response = cache_data["response"]
                cached_dims = cache_data.get("requested_dims")
            else:
                response = cache_data
                cached_dims = None

            c_vec = response.get("data", [{}])[0].get("embedding", [])
            is_suff = (args.dims is None and cached_dims is None) or \
                      (args.dims is not None and len(c_vec) >= args.dims)

            if is_suff:
                if not args.quiet:
                    msg = f"--- Cache Hit (Reuse): {cache_path} (len={len(c_vec)}) ---"
                    print(colors.colorize(msg, colors.sys_color))
                vec = c_vec[:args.dims] if args.dims else c_vec
            elif not args.quiet:
                msg = f"--- Cache Insufficient (len={len(c_vec)} < {args.dims or 'full'}). ---"
                print(colors.colorize(msg, colors.sys_color))
        except Exception:
            pass
    return vec

def _fetch_and_cache(text: str, model: str, base_url: str,
                     cache_path: str, args: argparse.Namespace,
                     colors: TerminalColors) -> List[float]:
    """Internal: Fetches embedding from API and saves to cache."""
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    insecure_flag = getattr(args, "insecure", False)
    verify_connection(base_url, insecure=insecure_flag)
    api_url = f"{base_url.rstrip('/')}/v1/embeddings"

    if not args.quiet:
        msg = f"--- Embedding: {api_url} ({model}, dims={args.dims or 'full'}) ---"
        print(colors.colorize(msg, colors.sys_color))

    response = call_embedding_api(api_url, model, text,
                                  insecure=insecure_flag, dimensions=args.dims)

    if "error" in response:
        print(colors.wrap_error(f"[Error] {response['error']}"))
        sys.exit(1)

    if "data" in response and response["data"]:
        vec = response["data"][0].get("embedding", [])
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"response": response, "requested_dims": args.dims},
                      f, ensure_ascii=False, indent=2)
        res = vec[:args.dims] if args.dims and len(vec) > args.dims else vec
    else:
        print(colors.wrap_error(f"[Error] Unexpected response format: {response}"))
        sys.exit(1)

    return res

def get_embedding(text: str, model: str, base_url: str,
                  colors: TerminalColors, args: argparse.Namespace) -> List[float]:
    """Gets embedding for a single text, using cache if available."""
    cache_dir = os.environ.get("RYS_CACHE_DIR", "tmp")
    cache_key = hashlib.sha256(f"{model}:{text}".encode("utf-8")).hexdigest()
    cache_path = os.path.join(cache_dir, f"embed_{cache_key}.json")

    vec = _check_cache(cache_path, args, colors)
    if not vec:
        vec = _fetch_and_cache(text, model, base_url, cache_path, args, colors)

    return vec

def run_embedding(args: argparse.Namespace) -> None:
    """Initializes and runs the embedding request."""
    colors = TerminalColors(enable_color=not args.no_color)
    base_url = build_base_url(args.host, args.port)

    inputs = args.inputs
    if not inputs and not sys.stdin.isatty():
        inputs = [sys.stdin.read().strip()]

    if not inputs:
        print(colors.wrap_error("[Error] No input text provided."))
        sys.exit(1)

    if len(inputs) == 3 and inputs[0] == "diff":
        v1 = get_embedding(inputs[1], args.model, base_url, colors, args)
        v2 = get_embedding(inputs[2], args.model, base_url, colors, args)
        sim = cosine_similarity(v1, v2)
        print(json.dumps({"similarity": sim}) if args.raw else f"Cosine Similarity: {sim:.4f}")
    elif len(inputs) == 2:
        v1 = get_embedding(inputs[0], args.model, base_url, colors, args)
        v2 = get_embedding(inputs[1], args.model, base_url, colors, args)
        sim = cosine_similarity(v1, v2)
        print(f"Cosine Similarity: {sim:.4f}")
    else:
        embedding = get_embedding(inputs[0], args.model, base_url, colors, args)
        print(json.dumps(embedding))

    return None

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Embedding Client v0.1 - OpenAI Compatible")
    parser.add_argument("inputs", nargs="*", help="Input text(s) to embed")
    parser.add_argument("--host", default="localhost", help="Target Host IP")
    parser.add_argument("--port", "-p", help="Target Port")
    parser.add_argument("--dims", type=int, help="Output dimensions (truncation)")
    parser.add_argument("--model", "-m", default="nomic-embed-text", help="Model name")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON response")
    parser.add_argument("--no-color", "-n", action="store_true", help="Disable color")
    parser.add_argument("--insecure", "-k", action="store_true", help="Skip SSL")

    args = parser.parse_args()
    run_embedding(args)
    return None

if __name__ == "__main__":
    main()
