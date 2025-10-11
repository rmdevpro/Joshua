#!/bin/bash
# Fully automated LLM consensus convergence
# Runs rounds until consensus or natural attrition to single model

REVIEW_DIR="/mnt/irina_storage/files/temp/paradigm_review"
MAX_ROUNDS=20
CURRENT_ROUND=2  # Starting from round 2 (already complete)

echo "=== LLM Consensus Convergence Process ==="
echo "Starting from Round ${CURRENT_ROUND} (complete)"
echo "Will iterate up to Round ${MAX_ROUNDS} or until consensus"
echo ""

while [ $CURRENT_ROUND -lt $MAX_ROUNDS ]; do
    NEXT_ROUND=$((CURRENT_ROUND + 1))
    
    echo "========================================"
    echo "Building Round ${NEXT_ROUND} package..."
    echo "========================================"
    
    # Build next round package
    ${REVIEW_DIR}/iterate_rounds.sh ${NEXT_ROUND}
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to build Round ${NEXT_ROUND} package"
        exit 1
    fi
    
    PACKAGE="${REVIEW_DIR}/round${NEXT_ROUND}_package.md"
    OUTPUT_DIR="${REVIEW_DIR}/round${NEXT_ROUND}_responses"
    
    echo ""
    echo "Sending to Fiedler for Round ${NEXT_ROUND} analysis..."
    
    # Send via fiedler (correlation ID will be auto-generated)
    # This part will be called from Claude Code context
    echo "READY_FOR_ROUND_${NEXT_ROUND}"
    echo "Package: ${PACKAGE}"
    echo "Output: ${OUTPUT_DIR}"
    
    # Wait for user to trigger Fiedler send from Claude Code
    break
done

