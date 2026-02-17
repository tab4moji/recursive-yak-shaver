#!/usr/bin/env bash
#
# phase5_standalone.bash (v1.2)
# Executes ONLY Phase 5 using cached Phase 4 data.
# Supports position-independent arguments.
#

# --- Argument Parsing ---
INPUT=""
export RYS_AUTO="false"
REQ_FILTER=""

for arg in "$@"; do
    case $arg in
        --auto)
            export RYS_AUTO="true"
            ;;
        --request=*)
            REQ_FILTER="${arg#*=}"
            ;;
        *)
            if [ -z "$INPUT" ]; then
                INPUT="$arg"
            fi
            ;;
    esac
done

if [ -z "$INPUT" ]; then
    echo "Usage: $0 <prompt_or_hash> [--auto] [--request=ID]"
    exit 1
fi

# --- Configuration ---
export RYS_LLM_HOST="${RYS_LLM_HOST:-localhost}"
export RYS_LLM_PORT="${RYS_LLM_PORT:-11434}"
export RYS_LLM_MODEL="${RYS_LLM_MODEL:-gemma3n:e4b}"

# XDG Base Directory Support
export RYS_CACHE_DIR="${RYS_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/rys}"
mkdir -p "${RYS_CACHE_DIR}"

# Determine Hash
if [[ "$INPUT" =~ ^[0-9a-f]{8}$ ]]; then
    prompt_hash="$INPUT"
else
    prompt_hash=$(printf "%s" "$INPUT" | md5sum | cut -c1-8)
fi
export RYS_UUID="${prompt_hash}"

P4_JSON="${RYS_CACHE_DIR}/.rys.${prompt_hash}.p4.json"

if [ ! -f "$P4_JSON" ]; then
    echo "Error: Cache file ${P4_JSON} not found."
    exit 1
fi

echo ">>> Phase 5 Standalone Execution (Session Hash: ${prompt_hash})"

# Extract integrated_requests and loop
requests_json=$(python3 -c "import json; d=json.load(open('${P4_JSON}')); print(json.dumps(d.get('integrated_requests', [])))")
requests_count=$(echo "$requests_json" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")

for (( i=0; i<$requests_count; i++ )); do
    req_json=$(echo "$requests_json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(json.dumps(d[$i]))")
    req_id=$(echo "$req_json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['request_id'])")
    
    # Filter by request ID if specified
    if [ -n "$REQ_FILTER" ] && [ "$req_id" != "$REQ_FILTER" ]; then
        continue
    fi

    skill=$(echo "$req_json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['skill'])")
    
    if [ "$skill" == "IDONTKNOW" ]; then
        echo -e "\n>>> Skipping ${req_id} (Reason: Out of scope)"
        echo "$req_json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Message: {d[\"topics\"][0][\"raw\"].split(\"| IDONTKNOW: \")[-1].strip()}')"
        continue
    fi

    # Pass --auto explicitly to coder_exec.py if active
    PASSTHROUGH=""
    if [ "$RYS_AUTO" == "true" ]; then
        PASSTHROUGH="--auto"
    fi

    python3 ./rys/phase5_coder_exec.py --request-json "$req_json" $PASSTHROUGH
done

echo -e "\nPhase 5 Standalone Complete."
