<think>
We are dealing with a scenario where we have a large payload (about 814KB) that we need to pass to an MCP tool. The payload is too large to pass inline. We are using the MCP protocol (which is based on JSON-RPC 2.0). 

Let's break down the questions:

1. **Does MCP protocol support file references/paths as parameters?**
   - The MCP protocol itself (as an extension of JSON-RPC 2.0) does not define a standard way to handle file references. However, it is common for RPC implementations to allow such mechanisms. You would need to check the specific implementation of the MCP tool you are using. Often, in such cases, the RPC method might accept a file path or a handle (like a temporary file) instead of the actual data. Alternatively, the method might be designed to accept a reference (like a URI) to a location (e.g., S3, HTTP, or a shared filesystem) where the payload is stored.

2. **Should we use streaming/chunking for large payloads?**
   - Streaming or chunking is a common approach for handling large data transfers. However, JSON-RPC 2.0 does not natively support streaming. If the payload is too large, it might cause issues (like memory limits, timeouts, etc.). Therefore, if the MCP tool supports it, breaking the payload into chunks and sending multiple requests (with a mechanism to reassemble) is an option. But note that this adds complexity. Alternatively, if the underlying transport supports streaming (like HTTP with chunked transfer encoding), you might use that, but the RPC layer (JSON-RPC) is not designed for that.

3. **What's the standard approach in JSON-RPC 2.0 for >1MB parameters?**
   - JSON-RPC 2.0 does not specify a standard way to handle large parameters. The specification does not set a size limit, but in practice, many implementations have limits (e.g., 1MB to 10MB) to prevent resource exhaustion. For parameters larger than what the system can handle, the common practice is to avoid passing the data inline. Instead, use a reference (like a file path, URL, or a token representing the data stored elsewhere) or break the data into multiple RPC calls (if the method supports it).

4. **Best practice: chunking, file paths, compression, or something else?**
   - The best practice depends on the context. Here are some options:
     - **File References**: If the client and server share a filesystem, you can write the payload to a file and pass the file path. This is efficient and avoids transferring the data over the RPC channel.
     - **External Storage**: Store the payload in an external storage (like S3, HDFS, or a database) and pass a reference (e.g., URI, key) to the RPC method. The server then retrieves the data from that location.
     - **Chunking**: If the RPC method supports it, break the data into chunks and send multiple requests. The server must reassemble the chunks. This can be complex and may require a session or transaction ID to group chunks.
     - **Compression**: Compressing the JSON (e.g., using gzip) can reduce the size, but 814KB compressed might still be too large for inline transfer if the system has a low limit. Also, the server must support decompression.
     - **Streaming**: If the transport protocol (like HTTP) supports streaming, you might stream the request body. However, JSON-RPC 2.0 is typically request-response and not designed for streaming. Some frameworks might allow it, but it's non-standard.

   Given that the operation happens 100s of times and must complete in seconds, the most efficient method would be to avoid transferring the entire payload over the RPC channel if possible. Using a shared filesystem or external storage (with low latency) would be ideal.

5. **This operation happens 100s of times and should complete in seconds - what's the industry-standard solution?**
   - The industry standard for handling large data in RPC is to avoid putting the large data in the RPC message. Instead, use a reference to the data. For example:
     - **Cloud Storage**: Use a cloud storage service (like S3, Google Cloud Storage, or Azure Blob) to upload the data and then pass the object key/URL to the RPC method. The server can then download it. This is scalable and efficient.
     - **Message Queues**: For very high throughput, you might use a message queue (like RabbitMQ, Kafka) to transfer the data asynchronously, but that might not fit the RPC model (which is typically synchronous).
     - **Shared Filesystem**: If both client and server are in the same network and have access to a shared filesystem, writing to a file and passing the path is very efficient.

   Since the requirement is to complete in seconds and the operation is frequent, the key is to minimize the data transfer over the RPC channel. Using a fast, shared storage (like a distributed filesystem or a high-performance object store) is common.

**Conclusion for the specific scenario:**

Given that we are calling `dewey_store_messages_bulk` and the payload is 814KB (which is not extremely large, but might exceed the inline limit of the system), the recommended approach is:

- **Check the MCP tool's documentation**: First, see if the method `dewey_store_messages_bulk` supports an alternative way to accept the data (like a file path or a URI). If it does, use that.

- **If not, extend the method**: If you control the MCP tool, consider extending the method to accept a file path or a reference. Then, the client would write the JSON to a temporary file (or upload to a shared storage) and pass the reference.

- **Compression**: If you must send inline, try compressing the JSON. 814KB might compress to 100-200KB, which might be acceptable. But check if the server supports compressed requests.

- **Chunking**: If the above are not possible, implement chunking. However, this would require changes to both client and server to handle multiple RPC calls for one logical operation.

