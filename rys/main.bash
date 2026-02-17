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
export RYS_SIMILARITY="0.0"

# XDG Base Directory Support
export RYS_CACHE_DIR="${RYS_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/rys}"
mkdir -p "${RYS_CACHE_DIR}"

# Simple Argument Parsing
for arg in "$@"; do
    if [[ $arg == --from=* ]]; then
        FROM_PHASE=${arg#--from=}
    elif [[ $arg == "--auto" ]]; then
        export RYS_AUTO="true"
    elif [[ $arg == --request=* ]]; then
        REQ_FILTER="${arg#--request=}"
    elif [[ $arg == --similarity=* ]]; then
        export RYS_SIMILARITY="${arg#--similarity=}"
    elif [[ $arg == -s* ]]; then
        export RYS_SIMILARITY="${arg#-s}"
    elif [[ -z "$PROMPT" ]]; then
        PROMPT="$arg"
    fi
done

# Ensure prompt
if [ -z "$PROMPT" ]; then
    echo "Usage: $0 \"Your prompt here\" [--from=N]"
    exit 1
fi

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

# Calculate Configuration Hash (Skills & Cheatsheets)
# Normalizes JSON to ignore formatting differences.
CONFIG_HASH=$(python3 -c '
import json, glob, os, hashlib
def get_norm(path):
    with open(path, "r") as f: return json.dumps(json.load(f), sort_keys=True, separators=(",", ":"))
files = ["config/skills.json"] + sorted(glob.glob("config/skills/*.json"))
contents = "".join(get_norm(f) for f in files if os.path.exists(f))
print(hashlib.md5(contents.encode()).hexdigest()[:8])
')

# --- Execution ---

# Phase 1: Translation (Input: PROMPT)
P1_HASH=$(printf "%s" "$PROMPT" | md5sum | cut -c1-8)
P1_JSON="${RYS_CACHE_DIR}/.cache.p1.${P1_HASH}.json"
export RYS_UUID="${P1_HASH}"

if run_check 1 "${P1_JSON}"; then
    echo -e "\n>>> 1. Translation Phase"
    python3 ./rys/phase1_translate.py --prompt "$PROMPT" --out-json "${P1_JSON}" ${common_args}
else
    echo -e "\n>>> 1. Translation Phase (Cached)"
    python3 -c "import json; d=json.load(open('${P1_JSON}')); print(d.get('content', d.get('translated_text', '')))"
fi
check_stop 1

# Phase 2: Dispatch (Input: P1_JSON + CONFIG)
P2_HASH=$( (md5sum < "${P1_JSON}" | cut -c1-8; echo "$CONFIG_HASH") | md5sum | cut -c1-8)
P2_JSON="${RYS_CACHE_DIR}/.cache.p2.${P2_HASH}.json"
export RYS_UUID="${P2_HASH}"

if run_check 2 "${P2_JSON}"; then
    echo -e "\n>>> 2. Dispatch Phase"
    python3 ./rys/phase2_dispatch.py --in-json "${P1_JSON}" --out-json "${P2_JSON}" ${common_args} --similarity "${RYS_SIMILARITY}"
else
    echo -e "\n>>> 2. Dispatch Phase (Cached)"
    python3 -c "import json; d=json.load(open('${P2_JSON}')); print(d.get('content', d.get('dispatch_out', '')))"
fi
check_stop 2

# Phase 3: Grouping (Input: P2_JSON + CONFIG)
P3_HASH=$( (md5sum < "${P2_JSON}" | cut -c1-8; echo "$CONFIG_HASH") | md5sum | cut -c1-8)
P3_JSON="${RYS_CACHE_DIR}/.cache.p3.${P3_HASH}.json"
export RYS_UUID="${P3_HASH}"

if run_check 3 "${P3_JSON}"; then
    echo -e "\n>>> 3. Grouping Phase"
    python3 ./rys/phase3_group.py --in-json "${P2_JSON}" --out-json "${P3_JSON}" ${common_args} --uuid "${RYS_UUID}"
else
    echo -e "\n>>> 3. Grouping Phase (Cached)"
    python3 -c "import json; d=json.load(open('${P3_JSON}')); [print(req['display']) for req in d.get('grouped_requests', [])]"
fi
check_stop 3

# Phase 4: Request Processing (Input: P3_JSON + CONFIG)
P4_HASH=$( (md5sum < "${P3_JSON}" | cut -c1-8; echo "$CONFIG_HASH") | md5sum | cut -c1-8)
P4_JSON="${RYS_CACHE_DIR}/.cache.p4.${P4_HASH}.json"
export RYS_UUID="${P4_HASH}"

if run_check 4 "${P4_JSON}"; then
    echo -e "\n>>> 4. REQUEST Processing Phase"
    python3 ./rys/phase4_request_loop.py --in-json "${P3_JSON}" --out-json "${P4_JSON}" --uuid "${RYS_UUID}" ${common_args}
else
    echo -e "\n>>> 4. REQUEST Processing Phase (Cached)"
    python3 -c "import json; d=json.load(open('${P4_JSON}')); [print(f'Handled {req[\"request_id\"]} ({req[\"skill\"]})') for req in d.get('integrated_requests', [])]"
fi
check_stop 4

# Phase 5: Script Generation (Input: P4_JSON + CONFIG)
P5_HASH=$( (md5sum < "${P4_JSON}" | cut -c1-8; echo "$CONFIG_HASH") | md5sum | cut -c1-8)
P5_JSON="${RYS_CACHE_DIR}/.cache.p5.${P5_HASH}.json"
export RYS_UUID="${P5_HASH}"

if run_check 5 "${P5_JSON}"; then
    echo -e "\n>>> 5. Script Generation Phase"
    req_arg=""
    if [ -n "$REQ_FILTER" ]; then req_arg="--request=${REQ_FILTER}"; fi
    python3 ./rys/phase5_generate.py --in-json "${P4_JSON}" --out-json "${P5_JSON}" --uuid "${RYS_UUID}" ${common_args} ${req_arg}
else
    echo -e "\n>>> 5. Script Generation Phase (Cached)"
    # Resolve and show path based on RYS_CACHE_DIR if the stored path is not found
    python3 -c "import json, os; d=json.load(open('${P5_JSON}')); cache_dir=os.environ.get('RYS_CACHE_DIR',''); \
    [print(f'Generated {s[\"request_id\"]} ({s[\"skill\"]}) -> {s[\"path\"] if os.path.exists(s[\"path\"]) else os.path.join(cache_dir, os.path.basename(s[\"path\"]))}') for s in d.get('generated_scripts', [])]"
fi
check_stop 5

# Phase 6: Execution (Always runs if reach here)
echo -e "\n>>> 6. Execution Phase"
auto_flag=""
if [ "$RYS_AUTO" == "true" ]; then auto_flag="--auto"; fi
python3 ./rys/phase6_execute.py --in-json "${P5_JSON}" $auto_flag

# --- Utility Hooks (Future Extensions) ---
# Example: RAG / Semantic Search
# python3 ./rys/embedding.py "Search Query" --quiet

echo -e "\nAll Done. Results stored in ${RYS_CACHE_DIR}"
