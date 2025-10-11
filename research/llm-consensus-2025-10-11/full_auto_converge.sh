#!/bin/bash
# Fully automated convergence loop - no human intervention
# Runs until consensus or natural attrition

REVIEW_DIR="/mnt/irina_storage/files/temp/paradigm_review"
CURRENT_ROUND=3
MAX_ROUNDS=15

echo "=== AUTONOMOUS LLM CONVERGENCE PROCESS ===" | tee -a ${REVIEW_DIR}/convergence.log
echo "Starting autonomous iteration from Round ${CURRENT_ROUND}" | tee -a ${REVIEW_DIR}/convergence.log
echo "Will run until consensus or Round ${MAX_ROUNDS}" | tee -a ${REVIEW_DIR}/convergence.log
echo "" | tee -a ${REVIEW_DIR}/convergence.log

# Function to check if round is complete
wait_for_round() {
    local round=$1
    local round_dir="${REVIEW_DIR}/round${round}_responses"
    local max_wait=600  # 10 minutes max
    local waited=0
    
    while [ $waited -lt $max_wait ]; do
        latest=$(ls -td ${round_dir}/2025* 2>/dev/null | head -1)
        if [ -n "$latest" ] && [ -f "${latest}/summary.json" ]; then
            echo "Round ${round} complete after ${waited}s" | tee -a ${REVIEW_DIR}/convergence.log
            return 0
        fi
        sleep 10
        waited=$((waited + 10))
    done
    
    echo "Round ${round} timeout after ${max_wait}s" | tee -a ${REVIEW_DIR}/convergence.log
    return 1
}

# Function to count active models
count_models() {
    local round=$1
    local round_dir="${REVIEW_DIR}/round${round}_responses"
    latest=$(ls -td ${round_dir}/2025* 2>/dev/null | head -1)
    if [ -n "$latest" ]; then
        ls ${latest}/*.md 2>/dev/null | grep -v fiedler.log | wc -l
    else
        echo "0"
    fi
}

echo "Waiting for Round ${CURRENT_ROUND} to complete..." | tee -a ${REVIEW_DIR}/convergence.log
