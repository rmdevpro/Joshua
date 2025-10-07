# LLM Review Process Documentation

## Overview
This document describes the process for sending documents to AI models for review using the Triplet Verifier tool.

---

## Current Process (v4+)

### Triplet Verifier Tool

**Location:** `/mnt/projects/ICCM/tools/triplet_verifier.py`

**Purpose:** Send any documents (papers, code, specifications) to all three AI models in parallel:
- Gemini 2.5 Pro
- GPT-5
- Grok 4

### Quick Start

```bash
cd /mnt/projects/ICCM/tools

./triplet_verifier.py \
    --files file1.md file2.md file3.md \
    --output-dir /output/directory \
    --prompt "Your review prompt"
```

### Example: Verify All 14 ICCM Papers

```bash
cd /mnt/projects/ICCM/tools

./triplet_verifier.py \
    --files \
        /mnt/projects/ICCM/docs/papers/CET_Architecture_Clarification_Summary.md \
        /mnt/projects/ICCM/docs/papers/01_ICCM_Primary_Paper_v4.1.md \
        /mnt/projects/ICCM/docs/papers/02_Progressive_Training_Methodology_v4.1.md \
        /mnt/projects/ICCM/docs/papers/03_CET_Architecture_Specialization_v4.md \
        /mnt/projects/ICCM/docs/papers/04A_Code_Execution_Feedback_v3.md \
        /mnt/projects/ICCM/docs/papers/04B_Production_Learning_Pipeline_v4.md \
        /mnt/projects/ICCM/docs/papers/05_CET_D_Requirements_Engineering_Implementation_v4.1.md \
        /mnt/projects/ICCM/docs/papers/06_Requirements_Validation_Through_Reconstruction_Testing_v3.md \
        /mnt/projects/ICCM/docs/papers/07A_Self_Bootstrapping_Development_v4.md \
        /mnt/projects/ICCM/docs/papers/07B_Continuous_Self_Improvement_v4.md \
        /mnt/projects/ICCM/docs/papers/08_Test_Lab_Infrastructure_v3.md \
        /mnt/projects/ICCM/docs/papers/09_Containerized_Code_Execution_for_Small_Labs_v3.md \
        /mnt/projects/ICCM/docs/papers/10_LLM_Orchestra_v4.md \
        /mnt/projects/ICCM/docs/papers/11_Testing_Infrastructure_v4.md \
        /mnt/projects/ICCM/docs/papers/12_Conversation_Storage_Retrieval_v3.md \
        /mnt/projects/ICCM/docs/papers/13_Bidirectional_Processing_v4.md \
        /mnt/projects/ICCM/docs/papers/14_Edge_CET_P_v4.md \
    --output-dir /mnt/projects/ICCM/docs/papers/final_verifications \
    --prompt "Please verify all 14 ICCM papers for architectural consistency. Confirm: 1) CETs generate ONLY context 2) LLMs generate ALL outputs 3) Method/class names reflect context engineering role. Report any remaining issues."
```

---

## How It Works

### 1. Compilation
- Reads all specified files in order
- Concatenates into single package
- Logs each file being added

### 2. Parallel Execution
- Sends complete package to all three models simultaneously
- Each model runs in separate thread
- Real-time progress logging

### 3. Output
- Saves each model's response to separate file:
  - `Gemini_2.5_Pro_Verification.md`
  - `GPT-5_Verification.md`
  - `Grok_4_Verification.md`
- Logs all activity to `verification_progress.log`

### 4. Summary
- Reports success/failure for each model
- Exit code 0 = all successful
- Exit code 1 = one or more failed

---

## Model Specifications

### Gemini 2.5 Pro
- **Context Window:** 2,000,000 tokens
- **Implementation:** Via `/mnt/projects/gemini-tool/gemini_client.py`
- **Timeout:** 600 seconds
- **Input Method:** stdin

