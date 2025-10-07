As the Senior Member, I have reviewed the feedback from the Junior Members. I appreciate the detailed analysis from both. DeepSeek's review was particularly sharp and aligned with the immediate scope of the requirements, identifying two critical, actionable gaps. GPT-4o's review was broader, touching on important system-level concerns, though several were outside the scope of this specific unit test suite.

My updated test suite incorporates the critical feedback and provides clear rationale for rejecting out-of-scope items, referencing requirements v1.3.

### Response to Junior Member Reviews

Here is a summary of the changes made in response to your feedback.

---

#### **Accepted Feedback**

The following critical tests, identified by DeepSeek, have been added to the suite.

1.  **URL Redirect Success Test (DeepSeek - Critical)**
    *   **Rationale:** The original suite correctly tested a redirect to a *blocked* IP, but missed the success path for a valid redirect. This is a critical logic path for URL resolution.
    *   **Action:** Added `test_resolve_url_redirect_success` to `TestUrlResolver` to verify that a 301/302 redirect to a valid, public URL is handled correctly.

2.  **Empty Base64 Content Test (DeepSeek - Critical)**
    *   **Rationale:** The suite tested an empty file but missed the edge case of an empty base64 string. This is a valid input that should be handled gracefully.
    *   **Action:** Added `test_resolve_empty_base64` to `TestBase64Resolver` to ensure an empty string resolves successfully to empty bytes.

---

#### **Rejected Feedback (Out of Scope for this Test Suite)**

The following points were raised but are considered out of scope for this unit test suite, which focuses specifically on the `resolve_attachment` function.

1.  **Provider-Specific Capability/MIME Testing (GPT-4o & DeepSeek)**
    *   **Rationale:** This testing is crucial but belongs to a higher-level integration test suite for the provider dispatch logic. The `resolve_attachment` function is designed to be provider-agnostic; its only job is to resolve content from a source into a standardized stream and metadata. Provider-specific validation occurs *after* resolution, as per requirements v1.3 §2.5.1.
    *   **Decision:** Rejected as out of scope for this module's unit tests.

2.  **Asynchronous Processing Tests (GPT-4o)**
    *   **Rationale:** The async functionality (`fiedler_send_async`, `fiedler_get_status`) is a separate system involving a job queue and background workers, as defined in requirements v1.3 §2.4. It is a distinct component from the synchronous `resolve_attachment` function under test here.
    *   **Decision:** Rejected as out of scope. These features require their own dedicated test suite.

3.  **Attachment "reference" Type (GPT-4o)**
    *   **Rationale:** While the `"reference"` type is listed in requirements v1.3 §2.1.1, its resolution logic (e.g., looking up an asset ID in a database) would precede the invocation of the file/URL/base64 resolvers. It is a different resolution mechanism, not a source handled by the current implementation of `resolve_attachment`.
    *   **Decision:** Rejected as out of scope for this specific function's test suite.

4.  **IPv6 SSRF Coverage Discrepancy (GPT-4o)**
    *   **Rationale:** The reviewer correctly notes that requirements v1.3 §1.0 defers comprehensive IPv6 SSRF protection. However, the existing implementation *does* include basic IPv6 private range blocking. A core principle of unit testing is to test the code as it is written. Therefore, the tests for IPv6 blocking are valid and necessary to ensure the current code works as intended and to prevent future regressions.
    *   **Decision:** Rejected. The tests will remain as they correctly validate the existing, implemented code.

---

### Updated Pytest Test Suite

**Prerequisites:**

Save the Fiedler implementation code to a file named `fiedler_resolver.py`. Then, save the following test suite as `test_fiedler_resolver.py` and run it using `pytest`.

```bash
pip install pytest pytest-mock python-magic requests pydantic
# On some systems, you may need to install libmagic
# For Debian/Ubuntu: sudo apt-get install libmagic1
# For macOS (with Homebrew): brew install libmagic
```

**`test_fiedler_resolver.py`**

