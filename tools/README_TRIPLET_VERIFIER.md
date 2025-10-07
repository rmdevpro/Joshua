# Triplet AI Verifier

Send document packages to Gemini 2.5 Pro, GPT-5, and Grok 4 in parallel for verification.

**Location:** `/mnt/projects/ICCM/tools/triplet_verifier.py`

## Requirements

- Python environment with `openai` package (uses `/mnt/projects/gemini-tool/venv/bin/python`)
- API keys embedded in script (GEMINI_API_KEY, OPENAI_API_KEY, XAI_API_KEY)

## Usage

```bash
cd /mnt/projects/ICCM/tools

./triplet_verifier.py \
    --files file1.md file2.md file3.md \
    --output-dir /path/to/output \
    --prompt "Your verification prompt"
```

## Example: Verify All 14 ICCM Papers

```bash
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

## Output Files

The tool creates:
- `Gemini_2.5_Pro_Verification.md` - Gemini's response
- `GPT-5_Verification.md` - GPT-5's response
- `Grok_4_Verification.md` - Grok 4's response
- `verification_progress.log` - Real-time progress log

## Monitor Progress

In another terminal:
```bash
tail -f /path/to/output/verification_progress.log
```

## Performance

Recent test with 737KB package (17 files):
- **Gemini 2.5 Pro**: 61.8s - 14,589 bytes
- **Grok 4**: 70.3s - 11,126 bytes
- **GPT-5**: 155.1s - 7,318 bytes

All three models run in parallel, so total wall time ≈ slowest model.

## Exit Codes

- `0` - All three verifications successful
- `1` - One or more verifications failed
