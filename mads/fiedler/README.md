# Fiedler MCP Server

**Orchestra Conductor Prototype** - Unified MCP interface for multiple LLM providers.

## Overview

Fiedler is an MCP (Model Context Protocol) server that provides a unified interface for sending prompts to multiple LLM providers simultaneously. It abstracts away provider-specific APIs and presents a consistent set of tools for orchestrating LLM calls.

**Key Features:**
- **Multi-Provider Support**: Google Gemini, OpenAI, Together.AI, xAI (Grok)
- **Parallel Execution**: Send to multiple models simultaneously
- **Secure Key Storage**: Encrypted API keys via OS keyring (Keychain/Credential Manager)
- **Persistent Configuration**: Set default models and output directory once
- **Automatic Retries**: Exponential backoff for transient failures
- **Token Management**: Budget checking and warnings
- **Correlation IDs**: Traceability across runs
- **Package Compilation**: Combine multiple files into single context

## Installation

### Prerequisites

- Docker
- API keys for providers you want to use:
  - `GEMINI_API_KEY` - Google Gemini
  - `OPENAI_API_KEY` - OpenAI
  - `TOGETHER_API_KEY` - Together.AI
  - `XAI_API_KEY` - xAI (Grok)

### Setup

#### Docker Deployment (Recommended)

1. **Build Docker image:**
   ```bash
   cd /mnt/projects/ICCM/fiedler
   docker-compose build
   ```

2. **Start container:**
   ```bash
   docker-compose up -d
   ```

3. **Configure API keys:**

   Store keys securely in the container using the keyring:
   ```bash
   docker exec -it fiedler-mcp python -c "
   from fiedler.tools.keys import fiedler_set_key
   fiedler_set_key('google', 'your_gemini_api_key')
   fiedler_set_key('openai', 'your_openai_api_key')
   fiedler_set_key('together', 'your_together_api_key')
   fiedler_set_key('xai', 'your_xai_api_key')
   "
   ```

4. **Configure Claude Code:**

   **Method 1: stdio adapter (Recommended for bare metal Claude Code)**

   Add to your project's MCP servers in `~/.claude.json`:
   ```json
   {
     "projects": {
       "/your/project/path": {
         "mcpServers": {
           "fiedler": {
             "type": "stdio",
             "command": "/mnt/projects/ICCM/fiedler/stdio_adapter.py",
             "args": []
           }
         }
       }
     }
   }
   ```

   **Method 2: Direct WebSocket (For containerized Claude or AutoGen frameworks)**

   ```json
   {
     "fiedler": {
       "transport": {
         "type": "ws",
         "url": "ws://localhost:9010"
       }
     }
   }
   ```

   **Note:** Claude Code MCP only officially supports stdio, SSE, and HTTP transports. The stdio adapter (`stdio_adapter.py`) bridges Claude Code's stdio requirement to Fiedler's WebSocket server.

5. **Restart Claude Code:**

   After adding the configuration, restart Claude Code to load the Fiedler MCP server. The following tools will be available:
   - `mcp__fiedler__fiedler_send` - Send prompts to models
   - `mcp__fiedler__fiedler_list_models` - List available models
   - `mcp__fiedler__fiedler_get_config` - Get configuration
   - `mcp__fiedler__fiedler_set_models` - Set default models
   - `mcp__fiedler__fiedler_set_output` - Set output directory
   - `mcp__fiedler__fiedler_set_key` - Store API keys securely
   - `mcp__fiedler__fiedler_list_keys` - List stored keys
   - `mcp__fiedler__fiedler_delete_key` - Delete stored keys

## Architecture

### stdio Adapter (stdio_adapter.py)

**Purpose:** Bridges Claude Code's stdio MCP transport to Fiedler's WebSocket server.

**Why needed:**
- Claude Code MCP officially supports: stdio, SSE, HTTP (WebSocket NOT supported)
- Fiedler runs as WebSocket server for AutoGen/multi-agent compatibility
- Adapter allows Claude Code to use stdio while maintaining WebSocket infrastructure

**Flow:**
```
Claude Code (stdio)
    ↓
stdio_adapter.py (process spawned by Claude)
    ↓ WebSocket
Fiedler WebSocket Server (port 9010)
    ↓
LLM Providers (Gemini, OpenAI, Together, xAI)
```

**Implementation:**
- Bidirectional relay: stdin → WebSocket, WebSocket → stdout
- Uses Python asyncio for concurrent I/O
- Requires websockets library (installed in `.venv/`)
- Single file, minimal dependencies

**Benefits:**
- Claude Code gets stdio (required)
- Fiedler keeps WebSocket (for agent ecosystem)
- No code changes to Fiedler core
- Works with relay/KGB logging infrastructure

#### Alternative: Local Python Installation

