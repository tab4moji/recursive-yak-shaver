#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stop Request (v0.1)
Force-stop an in-progress generation on yukinkoLLM.
"""
# pylint: disable=broad-exception-caught

import argparse
import json
import sys
import urllib.request
import urllib.error


def build_base_url(host: str, port: str | None) -> str:
    host = host.rstrip("/")
    if host.startswith("http://") or host.startswith("https://"):
        base = host
    else:
        base = f"http://{host}"
    if port:
        # if host already has :port, user should omit --port
        return f"{base}:{port}"
    return base


def post_json(url: str, payload: dict) -> str:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> None:
    parser = argparse.ArgumentParser(description="Force-stop yukinkoLLM generation")
    parser.add_argument("--host", default="localhost", help="Target Host/IP (with or without http://)")
    parser.add_argument("--port", "-p", help="Target Port (default: none)")
    parser.add_argument("--request-id", help="Target request_id (optional)")
    args = parser.parse_args()

    base = build_base_url(args.host, args.port)
    url = f"{base.rstrip('/')}/api/stop"

    payload: dict = {}
    if args.request_id:
        payload["request_id"] = args.request_id

    try:
        out = post_json(url, payload)
        sys.stdout.write(out + "\n")
    except urllib.error.HTTPError as exc:
        sys.stderr.write(f"HTTPError: {exc.code} {exc.reason}\n")
        sys.stderr.write(exc.read().decode("utf-8", errors="replace") + "\n")
        sys.exit(2)
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
