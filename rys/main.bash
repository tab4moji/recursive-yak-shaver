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

# Define Phase JSON paths
P1_JSON="./tmp/.rys.${prompt_hash}.p1.json"
P2_JSON="./tmp/.rys.${prompt_hash}.p2.json"
P3_JSON="./tmp/.rys.${prompt_hash}.p3.json"
P4_JSON="./tmp/.rys.${prompt_hash}.p4.json"
P5_JSON="./tmp/.rys.${prompt_hash}.p5.json"

common_args="--host ${HOST} --port ${PORT} --model ${MODEL}"
echo ">>> Initializing Session (Hash: ${prompt_hash}, Starting from Phase: ${FROM_PHASE})"

rys_uuid="${prompt_hash}"
echo "Session ID: ${rys_uuid}"

# --- Helper for Phase Control ---
run_check() {
    local phase_idx=$1
    local json_path=$2
    if [ "$FROM_PHASE" -gt "$phase_idx" ]; then
        if [ -f "$json_path" ]; then
            echo "[SKIP] Using cached results for Phase $phase_idx: $json_path"
            return 1 # Skip
        else
            echo "[ERROR] Cache missing for required Phase $phase_idx: $json_path"
            exit 1
        fi
    fi
    return 0 # Run
}

# --- Execution ---

# Force clear sub-caches for phases >= FROM_PHASE
for (( i=$FROM_PHASE; i<=5; i++ )); do
    rm -f ./tmp/.rys.${prompt_hash}.*.p${i}.*.json
done

echo -e "\n>>> 1. Translation Phase"
if run_check 1 "${P1_JSON}"; then
    python3 ./rys/phase1_translate.py --prompt "$PROMPT" --out-json "${P1_JSON}" ${common_args}
else
    python3 -c "import json; print(json.load(open('${P1_JSON}'))['translated_text'])"
fi

echo -e "\n>>> 2. Dispatch Phase"
if run_check 2 "${P2_JSON}"; then
    python3 ./rys/phase2_dispatch.py --in-json "${P1_JSON}" --out-json "${P2_JSON}" ${common_args}
else
    python3 -c "import json; print(json.load(open('${P2_JSON}'))['dispatch_out'])"
fi

echo -e "\n>>> 3. Request Visualization Phase"
if run_check 3 "${P3_JSON}"; then
    python3 ./rys/phase3_visualize.py --in-json "${P2_JSON}" --out-json "${P3_JSON}" ${common_args}
else
    python3 -c "import json; print(json.load(open('${P3_JSON}'))['titles_out'])"
fi

echo -e "\n>>> 4. Strategic Planning Phase"
if run_check 4 "${P4_JSON}"; then
    python3 ./rys/phase4_plan.py --in-json "${P3_JSON}" --out-json "${P4_JSON}" --uuid "${rys_uuid}" ${common_args}
else
    python3 -c "import json; d=json.load(open('${P4_JSON}')); [print(f'\n{t[\"title\"]}\n{t[\"refined_out\"]}') for t in d['planned_topics']]"
fi

echo -e "\n>>> 5. Step-by-Step Coding Phase"
if run_check 5 "${P5_JSON}"; then
    python3 ./rys/phase5_code.py --in-json "${P4_JSON}" --out-json "${P5_JSON}" --uuid "${rys_uuid}" ${common_args}
else
    python3 -c "import json; d=json.load(open('${P5_JSON}')); [print(f'\n{s[\"title\"]}\nFile: {s[\"path\"]}') for s in d['scripts']]"
fi

echo -e "\n>>> 6. Execution Loop (Interactive)"
python3 ./rys/phase6_execute.py --in-json "${P5_JSON}" ${AUTO_MODE}

echo -e "\nAll Done. Results stored in ./tmp/"