For development or testing without Docker:

1. **Install dependencies:**
   ```bash
   cd /mnt/projects/ICCM/fiedler
   pip install -e .
   ```

2. **Set environment variables:**
   ```bash
   export GEMINI_API_KEY="your_key_here"
   export OPENAI_API_KEY="your_key_here"
   export TOGETHER_API_KEY="your_key_here"
   export XAI_API_KEY="your_key_here"
   ```

3. **Configure Claude Code:**

   **Option A: stdio adapter (Recommended for Claude Code)**

   Add to `~/.claude.json`:
   ```json
   {
     "projects": {
       "/your/project/path": {
         "mcpServers": {
           "fiedler": {
             "type": "stdio",
             "command": "/mnt/projects/ICCM/fiedler/stdio_adapter.py",
             "args": []
           }
         }
       }
     }
   }
   ```

   **Option B: Direct WebSocket (For containerized Claude or AutoGen)**

   ```json
   {
     "projects": {
       "/your/project/path": {
         "mcpServers": {
           "fiedler": {
             "transport": {
               "type": "ws",
               "url": "ws://localhost:9010"
             }
           }
         }
       }
     }
   }
   ```

   **Note:** Claude Code MCP only supports stdio, SSE, HTTP. Use stdio adapter for bare metal Claude Code.

## Claude Code Integration

### How It Works

Fiedler integrates with Claude Code through the **Model Context Protocol (MCP)**. When configured, Fiedler runs as an MCP server that Claude Code connects to.

**Architecture (stdio adapter - Recommended):**
```
┌─────────────────┐
│  Claude Code    │ (The AI assistant)
└────────┬────────┘
         │
         │ MCP Protocol (stdio)
         │
    ┌────┴─────────────┐
    │  stdio_adapter   │ (Python bridge script)
    └────┬─────────────┘
         │
         │ WebSocket (ws://localhost:9010)
         │
    ┌────┴─────────────┐
    │  Fiedler Server  │
    └──────────────────┘
```

**Alternative Architecture (WebSocket direct - For AutoGen/containerized frameworks):**
```
┌─────────────────┐
│  AutoGen / LLM  │
│   Framework     │
└────────┬────────┘
         │
         │ WebSocket (ws://localhost:9010)
         │
    ┌────┴─────────────┐
    │  Fiedler Server  │
    └──────────────────┘
```

**MCP Server Implementation:**

The MCP server implements the WebSocket-based MCP protocol:
1. **Accepts WebSocket connections** on port 9010
2. **Routes to Fiedler tools** based on method name
3. **Returns JSON responses** over WebSocket
4. **Logs internally** (separate from protocol communication)

**Key MCP Methods:**
- `initialize` - Server handshake and capability negotiation
- `tools/list` - Returns available Fiedler tools
- `tools/call` - Executes a specific tool with arguments

**WebSocket Communication:**

Claude Code communicates with the Dockerized Fiedler via WebSocket at `ws://localhost:9010`. The Fiedler container exposes port 9010 (mapped from internal port 8080) for MCP communication.

### Natural Usage

Once configured, Claude Code automatically uses Fiedler when appropriate:

**User:** "Compare how Gemini and DeepSeek would solve this problem"

**Claude internally:**
1. Recognizes need for multi-model comparison
2. Calls `mcp__fiedler__fiedler_send` with models=["gemini-2.5-pro", "deepseek-r1"]
3. Receives results
4. Synthesizes natural response combining both perspectives

**User sees:** "I've analyzed the problem with both Gemini and DeepSeek. Here's their combined perspective..."

**User never sees:**
- Docker commands
- JSON payloads
- MCP protocol details
- File paths or technical internals

### Deployment Status

**Current deployment:**
- Container: `fiedler-mcp` (running)
- Port: 9010 (health checks)
- Image: `fiedler-mcp:latest`
- Status: Production-ready (8.7/10 rating from triplet verification)
- Tests: 50/50 passing (100% success rate)

**Verification:**
```bash
# Check container status
docker ps | grep fiedler-mcp

# Test MCP server response
echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}' | docker exec -i fiedler-mcp fiedler

# Check health endpoint
curl http://localhost:9010/health
```

## Development Timeline

**Development Velocity:** 3 hours 11 minutes (October 2, 2025)

- **Started:** 1:33 AM EDT - First requirements document created
- **Completed:** 4:44 AM EDT - Production deployment committed to git

**What Was Built:**
- Complete MCP server with 10 LLM provider integrations
- Triplet-verified architecture (3 rounds of reviews: 6.2/10 → 8.7/10)
- Docker deployment with docker-compose
- Comprehensive test suite (50 tests, 100% passing)
- Security features (path restrictions, size limits, secret management)
- Claude Code MCP integration
- Full documentation suite

