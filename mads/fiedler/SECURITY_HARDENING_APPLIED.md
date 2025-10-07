# Security Hardening Applied

**Date:** 2025-10-02
**Status:** ✅ Complete
**Review Correlation ID:** FIEDLER-SECURITY-R1

## Overview

Applied critical security fixes to Fiedler's keyring integration based on Fiedler triplet review feedback.

## Issues Addressed

### Critical Issues Fixed (2)

1. **Insecure Keyring Backend Acceptance** (GPT-5 Critical)
   - **Issue:** Linux/headless systems may use plaintext keyrings (keyrings.alt)
   - **Fix:** Added `_is_secure_backend()` validation
   - **Behavior:** Rejects/warns about insecure backends based on `FIEDLER_REQUIRE_SECURE_KEYRING` flag
   - **Files:** `fiedler/utils/secrets.py:29-57`

2. **Secret Exposure via Logging/Telemetry** (GPT-5 Critical)
   - **Issue:** API keys passed as MCP tool arguments may be logged
   - **Fix:** Marked `api_key` parameter as sensitive in MCP schema
   - **Schema:** Added `"format": "password"` and `"writeOnly": True`
   - **Files:** `fiedler/server.py:112-113`

### Major Issues Fixed (5)

3. **Broad Exception Handling** (All 3 Reviewers)
   - **Issue:** Bare `except Exception:` masks keyring failures
   - **Fix:** Catch specific `keyring.errors.KeyringError` with logging
   - **Files:** `fiedler/utils/secrets.py:87-98`

4. **Silent Security Downgrade** (All 3 Reviewers)
   - **Issue:** Keyring failures silently fall back to env vars
   - **Fix:** Added `logger.warning()` for all downgrades
   - **Files:** `fiedler/utils/secrets.py:89-92, 109-115`

5. **No "Require Secure Keyring" Control** (GPT-5 Major)
   - **Issue:** High-security deployments need to enforce keyring usage
   - **Fix:** Added `FIEDLER_REQUIRE_SECURE_KEYRING` environment flag
   - **Files:** `fiedler/utils/secrets.py:60-62, 101-106, 138-145`

6. **Hardcoded Provider Lists** (All 3 Reviewers)
   - **Issue:** Provider list duplicated in multiple files
   - **Fix:** Created `KNOWN_PROVIDERS` constant as single source of truth
   - **Files:** `fiedler/utils/secrets.py:18`, `fiedler/tools/keys.py:10`

7. **No Backend Visibility** (Gemini & Grok)
   - **Issue:** Users can't see which keyring backend is in use
   - **Fix:** Added `get_backend_info()` and exposed in `fiedler_list_keys`
   - **Files:** `fiedler/utils/secrets.py:223-242`, `fiedler/tools/keys.py:104-111`

### Minor Issues Fixed (2)

8. **API Key Trimming**
   - **Issue:** Accidental whitespace not handled
   - **Fix:** Added `api_key.strip()` before validation
   - **Files:** `fiedler/tools/keys.py:32`

9. **Delete Error Handling Too Narrow**
   - **Issue:** Only caught `PasswordDeleteError`
   - **Fix:** Catch all exceptions with logging
   - **Files:** `fiedler/utils/secrets.py:190-193`

## New Security Features

### 1. Backend Validation

**Function:** `_is_secure_backend() -> tuple[bool, str]`

```python
def _is_secure_backend() -> tuple[bool, str]:
    """
    Check if keyring backend is secure (not plaintext/null).

    Returns:
        (is_secure, backend_name) tuple
    """
    # Rejects: keyrings.alt.*, keyring.backends.null, keyring.backends.fail
    # Allows: macOS.Keyring, Windows.WinVaultKeyring, SecretService.Keyring, kwallet.DBusKeyring
```

**Used in:**
- `set_api_key()` - Validates before storing (raises if REQUIRE flag set)
- `get_backend_info()` - Exposes security status to users

### 2. Security Hardening Flag

**Environment Variable:** `FIEDLER_REQUIRE_SECURE_KEYRING`

**Values:** `"0"` (default), `"1"`, `"true"`, `"yes"`

**Behavior when enabled:**
- `set_api_key()`: Refuses to store keys if backend is insecure (raises RuntimeError)
- `get_api_key()`: Refuses env var fallback if keyring unavailable/failed (returns None)

**Use Case:** Production environments requiring encrypted-only key storage

**Example:**
```bash
export FIEDLER_REQUIRE_SECURE_KEYRING=1
fiedler_set_key provider="google" api_key="..."
# Raises: "Insecure keyring backend (keyrings.alt.file.PlaintextKeyring). Refusing to store secret."
```

### 3. Security Event Logging

**Logger:** `logging.getLogger("fiedler.utils.secrets")`

**Events Logged:**
- `WARNING`: Keyring get_password failures (with backend name)
- `WARNING`: Insecure backend usage (when REQUIRE not set)
- `WARNING`: Failed key deletion attempts
- `INFO`: Successful key storage (with backend name)
- `INFO`: Env var fallback (when keyring returns None)
- `ERROR`: Refused env var fallback (when REQUIRE set)

