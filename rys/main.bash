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

echo -e "\n>>> 4. Planning Phase (Grouped)"

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

    echo "  [Strategic Planning]"
    PLAN_OUT=$(${INVOKER} ${LLM_OPTS} --role=planner --prompt="${combined_goal}" < /dev/null)
    # Force newline before numbers if the LLM returned a single line, then indent
    echo "${PLAN_OUT}" | sed 's/ \([0-9]\+\.\)/\n\1/g' | sed 's/^/  /'
    echo "${PLAN_OUT}" > "${TEMP_PLAN}"

    echo -e "\n  [Technical Analysis]"
    TEMP_ENG="./tmp/.rys.${rys_uuid}.engineer_out.txt"
    ENG_OUT=$(${INVOKER} ${LLM_OPTS} --role=engineer --skills="${current_skill}" --prompt="${combined_goal}" < /dev/null)
    # Double indent (4 spaces total) for the content of Technical Analysis
    echo "${ENG_OUT}" | sed 's/^/    /'
    echo "${ENG_OUT}" > "${TEMP_ENG}"

    echo -e "\n  [Workflow Synthesis]"
    # Use the correct header "Technical Analysis" for the Refiner
    REFINER_INPUT="[Strategic Planning]\n$(cat "${TEMP_PLAN}")\n\n[Technical Analysis]\n$(cat "${TEMP_ENG}")"
    REFINED_OUT=$(${INVOKER} ${LLM_OPTS} --role=refiner --skills="${current_skill}" --prompt="${REFINER_INPUT}" < /dev/null)
    echo "${REFINED_OUT}" | sed 's/ \([0-9]\+\.\)/\n\1/g' | sed 's/^/  /'

    echo -e "\n  [Audit & Verification]"
    AUDIT_OUT=$(${INVOKER} ${LLM_OPTS} --role=auditor --risks="${RISKS_CONFIG}" --prompt="${REFINED_OUT}" < /dev/null)
    echo "${AUDIT_OUT}" | sed 's/^/  /'

    if echo "${AUDIT_OUT}" | grep -q "\[FAIL\]"; then
        echo -e "\n!!! AUDIT FAILED !!! Execution blocked for this topic."
    fi

done < "${TEMP_EXEC}"

# Re-enable set -e
set -e

rm -f ./tmp/.rys.${rys_uuid}*
