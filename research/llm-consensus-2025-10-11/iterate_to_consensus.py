#!/usr/bin/env python3
"""
Autonomous LLM Convergence System
Iterates rounds until consensus or natural attrition
"""
import os
import sys
import time
import json
import subprocess
from pathlib import Path

REVIEW_DIR = Path("/mnt/irina_storage/files/temp/paradigm_review")
CURRENT_ROUND = 3
MAX_ROUNDS = 15
CHECK_INTERVAL = 30  # seconds

def wait_for_round_completion(round_num, timeout=1200):
    """Wait for a round to complete (summary.json exists)"""
    round_dir = REVIEW_DIR / f"round{round_num}_responses"
    start = time.time()
    
    while time.time() - start < timeout:
        # Find latest response directory
        subdirs = sorted([d for d in round_dir.glob("2025*") if d.is_dir()], reverse=True)
        if subdirs:
            latest = subdirs[0]
            if (latest / "summary.json").exists():
                return latest
        time.sleep(CHECK_INTERVAL)
    
    return None

def count_responses(round_dir):
    """Count .md files (excluding fiedler.log)"""
    if not round_dir:
        return 0
    md_files = [f for f in round_dir.glob("*.md") if f.name != "fiedler.log"]
    return len(md_files)

def check_consensus(round_dir):
    """Check if models are signaling consensus"""
    if not round_dir:
        return False, 0
    
    md_files = [f for f in round_dir.glob("*.md") if f.name != "fiedler.log"]
    total = len(md_files)
    consensus_count = 0
    
    for md_file in md_files:
        content = md_file.read_text().lower()
        if "consensus reached" in content or "consensus achieved" in content:
            consensus_count += 1
    
    # Consensus if 2/3 or more models signal it
    return consensus_count >= (total * 2 // 3), consensus_count

def build_next_package(round_num):
    """Build package for next round"""
    script = REVIEW_DIR / "iterate_rounds.sh"
    result = subprocess.run([str(script), str(round_num)], 
                          capture_output=True, text=True)
    return result.returncode == 0

def send_to_fiedler(round_num, models):
    """Signal that round is ready - actual send happens via Claude Code"""
    package = REVIEW_DIR / f"round{round_num}_package.md"
    output_dir = REVIEW_DIR / f"round{round_num}_responses"
    
    # Write signal file for Claude Code to pick up
    signal = {
        "round": round_num,
        "package": str(package),
        "output_dir": str(output_dir),
        "models": models,
        "timestamp": time.time()
    }
    
    signal_file = REVIEW_DIR / f"round{round_num}_ready.json"
    signal_file.write_text(json.dumps(signal, indent=2))
    return signal_file

print("=== AUTONOMOUS LLM CONVERGENCE ===")
print(f"Starting from Round {CURRENT_ROUND}")
print(f"Will iterate to Round {MAX_ROUNDS} or until consensus\n")

# Main convergence loop
round_num = CURRENT_ROUND

while round_num <= MAX_ROUNDS:
    print(f"\n{'='*60}")
    print(f"ROUND {round_num}")
    print(f"{'='*60}")
    
    # Wait for current round to complete
    print(f"Waiting for Round {round_num} completion...")
    round_dir = wait_for_round_completion(round_num)
    
    if not round_dir:
        print(f"✗ Round {round_num} timeout - stopping")
        break
    
    # Check results
    model_count = count_responses(round_dir)
    has_consensus, consensus_count = check_consensus(round_dir)
    
    print(f"✓ Round {round_num} complete:")
    print(f"  - {model_count} models responded")
    print(f"  - {consensus_count} models signal consensus")
    
    # Check termination conditions
    if has_consensus:
        print(f"\n{'='*60}")
        print("🎯 CONSENSUS REACHED")
        print(f"{'='*60}")
        print(f"{consensus_count}/{model_count} models agree")
        break
    
    if model_count <= 1:
        print(f"\n{'='*60}")
        print("📉 NATURAL ATTRITION COMPLETE")
        print(f"{'='*60}")
        print(f"Only {model_count} model(s) remaining")
        break
    
    # Continue to next round
    next_round = round_num + 1
    print(f"\n→ Preparing Round {next_round}...")
    
    if not build_next_package(next_round):
        print(f"✗ Failed to build Round {next_round} package - stopping")
        break
    
    # Create signal for Claude Code
    signal_file = send_to_fiedler(next_round, [
        "gemini-2.5-pro", "gpt-5", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo",
        "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "deepseek-ai/DeepSeek-R1", "grok-4-0709"
    ])
    
    print(f"✓ Round {next_round} package ready:")
    print(f"  Signal file: {signal_file}")
    print(f"  Waiting for Claude Code to send to Fiedler...")
    
    round_num = next_round

print(f"\n{'='*60}")
print("CONVERGENCE PROCESS COMPLETE")
print(f"{'='*60}")
print(f"Final round: {round_num}")

