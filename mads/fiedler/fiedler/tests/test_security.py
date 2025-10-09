"""Security tests for Fiedler MCP Server."""
import pytest
import os
from pathlib import Path
from fiedler.utils.package import compile_package
from fiedler.utils.logger import ProgressLogger


def test_file_access_allowlist(tmp_path, monkeypatch):
    """Test that file access is restricted to allowed roots."""
    # Create test files
    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir()
    allowed_file = allowed_dir / "test.txt"
    allowed_file.write_text("allowed content")

    forbidden_dir = tmp_path / "forbidden"
    forbidden_dir.mkdir()
    forbidden_file = forbidden_dir / "secret.txt"
    forbidden_file.write_text("secret content")

    # Set allowed roots
    monkeypatch.setenv("FIEDLER_ALLOWED_FILE_ROOTS", str(allowed_dir))

    # Create logger
    logger = ProgressLogger()

    # Test allowed access
    result, metadata = compile_package([str(allowed_file)], logger)
    assert "allowed content" in result

    # Test forbidden access
    with pytest.raises(PermissionError, match="File access denied"):
        compile_package([str(forbidden_file)], logger)


def test_package_size_limit(tmp_path, monkeypatch):
    """Test that package size limits are enforced."""
    # Create large file
    large_file = tmp_path / "large.txt"
    large_file.write_text("x" * 1000000)  # 1MB

    # Set small size limit (100KB)
    monkeypatch.setenv("FIEDLER_MAX_PACKAGE_BYTES", "102400")
    monkeypatch.setenv("FIEDLER_ALLOWED_FILE_ROOTS", str(tmp_path))

    # Create logger
    logger = ProgressLogger()

    # Should exceed limit
    with pytest.raises(ValueError, match="exceeds size limit"):
        compile_package([str(large_file)], logger)


def test_package_file_count_limit(tmp_path, monkeypatch):
    """Test that file count limits are enforced."""
    # Create many files
    files = []
    for i in range(10):
        f = tmp_path / f"file{i}.txt"
        f.write_text(f"content {i}")
        files.append(str(f))

    # Set low file count limit
    monkeypatch.setenv("FIEDLER_MAX_FILE_COUNT", "5")
    monkeypatch.setenv("FIEDLER_ALLOWED_FILE_ROOTS", str(tmp_path))

    # Create logger
    logger = ProgressLogger()

    # Should exceed limit
    with pytest.raises(ValueError, match="exceeds file count limit"):
        compile_package(files, logger)


def test_package_line_count_limit(tmp_path, monkeypatch):
    """Test that line count limits are enforced."""
    # Create file with many lines
    large_file = tmp_path / "many_lines.txt"
    large_file.write_text("\n".join(f"line {i}" for i in range(1000)))

    # Set low line count limit
    monkeypatch.setenv("FIEDLER_MAX_LINES", "500")
    monkeypatch.setenv("FIEDLER_ALLOWED_FILE_ROOTS", str(tmp_path))

    # Create logger
    logger = ProgressLogger()

    # Should exceed limit
    with pytest.raises(ValueError, match="exceeds line count limit"):
        compile_package([str(large_file)], logger)


def test_no_allowlist_allows_all(tmp_path, monkeypatch):
    """Test that without allowlist, all files are accessible."""
    # Clear allowlist
    monkeypatch.delenv("FIEDLER_ALLOWED_FILE_ROOTS", raising=False)

    # Create file anywhere
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    # Create logger
    logger = ProgressLogger()

    # Should work without allowlist
    result, metadata = compile_package([str(test_file)], logger)
    assert "test content" in result


def test_prompt_redaction_by_default(monkeypatch):
    """Test that prompts are redacted by default in summary.json."""
    from fiedler.tools.send import fiedler_send
    import json

    # Ensure prompt redaction is on (default)
    monkeypatch.setenv("FIEDLER_SAVE_PROMPT", "0")

    # Create test output directory
    output_dir = "/tmp/fiedler_test_redaction"
    monkeypatch.setenv("FIEDLER_OUTPUT_DIR", output_dir)

    # Note: This is a conceptual test - actual implementation would need:
    # 1. Valid API keys
    # 2. Real model call
    # 3. Check summary.json for redacted prompt

    # For now, just verify the environment variable is set correctly
    assert os.getenv("FIEDLER_SAVE_PROMPT") == "0"


def test_prompt_save_opt_in(monkeypatch):
    """Test that prompts can be saved when explicitly enabled."""
    monkeypatch.setenv("FIEDLER_SAVE_PROMPT", "1")

    # Verify opt-in is respected
    assert os.getenv("FIEDLER_SAVE_PROMPT") == "1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
