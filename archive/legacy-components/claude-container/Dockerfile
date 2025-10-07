# Containerized Claude Code with MCP Relay
FROM node:22.19.0-bookworm-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code@2.0.5

# Create working directory
WORKDIR /workspace

# Copy MCP relay configuration (will be mounted at runtime)
# We'll use volume mounts for:
# - /root/.config/claude-code/mcp_config.json
# - /workspace (user's working directory)

# Environment variables will be passed at runtime:
# - ANTHROPIC_API_KEY or OAuth config
# - ANTHROPIC_BASE_URL (for gateway)
# - MCP server configurations

# Default command runs Claude Code CLI
ENTRYPOINT ["claude"]
CMD ["--help"]