**Development Process:**
1. **Requirements** - Triplet review of specifications
2. **Implementation** - Initial build with all providers
3. **Round 1 Review** - Security and architecture feedback (6.2/10)
4. **Round 2 Review** - Corrections applied (7.8/10)
5. **Final Review** - Production-ready validation (8.7/10)
6. **Docker Deployment** - Containerized with health checks
7. **MCP Integration** - Connected to Claude Code

This timeline demonstrates the triplet-accelerated development methodology used throughout the ICCM project, where multiple LLMs provide concurrent verification and guidance.

## Available Models

| Provider | Model ID | Aliases | Max Tokens |
|----------|----------|---------|------------|
| Google | gemini-2.5-pro | gemini, gemini-pro | 1,000,000 |
| OpenAI | gpt-5 | openai, gpt5 | 128,000 |
| OpenAI | gpt-4o | gpt4 | 128,000 |
| Together.AI | meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo | llama-3.1-70b | 131,072 |
| Together.AI | meta-llama/Llama-3.3-70B-Instruct-Turbo | llama-3.3-70b | 131,072 |
| Together.AI | deepseek-ai/DeepSeek-R1 | deepseek-r1 | 65,536 |
| Together.AI | Qwen/Qwen2.5-72B-Instruct-Turbo | qwen-2.5-72b | 32,768 |
| Together.AI | mistralai/Mistral-Large-2411 | mistral-large | 131,072 |
| Together.AI | nvidia/Llama-3.1-Nemotron-70B-Instruct-HF | nemotron-70b | 131,072 |
| xAI | grok-4-0709 | grok, grok-4 | 131,072 |

## MCP Tools

Fiedler provides 8 MCP tools for model orchestration and key management.

### Key Management Tools

#### fiedler_set_key

Store API key securely in system keyring (encrypted).

**Input:**
```json
{
  "provider": "google",
  "api_key": "your-api-key-here"
}
```

**Output:**
```json
{
  "status": "success",
  "provider": "google",
  "message": "API key stored securely for google",
  "storage": "system_keyring"
}
```

**Valid providers:** `google`, `openai`, `together`, `xai`

#### fiedler_list_keys

List providers with stored API keys.

**Input:** None

**Output:**
```json
{
  "keyring_available": true,
  "providers_with_keys": ["google", "openai"],
  "count": 2,
  "message": "2 provider(s) have stored keys"
}
```

#### fiedler_delete_key

Delete stored API key from system keyring.

**Input:**
```json
{
  "provider": "google"
}
```

**Output:**
```json
{
  "status": "success",
  "provider": "google",
  "message": "API key deleted for google"
}
```

### Model Management Tools

#### 1. fiedler_list_models

List all available models with their properties.

**Input:** None

**Output:**
```json
{
  "models": [
    {
      "name": "gemini-2.5-pro",
      "provider": "google",
      "aliases": ["gemini", "gemini-pro"],
      "max_tokens": 1000000,
      "capabilities": ["text", "vision"]
    },
    ...
  ]
}
```

### 2. fiedler_set_models

Configure default models for `fiedler_send`.

**Input:**
```json
{
  "models": ["gemini", "gpt-5", "grok"]
}
```

**Output:**
```json
{
  "status": "configured",
  "models": ["gemini-2.5-pro", "gpt-5", "grok-4-0709"],
  "message": "Default models updated (3 models configured)"
}
```

### 3. fiedler_set_output

Configure output directory for results.

**Input:**
```json
{
  "output_dir": "/mnt/projects/ICCM/results"
}
```

**Output:**
```json
{
  "status": "configured",
  "output_dir": "/mnt/projects/ICCM/results",
  "message": "Output directory updated"
}
```

### 4. fiedler_get_config

Get current configuration.

**Input:** None

**Output:**
```json
{
  "models": ["gemini-2.5-pro", "gpt-5", "grok-4-0709"],
  "output_dir": "/mnt/projects/ICCM/results",
  "total_available_models": 10
}
```

### 5. fiedler_send

Send prompt to models (uses defaults or override).

**Input:**
```json
{
  "prompt": "Explain quantum computing in simple terms",
  "files": ["/path/to/context1.md", "/path/to/context2.md"],
  "models": ["gemini", "gpt-5"]
}
```

**Parameters:**
- `prompt` (required): User prompt/question
- `files` (optional): List of file paths to compile into package
- `models` (optional): Override default models for this call

**Output:**
```json
{
  "status": "success",
  "correlation_id": "a1b2c3d4",
  "output_dir": "/mnt/projects/ICCM/results/20250102_143052_a1b2c3d4",
  "summary_file": "/mnt/projects/ICCM/results/20250102_143052_a1b2c3d4/summary.json",
  "results": [
    {
      "model": "gemini-2.5-pro",
      "status": "success",
      "output_file": "/mnt/projects/ICCM/results/20250102_143052_a1b2c3d4/gemini-2.5-pro.md",
      "duration": 12.3,
      "tokens": {"prompt": 1500, "completion": 800}
    },
    ...
  ],
  "message": "2/2 models succeeded"
}
```

