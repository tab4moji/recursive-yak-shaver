#!/bin/bash
# 0.1: RYS Robustness Verifier
# Purpose: Runs test.bash and pytest.bash 3 times each to ensure system stability.

set -e

RUNS=3
FAILED=0

for i in $(seq 1 $RUNS); do
    echo "========================================"
    echo "Starting Robustness Run $i / $RUNS"
    echo "========================================"
    
    # Clear cache to ensure a fresh start for each run
    echo "Clearing RYS cache..."
    rm -rf /home/pi/.cache/rys
    
    echo "Running tools/test.bash (Run $i)..."
    if ! tryit -d -q -t 240 'bash tools/test.bash'; then
        echo "Error: tools/test.bash failed on run $i"
        FAILED=1
        break
    fi
    
    echo "Running tools/pytest.bash (Run $i)..."
    if ! tryit -d -q -t 240 'bash tools/pytest.bash'; then
        echo "Error: tools/pytest.bash failed on run $i"
        FAILED=1
        break
    fi
    
    echo "Run $i successful."
done

if [ $FAILED -eq 0 ]; then
    echo "========================================"
    echo "All $RUNS runs completed successfully!"
    echo "========================================"
else
    echo "========================================"
    echo "Robustness verification FAILED."
    echo "========================================"
    exit 1
fi
