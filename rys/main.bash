#!/usr/bin/env bash

# Stop execution on error
set -e

# Configuration & Environment Variables
HOST="${RYS_LLM_HOST:-localhost}"
PORT="${RYS_LLM_PORT:-11434}"
MODEL="${RYS_LLM_MODEL:-gemma3n:e4b}"

FROM_PHASE=1
PROMPT=""
AUTO_MODE=""
STOP_PHASE=3

# Simple Argument Parsing
for arg in "$@"; do
    if [[ $arg == --from=* ]]; then
        FROM_PHASE=${arg#--from=}
    elif [[ $arg == "--auto" ]]; then
        AUTO_MODE="--auto"
    elif [[ -z "$PROMPT" ]]; then
        PROMPT="$arg"
    fi
done

# Ensure prompt
if [ -z "$PROMPT" ]; then
    echo "Usage: $0 \"Your prompt here\" [--from=N]"
    exit 1
fi

mkdir -p ./tmp/

# Generate Hash from prompt
prompt_hash=$(printf "%s" "$PROMPT" | md5sum | cut -c1-8)

# Define Phase JSON paths (v2.0 - 5 Phases Pipeline)
P1_JSON="./tmp/.rys.${prompt_hash}.p1.json"
P2_JSON="./tmp/.rys.${prompt_hash}.p2.json"
P3_JSON="./tmp/.rys.${prompt_hash}.p3.json"
P4_JSON="./tmp/.rys.${prompt_hash}.p4.json"

common_args="--host ${HOST} --port ${PORT} --model ${MODEL}"

# Force clear sub-caches for specified phases
IFS=',' read -ra TARGET_PHASES <<< "$FROM_PHASE"
RE_RUN_LIST=()
MIN_PHASE=5
ONLY_CACHE_USE=""

# Default stop phase logic
if [ "$FROM_PHASE" = "1" ]; then
    STOP_PHASE=4
else
    STOP_PHASE=5
fi

if [[ $FROM_PHASE =~ ^[0-9]+$ ]]; then
    # Traditional behavior: from N to 5
    for (( i=$FROM_PHASE; i<=4; i++ )); do
        RE_RUN_LIST+=($i)
    done
    MIN_PHASE=$FROM_PHASE
    # If explicitly starting from a later phase, stop at 5. Otherwise default 4.
    if [ "$FROM_PHASE" -gt 1 ]; then STOP_PHASE=5; fi
elif [[ $FROM_PHASE == ,* ]]; then
    # Compact behavior: use all caches up to N
    STOP_PHASE=${FROM_PHASE#,}
    MIN_PHASE=1
    ONLY_CACHE_USE="true"
    # No phases to re-run/clear
else
    # Explicit list: only specific phases, then stop at max
    for p in "${TARGET_PHASES[@]}"; do
        if [ -n "$p" ]; then
            RE_RUN_LIST+=($p)
            if [ "$p" -lt "$MIN_PHASE" ]; then MIN_PHASE=$p; fi
            if [ "$p" -gt "$STOP_PHASE" ] || [ "$STOP_PHASE" -eq 5 ]; then STOP_PHASE=$p; fi
        fi
    done
fi

if [ -z "$ONLY_CACHE_USE" ]; then
    for p in "${RE_RUN_LIST[@]}"; do
        if [ "$p" -ge 3 ]; then
            rm -f ./tmp/.rys.${prompt_hash}.*.p${p}*
            rm -f ./tmp/.rys.${prompt_hash}.p${p}.json
        fi
    done
fi

echo ">>> Initializing Session (Hash: ${prompt_hash}, Starting from Phase: ${MIN_PHASE}, Stopping after Phase: ${STOP_PHASE})"
if [[ ! $FROM_PHASE =~ ^[0-9]+$ ]]; then
    if [ -n "$ONLY_CACHE_USE" ]; then
        echo "Mode: Only use caches up to Phase ${STOP_PHASE}"
    else
        echo "Target re-run phases: ${RE_RUN_LIST[*]}"
    fi
fi

rys_uuid="${prompt_hash}"
echo "Session ID: ${rys_uuid}"

# --- Helper for Phase Control ---
run_check() {
    local phase_idx=$1
    local json_path=$2

    # In ONLY_CACHE_USE mode, always try to use cache first if it exists
    if [ -n "$ONLY_CACHE_USE" ] && [ -f "$json_path" ]; then
        # return 1 means skip (Use cache)
        return 1
    fi

    if [ "$MIN_PHASE" -eq "$phase_idx" ]; then
        return 0 # Always Run starting phase (unless in ONLY_CACHE_USE mode handled above)
    fi
    if [ "$MIN_PHASE" -gt "$phase_idx" ]; then
        if [ -f "$json_path" ]; then
            return 1 # Skip
        else
            # Error out if cache is missing and we're not running to recover
            # Note: The 'recover' logic was previously return 0 here.
            # If we want to keep recover logic, we should return 0 but maybe mark it.
            return 0
        fi
    fi
    return 0 # Run
}

check_stop() {
    local current_phase=$1
    if [ "$current_phase" -eq "$STOP_PHASE" ]; then
        echo -e "\nReached Stop Phase: $STOP_PHASE. Exiting."
        exit 0
    fi
}

# --- Execution ---

if run_check 1 "${P1_JSON}"; then
    echo -e "\n>>> 1. Translation Phase"
    python3 ./rys/phase1_translate.py --prompt "$PROMPT" --out-json "${P1_JSON}" ${common_args}
else
    echo -e "\n>>> 1. Translation Phase (Cached)"
    python3 -c "import json; d=json.load(open('${P1_JSON}')); print(d.get('content', d.get('translated_text', '')))"
fi
check_stop 1

if run_check 2 "${P2_JSON}"; then
    echo -e "\n>>> 2. Dispatch Phase"
    python3 ./rys/phase2_dispatch.py --in-json "${P1_JSON}" --out-json "${P2_JSON}" ${common_args}
else
    echo -e "\n>>> 2. Dispatch Phase (Cached)"
    python3 -c "import json; d=json.load(open('${P2_JSON}')); print(d.get('content', d.get('dispatch_out', '')))"
fi
check_stop 2

if run_check 3 "${P3_JSON}"; then
    echo -e "\n>>> 3. Grouping Phase"
    python3 ./rys/phase3_group.py --in-json "${P2_JSON}" --out-json "${P3_JSON}" ${common_args} --uuid "${rys_uuid}"
else
    echo -e "\n>>> 3. Grouping Phase (Cached)"
    python3 -c "import json; d=json.load(open('${P3_JSON}')); [print(req['display']) for req in d.get('grouped_requests', [])]"
fi
check_stop 3

if run_check 4 "${P4_JSON}"; then
    echo -e "\n>>> 4. REQUEST Processing Phase"
    python3 ./rys/phase4_request_loop.py --in-json "${P3_JSON}" --out-json "${P4_JSON}" --uuid "${rys_uuid}" ${common_args}
else
    echo -e "\n>>> 4. REQUEST Processing Phase (Cached)"
    python3 -c "import json; d=json.load(open('${P4_JSON}')); [print(f'Handled {req[\"id\"]} ({req[\"skill\"]})') for req in d.get('grouped_requests', [])]"
fi
check_stop 4

echo -e "\n>>> 5. Execution Loop (Interactive)"
python3 ./rys/phase5_execute.py --in-json "${P4_JSON}" ${AUTO_MODE}

echo -e "\nAll Done. Results stored in ./tmp/"