```python
import base64
import hashlib
import os
import socket
import stat
from unittest.mock import patch

import pytest
import requests
from pydantic import ValidationError

# Assume the implementation is in 'fiedler_resolver.py'
from fiedler_resolver import (
    Attachment,
    AttachmentResolution,
    MAX_ATTACHMENT_SIZE_BYTES,
    ResolutionStatus,
    resolve_attachment,
    validate_url_ssrf,
)

# --- Test Data and Constants ---

# A simple 1x1 PNG image data for consistent testing
TEST_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
TEST_PNG_BYTES = base64.b64decode(TEST_PNG_B64)
TEST_PNG_SHA256 = hashlib.sha256(TEST_PNG_BYTES).hexdigest()

# Simple text data for non-binary tests
TEST_TXT_CONTENT = "This is a test file."
TEST_TXT_BYTES = TEST_TXT_CONTENT.encode('utf-8')
TEST_TXT_SHA256 = hashlib.sha256(TEST_TXT_BYTES).hexdigest()


# --- Fixtures ---

@pytest.fixture
def temp_file_factory(tmp_path):
    """Factory fixture to create temporary files for testing."""
    created_files = []
    def _create_file(filename, content_bytes):
        file_path = tmp_path / filename
        file_path.write_bytes(content_bytes)
        created_files.append(file_path)
        return file_path
    yield _create_file


class MockResponse:
    """A mock requests.Response object for simulating network calls."""
    def __init__(self, content_bytes, status_code=200, headers=None, url="https://example.com/file", history=None):
        self.content_bytes = content_bytes
        self.status_code = status_code
        self.headers = headers or {}
        self.url = url
        self.history = history or []
        self.reason = 'OK' if status_code == 200 else 'Error'

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code} Error", response=self)

    def iter_content(self, chunk_size):
        for i in range(0, len(self.content_bytes), chunk_size):
            yield self.content_bytes[i:i + chunk_size]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# --- Test Suites ---

class TestFileResolver:
    """Tests for resolving attachments from local file paths (`source="file"`)."""

    def test_resolve_file_success(self, temp_file_factory):
        """Verify successful resolution of a valid local file."""
        file_path = temp_file_factory("test.png", TEST_PNG_BYTES)
        result = resolve_attachment(Attachment(source='file', content=str(file_path)))

        assert result.status == ResolutionStatus.SUCCESS
        assert result.mime_type == "image/png"
        assert result.sha256_hash == TEST_PNG_SHA256
        assert b"".join(result.content_stream()) == TEST_PNG_BYTES

    def test_resolve_empty_file(self, temp_file_factory):
        """Verify handling of a zero-byte file."""
        file_path = temp_file_factory("empty.txt", b"")
        result = resolve_attachment(Attachment(source='file', content=str(file_path)))

        assert result.status == ResolutionStatus.SUCCESS
        assert result.sha256_hash == hashlib.sha256(b"").hexdigest()
        assert b"".join(result.content_stream()) == b""

    def test_error_file_not_found(self):
        """Test error handling for a non-existent file path."""
        result = resolve_attachment(Attachment(source='file', content="/non/existent/path/file.txt"))
        assert result.status == ResolutionStatus.ERROR
        assert "File not found" in result.error_message

    def test_error_path_is_directory(self, tmp_path):
        """Test error handling when the path is a directory, not a file."""
        result = resolve_attachment(Attachment(source='file', content=str(tmp_path)))
        assert result.status == ResolutionStatus.ERROR
        assert "is not a regular file" in result.error_message

    def test_error_file_exceeds_size_limit(self, temp_file_factory):
        """Test that files exceeding the size limit are rejected."""
        large_size = MAX_ATTACHMENT_SIZE_BYTES + 1
        file_path = temp_file_factory("large_file.bin", b'a')
        with patch('os.path.getsize', return_value=large_size):
            result = resolve_attachment(Attachment(source='file', content=str(file_path)))
            assert result.status == ResolutionStatus.ERROR
            assert "exceeds size limit" in result.error_message

    def test_error_no_read_permissions(self, temp_file_factory):
        """SYNTHESIS-ADDED: Test error handling for a file without read permissions."""
        file_path = temp_file_factory("locked.txt", b"secret")
        os.chmod(file_path, stat.S_IWUSR)  # Write-only for owner
        result = resolve_attachment(Attachment(source='file', content=str(file_path)))
        assert result.status == ResolutionStatus.ERROR
        assert "Permission denied" in result.error_message


class TestBase64Resolver:
    """Tests for resolving attachments from base64 strings (`source="base64"`)."""

    def test_resolve_base64_success(self):
        """Verify successful resolution of a valid base64 string."""
        result = resolve_attachment(Attachment(source='base64', content=TEST_PNG_B64))
        assert result.status == ResolutionStatus.SUCCESS
        assert result.mime_type == "image/png"
        assert result.sha256_hash == TEST_PNG_SHA256
        assert b"".join(result.content_stream()) == TEST_PNG_BYTES

    def test_resolve_empty_base64(self):
        """DEEPSEEK-CRITICAL-ACCEPTED: Verify handling of an empty base64 string."""
        result = resolve_attachment(Attachment(source='base64', content=""))
        assert result.status == ResolutionStatus.SUCCESS
        assert result.sha256_hash == hashlib.sha256(b"").hexdigest()
        assert b"".join(result.content_stream()) == b""
        # MIME type for empty content is often ambiguous, accept common results
        assert result.mime_type in ["application/octet-stream", "text/plain", "inode/x-empty"]

    def test_error_invalid_base64_string(self):
        """Test error handling of a malformed base64 string."""
        result = resolve_attachment(Attachment(source='base64', content="this-is-not-base64!"))
        assert result.status == ResolutionStatus.ERROR
        assert "Invalid base64 content" in result.error_message

    def test_error_base64_exceeds_size_limit(self):
        """Test that decoded base64 content exceeding the size limit is rejected."""
        large_content = b'a' * (MAX_ATTACHMENT_SIZE_BYTES + 1)
        large_b64 = base64.b64encode(large_content).decode('ascii')
        result = resolve_attachment(Attachment(source='base64', content=large_b64))
        assert result.status == ResolutionStatus.ERROR
        assert "exceeds size limit" in result.error_message


@patch('fiedler_resolver.validate_url_ssrf', return_value=None) # Disable SSRF for non-security URL tests
class TestUrlResolver:
    """Tests for resolving URL attachments (`source="url"`), with mocked network calls."""

    @patch('requests.Session.get')
    def test_resolve_url_success(self, mock_get, mock_ssrf):
        """Verify successful resolution of a valid URL."""
        mock_get.return_value = MockResponse(TEST_PNG_BYTES, headers={'Content-Type': 'image/png'})
        result = resolve_attachment(Attachment(source='url', content="https://example.com/test.png"))

        assert result.status == ResolutionStatus.SUCCESS
        assert result.mime_type == "image/png"
        assert result.sha256_hash == TEST_PNG_SHA256
        assert b"".join(result.content_stream()) == TEST_PNG_BYTES
        mock_get.assert_called_once()

    @patch('requests.Session.get')
    def test_resolve_url_redirect_success(self, mock_get, mock_ssrf):
        """DEEPSEEK-CRITICAL-ACCEPTED: Verify successful resolution of a URL that redirects."""
        # Simulate a redirect from http to https
        initial_url = "http://example.com/image.png"
        final_url = "https://example.com/image.png"
        
        # requests uses a `history` list on the final response to track redirects
        redirect_response = MockResponse(b'', status_code=301, url=initial_url)
        final_response = MockResponse(TEST_PNG_BYTES, status_code=200, url=final_url, history=[redirect_response])
        mock_get.return_value = final_response

        result = resolve_attachment(Attachment(source='url', content=initial_url))
        
        assert result.status == ResolutionStatus.SUCCESS
        assert result.sha256_hash == TEST_PNG_SHA256
        assert b"".join(result.content_stream()) == TEST_PNG_BYTES
        mock_get.assert_called_once_with(initial_url, stream=True, timeout=10, allow_redirects=True)

    @patch('requests.Session.get')
    @patch('requests.Session.head')
    def test_resolve_url_head_fallback(self, mock_head, mock_get, mock_ssrf):
        """DEEPSEEK-INSPIRED: Verify successful fallback to GET if HEAD request fails."""
        mock_head.side_effect = requests.exceptions.RequestException("HEAD not allowed")
        mock_get.return_value = MockResponse(TEST_TXT_BYTES)
        result = resolve_attachment(Attachment(source='url', content="https://example.com/no-head.txt"))

        assert result.status == ResolutionStatus.SUCCESS
        assert result.sha256_hash == TEST_TXT_SHA256
        mock_head.assert_called_once()
        mock_get.assert_called_once()

    @patch('requests.Session.get')
    @patch('requests.Session.head')
    def test_error_head_request_size_too_large(self, mock_head, mock_get, mock_ssrf):
        """Test rejection based on Content-Length from a HEAD request."""
        large_size = MAX_ATTACHMENT_SIZE_BYTES + 1
        mock_head.return_value = MockResponse(b'', headers={'Content-Length': str(large_size)})
        result = resolve_attachment(Attachment(source='url', content="https://example.com/large.file"))

        assert result.status == ResolutionStatus.ERROR
        assert "exceeds size limit based on Content-Length" in result.error_message
        mock_get.assert_not_called()

    @patch('requests.Session.get')
    @patch('requests.Session.head')
    def test_error_streaming_download_size_too_large(self, mock_head, mock_get, mock_ssrf):
        """Test rejection when size limit is exceeded during streaming (no Content-Length)."""
        mock_head.return_value = MockResponse(b'', headers={}) # No Content-Length
        large_content = b'a' * (MAX_ATTACHMENT_SIZE_BYTES + 1)
        mock_get.return_value = MockResponse(large_content)
        result = resolve_attachment(Attachment(source='url', content="https://example.com/streamed_large.file"))

        assert result.status == ResolutionStatus.ERROR
        assert "exceeds size limit" in result.error_message

    @patch('requests.Session.get')
    def test_error_http_not_found(self, mock_get, mock_ssrf):
        """Test handling of HTTP errors like 404 Not Found."""
        mock_get.return_value = MockResponse(b'', status_code=404)
        result = resolve_attachment(Attachment(source='url', content="https://example.com/notfound.jpg"))
        assert result.status == ResolutionStatus.ERROR
        assert "URL request failed with status 404" in result.error_message


class TestSecurity:
    """A dedicated suite for testing security protections."""

    @pytest.mark.parametrize("blocked_host, resolved_ip", [
        ("localhost", "127.0.0.1"),
        ("internal.service.local", "192.168.1.100"),
        ("private.network", "10.0.0.5"),
        ("metadata.internal", "169.254.169.254"),
        ("loopback_ipv6", "::1"), # Note: Per GPT-4o, reqs defer IPv6, but implementation includes it. Test validates the code.
        ("private_ipv6", "fd00::1"),
    ])
    def test_ssrf_blocked_private_ips(self, monkeypatch, blocked_host, resolved_ip):
        """GEMINI-INSPIRED: Verify that various private and reserved IPs are blocked."""
        def mock_getaddrinfo(host, *args, **kwargs):
            if host == blocked_host:
                return [(socket.AF_INET, 1, 6, '', (resolved_ip, 80))]
            raise socket.gaierror("not found")

        monkeypatch.setattr(socket, 'getaddrinfo', mock_getaddrinfo)
        error = validate_url_ssrf(f"https://{blocked_host}/data")
        assert error is not None
        assert f"IP address {resolved_ip} is in a blocked range" in error

    def test_ssrf_allowed_public_ip(self, monkeypatch):
        """Verify that a public IP address is allowed."""
        def mock_getaddrinfo(host, *args, **kwargs):
            return [(socket.AF_INET, 1, 6, '', ("8.8.8.8", 443))]
        monkeypatch.setattr(socket, 'getaddrinfo', mock_getaddrinfo)
        assert validate_url_ssrf("https://google-dns.com") is None

    @pytest.mark.parametrize("invalid_scheme_url", ["ftp://example.com/file", "file:///etc/passwd"])
    def test_ssrf_invalid_scheme(self, invalid_scheme_url):
        """Verify that only http and https schemes are allowed."""
        error = validate_url_ssrf(invalid_scheme_url)
        assert "Invalid URL scheme" in error

    @patch('requests.Session.get')
    def test_ssrf_redirect_to_blocked_ip(self, mock_get, monkeypatch):
        """GEMINI-INSPIRED: Verify SSRF validation is re-run and fails on a redirect to a blocked IP."""
        def mock_getaddrinfo(host, *args, **kwargs):
            if host == "safe-start.com": return [(socket.AF_INET, 1, 6, '', ("50.1.1.1", 443))]
            if host == "blocked.internal": return [(socket.AF_INET, 1, 6, '', ("192.168.1.50", 80))]
            raise socket.gaierror("not found")
        monkeypatch.setattr('fiedler_resolver._cached_getaddrinfo', mock_getaddrinfo)

        # Mock a redirect response history
        redirect_target_response = MockResponse(b'', url="http://blocked.internal")
        initial_response = MockResponse(b'', url="https://safe-start.com", history=[redirect_target_response])
        mock_get.return_value = initial_response

        result = resolve_attachment(Attachment(source='url', content="https://safe-start.com"))
        assert result.status == ResolutionStatus.ERROR
        assert "SSRF validation failed for redirect/final URL" in result.error_message
        assert "192.168.1.50" in result.error_message

    def test_path_traversal_prevention(self, tmp_path):
        """GPT4o/DEEPSEEK-INSPIRED: Verify path traversal attempts are blocked."""
        # This relies on the implementation's os.path.abspath and startswith check
        base_dir = tmp_path / "safe_base"
        base_dir.mkdir()
        attachment = Attachment(source='file', content=str(base_dir / "../../etc/passwd"))
        # Patching the safe directory for the test
        with patch('fiedler_resolver.SAFE_FILE_DIR', str(base_dir)):
            result = resolve_attachment(attachment)
            assert result.status == ResolutionStatus.ERROR
            assert "is outside the allowed directory" in result.error_message

    def test_symlink_resolves_correctly_within_safe_dir(self, tmp_path):
        """DEEPSEEK-INSPIRED: Verify symlinks are resolved and checked."""
        base_dir = tmp_path / "safe_base"
        base_dir.mkdir()
        target_file = base_dir / "target.txt"
        target_file.write_bytes(TEST_TXT_BYTES)
        link_file = base_dir / "link.txt"
        os.symlink(target_file, link_file)

        with patch('fiedler_resolver.SAFE_FILE_DIR', str(base_dir)):
            result = resolve_attachment(Attachment(source='file', content=str(link_file)))
            assert result.status == ResolutionStatus.SUCCESS
            assert b"".join(result.content_stream()) == TEST_TXT_BYTES

    def test_toctou_prevention_with_checksum(self, temp_file_factory):
        """DEEPSEEK-INSPIRED: Test TOCTOU prevention via checksum validation."""
        file_path = temp_file_factory("file.txt", b"initial content")
        initial_hash = hashlib.sha256(b"initial content").hexdigest()

        # Simulate file being changed after checksum is calculated but before processing
        file_path.write_bytes(b"modified content")

        attachment = Attachment(source='file', content=str(file_path), checksum=initial_hash)
        result = resolve_attachment(attachment)
        assert result.status == ResolutionStatus.ERROR
        assert "Checksum mismatch" in result.error_message


class TestCoreFunctionality:
    """Tests for shared logic like stream caching, hashing, and MIME detection."""

    def test_stream_is_replayable(self, temp_file_factory):
        """Verify that the content_stream can be consumed multiple times."""
        file_path = temp_file_factory("replay.txt", TEST_TXT_BYTES)
        result = resolve_attachment(Attachment(source='file', content=str(file_path)))
        assert result.status == ResolutionStatus.SUCCESS

        content1 = b"".join(result.content_stream())
        content2 = b"".join(result.content_stream())
        assert content1 == content2 == TEST_TXT_BYTES

    def test_sha256_hash_correctness_across_sources(self, temp_file_factory):
        """Verify SHA256 hashes are calculated correctly for all sources."""
        # File source
        file_path = temp_file_factory("hash.png", TEST_PNG_BYTES)
        result = resolve_attachment(Attachment(source='file', content=str(file_path)))
        assert result.sha256_hash == TEST_PNG_SHA256

        # Base64 source
        result = resolve_attachment(Attachment(source='base64', content=TEST_PNG_B64))
        assert result.sha256_hash == TEST_PNG_SHA256

        # URL source
        with patch('fiedler_resolver.validate_url_ssrf', return_value=None), \
             patch('requests.Session.get', return_value=MockResponse(TEST_PNG_BYTES)):
            result = resolve_attachment(Attachment(source='url', content="https://example.com/hash.png"))
            assert result.sha256_hash == TEST_PNG_SHA256

    def test_mime_detection_precedence(self, temp_file_factory):
        """Test MIME detection order: manual override > magic bytes."""
        # Create a text file, but we will label it as something else
        file_path = temp_file_factory("mismatch.txt", TEST_TXT_BYTES)

        # Case 1: Auto-detection. Should detect 'text/plain'.
        result_auto = resolve_attachment(Attachment(source='file', content=str(file_path)))
        assert result_auto.mime_type == "text/plain"

        # Case 2: Manual override. Should use the provided type.
        result_manual = resolve_attachment(
            Attachment(source='file', content=str(file_path), mime_type="application/x-custom")
        )
        assert result_manual.mime_type == "application/x-custom"

    def test_main_resolver_dispatcher_invalid_source(self):
        """Test the main dispatcher rejects an unsupported source type."""
        with pytest.raises(ValidationError):
            # Pydantic model validation should fail first for an invalid 'source' literal
            Attachment(source='invalid_source', content='foo')
```
