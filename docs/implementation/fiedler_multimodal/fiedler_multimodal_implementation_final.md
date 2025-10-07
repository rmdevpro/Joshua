An excellent catch by DeepSeek. Enforcing the size limit during the stream is crucial to prevent memory exhaustion vulnerabilities.

Here is the complete, final implementation with the critical fix applied to `_process_response_stream`.

```python
import base64
import hashlib
import io
import os
import socket
from enum import Enum
from functools import lru_cache
from ipaddress import ip_address, ip_network
from typing import Callable, Generator, List, Optional, Tuple
from urllib.parse import urlparse

import magic
import requests
from pydantic import BaseModel, Field

# --- Constants ---
CHUNK_SIZE = 8192  # 8 KB
MAX_ATTACHMENT_SIZE_MB = 25
MAX_ATTACHMENT_SIZE_BYTES = MAX_ATTACHMENT_SIZE_MB * 1024 * 1024
REQUESTS_TIMEOUT_SECONDS = 30
MAX_REDIRECTS = 5

# --- SSRF Protection ---
# Cache DNS lookups to avoid repeated calls for the same domain.
@lru_cache(maxsize=128)
def _cached_getaddrinfo(host, port, family):
    return socket.getaddrinfo(host, port, family)

# Use the cached version for requests.
requests.utils.getaddrinfo = _cached_getaddrinfo

# Define private/reserved IP ranges to block.
# Sources: IANA, RFC1918, RFC3927, RFC5735, etc.
BLOCKED_IP_RANGES = [
    "0.0.0.0/8",         # Current network (only valid as source address)
    "10.0.0.0/8",        # Private-Use
    "100.64.0.0/10",     # Shared Address Space
    "127.0.0.0/8",       # Loopback
    "169.254.0.0/16",    # Link-Local
    "172.16.0.0/12",     # Private-Use
    "192.0.0.0/24",      # IETF Protocol Assignments
    "192.0.2.0/24",      # TEST-NET-1
    "192.88.99.0/24",    # 6to4 Relay Anycast
    "192.168.0.0/16",    # Private-Use
    "198.18.0.0/15",     # Network Interconnect Device Benchmark Testing
    "198.51.100.0/24",   # TEST-NET-2
    "203.0.113.0/24",    # TEST-NET-3
    "224.0.0.0/4",       # Multicast
    "240.0.0.0/4",       # Reserved for Future Use
    "255.255.255.255/32",# Broadcast
    "::1/128",           # Loopback Address
    "fc00::/7",          # Unique-Local
    "fe80::/10",         # Link-Local Unicast
    "ff00::/8",          # Multicast
]

# --- Enums and Models ---
class ResolutionStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"

class Attachment(BaseModel):
    source: str = Field(..., description="Source of the attachment: 'base64', 'file', or 'url'.")
    content: str = Field(..., description="Content based on the source: base64 string, file path, or URL.")
    mime_type: Optional[str] = Field(None, description="Optional MIME type to override detection.")

class AttachmentResolution(BaseModel):
    status: ResolutionStatus
    error_message: Optional[str] = None
    mime_type: Optional[str] = None
    sha256_hash: Optional[str] = None
    source_url: Optional[str] = None
    content_stream: Optional[Callable[[], Generator[bytes, None, None]]] = None

    class Config:
        arbitrary_types_allowed = True

# --- Helper Functions ---
def _detect_mime_and_hash(stream_generator: Generator[bytes, None, None]) -> Tuple[str, hashlib._Hash, Generator[bytes, None, None]]:
    """
    Detects MIME type from the first chunk and prepares a hash object.
    Returns a new generator that includes the first chunk and continues hashing the stream.
    """
    sha256_hasher = hashlib.sha256()
    mime_type = "application/octet-stream"  # Default MIME type

    try:
        first_chunk = next(stream_generator)
        sha256_hasher.update(first_chunk)
        # Use python-magic to detect MIME type from the initial bytes.
        mime_type = magic.from_buffer(first_chunk, mime=True)
    except StopIteration:
        # Handle empty stream
        first_chunk = b""

    def final_stream_generator():
        """
        A generator that yields the first chunk and then continues to process
        and hash the rest of the original stream.
        """
        yield first_chunk
        for chunk in stream_generator:
            sha256_hasher.update(chunk)
            yield chunk

    return mime_type, sha256_hasher, final_stream_generator()

def _get_stream_from_url(response: requests.Response) -> Generator[bytes, None, None]:
    """Creates a generator to stream content from a requests.Response."""
    yield from response.iter_content(chunk_size=CHUNK_SIZE)

# --- SSRF Validation Logic ---
def validate_url_ssrf(url: str) -> Optional[str]:
    """
    Validates a URL to prevent Server-Side Request Forgery (SSRF) attacks.
    Returns an error message string if validation fails, otherwise None.
    """
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or parsed_url.scheme.lower() not in ['http', 'https']:
            return "Invalid URL scheme. Only HTTP and HTTPS are allowed."

        hostname = parsed_url.hostname
        if not hostname:
            return "URL must contain a valid hostname."

        # This resolves the hostname to an IP address.
        addr_info = _cached_getaddrinfo(hostname, parsed_url.port, socket.AF_UNSPEC)
        # We only need to check one resolved IP.
        ip_str = addr_info[0][4][0]
        ip = ip_address(ip_str)

        if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_unspecified or ip.is_reserved:
             return f"Resolved IP address {ip} is in a blocked range."

        for blocked_range in BLOCKED_IP_RANGES:
            if ip in ip_network(blocked_range):
                return f"Resolved IP address {ip} is in a blocked range."

    except (ValueError, socket.gaierror) as e:
        return f"URL validation failed: {e}"
    except Exception as e:
        return f"An unexpected error occurred during URL validation: {e}"

    return None

# --- Core Resolution Logic ---
def _resolve_stream(
    stream_generator_factory: Callable[[], Generator[bytes, None, None]],
    manual_mime_type: Optional[str] = None
) -> AttachmentResolution:
    """
    Generic stream processor. Consumes a stream to hash and detect MIME type,
    then returns a new, replayable stream.
    """
    try:
        stream_generator = stream_generator_factory()
        detected_mime, sha256_hasher, final_stream_gen = _detect_mime_and_hash(stream_generator)

        # Cache the entire stream in memory to allow re-reading and get the final hash.
        final_stream_list = list(final_stream_gen())
        final_hash = sha256_hasher.hexdigest()

        def replay_stream():
            """Yields chunks from the in-memory list."""
            yield from final_stream_list

        return AttachmentResolution(
            status=ResolutionStatus.SUCCESS,
            mime_type=manual_mime_type or detected_mime,
            sha256_hash=final_hash,
            content_stream=replay_stream,
        )
    except Exception as e:
        return AttachmentResolution(
            status=ResolutionStatus.ERROR,
            error_message=f"Failed to process stream: {e}"
        )

def _process_response_stream(response: requests.Response) -> AttachmentResolution:
    """
    Processes a streaming requests.Response object. It detects the MIME type,
    calculates the SHA256 hash, and caches the stream content in-memory to
    allow it to be re-read by the provider. It also enforces the size limit
    during streaming to prevent memory exhaustion.
    """
    stream_generator = _get_stream_from_url(response)
    mime_type, sha256_hasher, final_stream_gen = _detect_mime_and_hash(stream_generator)

    # --- CRITICAL FIX: Enforce size limit during streaming ---
    total_size = 0
    chunks = []
    for chunk in final_stream_gen():
        total_size += len(chunk)
        if total_size > MAX_ATTACHMENT_SIZE_BYTES:
            return AttachmentResolution(
                status=ResolutionStatus.ERROR,
                error_message="Attachment exceeds size limit."
            )
        chunks.append(chunk)

    final_hash = sha256_hasher.hexdigest()

    def replay_stream():
        """Replays the cached stream content from the in-memory list."""
        yield from chunks
    # --- END FIX ---

    return AttachmentResolution(
        status=ResolutionStatus.SUCCESS,
        mime_type=mime_type,
        sha256_hash=final_hash,
        content_stream=replay_stream,
        source_url=response.url
    )

def _resolve_url(url: str, manual_mime_type: Optional[str]) -> AttachmentResolution:
    """Resolves a URL attachment with SSRF protection and size validation."""
    # 1. Initial SSRF check on the provided URL
    ssrf_error = validate_url_ssrf(url)
    if ssrf_error:
        return AttachmentResolution(status=ResolutionStatus.ERROR, error_message=ssrf_error)

    try:
        with requests.Session() as session:
            session.max_redirects = MAX_REDIRECTS
            # Use a HEAD request first to check Content-Length if available.
            try:
                head_response = session.head(url, timeout=REQUESTS_TIMEOUT_SECONDS, allow_redirects=True)
                head_response.raise_for_status()
                content_length = head_response.headers.get('Content-Length')
                if content_length and int(content_length) > MAX_ATTACHMENT_SIZE_BYTES:
                    return AttachmentResolution(
                        status=ResolutionStatus.ERROR,
                        error_message="Attachment exceeds size limit based on Content-Length header."
                    )
            except requests.RequestException:
                # HEAD request might fail or not be supported, proceed to GET.
                pass

            # 2. Perform the actual GET request with streaming.
            with session.get(url, stream=True, timeout=REQUESTS_TIMEOUT_SECONDS) as response:
                response.raise_for_status()

                # 3. Validate all redirect URLs and the final URL against SSRF policy.
                all_urls_to_check = [r.url for r in response.history] + [response.url]
                for u in all_urls_to_check:
                    ssrf_error = validate_url_ssrf(u)
                    if ssrf_error:
                        return AttachmentResolution(
                            status=ResolutionStatus.ERROR,
                            error_message=f"SSRF validation failed for redirect/final URL {u}: {ssrf_error}"
                        )

                # 4. Process the stream, which now includes the size check.
                resolution = _process_response_stream(response)
                # Override mime_type if one was manually provided.
                if resolution.status == ResolutionStatus.SUCCESS and manual_mime_type:
                    resolution.mime_type = manual_mime_type
                return resolution

    except requests.exceptions.RequestException as e:
        return AttachmentResolution(status=ResolutionStatus.ERROR, error_message=f"URL request failed: {e}")
    except Exception as e:
        return AttachmentResolution(status=ResolutionStatus.ERROR, error_message=f"An unexpected error occurred: {e}")

def _resolve_base64(content: str, manual_mime_type: Optional[str]) -> AttachmentResolution:
    """Resolves a base64-encoded attachment."""
    try:
        decoded_data = base64.b64decode(content)
        if len(decoded_data) > MAX_ATTACHMENT_SIZE_BYTES:
            return AttachmentResolution(
                status=ResolutionStatus.ERROR,
                error_message="Attachment exceeds size limit."
            )

        stream = io.BytesIO(decoded_data)
        return _resolve_stream(lambda: (c for c in [stream.read()]), manual_mime_type)

    except (ValueError, TypeError) as e:
        return AttachmentResolution(
            status=ResolutionStatus.ERROR,
            error_message=f"Invalid base64 content: {e}"
        )

def _resolve_file(path: str, manual_mime_type: Optional[str]) -> AttachmentResolution:
    """Resolves a local file path attachment."""
    if not os.path.exists(path) or not os.path.isfile(path):
        return AttachmentResolution(
            status=ResolutionStatus.ERROR,
            error_message="File not found or is not a regular file."
        )

    if os.path.getsize(path) > MAX_ATTACHMENT_SIZE_BYTES:
        return AttachmentResolution(
            status=ResolutionStatus.ERROR,
            error_message="Attachment exceeds size limit."
        )

    def stream_file():
        with open(path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                yield chunk

    return _resolve_stream(stream_file, manual_mime_type)

# --- Public API ---
def resolve_attachment(attachment: Attachment) -> AttachmentResolution:
    """
    Resolves an attachment from its source (URL, base64, or file path).

    This function handles fetching, validation (size, SSRF), MIME type
    detection, and hashing. It returns a standardized AttachmentResolution
    object containing a replayable content stream.
    """
    if attachment.source == 'url':
        return _resolve_url(attachment.content, attachment.mime_type)
    elif attachment.source == 'base64':
        return _resolve_base64(attachment.content, attachment.mime_type)
    elif attachment.source == 'file':
        return _resolve_file(attachment.content, attachment.mime_type)
    else:
        return AttachmentResolution(
            status=ResolutionStatus.ERROR,
            error_message=f"Unsupported attachment source: '{attachment.source}'"
        )
```
