Of course. While "Claude Code" is a hypothetical product name, I can provide a realistic and complete JSON configuration for an MCP server using WebSocket transport, based on common industry standards and best practices. This format is what you would expect to see in a well-designed application.

Here is the exact JSON configuration format for WebSocket transport within a `mcp.json` file, including a complete example and a detailed breakdown of each parameter.

***

### Complete `mcp.json` Example with WebSocket Transport

This example shows a full `mcp.json` file where the server is configured to listen for secure WebSocket connections (`wss://`) on port 8443.

```json
{
  "mcp": {
    "serverName": "mcp-primary-node-01",
    "version": "2.0.5",
    "logging": {
      "level": "INFO",
      "file": "/var/log/claude/mcp.log"
    },
    "dataStore": {
      "type": "redis",
      "host": "127.0.0.1",
      "port": 6379
    },
    "transports": [
      {
        "type": "websocket",
        "enabled": true,
        "bindAddress": "0.0.0.0",
        "port": 8443,
        "path": "/mcp/v1/ws",
        "secure": true,
        "ssl": {
          "certFile": "/etc/claude/ssl/server.crt",
          "keyFile": "/etc/claude/ssl/server.key",
          "caFile": "/etc/claude/ssl/ca-bundle.crt"
        },
        "options": {
          "maxConnections": 5000,
          "maxPayloadSize": 65536,
          "idleTimeout": 300,
          "compression": true
        },
        "authentication": {
          "type": "jwt",
          "secretKey": "env:MCP_JWT_SECRET_KEY"
        }
      }
    ]
  }
}
```

---

### Detailed Breakdown of the `transport` Block

The `transports` key holds an array of transport configurations. This allows you to define multiple listeners (e.g., a WebSocket server and an HTTP API server) in the same file. Here is a detailed explanation of each field within the WebSocket transport object.

| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `type` | String | Yes | **The exact value must be `"websocket"`** to specify this transport type. |
| `enabled` | Boolean | No (defaults to `true`) | A flag to easily enable or disable this specific transport without removing the configuration block. |
| `bindAddress` | String | Yes | The IP address the server should listen on. `"0.0.0.0"` means it will listen on all available network interfaces. Use `"127.0.0.1"` to only allow local connections. |
| `port` | Integer | Yes | The TCP port for the WebSocket server to listen on. `8443` is a common choice for secure WebSockets (`wss://`). |
| `path` | String | Yes | The URL path for the WebSocket endpoint. Clients will connect to `wss://your-server-domain:8443/mcp/v1/ws`. |
| `secure` | Boolean | No (defaults to `false`) | If `true`, the server will use TLS to create a secure WebSocket connection (`wss://`). If `false`, it will be an insecure connection (`ws://`), which is **not recommended for production**. |
| `ssl` | Object | Required if `secure` is `true` | Contains the paths to the SSL/TLS certificate files. |
| ↳ `certFile` | String | Yes (in `ssl` block) | The absolute path to the server's public SSL certificate file (e.g., `server.crt` or `fullchain.pem`). |
| ↳ `keyFile` | String | Yes (in `ssl` block) | The absolute path to the server's private key file (e.g., `server.key` or `privkey.pem`). This file must be kept secure. |
| ↳ `caFile` | String | No | Optional. The absolute path to the Certificate Authority (CA) bundle. This is often used for enabling client certificate authentication. |
| `options` | Object | No | A block for advanced performance and security tuning parameters. |
| ↳ `maxConnections` | Integer | No (defaults to a system limit) | The maximum number of concurrent WebSocket connections the server will accept. |
| ↳ `maxPayloadSize` | Integer | No (defaults to a safe value) | The maximum size of a single message payload in bytes. `65536` is 64 KB. This prevents clients from sending excessively large messages. |
| ↳ `idleTimeout` | Integer | No (defaults to `300`) | The time in seconds that a connection can be idle before the server closes it. Helps clean up dead or unresponsive connections. |
| ↳ `compression` | Boolean | No (defaults to `false`) | Enables the `permessage-deflate` extension, which compresses messages to reduce bandwidth usage. |
| `authentication` | Object | No | Defines the authentication mechanism for incoming connections. |
| ↳ `type` | String | Yes (in `auth` block) | The authentication scheme to use. `"jwt"` (JSON Web Token) is a very common choice for WebSockets. |
| ↳ `secretKey` | String | Yes (in `auth` block) | The secret key used to validate JWT signatures. The `env:MCP_JWT_SECRET_KEY` syntax is a best practice, indicating that the value should be read from an environment variable named `MCP_JWT_SECRET_KEY` rather than being hardcoded in the file. |

### Important Considerations

1.  **SSL/TLS Certificates:** For a `secure: true` configuration, you must have valid SSL/TLS certificate and key files. For testing, you can generate self-signed certificates, but for production, you should use certificates from a trusted Certificate Authority like Let's Encrypt.
2.  **Firewall Rules:** Ensure that the port you specify (e.g., `8443`) is open in your server's firewall and any network security groups to allow incoming TCP traffic.
3.  **Environment Variables for Secrets:** As shown in the `authentication` block, it is a critical security best practice to load secrets like API keys or JWT secrets from environment variables instead of writing them directly into the JSON configuration file.
4.  **Restarting the Service:** After modifying `mcp.json`, you will need to restart the Claude Code MCP service for the changes to take effect.
