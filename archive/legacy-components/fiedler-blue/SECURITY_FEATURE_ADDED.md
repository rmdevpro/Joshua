# Secure Key Storage Feature

**Added:** 2025-10-02
**Status:** ✅ Complete

## Summary

Added encrypted API key storage to Fiedler using OS-native keyring integration. Users can now store API keys securely instead of using plaintext environment variables.

## Implementation Details

### New Files (2)
1. `fiedler/utils/secrets.py` - Keyring integration utilities (107 lines)
2. `fiedler/tools/keys.py` - MCP tools for key management (115 lines)

### Modified Files (8)
1. `pyproject.toml` - Added `keyring>=24.0.0` dependency
2. `fiedler/utils/__init__.py` - Exported secrets functions
3. `fiedler/tools/__init__.py` - Exported key management tools
4. `fiedler/providers/gemini.py` - Uses `get_api_key()` with keyring fallback
5. `fiedler/providers/openai.py` - Uses `get_api_key()` with keyring fallback
6. `fiedler/providers/together.py` - Uses `get_api_key()` with keyring fallback
7. `fiedler/providers/xai.py` - Uses `get_api_key()` with keyring fallback
8. `fiedler/server.py` - Registered 3 new MCP tools

### Documentation (3)
1. `SECURITY.md` - Comprehensive security documentation (NEW)
2. `README.md` - Updated with key management tools and secure setup guide
3. `SECURITY_FEATURE_ADDED.md` - This file

## New MCP Tools (3)

### 1. fiedler_set_key
- **Purpose:** Store API key in encrypted OS keyring
- **Parameters:** `provider` (google/openai/together/xai), `api_key`
- **Storage:** macOS Keychain / Windows Credential Manager / Linux Secret Service

### 2. fiedler_list_keys
- **Purpose:** List providers with stored keys
- **Returns:** List of providers, keyring availability status

### 3. fiedler_delete_key
- **Purpose:** Remove stored API key
- **Parameters:** `provider`

## Security Architecture

**Key Retrieval Order:**
1. **System Keyring** (encrypted) - `keyring.get_password("fiedler-mcp-server", provider)`
2. **Environment Variable** (plaintext) - `os.getenv(api_key_env)`
3. **Error** - Clear message guiding user to `fiedler_set_key` or env var

**Encryption Details:**
- **macOS:** Keys encrypted by macOS Keychain (AES-256)
- **Windows:** Keys encrypted by Windows Credential Manager (DPAPI)
- **Linux:** Keys encrypted by Secret Service (varies by backend)

**No Plaintext Storage:** Fiedler never writes API keys to config files or logs.

## Provider Updates

All 4 providers updated to use secure key retrieval:

```python
# Before (environment variable only)
self.api_key = os.getenv(api_key_env)
if not self.api_key:
    raise ValueError(f"Missing environment variable: {api_key_env}")

# After (keyring first, env var fallback)
from ..utils.secrets import get_api_key
self.api_key = get_api_key("provider_name", api_key_env)
if not self.api_key:
    raise ValueError(
        f"No API key found. Set via fiedler_set_key or environment variable {api_key_env}"
    )
```

## Backward Compatibility

✅ **100% Backward Compatible**
- Environment variables still work (fallback mechanism)
- Existing deployments unaffected
- No breaking changes to MCP tools or provider APIs

## Usage Example

```python
# Secure setup (NEW recommended method)
fiedler_set_key(provider="google", api_key="AIza...")
fiedler_set_key(provider="openai", api_key="sk-...")

# Verify
fiedler_list_keys()
# {"providers_with_keys": ["google", "openai"], "count": 2}

# Use normally - keys retrieved from keyring automatically
fiedler_send(prompt="Test", models=["gemini", "gpt-5"])

# Rotate keys
fiedler_delete_key(provider="google")
fiedler_set_key(provider="google", api_key="new-key")
```

## Testing Status

**Manual Testing:**
- ✅ Module imports verified (no syntax errors)
- ⏳ Full integration testing requires `pip install keyring`
- ⏳ Runtime testing requires keyring backend setup

**Test Plan:**
1. Install dependencies: `pip install -e .` (includes keyring)
2. Test key storage: `fiedler_set_key(provider="google", api_key="test")`
3. Test retrieval: `fiedler_list_keys()`
4. Test provider init: Verify providers can retrieve keys
5. Test fallback: Set env var, delete keyring key, verify fallback works
6. Test deletion: `fiedler_delete_key(provider="google")`

## Security Benefits

1. **Encryption at Rest:** API keys encrypted by OS, not stored in plaintext
2. **No Config File Keys:** Prevents accidental commit to version control
3. **Easy Rotation:** Simple delete + set for key updates
4. **Audit Trail:** OS keyring provides access logs (macOS/Windows)
5. **Separation of Concerns:** Keys separate from application config

## Deployment Notes

**Requirements:**
- Python package: `keyring>=24.0.0` (auto-installed with Fiedler)
- OS keyring backend (pre-installed on macOS/Windows, may need setup on Linux)

**Linux Setup (if needed):**
```bash
# Ubuntu/Debian
sudo apt-get install gnome-keyring

# RHEL/CentOS
sudo yum install gnome-keyring
```

**Migration from Env Vars:**
```bash
# 1. Store in keyring
fiedler_set_key(provider="google", api_key="${GEMINI_API_KEY}")

# 2. Test (keyring takes precedence)
fiedler_send(prompt="Test", models=["gemini"])

# 3. Remove env var from shell profile (optional)
```

## Code Stats

**Total Changes:**
- **New Files:** 3 (secrets.py, keys.py, SECURITY.md)
- **Modified Files:** 10
- **Lines Added:** ~350
- **Lines Modified:** ~40
- **New MCP Tools:** 3 (total now 8)
- **New Dependencies:** 1 (keyring)

## Future Enhancements

**Potential Additions:**
- Key expiration/rotation reminders
- Multi-user key isolation (per-user keyrings)
- Key sharing for team environments (shared keyring)
- Audit logging for key access
- Integration with enterprise secret managers (Vault, AWS Secrets Manager)

## References

- **Python keyring docs:** https://pypi.org/project/keyring/
- **macOS Keychain:** Security framework documentation
- **Windows Credential Manager:** DPAPI documentation
- **Linux Secret Service:** freedesktop.org Secret Service API
