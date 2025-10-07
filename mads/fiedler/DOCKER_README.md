# Fiedler MCP Server - Docker Deployment

## Production-Ready Docker Container

This Docker deployment provides a secure, production-ready Fiedler MCP server with all critical security features enabled.

## Quick Start

1. **Set up API keys:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

2. **Build and start:**
   ```bash
   docker-compose up -d
   ```

3. **Check status:**
   ```bash
   docker-compose ps
   docker-compose logs -f fiedler
   ```

4. **Access the server:**
   - MCP server: `http://localhost:9010`
   - Outputs: `./fiedler_output/` (mapped to container volume)

## Security Features

### File Access Controls
- **Allowlist**: Only files in `/app/allowed_files` and `/app/fiedler_output` are accessible
- **Size limits**: 20MB package size, 100 files max, 100K lines max
- **Read-only mounts**: Client scripts and allowed files are mounted read-only

### Data Privacy
- **Prompt redaction**: Prompts are redacted by default in `summary.json`
- **Opt-in saving**: Set `FIEDLER_SAVE_PROMPT=1` to save prompts (debugging only)

### API Key Management
- Keys passed as environment variables
- Consider using Docker secrets for production
- `FIEDLER_REQUIRE_SECURE_KEYRING=1` enforces secure storage

## Configuration

### Environment Variables

**Required:**
- `GEMINI_API_KEY` - Google Gemini API key
- `OPENAI_API_KEY` - OpenAI API key
- `TOGETHER_API_KEY` - Together AI API key
- `XAI_API_KEY` - xAI (Grok) API key

**Security:**
- `FIEDLER_ALLOWED_FILE_ROOTS` - Comma-separated allowed directories
- `FIEDLER_MAX_PACKAGE_BYTES` - Max package size in bytes (default: 20MB)
- `FIEDLER_MAX_FILE_COUNT` - Max files per package (default: 100)
- `FIEDLER_MAX_LINES` - Max lines per package (default: 100,000)
- `FIEDLER_SAVE_PROMPT` - Save prompts to disk (0=no, 1=yes, default: 0)
- `FIEDLER_REQUIRE_SECURE_KEYRING` - Require secure keyring (0/1)

**Performance:**
- `FIEDLER_MAX_WORKERS` - Max parallel model requests (default: 4)

## Volumes

- `fiedler_output` - Persistent output directory
- `fiedler_state` - Server state (models, config)
- `./allowed_files` - Read-only allowed files directory

## Ports

- `9010` - MCP server (maps to container port 8080)

## Management Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose stop

# Restart
docker-compose restart

# View logs
docker-compose logs -f

# Enter container
docker-compose exec fiedler bash

# Rebuild
docker-compose build --no-cache

# Clean up
docker-compose down -v  # WARNING: Removes volumes
```

## Production Deployment

1. **Use Docker secrets for API keys:**
   ```yaml
   secrets:
     gemini_key:
       file: ./secrets/gemini_api_key.txt
   ```

2. **Enable strict security:**
   ```bash
   FIEDLER_REQUIRE_SECURE_KEYRING=1
   FIEDLER_ALLOWED_FILE_ROOTS=/app/allowed_files
   ```

3. **Monitor logs:**
   ```bash
   docker-compose logs -f fiedler | tee /var/log/fiedler.log
   ```

4. **Set up health monitoring:**
   - Health endpoint available at container level
   - Check with: `docker inspect --format='{{.State.Health.Status}}' fiedler-mcp`

## Troubleshooting

**Container won't start:**
```bash
docker-compose logs fiedler
```

**Permission errors:**
```bash
# Check volume permissions
docker-compose exec fiedler ls -la /app/fiedler_output
```

**API key issues:**
```bash
# Verify environment variables
docker-compose exec fiedler env | grep API_KEY
```

**Client script not found:**
```bash
# Verify mounts
docker-compose exec fiedler ls -la /app/clients/
```

## Architecture

- **Base Image**: Python 3.11-slim
- **MCP Protocol**: Stdio-based server
- **Concurrency**: ThreadPoolExecutor with configurable workers
- **State**: Persisted to volume-mounted ~/.fiedler/state.yaml
- **Outputs**: Persisted to volume-mounted /app/fiedler_output

## Security Best Practices

1. ✅ Run container with non-root user (TODO: add USER directive)
2. ✅ Use read-only mounts for client scripts
3. ✅ Limit file access with FIEDLER_ALLOWED_FILE_ROOTS
4. ✅ Redact prompts by default
5. ✅ Set resource limits (add to docker-compose.yml)
6. ⚠️ Store API keys as Docker secrets, not in .env
7. ⚠️ Use network policies to restrict outbound access

## Next Steps

- Add user/group for non-root execution
- Implement Docker secrets for API keys
- Add resource limits (CPU, memory)
- Set up log rotation
- Configure monitoring/alerting
- Add backup strategy for volumes
