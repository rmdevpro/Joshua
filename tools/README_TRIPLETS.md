# Triplet Verification Tool

Send document packages to all three AI models (Fiedler's default models simultaneously.

## Usage

### Mode 1: Pre-compiled Package

```bash
python /mnt/projects/ICCM/tools/send_to_triplets.py <package_file> <output_dir> [--prompt "custom prompt"]
```

### Mode 2: Auto-compile from File List (Recommended)

```bash
python /mnt/projects/ICCM/tools/send_to_triplets.py \
    --files file1.md file2.md file3.md \
    --output-dir <output_dir> \
    [--header header.md] \
    [--prompt "custom prompt"]
```

## Examples

### Pre-compiled Package

```bash
python /mnt/projects/ICCM/tools/send_to_triplets.py \
    /tmp/iccm_complete_v4_verification_package.md \
    /mnt/projects/ICCM/docs/papers/v4_verifications
```

### Auto-compile from Files

```bash
python /mnt/projects/ICCM/tools/send_to_triplets.py \
    --files \
        /mnt/projects/ICCM/docs/papers/01_*.md \
        /mnt/projects/ICCM/docs/papers/02_*.md \
        /mnt/projects/ICCM/docs/papers/03_*.md \
    --header /mnt/projects/ICCM/docs/papers/verification_request.md \
    --output-dir /mnt/projects/ICCM/docs/papers/v4_verifications \
    --prompt "Please verify architectural consistency"
```

## Tail the Log

In another terminal, watch progress in real-time:

```bash
tail -f /mnt/projects/ICCM/docs/papers/v4_verifications/verification_progress.log
```

## Features

- ✅ **Auto-compile from file list** - No need to manually create package files
- ✅ **Parallel execution** - Sends to all three models simultaneously
- ✅ **Real-time progress logging** - Watch compilation and verification progress
- ✅ **Flexible input** - Use pre-compiled package OR file list with optional header
- ✅ **Consistent output** - Standardized file naming and organization
- ✅ **Error handling** - Validates files, handles failures gracefully
- ✅ **Summary report** - Comprehensive results when complete
- ✅ **Automatic cleanup** - Temporary files removed after verification

## Output Files

The tool creates:
- `Gemini_2.5_Pro_Verification.md` - Gemini's verification response
- `GPT-5_Verification.md` - GPT-5's verification response  
- `Grok_4_Verification.md` - Grok 4's verification response
- `verification_progress.log` - Real-time progress log

## Exit Codes

- `0` - All verifications successful
- `1` - One or more verifications failed
