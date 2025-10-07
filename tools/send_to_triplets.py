#!/usr/bin/env python3
"""
Send document packages to Gemini 2.5 Pro, GPT-5, and Grok 4 simultaneously.
Logs progress in real-time and saves outputs to organized directory.

Usage:
    # Pre-compiled package:
    python send_to_triplets.py <package_file> <output_dir> [--prompt "custom prompt"]

    # Compile from file list:
    python send_to_triplets.py --files file1.md file2.md file3.md --output-dir <dir> [--header header.md] [--prompt "custom"]

Examples:
    python send_to_triplets.py /tmp/package.md /mnt/projects/ICCM/docs/papers/v4_verifications

    python send_to_triplets.py --files paper1.md paper2.md --output-dir /output --header request.md
"""

import argparse
import subprocess
import threading
import time
import sys
import tempfile
from datetime import datetime
from pathlib import Path


class ProgressLogger:
    """Thread-safe logger for real-time progress updates"""

    def __init__(self, log_file):
        self.log_file = Path(log_file)
        self.lock = threading.Lock()

        # Initialize log file
        with open(self.log_file, 'w') as f:
            f.write(f"=== ICCM Triplet Verification Started at {datetime.now()} ===\n\n")

    def log(self, message, model=None):
        """Thread-safe logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}]" + (f" [{model}]" if model else "")
        full_message = f"{prefix} {message}\n"

        with self.lock:
            # Write to log file
            with open(self.log_file, 'a') as f:
                f.write(full_message)

            # Print to console
            print(full_message, end='', flush=True)


class ModelVerifier:
    """Handles verification for a single AI model"""

    def __init__(self, name, logger):
        self.name = name
        self.logger = logger
        self.start_time = None
        self.end_time = None
        self.success = False
        self.error = None
        self.output_file = None

    def verify(self, package_file, output_dir, prompt):
        """Run verification for this model"""
        self.start_time = time.time()
        self.logger.log(f"Starting verification...", self.name)

        try:
            # Configure model-specific settings
            if self.name == "Gemini_2.5_Pro":
                self.output_file = output_dir / f"{self.name}_Verification.md"
                self._verify_gemini(package_file, self.output_file, prompt)

            elif self.name == "GPT-5":
                self.output_file = output_dir / f"{self.name}_Verification.md"
                self._verify_gpt5(package_file, self.output_file, prompt)

            elif self.name == "Grok_4":
                self.output_file = output_dir / f"{self.name}_Verification.md"
                self._verify_grok(package_file, self.output_file, prompt)

            else:
                raise ValueError(f"Unknown model: {self.name}")

            self.end_time = time.time()
            duration = self.end_time - self.start_time

            # Check if output was generated
            if self.output_file.exists() and self.output_file.stat().st_size > 0:
                size = self.output_file.stat().st_size
                self.success = True
                self.logger.log(
                    f"✅ Completed in {duration:.1f}s - Output: {size:,} bytes",
                    self.name
                )
            else:
                self.success = False
                self.error = "No output generated"
                self.logger.log(f"❌ Failed - {self.error}", self.name)

        except Exception as e:
            self.end_time = time.time()
            self.success = False
            self.error = str(e)
            self.logger.log(f"❌ Error: {self.error}", self.name)

    def _verify_gemini(self, package_file, output_file, prompt):
        """Send to Gemini 2.5 Pro"""
        cmd = [
            "/mnt/projects/gemini-tool/venv/bin/python", "gemini_client.py",
            "--model", "gemini-2.5-pro",
            "--stdin"
        ]

        env = {
            "GEMINI_API_KEY": "AIzaSyAJ9ZCiRRw_aMBjEnv5GvPc7J2eeICzy4U",
            "PATH": subprocess.os.environ.get("PATH", "")
        }

        self.logger.log(f"Calling gemini_client.py...", self.name)

        # Read package file
        with open(package_file, 'r') as f:
            package_content = f.read()

        # Combine package with prompt
        full_input = f"{prompt}\n\n{package_content}"

        # Run command
        with open(output_file, 'w') as out_f:
            result = subprocess.run(
                cmd,
                input=full_input,
                stdout=out_f,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd="/mnt/projects/gemini-tool"
            )

        if result.returncode != 0:
            raise RuntimeError(f"gemini_client.py failed: {result.stderr}")

    def _verify_gpt5(self, package_file, output_file, prompt):
        """Send to GPT-5"""
        cmd = [
            "/mnt/projects/gemini-tool/venv/bin/python", "openai_assistant_review.py",
            str(package_file),
            "--output", str(output_file)
        ]

        env = {
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
            "OPENAI_MODEL": "o1-preview",
            "PATH": subprocess.os.environ.get("PATH", "")
        }

        self.logger.log(f"Calling openai_assistant_review.py...", self.name)

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd="/mnt/projects/gemini-tool"
        )

        if result.returncode != 0:
            raise RuntimeError(f"openai_assistant_review.py failed: {result.stderr}")

    def _verify_grok(self, package_file, output_file, prompt):
        """Send to Grok 4"""
        cmd = [
            "/mnt/projects/gemini-tool/venv/bin/python", "/mnt/projects/ICCM/tools/grok_client.py",
            "--file", str(package_file),
            "--model", "grok-4-0709",
            "--temperature", "0.2",
            "--max-tokens", "16384",
            prompt
        ]

        env = {
            "XAI_API_KEY": os.environ.get("XAI_API_KEY", ""),
            "PATH": subprocess.os.environ.get("PATH", "")
        }

        self.logger.log(f"Calling grok_client.py...", self.name)

        with open(output_file, 'w') as out_f:
            result = subprocess.run(
                cmd,
                stdout=out_f,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd="/mnt/projects/gemini-tool"
            )

        if result.returncode != 0:
            raise RuntimeError(f"grok_client.py failed: {result.stderr}")


def compile_package(files, header=None, logger=None):
    """Compile list of files into a single package"""
    if logger:
        logger.log(f"Compiling package from {len(files)} files...")

    # Create temporary package file
    package = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
    package_path = Path(package.name)

    try:
        # Write header if provided
        if header:
            if logger:
                logger.log(f"Adding header: {header}")
            with open(header, 'r') as f:
                package.write(f.read())
                package.write("\n\n")

        # Write each file with separator
        for i, file_path in enumerate(files):
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            if logger:
                logger.log(f"Adding file {i+1}/{len(files)}: {file_path.name}")

            # Add separator
            package.write(f"\n\n---\n## {file_path.stem}\n---\n\n")

            # Add file content
            with open(file_path, 'r') as f:
                package.write(f.read())

        package.close()

        if logger:
            size = package_path.stat().st_size
            logger.log(f"✅ Package compiled: {size:,} bytes at {package_path}")

        return package_path

    except Exception as e:
        package.close()
        if package_path.exists():
            package_path.unlink()
        raise e


def main():
    parser = argparse.ArgumentParser(
        description="Send package to Gemini, GPT-5, and Grok for verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use pre-compiled package:
  python send_to_triplets.py /tmp/package.md /output

  # Compile from files:
  python send_to_triplets.py --files a.md b.md c.md --output-dir /output --header request.md
        """
    )

    # Mode 1: Pre-compiled package (positional args)
    parser.add_argument(
        "package_file",
        nargs="?",
        type=Path,
        help="Pre-compiled package file to send (use OR --files)"
    )
    parser.add_argument(
        "output_dir_pos",
        nargs="?",
        type=Path,
        help="Directory to save verification outputs (for package_file mode)"
    )

    # Mode 2: Compile from files (named args)
    parser.add_argument(
        "--files",
        nargs="+",
        type=Path,
        help="List of files to compile into package"
    )
    parser.add_argument(
        "--header",
        type=Path,
        help="Optional header file to prepend to package"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to save verification outputs (for --files mode)"
    )

    # Common args
    parser.add_argument(
        "--prompt",
        default="Please verify these corrected papers for architectural consistency with the CET Architecture Clarification. Report any remaining issues.",
        help="Prompt to send to models"
    )

    args = parser.parse_args()

    # Validate mode selection
    if args.files and args.package_file:
        print("❌ Error: Cannot use both package_file and --files mode")
        sys.exit(1)

    if not args.files and not args.package_file:
        print("❌ Error: Must provide either package_file or --files")
        parser.print_help()
        sys.exit(1)

    # Determine output directory
    if args.files:
        if not args.output_dir:
            print("❌ Error: --output-dir required when using --files mode")
            sys.exit(1)
        output_dir = args.output_dir
    else:
        if not args.output_dir_pos:
            print("❌ Error: output_dir required")
            sys.exit(1)
        output_dir = args.output_dir_pos

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logger
    log_file = output_dir / "verification_progress.log"
    logger = ProgressLogger(log_file)

    # Compile package if using --files mode
    temp_package = None
    if args.files:
        try:
            # Validate all files exist
            for f in args.files:
                if not f.exists():
                    print(f"❌ Error: File not found: {f}")
                    sys.exit(1)

            if args.header and not args.header.exists():
                print(f"❌ Error: Header file not found: {args.header}")
                sys.exit(1)

            # Compile package
            package_file = compile_package(args.files, args.header, logger)
            temp_package = package_file  # Mark for cleanup
        except Exception as e:
            print(f"❌ Error compiling package: {e}")
            sys.exit(1)
    else:
        # Use provided package file
        if not args.package_file.exists():
            print(f"❌ Error: Package file not found: {args.package_file}")
            sys.exit(1)
        package_file = args.package_file

    logger.log(f"Package: {package_file}")
    logger.log(f"Output:  {output_dir}")
    logger.log(f"Log:     {log_file}")
    logger.log(f"Prompt:  {args.prompt[:80]}...")
    logger.log("")

    # Create verifiers
    verifiers = [
        ModelVerifier("Gemini_2.5_Pro", logger),
        ModelVerifier("GPT-5", logger),
        ModelVerifier("Grok_4", logger)
    ]

    # Launch all verifications in parallel
    logger.log("🚀 Launching all three verifications in parallel...")
    logger.log("")

    threads = []
    for verifier in verifiers:
        thread = threading.Thread(
            target=verifier.verify,
            args=(package_file, output_dir, args.prompt)
        )
        thread.start()
        threads.append(thread)

    # Wait for all to complete
    for thread in threads:
        thread.join()

    # Generate summary
    logger.log("")
    logger.log("=" * 60)
    logger.log("VERIFICATION SUMMARY")
    logger.log("=" * 60)

    success_count = sum(1 for v in verifiers if v.success)

    for verifier in verifiers:
        status = "✅ SUCCESS" if verifier.success else "❌ FAILED"
        duration = verifier.end_time - verifier.start_time if verifier.end_time else 0

        logger.log(f"{status:12} {verifier.name:15} ({duration:.1f}s)")

        if verifier.success:
            logger.log(f"             Output: {verifier.output_file}")
        elif verifier.error:
            logger.log(f"             Error: {verifier.error}")

    logger.log("")
    logger.log(f"Results: {success_count}/{len(verifiers)} successful")
    logger.log("=" * 60)

    # Cleanup temporary package if created
    if temp_package and temp_package.exists():
        logger.log(f"Cleaning up temporary package: {temp_package}")
        temp_package.unlink()

    if success_count == len(verifiers):
        logger.log("✅ All verifications completed successfully!")
        sys.exit(0)
    else:
        logger.log("⚠️  Some verifications failed - check log for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
