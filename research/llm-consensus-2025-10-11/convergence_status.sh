#!/bin/bash
# Quick status check - called by main loop
ROUND=$1
REVIEW_DIR="/mnt/irina_storage/files/temp/paradigm_review"
ROUND_DIR="${REVIEW_DIR}/round${ROUND}_responses"

LATEST=$(ls -td ${ROUND_DIR}/2025* 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
    echo "STATUS=NOT_STARTED"
    exit 1
fi

if [ ! -f "${LATEST}/summary.json" ]; then
    echo "STATUS=PROCESSING"
    exit 2
fi

# Round complete - analyze
MD_COUNT=$(ls ${LATEST}/*.md 2>/dev/null | grep -v fiedler.log | wc -l)
CONSENSUS=$(grep -li "STATUS.*CONSENSUS" ${LATEST}/*.md 2>/dev/null | wc -l)

echo "STATUS=COMPLETE"
echo "MODELS=${MD_COUNT}"
echo "CONSENSUS=${CONSENSUS}"
echo "DIR=${LATEST}"

# Check termination
if [ $CONSENSUS -ge $((MD_COUNT * 2 / 3)) ] && [ $CONSENSUS -gt 0 ]; then
    echo "TERMINATION=CONSENSUS_REACHED"
    exit 0
fi

if [ $MD_COUNT -le 1 ]; then
    echo "TERMINATION=ATTRITION"
    exit 0
fi

echo "TERMINATION=CONTINUE"
exit 3  # Continue to next round

