#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2: Dispatch (v1.1)
Reads translated prompt, returns dispatch info via JSON.
"""

import sys
import os
import argparse
import json
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

from chat_types import ChatConfig
from chat_ui import TerminalColors
from chat_api import build_base_url, verify_connection
from phase_utils import call_role
from embedding import get_embedding, cosine_similarity

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-json", required=True)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default="11434")
    parser.add_argument("--model", default="gemma3n:e4b")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--similarity", type=float, default=0.0)
    parser.add_argument("--embed-model", default="gemma:latest")
    args = parser.parse_args()

    if not os.path.exists(args.in_json):
        print(f">>> Skipping Phase 2: Input file {args.in_json} not found.")
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return

    with open(args.in_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Use 'content' if available, fallback to 'translated_text'
    input_text = data.get("content", data.get("translated_text", ""))

    base_url = build_base_url(args.host, args.port)
    verify_connection(base_url)
    config = ChatConfig(api_url=f"{base_url.rstrip('/')}/v1/chat/completions", model=args.model, quiet_mode=True, stream_output=True, insecure=False)
    colors = TerminalColors(enable_color=True)

    # Embedding Similarity Cache Search
    if args.similarity > 0:
        # Dummy args for get_embedding
        class DummyArgs:
            def __init__(self, quiet=True, dims=None, insecure=False):
                self.quiet = quiet
                self.dims = dims
                self.insecure = insecure
        
        embed_args = DummyArgs()
        try:
            current_vec = get_embedding(input_text, args.embed_model, base_url, colors, embed_args)
            
            best_match = None
            max_sim = -1.0
            
            cache_files = glob.glob(os.path.join("tmp", ".cache.p2.*.json"))
            for cache_path in cache_files:
                if os.path.abspath(cache_path) == os.path.abspath(args.out_json):
                    continue
                
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        cache_data = json.load(f)
                    
                    cached_text = cache_data.get("translated_text")
                    if not cached_text:
                        continue
                    
                    cached_vec = get_embedding(cached_text, args.embed_model, base_url, colors, embed_args)
                    sim = cosine_similarity(current_vec, cached_vec)
                    
                    if sim >= args.similarity and sim > max_sim:
                        max_sim = sim
                        best_match = cache_data
                except Exception:
                    continue
            
            if best_match:
                print(colors.colorize(f">>> Embedding Cache Hit (similarity: {max_sim:.4f})", colors.sys_color))
                # Save the best match content to the current output path
                # This ensures that P3_HASH (derived from P2 content) will match the previous run
                with open(args.out_json, "w", encoding="utf-8") as f:
                    json.dump(best_match, f, ensure_ascii=False, indent=2)
                return

        except Exception as e:
            print(colors.wrap_error(f"[Warning] Embedding cache search failed: {e}"))

    dispatch_out = call_role(SCRIPT_DIR, "dispatcher", input_text, config, colors, include_skills=True)
    
    data["content"] = dispatch_out
    data["dispatch_out"] = dispatch_out
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
