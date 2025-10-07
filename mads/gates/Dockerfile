FROM node:22-alpine

# Install LibreOffice and dependencies
RUN apk add --no-cache \
    libreoffice \
    libreoffice-writer \
    ttf-liberation \
    && rm -rf /var/cache/apk/*

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm install --omit=dev

# Copy application files
COPY server.js ./

# Create output directory
RUN mkdir -p /app/output && chmod 777 /app/output

# Expose WebSocket port
EXPOSE 8050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8050/health || exit 1

# Start server
CMD ["node", "server.js"]
