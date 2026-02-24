#!/usr/bin/env python3
# Purpose: yukinkoLLM OpenAI互換APIを「とにかく止めてから hello」するスクリプト
# History:
# 1. 2026-02-12: Initial version

from __future__ import annotations

import json
import sys
import time
import urllib.request
import urllib.error
from typing import Dict, Iterator, Optional


class TestFailure(RuntimeError):
    pass


def http_json(method: str, url: str, payload: Optional[dict], timeout_sec: float) -> Dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Bearer sk-test",
    }
    req = urllib.request.Request(url=url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            if not body:
                return {}
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        raise TestFailure(f"HTTP {e.code}: {body[:300]}")
    except Exception as e:
        raise TestFailure(str(e))


def iter_sse_data(resp) -> Iterator[str]:
    while True:
        line = resp.readline()
        if not line:
            return
        s = line.decode("utf-8", errors="replace").strip()
        if not s:
            continue
        if s.startswith("data:"):
            yield s[len("data:") :].strip()


def panic_cancel(base_url: str) -> None:
    # mapping無くても /v1/responses/resp_*/cancel が cancel command を流す実装なので、
    # 適当なIDで「生成中なら止める」を狙う。
    url = f"{base_url}/v1/responses/resp_panic/cancel"
    try:
        obj = http_json("POST", url, payload={}, timeout_sec=3.0)
        status = obj.get("status")
        print(f"[panic_cancel] status={status!r}")
    except Exception as e:
        # 404/接続失敗でも hello を試したいので握りつぶす
        print(f"[panic_cancel] ignored error: {e}")


def hello_stream(base_url: str, text: str, timeout_sec: float = 20.0) -> str:
    url = f"{base_url}/v1/chat/completions"
    payload = {
        "model": "gemma:latest",
        "stream": True,
        "messages": [{"role": "user", "content": text}],
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Authorization": "Bearer sk-test",
    }
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    t0 = time.time()
    out = []

    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        for data in iter_sse_data(resp):
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            choices = chunk.get("choices") or []
            if choices and isinstance(choices, list) and isinstance(choices[0], dict):
                delta = choices[0].get("delta")
                if isinstance(delta, dict):
                    content = delta.get("content")
                    if isinstance(content, str) and content:
                        out.append(content)
                        # すぐ実験したい用：出力も即見せる
                        sys.stdout.write(content)
                        sys.stdout.flush()

            if time.time() - t0 > timeout_sec:
                raise TestFailure("Timeout in SSE stream")

    sys.stdout.write("\n")
    return "".join(out)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 quick_reset_hello.py http://127.0.0.1:11434 [hello_text]")
        return 2

    base_url = sys.argv[1].rstrip("/")
    hello_text = sys.argv[2] if len(sys.argv) >= 3 else "hello"

    panic_cancel(base_url)
    try:
        result = hello_stream(base_url, hello_text)
    except TestFailure as e:
        print(f"\n[NG] {e}", file=sys.stderr)
        return 1

    if not result.strip():
        print("[NG] empty response", file=sys.stderr)
        return 1

    print("[OK] hello")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

