#!/bin/bash
# Show convergence progress across all rounds

REVIEW_DIR="/mnt/irina_storage/files/temp/paradigm_review"

echo "=== LLM CONSENSUS CONVERGENCE TRACKER ==="
echo ""

for round in 1 2 3 4 5 6 7 8 9 10; do
    ROUND_DIR="${REVIEW_DIR}/round${round}_responses"
    if [ "$round" == "1" ]; then
        ROUND_DIR="${REVIEW_DIR}/responses"
    fi
    
    LATEST=$(ls -td ${ROUND_DIR}/2025* 2>/dev/null | head -1)
    
    if [ -z "$LATEST" ]; then
        continue
    fi
    
    MD_COUNT=$(ls ${LATEST}/*.md 2>/dev/null | grep -v fiedler.log | wc -l)
    HAS_SUMMARY=""
    if [ -f "${LATEST}/summary.json" ]; then
        HAS_SUMMARY="✓"
    else
        HAS_SUMMARY="⏳"
    fi
    
    TOTAL_LINES=$(cat ${LATEST}/*.md 2>/dev/null | grep -v fiedler.log | wc -l)
    
    printf "Round %2d: %s  %d models, %6d total lines" "$round" "$HAS_SUMMARY" "$MD_COUNT" "$TOTAL_LINES"
    
    # List models
    echo -n " ("
    ls ${LATEST}/*.md 2>/dev/null | grep -v fiedler.log | while read f; do
        model=$(basename "$f" .md | cut -d'_' -f1)
        echo -n "$model "
    done | head -c 60
    echo ")"
done

