Handling large payload transfers in modern Remote Procedure Call (RPC) and Message Communication Protocols (MCP) can be challenging, especially when dealing with payloads greater than 1MB. Let's address your questions step by step.

### 1. Does MCP protocol support file references/paths as parameters?
MCP implementations vary in their specifications, but many modern protocols do support passing file references or paths as a means of transferring larger payloads. However, the specific capabilities depend on the MCP tool you are using. If "dewey_store_messages_bulk" supports it, you could upload your large payload to a temporary storage that the service can access and then pass the file reference to that location as a parameter.

### 2. Should we use streaming/chunking for large payloads?
Yes, streaming or chunking is a common practice for handling large payloads. Instead of sending one massive request, you can split the data into smaller, manageable chunks. This approach reduces memory overhead and can help avoid issues with network timeouts. Each chunk can be sent in a separate request, and you can implement logic on the server-side to recombine these chunks into a single payload.

### 3. What's the standard approach in JSON-RPC 2.0 for >1MB parameters?
JSON-RPC 2.0 doesn't have a built-in mechanism specifically for managing large payloads. However, the general best practices include:
- **Chunking**: Send the data in smaller parts as separate requests.
- **References**: Instead of sending large JSON objects directly, you can upload them to a server or storage service and send the reference or URL as a parameter.
- **Compression**: Consider compressing the data before sending, although this requires server support for decompression.

### 4. Best practice: chunking, file paths, compression, or something else?
The best practice for dealing with large payloads often combines several strategies:
- **Chunking**: Break down large payloads into smaller segments to prevent hitting size limits and mitigate network issues.
- **File Paths / References**: Upload the large JSON payload to a file service (e.g., AWS S3, Google Cloud Storage) and send just the reference or path.
- **Compression**: Compress the payload to reduce its size if network bandwidth is a constraint.

Use chunking for immediate payload handling, and if supported by your protocol, file references can be more efficient for repeated operations.

### 5. This operation happens 100s of times and should complete in seconds - what's the industry-standard solution?
For high volume and speed:
- **Upload large payloads to a temporary file storage**: This will offload the transfer from the request itself and reduce the payload size in the request.
- **Batching requests**: If possible, send multiple chunks in parallel to expedite the transfer.
- **Asynchronous processing**: Use an async workflow where you can track the status of each uploaded chunk and handle any errors or retries without blocking further operations.
- **Optimize network settings and server resources**: Ensure that the server handling these requests is optimized for high throughput and low latency.

By implementing a combination of these strategies, you should be able to efficiently handle large payload transfers while maintaining the performance needed for your operations.