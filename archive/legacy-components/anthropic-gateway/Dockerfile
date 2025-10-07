# Anthropic API Gateway - Reverse Proxy with Logging
FROM node:22-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --production

# Copy gateway code
COPY . .

# Expose gateway port
EXPOSE 8089

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node healthcheck.js || exit 1

# Run gateway
CMD ["node", "gateway.js"]
