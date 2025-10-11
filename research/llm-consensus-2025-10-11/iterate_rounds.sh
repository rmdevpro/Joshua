#!/bin/bash
# Iterative LLM consensus builder
# Each round packages all previous responses without loading into context

REVIEW_DIR="/mnt/irina_storage/files/temp/paradigm_review"
ROUND=$1

if [ -z "$ROUND" ]; then
    echo "Usage: $0 <round_number>"
    exit 1
fi

PREV_ROUND=$((ROUND - 1))
PREV_RESPONSES="${REVIEW_DIR}/round${PREV_ROUND}_responses"
PACKAGE_FILE="${REVIEW_DIR}/round${ROUND}_package.md"

# Find the most recent round response directory
PREV_DIR=$(ls -td ${PREV_RESPONSES}/2025* 2>/dev/null | head -1)

if [ -z "$PREV_DIR" ]; then
    echo "ERROR: Cannot find previous round responses in ${PREV_RESPONSES}"
    exit 1
fi

echo "Building Round ${ROUND} package..."
echo "Previous responses from: ${PREV_DIR}"

# Start package with header
cat > "$PACKAGE_FILE" << EOF
# Round ${ROUND} Analysis Package
# Paradigm Shift in LLM-Native Architecture - Iterative Consensus Building

## Round ${ROUND} Instructions

This is Round ${ROUND} of iterative consensus building. You have now seen:
- Original paradigm shift materials
- Round 1-${PREV_ROUND} analyses from all participating LLMs

Your task:
1. Identify where consensus is forming
2. Identify remaining disagreements
3. Propose resolution of disagreements with evidence
4. Move toward unified recommendations
5. Signal if you believe consensus has been reached

If you are reaching context limits, provide your final position before dropping out.

---

# ORIGINAL MATERIALS (for reference)

EOF

# Append original materials
cat "${REVIEW_DIR}/complete_package.md" >> "$PACKAGE_FILE"

echo "" >> "$PACKAGE_FILE"
echo "---" >> "$PACKAGE_FILE"
echo "" >> "$PACKAGE_FILE"
echo "# ROUND ${PREV_ROUND} ANALYSES" >> "$PACKAGE_FILE"
echo "" >> "$PACKAGE_FILE"

# Append all previous round responses
for file in ${PREV_DIR}/*.md; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        model_name="${filename%.md}"
        echo "## ${model_name} (Round ${PREV_ROUND})" >> "$PACKAGE_FILE"
        echo "" >> "$PACKAGE_FILE"
        cat "$file" >> "$PACKAGE_FILE"
        echo "" >> "$PACKAGE_FILE"
        echo "---" >> "$PACKAGE_FILE"
        echo "" >> "$PACKAGE_FILE"
    fi
done

# Show package stats
SIZE=$(du -h "$PACKAGE_FILE" | cut -f1)
LINES=$(wc -l < "$PACKAGE_FILE")

echo ""
echo "Round ${ROUND} package created:"
echo "  File: ${PACKAGE_FILE}"
echo "  Size: ${SIZE}"
echo "  Lines: ${LINES}"
echo ""
echo "Ready to send to Fiedler for Round ${ROUND} analysis"

