#!/usr/bin/env bash
#
# execute_request.bash
# Handles the execution of a single REQUEST package (JSON format).
#

REQUEST_ID="$1"
SKILL="$2"
JSON_DATA="$3"

echo "=================================================="
echo ">>> Phase 5: Executing ${REQUEST_ID}"
echo "Skill: ${SKILL}"
echo "--------------------------------------------------"
# For now, just print the IDs of the topics being processed
echo "Processing Topics: "
echo "$JSON_DATA" | python3 -c "import sys, json; data=json.load(sys.stdin); print(', '.join([t['id'] for t in data['topics']]))"
echo "=================================================="
echo ""