Given the frequency (100s of times) and the time constraint (seconds), the most robust and efficient solution is to use a shared storage (like a fast object store) and pass the reference.

**Proposed Solution:**

1. Client uploads the JSON payload to a pre-agreed shared storage (e.g., an S3 bucket, a shared NFS, or a database) and obtains a reference (e.g., a file path, a URL, or a unique key).
2. Client calls the MCP tool `dewey_store_messages_bulk` with the reference as a parameter (instead of the entire JSON array).
3. The MCP tool retrieves the payload from the shared storage using the reference, processes it, and then deletes the temporary file (or the client does cleanup later).

This approach minimizes the data sent over RPC and leverages the shared storage for the bulk data transfer, which is optimized for large objects.

**Note on Security and Cleanup**: When using shared storage, ensure proper access controls and a mechanism to clean up the temporary data after processing.
</think>
Based on your scenario of transferring large payloads (e.g., 814KB JSON) to the `dewey_store_messages_bulk` MCP tool, here's a concise analysis and recommendations:

### 1. **MCP Protocol Support for File References**
   - **Yes**, but implementation-specific. Modern RPC/MCP protocols (like gRPC, Thrift, or custom JSON-RPC extensions) often support file references via:
     - **Temporary object storage URIs** (e.g., `s3://bucket/key`, GCS, signed URLs).
     - **Shared filesystem paths** (e.g., `/tmp/file_id`), if client/server share storage.
     - **Content tokens** (e.g., upload ID from a separate transfer service).
   - **Action**: Check your MCP tool's documentation or source code for parameters like `file_uri`, `data_ref`, or `upload_id`. If unsupported, extend the protocol.

### 2. **Streaming/Chunking**
   - **Avoid for JSON-RPC 2.0**. Native JSON-RPC doesn't support streaming. Chunking requires custom session logic (stateful reassembly), adding complexity.
   - **Use if**: Your transport supports streaming (e.g., HTTP/2 with gRPC). For pure JSON-RPC, prefer references.

### 3. **JSON-RPC 2.0 Standard for >1MB Payloads**
   - **No native handling**. JSON-RPC 2.0 has no built-in mechanism for large payloads. Solutions are implementation-specific:
     - **Reference passing**: Replace payloads with file URIs/storage keys.
     - **HTTP extensions**: Use `multipart/form-data` or chunked encoding if over HTTP(S).
     - **Size limits**: Many servers reject >1-10MB requests by default (adjust server limits if needed).

### 4. **Best Practices**
   - **✅ File References (Recommended)**  
     Upload payload to shared storage (S3, Redis, temp FS) → pass reference URI/key → process/delete server-side.  
     *Pros*: Efficient for frequent calls, avoids inline bottlenecks.
   - **🟡 Compression**  
     Gzip JSON (70-90% size reduction). Enable via `Content-Encoding: gzip`.  
     *Use if*: References aren't feasible and network is slow (test latency impact).
   - **❌ Chunking/Streaming**  
     Only use if protocol supports it natively (e.g., gRPC). Avoid for JSON-RPC.
   - **⚠️ Base64 Encoding**  
     Increases size by ~33% — **not recommended**.

### 5. **Industry Standard for High-Throughput (100s of calls/sec)**
   - **File References + Object Storage**  
     1. Client uploads payload to low-latency storage (e.g., in-memory Redis, local SSD FS, or S3).  
     2. Call MCP with `{ "messages_ref": "s3://bucket/12345" }`.  
     3. Server fetches, processes, and deletes data.  
     - **Why?**  
       - Decouples transfer from execution.  
       - Storage systems handle large data efficiently.  
       - Achieves sub-second latency at scale.  
     - **Tools**: MinIO for self-hosted S3, Redis for ephemeral data, or cloud storage.

### Implementation Example
```python
# Client-side
import boto3  # For S3 upload
import requests

# Upload payload to storage
s3 = boto3.client("s3")
s3.put_object(Bucket="dewey-temp", Key="12345.json", Body=json_data)

# Call MCP with reference
rpc_payload = {
    "jsonrpc": "2.0",
    "method": "dewey_store_messages_bulk",
    "params": {"messages_ref": "s3://dewey-temp/12345.json"},
    "id": 1
}
response = requests.post("http://mcp-server", json=rpc_payload)
```

### Key Recommendations
1. **Implement file references** in `dewey_store_messages_bulk` (modify tool if needed).  
2. **Use ephemeral storage** (e.g., Redis/S3 with 5m TTL) for auto-cleanup.  
3. **Benchmark**: Test with 1,000 concurrent requests. Target <500ms E2E latency.  
4. **Fallback**: If references are impossible, compress JSON + increase server max body size.

This approach minimizes RPC overhead, leverages battle-tested storage systems, and scales to 100s of operations/sec.