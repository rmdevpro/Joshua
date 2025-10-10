"""Secure API key management using system keyring."""
import os
import asyncio
from typing import Optional

try:
    import keyring
    import keyring.errors
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

from joshua_logger import Logger
logger = Logger()

SERVICE_NAME = "fiedler-mcp-server"

# Provider registry - single source of truth
KNOWN_PROVIDERS = ["google", "openai", "together", "xai"]


def _get_backend_name() -> str:
    """Get the name of the current keyring backend."""
    if not KEYRING_AVAILABLE:
        return "unavailable"
    kr = keyring.get_keyring()
    return f"{kr.__class__.__module__}.{kr.__class__.__name__}"


def _is_secure_backend() -> tuple[bool, str]:
    """
    Check if keyring backend is secure (not plaintext/null).

    Returns:
        (is_secure, backend_name) tuple
    """
    if not KEYRING_AVAILABLE:
        return (False, "unavailable")

    backend_name = _get_backend_name()

    # Reject known insecure backends
    insecure_prefixes = (
        "keyrings.alt.",            # plaintext/file-based backends
        "keyring.backends.null",    # no-op backend
        "keyring.backends.fail",    # failing backend
    )
    if backend_name.startswith(insecure_prefixes):
        return (False, backend_name)

    # Allow common secure backends
    allowed = {
        "keyring.backends.macOS.Keyring",
        "keyring.backends.Windows.WinVaultKeyring",
        "keyring.backends.SecretService.Keyring",
        "keyring.backends.kwallet.DBusKeyring",
    }
    return (backend_name in allowed, backend_name)


def _require_secure_keyring() -> bool:
    """Check if FIEDLER_REQUIRE_SECURE_KEYRING environment flag is set."""
    return os.getenv("FIEDLER_REQUIRE_SECURE_KEYRING", "0") in ("1", "true", "yes")


def get_api_key(provider: str, env_var_name: str) -> Optional[str]:
    """
    Get API key from keyring or environment variable.

    Fallback order:
    1. System keyring (secure, encrypted)
    2. Environment variable (only if FIEDLER_REQUIRE_SECURE_KEYRING not set)
    3. None (caller should handle missing key)

    Args:
        provider: Provider name (e.g., "google", "openai", "together", "xai")
        env_var_name: Environment variable name to check as fallback

    Returns:
        API key string or None
    """
    # Try keyring first (most secure)
    if KEYRING_AVAILABLE:
        try:
            key = keyring.get_password(SERVICE_NAME, provider)
            if key:
                return key
        except keyring.errors.KeyringError as e:
            # Specific keyring errors - log warning
            asyncio.run(logger.log(
                "WARN",
                f"Keyring get_password failed for provider={provider} using backend={_get_backend_name()}: {e}",
                "fiedler-utils"
            ))
        except Exception as e:
            # Catch any other errors
            asyncio.run(logger.log(
                "WARN",
                f"Unexpected error accessing keyring for provider={provider}: {e}",
                "fiedler-utils"
            ))

    # Check if fallback to env var is allowed
    if _require_secure_keyring():
        asyncio.run(logger.log(
            "ERROR",
            f"Secure keyring required but unavailable or failed (backend={_get_backend_name() if KEYRING_AVAILABLE else 'unavailable'}); refusing env fallback.",
            "fiedler-utils"
        ))
        return None

    # Fall back to environment variable
    env_key = os.getenv(env_var_name)
    if env_key and KEYRING_AVAILABLE:
        # Warn if falling back despite keyring being available
        asyncio.run(logger.log(
            "INFO",
            f"Using environment variable {env_var_name} for provider={provider} (keyring returned None)",
            "fiedler-utils"
        ))
    return env_key


def set_api_key(provider: str, api_key: str) -> None:
    """
    Store API key in system keyring.

    Args:
        provider: Provider name (e.g., "google", "openai", "together", "xai")
        api_key: API key to store (will be encrypted by OS keyring)

    Raises:
        RuntimeError: If keyring is not available or backend is insecure
    """
    if not KEYRING_AVAILABLE:
        raise RuntimeError(
            "Keyring library not available. Install with: pip install keyring"
        )

    # Validate backend security
    is_secure, backend = _is_secure_backend()

    if _require_secure_keyring():
        # Strict mode - refuse insecure backends
        if not is_secure:
            raise RuntimeError(
                f"Insecure or unavailable keyring backend ({backend}). "
                "Refusing to store secret. Install/enable an OS-native keyring "
                "or unset FIEDLER_REQUIRE_SECURE_KEYRING."
            )
    else:
        # Permissive mode - warn about insecure backends
        if not is_secure:
            asyncio.run(logger.log(
                "WARN",
                f"Storing key using a non-secure keyring backend ({backend}). Consider enabling FIEDLER_REQUIRE_SECURE_KEYRING=1.",
                "fiedler-utils"
            ))

    # Store the key
    try:
        keyring.set_password(SERVICE_NAME, provider, api_key)
        asyncio.run(logger.log("INFO", f"API key stored for provider={provider} using backend={backend}", "fiedler-utils"))
    except Exception as e:
        raise RuntimeError(
            f"Failed to store API key in keyring (backend={backend}): {e}"
        ) from e


def delete_api_key(provider: str) -> bool:
    """
    Delete API key from system keyring.

    Args:
        provider: Provider name

    Returns:
        True if key was deleted, False if no key was stored

    Raises:
        RuntimeError: If keyring is not available
    """
    if not KEYRING_AVAILABLE:
        raise RuntimeError(
            "Keyring library not available. Install with: pip install keyring"
        )

    try:
        existing = keyring.get_password(SERVICE_NAME, provider)
        if existing:
            keyring.delete_password(SERVICE_NAME, provider)
            asyncio.run(logger.log("INFO", f"API key deleted for provider={provider}", "fiedler-utils"))
            return True
        return False
    except Exception as e:
        # Catch all keyring errors during deletion
        asyncio.run(logger.log("WARN", f"Failed to delete key for provider={provider}: {e}", "fiedler-utils"))
        return False


def list_stored_providers() -> list[str]:
    """
    List providers that have keys stored in keyring.

    Returns:
        List of provider names with stored keys
    """
    if not KEYRING_AVAILABLE:
        return []

    stored = []
    for provider in KNOWN_PROVIDERS:
        try:
            if keyring.get_password(SERVICE_NAME, provider):
                stored.append(provider)
        except Exception as e:
            # Log errors but continue checking other providers
            asyncio.run(logger.log(
                "WARN",
                f"Could not check keyring for provider '{provider}': {e}. It will be omitted from the list.",
                "fiedler-utils"
            ))
            continue

    return stored


def get_backend_info() -> dict[str, str]:
    """
    Get keyring backend information for diagnostics.

    Returns:
        Dict with backend name and security status
    """
    if not KEYRING_AVAILABLE:
        return {
            "available": False,
            "backend": "unavailable",
            "secure": False
        }

    is_secure, backend = _is_secure_backend()
    return {
        "available": True,
        "backend": backend,
        "secure": is_secure
    }
