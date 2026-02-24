#!/usr/bin/env python3
import urllib.request
import json
import argparse
import sys

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Chat Tester v7.4 - OpenAI Compatible Client with Vision"
    )
    parser.add_argument("--host", default="localhost", help="Target Host IP")
    parser.add_argument("--port", "-p", default="11434", help="Target Port")
    parser.add_argument("--model", "-m", default="gemma3n:e4b", help="Model name")
    parser.add_argument("--system", "-s", default="You are a helpful assistant.",
                        help="System prompt")
    parser.add_argument("--msg", default="hello", help="Message to send")
    parser.add_argument("--session-file", help="History file path")
    parser.add_argument("--session-json", help="History JSON string")
    parser.add_argument("--quit", "-q", action="store_true", help="Quiet mode")
    parser.add_argument("--stream", action="store_true", help="Force streaming")
    parser.add_argument("--no-color", "-n", action="store_true", help="Disable color")
    parser.add_argument("--insecure", "-k", action="store_true", help="Skip SSL")

    args = parser.parse_args()

    # エンドポイント
    base_url = args.host if args.host.startswith("http") else f"http://{args.host}"
    url = f"{base_url}:{args.port}/v1/chat/completions"

    # ペイロード (ここが重要: stream=False)
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.msg}],
        "stream": False
    }

    print(f"Sending '{args.msg}' to {url} ...")

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        # ストリーミングではないので、レスポンスを一括で読み込む
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
            
            # 結果の抽出
            try:
                content = data["choices"][0]["message"]["content"]
                print("-" * 20)
                print(content)
                print("-" * 20)
            except (KeyError, IndexError):
                print(f"Error: Unexpected format.\n{body}")

    except urllib.error.URLError as e:
        print(f"Connection Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
