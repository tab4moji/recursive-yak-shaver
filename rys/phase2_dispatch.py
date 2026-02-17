#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=useless-return
"""
プログラム名: rys/phase2_dispatch.py
目的: 翻訳済みプロンプトを読み込み、dispatcherロールを呼び出して実行依頼内容を解析・配分する。
更新履歴:
    1. 2026/02/17: pylint指摘事項の修正（リファクタリング、ドキュメント追加、インポート位置調整）。
    2. 2026/02/17: 残りの指摘（空白、局所変数、useless-return等）を修正。
"""

import sys
import os
import argparse
import json
import glob

# 自作モジュールのインポート
# sys.pathの調整はインポート前に行う必要があるため、pylintの指摘対象になるが、
# 実行時のパス構成に依存するため、この位置に維持する。
# pylint: disable=wrong-import-position
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

from chat_types import ChatConfig
from chat_ui import TerminalColors
from chat_api import build_base_url, verify_connection
from phase_utils import call_role
from embedding import get_embedding, cosine_similarity

# pylint: disable=too-few-public-methods
class EmbeddingArgs:
    """
    get_embedding関数に渡す引数を模倣するクラス。
    """
    def __init__(self, quiet=True, dims=None, insecure=False):
        self.quiet = quiet
        self.dims = dims
        self.insecure = insecure

def search_embedding_cache(input_text, args, base_url, colors):
    """
    埋め込みベクトルの類似度を用いてキャッシュを検索する。
    
    Args:
        input_text (str): 検索対象のテキスト。
        args (argparse.Namespace): コマンドライン引数。
        base_url (str): APIのベースURL。
        colors (TerminalColors): カラー表示用オブジェクト。
        
    Returns:
        dict: ヒットしたキャッシュデータ、なければNone。
    """
    best_match = None
    max_sim = -1.0
    embed_args = EmbeddingArgs()
    try:
        cur_vec = get_embedding(input_text, args.embed_model, base_url, colors, embed_args)
        for c_path in glob.glob(os.path.join("tmp", ".cache.p2.*.json")):
            if os.path.abspath(c_path) == os.path.abspath(args.out_json):
                continue
            try:
                with open(c_path, "r", encoding="utf-8") as f_cache:
                    c_data = json.load(f_cache)
                c_text = c_data.get("translated_text")
                if c_text:
                    sim = cosine_similarity(
                        cur_vec,
                        get_embedding(c_text, args.embed_model, base_url, colors, embed_args)
                    )
                    if sim >= args.similarity and sim > max_sim:
                        max_sim, best_match = sim, c_data
            except (json.JSONDecodeError, IOError, ValueError, KeyError):
                continue
        if best_match:
            msg = f">>> Embedding Cache Hit (similarity: {max_sim:.4f})"
            print(colors.colorize(msg, colors.sys_color))
    except (ConnectionError, ValueError, RuntimeError) as err:
        print(colors.wrap_error(f"[Warning] Cache search failed: {err}"), file=sys.stderr)
    return best_match

def main():
    """
    メイン実行関数。
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-json", required=True)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default="11434")
    parser.add_argument("--model", default="gemma3n:e4b")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--similarity", type=float, default=0.0)
    parser.add_argument("--embed-model", default="gemma:latest")
    args = parser.parse_args()
    result_data = {}
    try:
        if not os.path.exists(args.in_json):
            raise FileNotFoundError(f"Input file {args.in_json} not found.")
        with open(args.in_json, "r", encoding="utf-8") as f_in:
            data = json.load(f_in)
        input_text = data.get("content", data.get("translated_text", ""))
        base_url = build_base_url(args.host, args.port)
        verify_connection(base_url)
        config = ChatConfig(
            api_url=f"{base_url.rstrip('/')}/v1/chat/completions",
            model=args.model,
            quiet_mode=True,
            stream_output=True,
            insecure=False
        )
        colors = TerminalColors(enable_color=True)
        best_match = None
        if args.similarity > 0:
            best_match = search_embedding_cache(input_text, args, base_url, colors)
        if best_match:
            result_data = best_match
        else:
            dispatch_out = call_role(
                SCRIPT_DIR, "dispatcher", input_text, config, colors, include_skills=True
            )
            data["content"] = dispatch_out
            data["dispatch_out"] = dispatch_out
            result_data = data
    except (FileNotFoundError, ConnectionError, json.JSONDecodeError, IOError) as e:
        print(f">>> Skipping Phase 2: {e}", file=sys.stderr)
    with open(args.out_json, "w", encoding="utf-8") as f_out:
        json.dump(result_data, f_out, ensure_ascii=False, indent=2)
    return

if __name__ == "__main__":
    main()
