#!/usr/bin/env bash

# Stop execution on error
set -e

# Configuration & Environment Variables
export RYS_LLM_HOST="${RYS_LLM_HOST:-localhost}"
export RYS_LLM_PORT="${RYS_LLM_PORT:-11434}"
export RYS_LLM_MODEL="${RYS_LLM_MODEL:-gemma3n:e4b}"

FROM_PHASE=,6
PROMPT=""
export RYS_AUTO="false"
STOP_PHASE=6
REQ_FILTER=""

# Simple Argument Parsing
for arg in "$@"; do
    if [[ $arg == --from=* ]]; then
        FROM_PHASE=${arg#--from=}
    elif [[ $arg == "--auto" ]]; then
        export RYS_AUTO="true"
    elif [[ $arg == --request=* ]]; then
        REQ_FILTER="${arg#--request=}"
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

# Initial Session ID based on prompt
prompt_hash=$(printf "%s" "$PROMPT" | md5sum | cut -c1-8)

common_args="--host ${RYS_LLM_HOST} --port ${RYS_LLM_PORT} --model ${RYS_LLM_MODEL}"

# --- Phase Control Logic ---
MIN_PHASE=6
ONLY_CACHE_USE=""

if [[ $FROM_PHASE =~ ^([0-9]+),([0-9]+)$ ]]; then
    # Range mode: START,STOP
    MIN_PHASE="${BASH_REMATCH[1]}"
    STOP_PHASE="${BASH_REMATCH[2]}"
elif [[ $FROM_PHASE =~ ^[0-9]+$ ]]; then
    # Standard: From N to 6
    MIN_PHASE=$FROM_PHASE
elif [[ $FROM_PHASE == ,* ]]; then
    # Cache Priority: Use caches up to N
    STOP_PHASE=${FROM_PHASE#,}
    MIN_PHASE=1
    ONLY_CACHE_USE="true"
fi

echo "Session ID: ${prompt_hash} (Mode: ${FROM_PHASE}, Stop: ${STOP_PHASE})"

run_check() {
    local phase_idx=$1
    local json_path=$2

    # In ONLY_CACHE_USE mode, always try to use cache first if it exists
    if [ -n "$ONLY_CACHE_USE" ] && [ -f "$json_path" ]; then
        return 1 # Skip (Use cache)
    fi

    if [ "$MIN_PHASE" -eq "$phase_idx" ]; then
        return 0 # Always Run starting phase
    fi
    if [ "$MIN_PHASE" -gt "$phase_idx" ]; then
        if [ -f "$json_path" ]; then
            return 1 # Skip
        else
            return 0 # Recover missing cache
        fi
    fi
    return 0 # Run
}

check_stop() {
    if [ "$1" -eq "$STOP_PHASE" ]; then
        echo -e "\nReached Stop Phase: $STOP_PHASE. Exiting."
        exit 0
    fi
}

# --- Execution ---

# Phase 1: Translation (Input: PROMPT)
P1_HASH=$(printf "%s" "$PROMPT" | md5sum | cut -c1-8)
P1_JSON="./tmp/.cache.p1.${P1_HASH}.json"
export RYS_UUID="${P1_HASH}"

if run_check 1 "${P1_JSON}"; then
    echo -e "\n>>> 1. Translation Phase"
    python3 ./rys/phase1_translate.py --prompt "$PROMPT" --out-json "${P1_JSON}" ${common_args}
else
    echo -e "\n>>> 1. Translation Phase (Cached)"
    python3 -c "import json; d=json.load(open('${P1_JSON}')); print(d.get('content', d.get('translated_text', '')))"
fi
check_stop 1

# Phase 2: Dispatch (Input: P1_JSON)
P2_HASH=$(md5sum < "${P1_JSON}" | cut -c1-8)
P2_JSON="./tmp/.cache.p2.${P2_HASH}.json"
export RYS_UUID="${P2_HASH}"

if run_check 2 "${P2_JSON}"; then
    echo -e "\n>>> 2. Dispatch Phase"
    python3 ./rys/phase2_dispatch.py --in-json "${P1_JSON}" --out-json "${P2_JSON}" ${common_args}
else
    echo -e "\n>>> 2. Dispatch Phase (Cached)"
    python3 -c "import json; d=json.load(open('${P2_JSON}')); print(d.get('content', d.get('dispatch_out', '')))"
fi
check_stop 2

# Phase 3: Grouping (Input: P2_JSON)
P3_HASH=$(md5sum < "${P2_JSON}" | cut -c1-8)
P3_JSON="./tmp/.cache.p3.${P3_HASH}.json"
export RYS_UUID="${P3_HASH}"

if run_check 3 "${P3_JSON}"; then
    echo -e "\n>>> 3. Grouping Phase"
    python3 ./rys/phase3_group.py --in-json "${P2_JSON}" --out-json "${P3_JSON}" ${common_args} --uuid "${RYS_UUID}"
else
    echo -e "\n>>> 3. Grouping Phase (Cached)"
    python3 -c "import json; d=json.load(open('${P3_JSON}')); [print(req['display']) for req in d.get('grouped_requests', [])]"
fi
check_stop 3

# Phase 4: Request Processing (Input: P3_JSON)
P4_HASH=$(md5sum < "${P3_JSON}" | cut -c1-8)
P4_JSON="./tmp/.cache.p4.${P4_HASH}.json"
export RYS_UUID="${P4_HASH}"

if run_check 4 "${P4_JSON}"; then
    echo -e "\n>>> 4. REQUEST Processing Phase"
    python3 ./rys/phase4_request_loop.py --in-json "${P3_JSON}" --out-json "${P4_JSON}" --uuid "${RYS_UUID}" ${common_args}
else
    echo -e "\n>>> 4. REQUEST Processing Phase (Cached)"
    python3 -c "import json; d=json.load(open('${P4_JSON}')); [print(f'Handled {req[\"request_id\"]} ({req[\"skill\"]})') for req in d.get('integrated_requests', [])]"
fi
check_stop 4

# Phase 5: Script Generation (Input: P4_JSON)
P5_HASH=$(md5sum < "${P4_JSON}" | cut -c1-8)
P5_JSON="./tmp/.cache.p5.${P5_HASH}.json"
export RYS_UUID="${P5_HASH}"

if run_check 5 "${P5_JSON}"; then
    echo -e "\n>>> 5. Script Generation Phase"
    req_arg=""
    if [ -n "$REQ_FILTER" ]; then req_arg="--request=${REQ_FILTER}"; fi
    python3 ./rys/phase5_generate.py --in-json "${P4_JSON}" --out-json "${P5_JSON}" --uuid "${RYS_UUID}" ${common_args} ${req_arg}
else
    echo -e "\n>>> 5. Script Generation Phase (Cached)"
    python3 -c "import json; d=json.load(open('${P5_JSON}')); [print(f'Generated {s[\"request_id\"]} ({s[\"skill\"]}) -> {s[\"path\"]}') for s in d.get('generated_scripts', [])]"
fi
check_stop 5

# Phase 6: Execution (Always runs if reach here)
echo -e "\n>>> 6. Execution Phase"
auto_flag=""
if [ "$RYS_AUTO" == "true" ]; then auto_flag="--auto"; fi
python3 ./rys/phase6_execute.py --in-json "${P5_JSON}" $auto_flag

echo -e "\nAll Done. Results stored in ./tmp/"
