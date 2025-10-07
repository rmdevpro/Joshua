REST + JSON
- Advantages: Ubiquitous and simple; excellent HTTP semantics (status, caching, proxies, observability) and human-readable payloads.
- Disadvantages: Over/under-fetching and chatty calls between services; weak contracts and versioning pain (no enforced compatibility).
- Best use case: Public/external CRUD APIs and browser/mobile consumption where cacheability and broad compatibility matter.

gRPC + Protocol Buffers
- Advantages: High performance with small binary payloads and low latency over HTTP/2; strong typed schemas with cross-language code generation.
- Disadvantages: Limited native browser support (often requires a REST/JSON gateway); harder debugging/observability (binary payloads) and steeper learning curve.
- Best use case: Internal service-to-service RPC where throughput, latency, and streaming are critical; high-scale polyglot backends.

GraphQL
- Advantages: Client-driven queries minimize over/under-fetching; single endpoint and unified schema enable rapid product iteration and cross-service composition.
- Disadvantages: Server complexity (query planning, N+1, query cost control); coarse-grained HTTP caching and nuanced authorization/rate limiting per field.
- Best use case: Aggregation/BFF layer for diverse clients (web/mobile) needing tailored data from many services and fast-evolving UI needs.

Rule of thumb
- Choose REST when simplicity, interoperability, and caching for resource-oriented APIs are priorities.
- Choose gRPC for internal microservice meshes needing strong contracts, low latency, and streaming.
- Choose GraphQL when optimizing client experiences and aggregating many backends behind a flexible schema.