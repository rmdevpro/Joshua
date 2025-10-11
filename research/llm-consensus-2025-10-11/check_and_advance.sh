#!/bin/bash
# Check if current round is complete and show stats

REVIEW_DIR="/mnt/irina_storage/files/temp/paradigm_review"
ROUND=$1

if [ -z "$ROUND" ]; then
    echo "Usage: $0 <current_round_number>"
    exit 1
fi

RESPONSES_DIR="${REVIEW_DIR}/round${ROUND}_responses"

# Find most recent response directory
LATEST=$(ls -td ${RESPONSES_DIR}/2025* 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
    echo "No responses found yet for Round ${ROUND}"
    exit 1
fi

echo "=== Round ${ROUND} Status ==="
echo "Response directory: ${LATEST}"
echo ""

# Count responses
MD_COUNT=$(ls ${LATEST}/*.md 2>/dev/null | grep -v fiedler.log | wc -l)
echo "Responses received: ${MD_COUNT}/10"
echo ""

# Show sizes
echo "Response sizes (lines):"
wc -l ${LATEST}/*.md 2>/dev/null | grep -v fiedler.log | grep -v total | sort -n | while read lines file; do
    model=$(basename "$file" .md)
    printf "  %-50s %5d lines\n" "$model" "$lines"
done

# Show total size
TOTAL_SIZE=$(du -sh ${LATEST} | cut -f1)
echo ""
echo "Total size: ${TOTAL_SIZE}"

# Check if complete (has summary.json)
if [ -f "${LATEST}/summary.json" ]; then
    echo ""
    echo "✓ Round ${ROUND} appears complete (summary.json present)"
    echo ""
    echo "Ready to build Round $((ROUND + 1)) package with:"
    echo "  ./iterate_rounds.sh $((ROUND + 1))"
else
    echo ""
    echo "⏳ Round ${ROUND} still processing..."
fi

