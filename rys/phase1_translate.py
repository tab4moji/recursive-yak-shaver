#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
プログラム名: phase1_translate.py
目的・機能: ユーザープロンプトを読み込み、指定されたロール（翻訳）を使用して翻訳結果をJSONで返す。
更新履歴:
    1.0: 2026-02-17 新規作成
    1.1: 2026-02-17 pylint指摘対応、規約準拠修正
"""

import sys
import os
import json

# pylint: disable=wrong-import-position,useless-return
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

from phase_utils import call_role, get_common_parser, init_llm_config

def main():
    """
    メイン処理: 引数を解析し、翻訳を実行して結果をファイルに出力する。
    """
    parser = get_common_parser("Phase 1: Translation Phase")
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()

    config, colors = init_llm_config(args)

    translated_text = call_role(SCRIPT_DIR, "translater", args.prompt, config, colors)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(
            {"content": translated_text, "translated_text": translated_text},
            f,
            ensure_ascii=False,
            indent=2
        )

    return

if __name__ == "__main__":
    main()
