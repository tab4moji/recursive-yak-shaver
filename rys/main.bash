#!/usr/bin/env bash

# Stop execution on error
set -e

# --- Configuration & Environment Variables ---
HOST="${RYS_LLM_HOST:-localhost}"
PORT="${RYS_LLM_PORT:-11434}"
MODEL="${RYS_LLM_MODEL:-gemma3n:e4b}"

# Define common options
LLM_OPTS="--host=${HOST} --port=${PORT} --model=${MODEL}"

rys_uuid=$(date +%Y%m%d_%H%M%S)

# Paths
INVOKER="./rys/invoke_role.py"
GROUPER="./rys/group_requests.py"
TEMP_TRANS="./tmp/.rys.${rys_uuid}.request.translated.txt"
TEMP_DISP="./tmp/.rys.${rys_uuid}.request.dispatched.txt"
TEMP_EXEC="./tmp/.rys.${rys_uuid}.exec_plan.tsv"
TEMP_PLAN="./tmp/.rys.${rys_uuid}.request_plan.txt"
TEMP_TITLES="./tmp/.rys.${rys_uuid}.titles.txt"
RISKS_CONFIG="./config/risks.json"

# Ensure prompt
if [ -z "$1" ]; then
    echo "Usage: $0 \"Your prompt here\""
    exit 1
fi

# --- Execution Flow ---

mkdir -p ./tmp/

echo ">>> 1. Translation Phase"
${INVOKER} ${LLM_OPTS} --role=translater --prompt="$1" | tee "${TEMP_TRANS}"

echo -e "\n>>> 2. Dispatch Phase"
${INVOKER} ${LLM_OPTS} --role=dispatcher --skills --prompt="$(cat "${TEMP_TRANS}")" | tee "${TEMP_DISP}"

echo -e "\n>>> 3. Request Visualization Phase"
# group_requests.py generates visualization on stdout AND writes execution plan to TEMP_EXEC
if [ -f "${GROUPER}" ]; then
    VISUAL_INPUT=$(cat "${TEMP_DISP}" | "${GROUPER}" --plan-file="${TEMP_EXEC}")
    echo "${VISUAL_INPUT}" | ${INVOKER} ${LLM_OPTS} --role=titler --prompt="${VISUAL_INPUT}" | tee "${TEMP_TITLES}"
else
    echo "Warning: ${GROUPER} not found."
    cat "${TEMP_DISP}"
fi

echo -e "\n>>> 4. Execution Phase (Grouped)"

# Check if execution plan exists
if [ ! -f "${TEMP_EXEC}" ] || [ ! -s "${TEMP_EXEC}" ]; then
    echo "No valid execution plan found (or no skills assigned)."
    exit 0
fi

# Get job count
TOTAL_JOBS=$(wc -l < "${TEMP_EXEC}" | tr -d ' ')
echo "Total topics to execute: ${TOTAL_JOBS}"

# Disable set -e temporarily to ensure the loop completes and output is seen
set +e

PROCESSED_JOBS=0
while IFS=$'\t' read -r req_index current_skill topic || [ -n "$req_index" ]; do
    [ -z "$req_index" ] && continue
    ((PROCESSED_JOBS++))

    # Extract only the REQUEST title line for this index from TEMP_TITLES
    REQ_TITLE=$(grep "^REQUEST ${req_index}:" "${TEMP_TITLES}")

    echo -e "\n---------------------------------------------------"
    echo "${REQ_TITLE}"
    echo "- TOPIC: ${topic}"
    echo "Assigned Skill: ${current_skill}"

    # Goal for the Planner is just the single topic
    combined_goal="- TOPIC: ${topic}"

    echo "[Planning Phase]"
    PLAN_OUT=$(${INVOKER} ${LLM_OPTS} --role=planner --prompt="${combined_goal}" < /dev/null)
    echo "${PLAN_OUT}"
    echo "${PLAN_OUT}" > "${TEMP_PLAN}"

    echo -e "\n[Refining Phase]"
    REFINED_OUT=$(${INVOKER} ${LLM_OPTS} --role=refiner --skills="${current_skill}" --prompt="$(cat "${TEMP_PLAN}")" < /dev/null)
    echo "${REFINED_OUT}"

    echo -e "\n[Auditing Phase]"
    AUDIT_OUT=$(${INVOKER} ${LLM_OPTS} --role=auditor --risks="${RISKS_CONFIG}" --prompt="${REFINED_OUT}" < /dev/null)
    echo "${AUDIT_OUT}"

    if echo "${AUDIT_OUT}" | grep -q "\[FAIL\]"; then
        echo -e "\n!!! AUDIT FAILED !!! Execution blocked for this topic."
    fi

done < "${TEMP_EXEC}"

# Re-enable set -e
set -e

rm -f ./tmp/.rys.${rys_uuid}*