### GPT-5
- **Context Window:** Unknown (handles 200K+ tokens)
- **Implementation:** Via OpenAI Python SDK
- **API Method:** `chat.completions.create()`
- **Parameter:** `max_completion_tokens=32768`

### Grok 4
- **Context Window:** 256,000 tokens
- **Implementation:** Via `/mnt/projects/ICCM/tools/grok_client.py`
- **Model:** `grok-4-0709`
- **Parameters:** `temperature=0.2`, `max_tokens=16384`

---

## Performance Benchmarks

### Recent Test (October 2025)
**Package:** 737KB, 17 files (all 14 ICCM papers + architecture clarification)

**Results:**
- **Gemini 2.5 Pro:** 61.8s - 14,589 bytes output
- **Grok 4:** 70.3s - 11,126 bytes output
- **GPT-5:** 155.1s - 7,318 bytes output

**Total wall time:** ~155s (all three run in parallel)

---

## Monitoring Progress

In a separate terminal:
```bash
tail -f /path/to/output/verification_progress.log
```

Example log output:
```
[23:52:03] Compiling package from 17 files...
[23:52:03] Adding file 1/17: CET_Architecture_Clarification_Summary.md
[23:52:03] Adding file 2/17: 01_ICCM_Primary_Paper_v4.1.md
...
[23:52:03] ✅ Package compiled: 737,083 bytes
[23:52:03] 🚀 Launching all three verifications in parallel...
[23:52:03] [Gemini 2.5 Pro] Starting verification...
[23:52:03] [GPT-5] Starting verification...
[23:52:03] [Grok 4] Starting verification...
[23:53:04] [Gemini 2.5 Pro] ✅ Completed in 61.8s - Output: 14,589 bytes
[23:53:13] [Grok 4] ✅ Completed in 70.3s - Output: 11,126 bytes
[23:54:38] [GPT-5] ✅ Completed in 155.1s - Output: 7,318 bytes
```

---

## Use Cases

### Code Review
```bash
./triplet_verifier.py \
    --files src/main.py src/utils.py \
    --output-dir /tmp/code_review \
    --prompt "Review this code for bugs, security issues, and improvements"
```

### Documentation Review
```bash
./triplet_verifier.py \
    --files README.md API.md CONTRIBUTING.md \
    --output-dir /tmp/doc_review \
    --prompt "Check documentation for completeness and clarity"
```

### Architecture Verification
```bash
./triplet_verifier.py \
    --files architecture.md requirements.md design.md \
    --output-dir /tmp/arch_review \
    --prompt "Verify architectural consistency and identify gaps"
```

---

## Technical Details

### API Keys
All API keys are embedded in the script:
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `XAI_API_KEY`

No environment setup required.

### Python Environment
Uses: `/mnt/projects/gemini-tool/venv/bin/python`

Shebang in script ensures correct interpreter.

### Error Handling
- Each model runs independently
- Failure of one model doesn't stop others
- All errors logged to progress log
- Non-zero exit code if any model fails

---

## Comparison to Legacy Process

### Old Process (v3)
- Manual bash scripts for package creation
- Sequential API calls to each model
- Separate commands for each model
- Manual timeout management
- Complex error handling

### New Process (v4+)
- ✅ Single tool for all operations
- ✅ Automatic parallel execution
- ✅ Consistent interface for all models
- ✅ Built-in timeout handling
- ✅ Real-time progress logging
- ✅ Clean error reporting

---

## References

- **Tool Documentation:** `/mnt/projects/ICCM/tools/README_TRIPLET_VERIFIER.md`
- **Tool Source:** `/mnt/projects/ICCM/tools/triplet_verifier.py`
- **Claude Instructions:** `/home/aristotle9/CLAUDE.md` (see "Triplet AI Review Process")

---

## Update Log

**2025-10-01:** Triplet verifier tool created and tested with all 14 ICCM papers
**2025-10-01:** Documentation updated to reflect new unified process
**2025-10-01:** Legacy manual process deprecated in favor of triplet_verifier.py
