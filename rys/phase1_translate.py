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
import argparse
import json

# pylint: disable=wrong-import-position,useless-return
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

from chat_types import ChatConfig
from chat_ui import TerminalColors
from chat_api import build_base_url, verify_connection
from phase_utils import call_role

def main():
    """
    メイン処理: 引数を解析し、翻訳を実行して結果をファイルに出力する。
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default="11434")
    parser.add_argument("--model", default="gemma3n:e4b")
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

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

    translated_text = call_role(SCRIPT_DIR, "translater", args.prompt, config, colors)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(
            {"content": translated_text, "translated_text": translated_text},
            f,
            ensure_ascii=False,
            indent=2
        )

    return
