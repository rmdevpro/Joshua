Excellent question. This is a classic architectural problem when RPC systems scale beyond simple, small requests. Let's break down the solutions by answering your specific questions and then providing a recommended best practice.

### Executive Summary

For your use case (814KB payloads, 100s of calls/sec), the industry-standard and most robust solution is **Side-Loading via an Object Store (File Reference Pattern)**. While you should first try **HTTP-level compression**, side-loading is the scalable, long-term answer. Streaming is generally overkill for payloads of this size and adds significant complexity.

---

### 1. Does MCP protocol support file references/paths as parameters?

The MCP protocol itself, like most RPC protocols (including JSON-RPC 2.0), is agnostic about the *meaning* of its parameters. A parameter is just a data type like a string, number, or object.

The protocol doesn't have a special "file path" parameter type that a server would magically understand and fetch. However, you can absolutely implement this pattern at the application level:

*   **Your Parameter:** The `dewey_store_messages_bulk` method would be designed to accept a `string` parameter (e.g., `payload_uri`).
*   **Client's Role:** Before calling the RPC, the client uploads the large JSON payload to a pre-agreed location (like an S3 bucket, a shared network drive, or a temporary file store) and gets a URI or path.
*   **RPC Call:** The client then makes the RPC call with the tiny payload: `dewey_store_messages_bulk(payload_uri="s3://my-bucket/temp-payloads/xyz-123.json")`.
*   **Server's Role:** The server-side implementation of the method receives this string. Its first step is to use a client library (e.g., Boto3 for S3) to fetch the content from the given URI, and then proceed with its business logic.

So, the answer is: **No, not natively in the protocol, but it's a very common and powerful application-level pattern that you implement yourself.**

### 2. Should we use streaming/chunking for large payloads?

Streaming is a valid approach, but it's typically better suited for:
*   **Extremely large payloads:** Gigabytes of data where holding the entire file in memory on either the client or server is not feasible.
*   **Unbounded data:** Live data feeds where the total size isn't known upfront.
*   **Protocols with native support:** gRPC and WebSockets have excellent, first-class support for streaming, making it relatively easy to implement.

For JSON-RPC over HTTP, implementing streaming is complex. You would have to create a stateful, multi-call workflow, for example:
1.  `start_bulk_upload()` -> returns `upload_id`
2.  `append_chunk(upload_id, chunk_data_base64)` (called multiple times)
3.  `finish_bulk_upload(upload_id)` -> triggers the actual processing

This adds significant complexity (state management, error handling for partial uploads, timeouts) and is likely **over-engineering for payloads in the ~1MB range**.

### 3. What's the standard approach in JSON-RPC 2.0 for >1MB parameters?

JSON-RPC 2.0 is just a specification for the message format. It says nothing about transport layers or payload size limits. The limits you are hitting are almost certainly imposed by the transport (e.g., HTTP server's max request body size) or the infrastructure (e.g., load balancer or API gateway configuration).

Therefore, there is no "standard" within the JSON-RPC spec itself. The standard approaches are engineering patterns built *on top* of the protocol:

1.  **Side-Loading (File Reference):** As described in #1. This is the most common pattern for decoupling the control plane (the RPC call) from the data plane (the large payload).
2.  **Increased Server Limits:** The simplest solution is to just increase the max request body size on your web server/proxy. For 1MB, this is often feasible, but it's a temporary fix that doesn't scale well and can open you up to DoS vulnerabilities.
3.  **Compression:** Using standard HTTP `Content-Encoding: gzip` can significantly reduce the payload size on the wire. An 814KB JSON array could easily compress down to 100-200KB, which might be small enough to pass inline.

### 4. Best practice: chunking, file paths, compression, or something else?

Here is a breakdown of the best practices, in order of recommendation for your specific use case.

| Method | Pros | Cons | Best For |
| :--- | :--- | :--- | :--- |
| **1. Compression** | **Easiest to implement** (often just a config flag in client/server). Low overhead. | May not be enough if payloads grow. Doesn't solve server memory issues. | The first thing you should always try. Often sufficient for payloads up to 2-5MB. |
| **2. File Paths (Side-Loading)** | **Most scalable and robust.** Decouples data/control. RPC call is tiny and fast. Avoids all RPC/HTTP size limits. | Higher initial implementation complexity (object store, auth, cleanup). Adds latency (upload/download). | **The industry-standard for this problem.** Perfect for 1MB+ payloads, especially in cloud environments. |
| **3. Streaming/Chunking** | **Lowest memory footprint.** Ideal for massive or unbounded data. | **Very high complexity** over HTTP/JSON-RPC. Stateful and harder to manage. | Truly massive files (>100MB), live data streams. Generally not recommended for your use case. |
| **4. Use a Binary Protocol** | Highly efficient (e.g., gRPC, Thrift). Often have built-in streaming. | Requires changing your entire RPC stack, which may not be an option. | Greenfield projects or when performance is the absolute top priority and you can dictate the stack. |

### 5. This operation happens 100s of times and should complete in seconds - what's the industry-standard solution?

Given your constraints of high frequency and low latency, here is the recommended, industry-standard approach:

**Recommended Solution: Side-Loading via a Cloud Object Store (e.g., S3, GCS, Azure Blob)**

This pattern is purpose-built for your exact scenario and is used by countless large-scale systems.

**Workflow:**
1.  **Client:**
    *   Serializes the 599 messages into an 814KB JSON string.
    *   **Compresses this JSON using gzip** (e.g., `payload.json.gz`). This reduces upload/download time and storage cost.
    *   Uploads the compressed file to a dedicated object store bucket (e.g., `s3://dewey-ingest-bucket/unique-id.json.gz`). The key should be unique (e.g., a UUID).
    *   Makes the MCP call: `dewey_store_messages_bulk(payload_uri="s3://dewey-ingest-bucket/unique-id.json.gz")`.

2.  **Server (`dewey_store_messages_bulk` implementation):**
    *   Receives the S3 URI.
    *   Uses the cloud SDK to download the object `unique-id.json.gz` into memory.
    *   Decompresses the gzip stream.
    *   Deserializes the JSON and processes the messages.
    *   (Optional but recommended) Deletes the object from S3 to clean up. You can also set up lifecycle policies on the bucket to auto-delete objects after 24 hours.

**Why this is the best fit:**
*   **Performance:** Your RPC call itself becomes instantaneous. The latency is shifted to the object store transfer. If your client, server, and S3 bucket are all in the same cloud region (e.g., `us-east-1`), this transfer is incredibly fast, often taking only milliseconds.
*   **Scalability:** Your RPC server is no longer burdened with handling large request bodies. It just handles tiny, fast control messages. You are offloading the heavy lifting to a service (S3) designed for massive scale.
*   **Robustness:** This pattern is resilient. If the data processing fails, you still have the original payload in S3 and can retry the RPC call with the same URI without the client needing to re-upload.
*   **Security:** You can use pre-signed URLs to give clients temporary, secure upload access to the bucket without sharing credentials.
