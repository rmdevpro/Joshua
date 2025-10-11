#!/bin/bash
# Active convergence driver - monitors and sends to Fiedler
REVIEW_DIR="/mnt/irina_storage/files/temp/paradigm_review"
LOG="${REVIEW_DIR}/driver.log"

echo "=== CONVERGENCE DRIVER ACTIVE ===" | tee $LOG
date | tee -a $LOG

# This file signals when a round is ready
SIGNAL_FILE="${REVIEW_DIR}/next_round.signal"

# Track current round
CURRENT_ROUND=4

while [ $CURRENT_ROUND -le 15 ]; do
    echo "Monitoring Round ${CURRENT_ROUND}..." | tee -a $LOG
    
    # Wait for round completion
    ROUND_DIR="${REVIEW_DIR}/round${CURRENT_ROUND}_responses"
    
    for wait in {1..120}; do
        LATEST=$(ls -td ${ROUND_DIR}/2025* 2>/dev/null | head -1)
        if [ -n "$LATEST" ] && [ -f "${LATEST}/summary.json" ]; then
            break
        fi
        sleep 10
    done
    
    if [ -z "$LATEST" ]; then
        echo "Round ${CURRENT_ROUND} timeout" | tee -a $LOG
        break
    fi
    
    # Check results
    MD_COUNT=$(ls ${LATEST}/*.md 2>/dev/null | grep -v fiedler.log | wc -l)
    CONSENSUS=$(grep -li "STATUS.*CONSENSUS" ${LATEST}/*.md 2>/dev/null | wc -l)
    
    echo "Round ${CURRENT_ROUND}: ${MD_COUNT} models, ${CONSENSUS} consensus" | tee -a $LOG
    
    # Check termination
    if [ $CONSENSUS -ge $((MD_COUNT * 2 / 3)) ]; then
        echo "CONSENSUS DETECTED - STOPPING" | tee -a $LOG
        echo "CONVERGED_AT_ROUND_${CURRENT_ROUND}" > ${REVIEW_DIR}/final.flag
        exit 0
    fi
    
    if [ $MD_COUNT -le 1 ]; then
        echo "ATTRITION COMPLETE - STOPPING" | tee -a $LOG
        echo "ATTRITED_AT_ROUND_${CURRENT_ROUND}" > ${REVIEW_DIR}/final.flag
        exit 0
    fi
    
    # Prepare next round
    NEXT=$((CURRENT_ROUND + 1))
    echo "Preparing Round ${NEXT}..." | tee -a $LOG
    ${REVIEW_DIR}/iterate_rounds.sh ${NEXT} >> $LOG 2>&1
    
    echo "NEXT_ROUND=${NEXT}" > $SIGNAL_FILE
    CURRENT_ROUND=$NEXT
    
    # Small delay before next iteration
    sleep 5
done

echo "DRIVER COMPLETED" | tee -a $LOG
