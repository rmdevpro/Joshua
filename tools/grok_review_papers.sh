#!/bin/bash
# Grok Paper Review Script
# Usage: ./grok_review_papers.sh <paper_file> <review_prompt>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
XAI_API_KEY="${XAI_API_KEY:-}"

# Activate virtual environment
source "$SCRIPT_DIR/grok_venv/bin/activate"

# Run Grok client
XAI_API_KEY="$XAI_API_KEY" python "$SCRIPT_DIR/grok_client.py" "$@"
