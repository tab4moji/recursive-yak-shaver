#!/usr/bin/env bash
#
# execute_request.bash
# Handles the execution of a single REQUEST package (JSON format).
#

REQUEST_ID="$1"
SKILL="$2"
JSON_DATA="$3"

# Phase 5: Coding & Execution
python3 ./rys/phase5_coder_exec.py --request-json "$JSON_DATA"
