# Fiedler Security Features

## Secure API Key Storage

Fiedler integrates with your operating system's secure credential storage to encrypt and protect API keys.

### How It Works

**Storage Locations by OS:**
- **macOS:** Keychain (encrypted by macOS)
- **Windows:** Credential Manager (encrypted by Windows)
- **Linux:** Secret Service (D-Bus) or encrypted file backend

**Fallback Order:**
1. System keyring (encrypted, most secure) ✅
2. Environment variable (plaintext, less secure) ⚠️
3. Error if neither found ❌

### MCP Tools for Key Management

#### 1. fiedler_set_key

Store API key securely in system keyring:

```json
{
  "provider": "google",
  "api_key": "your-api-key-here"
}
```

**Valid providers:** `google`, `openai`, `together`, `xai`

**Returns:**
```json
{
  "status": "success",
  "provider": "google",
  "message": "API key stored securely for google",
  "storage": "system_keyring"
}
```

#### 2. fiedler_list_keys

Check which providers have stored keys:

```json
{}
```

**Returns:**
```json
{
  "keyring_available": true,
  "providers_with_keys": ["google", "openai"],
  "count": 2,
  "message": "2 provider(s) have stored keys"
}
```

#### 3. fiedler_delete_key

Remove stored API key:

```json
{
  "provider": "google"
}
```

**Returns:**
```json
{
  "status": "success",
  "provider": "google",
  "message": "API key deleted for google"
}
```

### Usage Examples

**Initial Setup (Recommended):**

```bash
# Store all your API keys securely
fiedler_set_key(provider="google", api_key="AIza...")
fiedler_set_key(provider="openai", api_key="sk-...")
fiedler_set_key(provider="together", api_key="...")
fiedler_set_key(provider="xai", api_key="xai-...")

# Verify storage
fiedler_list_keys()
# Returns: {"providers_with_keys": ["google", "openai", "together", "xai"], "count": 4}
```

**Key Rotation:**

```bash
# Replace existing key
fiedler_set_key(provider="openai", api_key="new-key-here")

# Or delete and re-add
fiedler_delete_key(provider="openai")
fiedler_set_key(provider="openai", api_key="new-key-here")
```

**Environment Variables (Still Supported):**

If you prefer environment variables (e.g., for CI/CD):

```bash
export GEMINI_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export TOGETHER_API_KEY="your-key"
export XAI_API_KEY="your-key"
```

Fiedler will check keyring first, then fall back to env vars.

### Security Best Practices

✅ **DO:**
- Use `fiedler_set_key` to store keys in encrypted keyring
- Rotate keys regularly using `fiedler_delete_key` + `fiedler_set_key`
- Use environment variables only in CI/CD or containerized environments
- Verify stored keys with `fiedler_list_keys` after setup

❌ **DON'T:**
- Store API keys in config files (never checked into version control)
- Hard-code API keys in scripts
- Share API keys via plain text (email, chat, etc.)
- Use the same API key across multiple systems

### Technical Details

**Encryption:**
- Keys stored via OS-native keyring are encrypted at rest
- Encryption method determined by OS (Keychain/Credential Manager/Secret Service)
- No plaintext keys stored on disk by Fiedler

**Dependencies:**
- `keyring>=24.0.0` (Python library)
- OS-native keyring backend (pre-installed on macOS/Windows/Linux)

**Fallback Behavior:**
- If keyring unavailable, Fiedler shows helpful error message
- Environment variables still work as fallback
- No degraded security - clear error if neither method available

### Troubleshooting

**"Keyring library not available":**
```bash
pip install keyring
```

**Linux: "No keyring backend available":**
```bash
# Install Secret Service backend
sudo apt-get install gnome-keyring  # Ubuntu/Debian
sudo yum install gnome-keyring      # RHEL/CentOS
```

**Check keyring status:**
```bash
python -c "import keyring; print(keyring.get_keyring())"
```

### Migration from Environment Variables

If currently using env vars, migrate to keyring:

```bash
# 1. Store keys in keyring
fiedler_set_key(provider="google", api_key="${GEMINI_API_KEY}")
fiedler_set_key(provider="openai", api_key="${OPENAI_API_KEY}")

# 2. Verify
fiedler_list_keys()

# 3. Remove env vars from shell profile
# (edit ~/.bashrc, ~/.zshrc, etc.)

# 4. Test
fiedler_send(prompt="Test", models=["gemini"])
```

**No downtime** - keys work from keyring immediately after storage.
