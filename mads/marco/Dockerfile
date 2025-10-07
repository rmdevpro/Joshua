# Marco Internet Gateway - Dockerfile
# Based on official Microsoft Playwright image for browser automation

FROM mcr.microsoft.com/playwright:v1.43.0-jammy

# Set working directory
WORKDIR /home/pwuser/app

# Copy package files (as root for installation)
USER root
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --omit=dev

# Copy application code
COPY . .

# Set ownership to non-root user
RUN chown -R pwuser:pwuser /home/pwuser/app

# Switch to non-root user for runtime (security requirement)
USER pwuser

# Expose port for WebSocket MCP + HTTP health check
EXPOSE 8030

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:8030/health', (r) => { process.exit(r.statusCode === 200 ? 0 : 1); }).on('error', () => process.exit(1));"

# Start the server
CMD ["node", "server.js"]