**Example Log Output:**
```
WARNING:fiedler.utils.secrets:Keyring get_password failed for provider=google using backend=keyring.backends.SecretService.Keyring: org.freedesktop.DBus.Error.NoReply
WARNING:fiedler.utils.secrets:Storing key using a non-secure keyring backend (keyrings.alt.file.PlaintextKeyring). Consider enabling FIEDLER_REQUIRE_SECURE_KEYRING=1.
INFO:fiedler.utils.secrets:API key stored for provider=openai using backend=keyring.backends.macOS.Keyring
```

### 4. Backend Diagnostics

**Function:** `get_backend_info() -> dict[str, str]`

**Returns:**
```python
{
    "available": True,
    "backend": "keyring.backends.macOS.Keyring",
    "secure": True
}
```

**Exposed in:**
- `fiedler_list_keys()` response
- `fiedler_set_key()` success response

## Code Changes Summary

### Files Modified (4)

1. **fiedler/utils/secrets.py** (~130 lines changed)
   - Added: `KNOWN_PROVIDERS`, `_get_backend_name()`, `_is_secure_backend()`, `_require_secure_keyring()`, `get_backend_info()`
   - Updated: `get_api_key()`, `set_api_key()`, `delete_api_key()`, `list_stored_providers()`
   - Added: `import logging`, `import keyring.errors`

2. **fiedler/tools/keys.py** (~25 lines changed)
   - Updated: Import `KNOWN_PROVIDERS`, `get_backend_info()`
   - Updated: `fiedler_set_key()`, `fiedler_delete_key()`, `fiedler_list_keys()`
   - Added: `api_key.strip()`, backend info in responses

3. **fiedler/server.py** (2 lines changed)
   - Updated: `fiedler_set_key` schema - added `"format": "password"`, `"writeOnly": True`

4. **fiedler/utils/__init__.py** (2 lines changed)
   - Added exports: `get_backend_info`, `KNOWN_PROVIDERS`

### Lines Changed by Issue Severity

- **Critical Fixes:** ~60 lines
- **Major Fixes:** ~90 lines
- **Minor Fixes:** ~10 lines
- **Total:** ~160 lines added/modified

## Security Posture Improvements

### Before Hardening
- ❌ Silent failures with insecure backends
- ❌ No visibility into backend security
- ❌ No way to enforce secure keyring
- ❌ API keys may be logged by MCP framework
- ❌ Silent downgrade to plaintext env vars

### After Hardening
- ✅ Insecure backends rejected (when REQUIRE=1) or warned
- ✅ Backend security status visible in `fiedler_list_keys`
- ✅ `FIEDLER_REQUIRE_SECURE_KEYRING` enforces encrypted storage
- ✅ API keys marked sensitive in MCP schema (format=password, writeOnly)
- ✅ All security events logged with context

## Testing Status

**Manual Validation:**
- ✅ Module imports verified (no syntax errors)
- ✅ Logging logic reviewed
- ✅ Exception handling paths reviewed
- ✅ Backend validation logic reviewed

**Production Testing Required:**
- ⏳ Test with `FIEDLER_REQUIRE_SECURE_KEYRING=1`
- ⏳ Test insecure backend detection (Linux with keyrings.alt)
- ⏳ Verify logging output in production
- ⏳ Verify MCP framework respects writeOnly schema

## Security Recommendations for Deployment

1. **Enable Logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

2. **High-Security Environments:**
   ```bash
   export FIEDLER_REQUIRE_SECURE_KEYRING=1
   ```

3. **Verify Backend:**
   ```python
   # Check backend status before storing production keys
   result = fiedler_list_keys()
   print(f"Backend: {result['backend']}, Secure: {result['backend_secure']}")
   ```

4. **Linux Production Servers:**
   - Install gnome-keyring or kwallet
   - Do NOT install keyrings.alt
   - Verify Secret Service D-Bus is available

5. **Monitor Logs:**
   - Watch for `WARNING` messages about keyring failures
   - Alert on insecure backend usage in production

## Backward Compatibility

✅ **100% Backward Compatible**

- Default behavior unchanged (REQUIRE flag defaults to 0)
- Existing env var fallback still works
- No breaking changes to MCP tool signatures
- New fields in responses are additive

## Documentation Updates Needed

1. **SECURITY.md:** Add section on `FIEDLER_REQUIRE_SECURE_KEYRING`
2. **README.md:** Update security section with hardening options
3. **SECURITY.md:** Add Linux backend warnings
4. **SECURITY.md:** Document logging configuration

## References

**Triplet Reviews:**
- Gemini 2.5 Pro: `/mnt/projects/ICCM/architecture/triplet_submissions/fiedler_security_review/Gemini_2.5_Pro_Verification.md`
- GPT-5: `/mnt/projects/ICCM/architecture/triplet_submissions/fiedler_security_review/GPT-5_Verification.md`
- Grok 4: `/mnt/projects/ICCM/architecture/triplet_submissions/fiedler_security_review/Grok_4_Verification.md`

**Review Request:**
- `/mnt/projects/ICCM/architecture/fiedler_security_feature_review_request.md`

---

**Status:** Production-ready after logging validation
**Next Steps:** Phase 1 Requirements Extraction
