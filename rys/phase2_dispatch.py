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
import json
import glob

# 自作モジュールのインポート
# sys.pathの調整はインポート前に行う必要があるため、pylintの指摘対象になるが、
# 実行時のパス構成に依存するため、この位置に維持する。
# pylint: disable=wrong-import-position
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

from chat_api import build_base_url
from phase_utils import call_role, get_common_parser, init_llm_config, load_phase_json
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
    parser = get_common_parser("Phase 2: Dispatch Phase")
    parser.add_argument("--similarity", type=float, default=0.0)
    parser.add_argument("--embed-model", default="gemma:latest")
    args = parser.parse_args()

    result_data = {}
    try:
        data = load_phase_json(args.in_json)
        input_text = data.get("content", data.get("translated_text", ""))
        config, colors = init_llm_config(args)

        best_match = None
        base_url = build_base_url(args.host, args.port)
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
        print(f">>> Error in Phase 2: {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.out_json, "w", encoding="utf-8") as f_out:
        json.dump(result_data, f_out, ensure_ascii=False, indent=2)
    return

if __name__ == "__main__":
    main()
