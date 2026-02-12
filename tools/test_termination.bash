#!/usr/bin/env bash
# tools/test_termination.bash
# 2026-02-12 v1.0
# テキスト生成の強制終了テストスクリプト

# 1. 動作予測時間を 10 秒に設定し、3 秒でタイムアウトさせるテスト (tryit 使用)
# 2. 直接実行して Ctrl+C で止めるテスト

HOST="${RYS_LLM_HOST:-localhost}"
PORT="${RYS_LLM_PORT:-11434}"
MODEL="${RYS_LLM_MODEL:-gemma3n:e4b}"

echo "===================================================="
echo "RYS: Text Generation Forced Termination Test"
echo "===================================================="
echo "Host: $HOST"
echo "Model: $MODEL"
echo "----------------------------------------------------"

PROMPT="1から1000まで、それぞれの数字の意味を詳しく説明しながらカウントアップしてくれ。非常に長い回答を期待している。"

echo ">>> [TEST 1] Testing with 'tryit' (Timeout in 5 seconds)"
echo "コマンド: tryit -q -t 5 'python3 ./rys/invoke_role.py --host $HOST --prompt "$PROMPT"'"
echo "----------------------------------------------------"

if command -v tryit > /dev/null; then
    tryit -q -t 5 "python3 ./rys/invoke_role.py --host $HOST --prompt "$PROMPT""
    echo -e "
>>> tryit test finished."
else
    echo "tryit command not found. Skipping Test 1."
fi

echo -e "
----------------------------------------------------"
echo ">>> [TEST 2] Background execution and manual kill (after 3 seconds)"
echo "----------------------------------------------------"

python3 ./rys/invoke_role.py --host "$HOST" --prompt "$PROMPT" &
TARGET_PID=$!
echo "Started invoke_role.py with PID: $TARGET_PID"

sleep 3
echo -e "
>>> Sending SIGINT (Ctrl+C equivalent) to $TARGET_PID..."
kill -INT "$TARGET_PID"

# Wait for process to exit
wait "$TARGET_PID" 2>/dev/null
EXIT_CODE=$?

echo "Process exited with code: $EXIT_CODE"
if [ $EXIT_CODE -eq 130 ]; then
    echo "Result: SUCCESS (Exited by SIGINT)"
else
    echo "Result: Finished or Terminated (Code $EXIT_CODE)"
fi

echo "===================================================="
