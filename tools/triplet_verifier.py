#!/mnt/projects/gemini-tool/venv/bin/python
"""
Triplet AI Verifier
Sends document packages to Gemini 2.5 Pro, GPT-5, and Grok 4 in parallel
"""

import argparse
import os
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path


class ProgressLogger:
    """Thread-safe logger for real-time progress updates"""

    def __init__(self, log_file):
        self.log_file = Path(log_file)
        self.lock = threading.Lock()

        # Initialize log file
        with open(self.log_file, 'w') as f:
            f.write(f"=== Triplet Verification Started at {datetime.now()} ===\n\n")

    def log(self, message, model=None):
        """Thread-safe logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}]" + (f" [{model}]" if model else "")
        full_message = f"{prefix} {message}\n"

        with self.lock:
            with open(self.log_file, 'a') as f:
                f.write(full_message)
            print(full_message, end='', flush=True)


def compile_package(files, logger):
    """Compile list of files into a single package string"""
    logger.log(f"Compiling package from {len(files)} files...")

    contents = []
    for i, file_path in enumerate(files):
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.log(f"Adding file {i+1}/{len(files)}: {file_path.name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            contents.append(f.read())

    package = "\n\n".join(contents)
    size = len(package.encode('utf-8'))
    logger.log(f"✅ Package compiled: {size:,} bytes")

    return package


def verify_gemini(package, prompt, output_file, logger):
    """Send to Gemini 2.5 Pro via gemini_client.py"""
    model_name = "Gemini 2.5 Pro"
    start_time = time.time()
    logger.log("Starting verification...", model_name)

    try:
        # Combine prompt and package
        full_input = f"{prompt}\n\n{package}"

        # Call gemini_client.py with stdin
        cmd = [
            "/mnt/projects/gemini-tool/venv/bin/python",
            "/mnt/projects/gemini-tool/gemini_client.py",
            "--model", "gemini-2.5-pro",
            "--timeout", "600",
            "--stdin"
        ]

        env = os.environ.copy()
        if "GEMINI_API_KEY" not in env:
            env["GEMINI_API_KEY"] = "AIzaSyAJ9ZCiRRw_aMBjEnv5GvPc7J2eeICzy4U"

        result = subprocess.run(
            cmd,
            input=full_input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd="/mnt/projects/gemini-tool",
            timeout=650
        )

        if result.returncode != 0:
            raise RuntimeError(f"gemini_client.py failed: {result.stderr}")

        # Save output
        with open(output_file, 'w') as f:
            f.write(result.stdout)

        duration = time.time() - start_time
        size = Path(output_file).stat().st_size
        logger.log(f"✅ Completed in {duration:.1f}s - Output: {size:,} bytes", model_name)
        return True

    except Exception as e:
        duration = time.time() - start_time
        logger.log(f"❌ Error after {duration:.1f}s: {e}", model_name)
        return False


def verify_gpt5(package, prompt, output_file, logger):
    """Send to GPT-5 via OpenAI Chat Completions API"""
    model_name = "GPT-5"
    start_time = time.time()
    logger.log("Starting verification...", model_name)

    try:
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY", "")

        client = OpenAI(api_key=api_key)

        # Combine prompt and package
        full_input = f"{prompt}\n\n{package}"

        # Call GPT-5 API
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": full_input}],
            max_completion_tokens=32768
        )

        # Save output
        content = response.choices[0].message.content
        with open(output_file, 'w') as f:
            f.write(content)

        duration = time.time() - start_time
        size = Path(output_file).stat().st_size
        logger.log(f"✅ Completed in {duration:.1f}s - Output: {size:,} bytes", model_name)
        return True

    except Exception as e:
        duration = time.time() - start_time
        logger.log(f"❌ Error after {duration:.1f}s: {e}", model_name)
        return False


def verify_grok(package, prompt, output_file, logger):
    """Send to Grok 4 via grok_client.py"""
    model_name = "Grok 4"
    start_time = time.time()
    logger.log("Starting verification...", model_name)

    temp_file = None
    try:
        # Write package to temp file (Grok client uses --file)
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        temp_file.write(package)
        temp_file.close()

        # Call grok_client.py
        cmd = [
            "/mnt/projects/gemini-tool/venv/bin/python",
            "/mnt/projects/ICCM/tools/grok_client.py",
            "--file", temp_file.name,
            "--model", "grok-4-0709",
            "--temperature", "0.2",
            "--max-tokens", "16384",
            prompt  # Prompt as positional argument
        ]

        env = os.environ.copy()
        if "XAI_API_KEY" not in env:
            env["XAI_API_KEY"] = ""

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            timeout=650
        )

        if result.returncode != 0:
            raise RuntimeError(f"grok_client.py failed: {result.stderr}")

        # Save output
        with open(output_file, 'w') as f:
            f.write(result.stdout)

        duration = time.time() - start_time
        size = Path(output_file).stat().st_size
        logger.log(f"✅ Completed in {duration:.1f}s - Output: {size:,} bytes", model_name)
        return True

    except Exception as e:
        duration = time.time() - start_time
        logger.log(f"❌ Error after {duration:.1f}s: {e}", model_name)
        return False

    finally:
        # Cleanup temp file
        if temp_file and Path(temp_file.name).exists():
            Path(temp_file.name).unlink()


def main():
    parser = argparse.ArgumentParser(
        description="Send documents to Gemini 2.5 Pro, GPT-5, and Grok 4 for verification"
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="List of files to verify"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to save verification outputs"
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Verification prompt"
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logger
    log_file = output_dir / "verification_progress.log"
    logger = ProgressLogger(log_file)

    logger.log(f"Files: {len(args.files)}")
    logger.log(f"Output: {output_dir}")
    logger.log(f"Prompt: {args.prompt[:80]}...")
    logger.log("")

    # Compile package
    try:
        package = compile_package(args.files, logger)
    except Exception as e:
        logger.log(f"❌ Failed to compile package: {e}")
        sys.exit(1)

    logger.log("")
    logger.log("🚀 Launching all three verifications in parallel...")
    logger.log("")

    # Prepare verification tasks
    tasks = {
        "Gemini 2.5 Pro": (verify_gemini, output_dir / "Gemini_2.5_Pro_Verification.md"),
        "GPT-5": (verify_gpt5, output_dir / "GPT-5_Verification.md"),
        "Grok 4": (verify_grok, output_dir / "Grok_4_Verification.md"),
    }

    # Execute in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(func, package, args.prompt, output_file, logger): name
            for name, (func, output_file) in tasks.items()
        }

        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                logger.log(f"❌ Unexpected error: {e}", name)
                results[name] = False

    # Summary
    logger.log("")
    logger.log("=" * 60)
    logger.log("VERIFICATION SUMMARY")
    logger.log("=" * 60)

    success_count = sum(results.values())

    for name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.log(f"{status:12} {name:15}")
        if success:
            output_file = tasks[name][1]
            logger.log(f"             Output: {output_file}")

    logger.log("")
    logger.log(f"Results: {success_count}/3 successful")
    logger.log("=" * 60)

    if success_count == 3:
        logger.log("✅ All verifications completed successfully!")
        sys.exit(0)
    else:
        logger.log("⚠️  Some verifications failed - check log for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