**Status Values:**
- `success`: All models succeeded
- `partial_success`: Some models succeeded
- `failure`: All models failed

## Usage Examples

### Secure Setup (Recommended)

```python
# Store API keys securely in OS keyring (encrypted)
fiedler_set_key(provider="google", api_key="AIza...")
fiedler_set_key(provider="openai", api_key="sk-...")
fiedler_set_key(provider="together", api_key="...")
fiedler_set_key(provider="xai", api_key="xai-...")

# Verify keys are stored
fiedler_list_keys()
# Returns: {"providers_with_keys": ["google", "openai", "together", "xai"]}

# Set default models
fiedler_set_models(models=["gemini", "gpt-5", "grok"])

# Set output directory
fiedler_set_output(output_dir="/mnt/projects/ICCM/results")
```

**Security Note:** Keys stored via `fiedler_set_key` are encrypted by your OS (macOS Keychain, Windows Credential Manager, Linux Secret Service). This is more secure than environment variables.

### Send to Default Models

```python
result = fiedler_send(
    prompt="Review this architecture for consistency"
)
```

### Send with Package

```python
result = fiedler_send(
    prompt="Synthesize requirements from these papers",
    files=[
        "/mnt/projects/ICCM/docs/papers/01_Primary_Paper.md",
        "/mnt/projects/ICCM/docs/papers/02_Training.md"
    ]
)
```

### Override Models for Single Call

```python
result = fiedler_send(
    prompt="Quick test",
    models=["gemini"]  # Override defaults
)
```

## Output Structure

Each `fiedler_send` creates a timestamped directory:

```
/output_dir/
  20250102_143052_a1b2c3d4/
    summary.json           # Run metadata and results
    fiedler.log            # Progress log
    gemini-2.5-pro.md      # Response from Gemini
    gpt-5.md               # Response from GPT-5
    grok-4-0709.md         # Response from Grok
```

## Error Handling

- **Automatic Retries**: 3 attempts with exponential backoff (1s, 2s, 4s)
- **Partial Success**: Returns results from successful models even if some fail
- **Token Warnings**: Warns at 80% of max_tokens
- **Detailed Logging**: All progress logged to `fiedler.log`

## State Management

Configuration persisted at `~/.fiedler/state.yaml`:

```yaml
models:
  - gemini-2.5-pro
  - gpt-5
  - grok-4-0709
output_dir: /mnt/projects/ICCM/results
```

## Architecture

```
fiedler/
├── config/
│   └── models.yaml          # Provider/model registry
├── fiedler/
│   ├── utils/
│   │   ├── logger.py        # Thread-safe logging
│   │   ├── state.py         # Persistent state
│   │   ├── tokens.py        # Token estimation
│   │   └── package.py       # File compilation
│   ├── providers/
│   │   ├── base.py          # Abstract provider
│   │   ├── gemini.py        # Gemini subprocess wrapper
│   │   ├── openai.py        # OpenAI SDK provider
│   │   ├── together.py      # Together.AI provider
│   │   └── xai.py           # xAI subprocess wrapper
│   ├── tools/
│   │   ├── models.py        # fiedler_list_models
│   │   ├── config.py        # Configuration tools
│   │   ├── keys.py          # Secure key management
│   │   └── send.py          # fiedler_send orchestrator
│   └── server.py            # MCP stdio server (runs via `fiedler` command)
├── pyproject.toml
├── docker-compose.yml       # Docker deployment config
└── Dockerfile               # Container image definition
```

**Key Components:**

- **`server.py`** - Stdio-based MCP server for Claude Code integration
  - Installed as `fiedler` console script entry point (see `pyproject.toml`)
  - Reads JSON-RPC requests from stdin
  - Routes to Fiedler tools via MCP protocol
  - Returns JSON responses to stdout
  - Logs to stderr (preserves stdout for MCP protocol)

- **`tools/`** - MCP tool implementations
  - Each tool is a Python function returning structured data
  - Tools are discovered and exposed via MCP `tools/list` method
  - Tool execution happens via MCP `tools/call` method

- **`providers/`** - LLM provider abstractions
  - Unified interface across different APIs
  - Automatic retries with exponential backoff
  - Token management and budget checking

- **Docker deployment** - Production containerization
  - Persistent state via Docker volumes
  - Health check endpoint on port 9010
  - Isolated environment with all dependencies

## License

Part of the ICCM (Intelligent Context and Conversation Management) system.

## Version

1.0.0 - Initial release
