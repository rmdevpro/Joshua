# Anthropic API Gateway

Reverse proxy gateway for Anthropic API that logs all conversations to Dewey/Winni database.

## Architecture

This gateway implements the **GPT-5 recommended approach** from the triplet consultation:
- No TLS/SSL interception (avoids certificate trust issues)
- Simple HTTP reverse proxy
- Logs sanitized request/response to Dewey
- Works identically on bare metal and containers

## How It Works

1. Claude Code connects to gateway via `ANTHROPIC_BASE_URL=http://anthropic-gateway:8089/v1`
2. Gateway forwards requests to `https://api.anthropic.com`
3. Gateway captures request/response and sanitizes sensitive data
4. Gateway logs conversation to Dewey asynchronously
5. Dewey stores in Winni PostgreSQL database

## Configuration

Environment variables:

- `PORT` - Gateway port (default: 8089)
- `UPSTREAM_URL` - Anthropic API URL (default: https://api.anthropic.com)
- `DEWEY_URL` - Dewey logging endpoint (default: http://192.168.1.210:8080/conversations)
- `REDACT_API_KEYS` - Redact API keys from logs (default: true)

## Usage

### Docker Compose (Recommended)

```bash
cd /mnt/projects/ICCM/claude-container
docker-compose up -d
```

### Standalone

```bash
cd /mnt/projects/ICCM/anthropic-gateway
npm install
DEWEY_URL=http://192.168.1.210:8080/conversations npm start
```

## Testing

Health check:
```bash
curl http://localhost:8089/health
```

Test proxy (with API key):
```bash
curl http://localhost:8089/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}'
```

## Security

- **API Key Redaction**: All `x-api-key`, `authorization`, and `cookie` headers are redacted before logging
- **No Key Storage**: API keys are never persisted, only forwarded to upstream
- **Async Logging**: Logging failures don't block API requests
- **Network Isolation**: Gateway runs on isolated Docker network

## Integration with ICCM

- **KGB**: Complements existing WebSocket logging (KGB handles MCP, Gateway handles HTTPS)
- **Dewey**: Uses existing Dewey API for unified storage
- **Winni**: Logs stored in same PostgreSQL database as MCP conversations
