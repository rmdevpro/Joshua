"""API key management tools."""
from typing import Dict, Any

from ..utils.secrets import (
    set_api_key,
    delete_api_key,
    list_stored_providers,
    get_backend_info,
    KEYRING_AVAILABLE,
    KNOWN_PROVIDERS,
)


def fiedler_set_key(provider: str, api_key: str) -> Dict[str, Any]:
    """
    Store API key securely in system keyring.

    Args:
        provider: Provider name (google, openai, together, xai)
        api_key: API key to store (encrypted by OS keyring)

    Returns:
        Dict with status and message
    """
    # Validate provider
    if provider not in KNOWN_PROVIDERS:
        raise ValueError(
            f"Invalid provider '{provider}'. Must be one of: {', '.join(KNOWN_PROVIDERS)}"
        )

    # Trim and validate key is not empty
    api_key = api_key.strip()
    if not api_key:
        raise ValueError("API key cannot be empty")

    # Store in keyring
    try:
        set_api_key(provider, api_key)
        backend_info = get_backend_info()
        return {
            "status": "success",
            "provider": provider,
            "message": f"API key stored securely for {provider}",
            "storage": "system_keyring",
            "backend": backend_info.get("backend", "unknown")
        }
    except Exception as e:
        # Catch all errors (keyring unavailable, insecure backend, etc.)
        return {
            "status": "error",
            "provider": provider,
            "message": str(e),
            "storage": "unavailable"
        }


def fiedler_delete_key(provider: str) -> Dict[str, Any]:
    """
    Delete stored API key from system keyring.

    Args:
        provider: Provider name (google, openai, together, xai)

    Returns:
        Dict with status and message
    """
    # Validate provider
    if provider not in KNOWN_PROVIDERS:
        raise ValueError(
            f"Invalid provider '{provider}'. Must be one of: {', '.join(KNOWN_PROVIDERS)}"
        )

    try:
        deleted = delete_api_key(provider)
        if deleted:
            return {
                "status": "success",
                "provider": provider,
                "message": f"API key deleted for {provider}"
            }
        else:
            return {
                "status": "not_found",
                "provider": provider,
                "message": f"No API key stored for {provider}"
            }
    except Exception as e:
        # Catch all errors
        return {
            "status": "error",
            "provider": provider,
            "message": str(e)
        }


def fiedler_list_keys() -> Dict[str, Any]:
    """
    List providers with stored API keys.

    Returns:
        Dict with list of providers, keyring availability, and backend info
    """
    stored = list_stored_providers()
    backend_info = get_backend_info()

    return {
        "keyring_available": KEYRING_AVAILABLE,
        "providers_with_keys": stored,
        "count": len(stored),
        "backend": backend_info.get("backend", "unavailable"),
        "backend_secure": backend_info.get("secure", False),
        "message": f"{len(stored)} provider(s) have stored keys" if KEYRING_AVAILABLE
                   else "Keyring not available - install with: pip install keyring"
    }
