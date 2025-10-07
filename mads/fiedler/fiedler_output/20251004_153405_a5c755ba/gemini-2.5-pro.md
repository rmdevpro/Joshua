Excellent. This is a well-defined design problem. Based on your context and requirements, here are my recommendations for designing "Marco."

### Executive Summary

Marco should be designed as a **robust, stateful service**, not a simple, stateless relay. It will act as a true gateway, managing a persistent browser instance and providing shared access to your entire ICCM system. This approach prioritizes reliability, performance, and long-term maintainability.

---

### 1. Architecture Pattern

**Recommendation: B) Build Marco as a full WebSocket MCP server that manages Playwright internally.**

**Reasoning:**

*   **Aligns with "Gateway" Concept:** A gateway is more than a simple pipe. It's a managed entry point. This pattern allows Marco to handle connection management, potential request queuing, state monitoring (is the browser alive?), and adding its own control logic (e.g., a tool to restart a hung browser session).
*   **Handles Multiple Clients:** The goal is to serve *all* services. A simple 1-to-1 bridge (Option A) would imply only one service could use the browser at a time. A full server can accept connections from Fiedler, Dewey, etc., simultaneously and manage access to the single, shared Playwright resource.
*   **Consistency with Fiedler/Dewey:** You mentioned Fiedler and Dewey are core services. Building Marco as a proper service, rather than a simple utility, follows this established pattern. It will have its own logging, state, and control surface, just like the other major components.
*   **Avoids Unnecessary Complexity:** Option C (separate containers) introduces network overhead and deployment complexity between Marco and Playwright for little gain. Since Playwright is designed to be driven by a parent process via stdio, managing it as an internal subprocess is the most direct and efficient model.

### 2. Code Reuse

**Recommendation: C) Create a shared library for stdio-WebSocket bridging and use it in both Marco and MCP Relay.**

**Reasoning:**

*   **Don't Repeat Yourself (DRY):** This is a core software engineering principle. The logic for bridging stdio to a WebSocket is generic. Creating a shared library (e.g., a private npm package or a git submodule) ensures that any bug fixes, performance improvements, or feature additions to the bridging logic benefit both services automatically.
*   **Maintainability:** Option A (copy-paste) is a recipe for future pain. You will inevitably fix a bug in one place and forget the other, leading to divergent and hard-to-debug behavior.
*   **Clarity of Purpose:** This approach allows the code for Marco and MCP Relay to focus on their specific business logic. Marco's code will be about managing Playwright and browser automation, while the generic plumbing is neatly abstracted away in the shared library.

### 3. Process Management

**Recommendation: A) Launch Playwright on startup, restart if it crashes.**

**Reasoning:**

*   **Low Latency & High Availability:** As a core system gateway, Marco should be "always ready." Launching the browser on startup ensures that the first request from any client is handled immediately, without a multi-second "cold start" delay while a new browser instance spins up (Option B).
*   **Resource Management Simplicity:** A single, long-lived browser process is far more resource-efficient than launching one per client (Option C), which would be prohibitively expensive in terms of RAM and CPU.
*   **State Management:** While a single browser instance means a shared state (cookies, sessions), this is often a desired feature for a system-level tool that performs a sequence of related actions. To handle cases where the browser gets into a bad state, you can implement a special MCP tool within Marco itself, like `<tool>reset_browser_session</tool>`, which would programmatically kill and restart the Playwright subprocess without restarting the entire Marco container. This gives you the best of both worlds: persistence and on-demand reset.

### 4. Configuration

**Recommendation: A combination of A and B.**
*   **A) Environment variables in `docker-compose.yml`** for service-level configuration.
*   **B) Configuration file (`marco/config/browser.yaml`)** for complex browser-specific settings.

**Reasoning:**

*   **Follows 12-Factor App Principles:** Use environment variables for anything that differs between environments (dev, staging, prod), such as ports, logging levels, or credentials. This is the standard for modern containerized applications.
    *   *Example `docker-compose.yml` env vars:* `MARCO_PORT=9030`, `LOG_LEVEL=info`.
*   **Manages Complexity:** Use a version-controlled config file for complex, static configuration that doesn't change between environments. Browser launch arguments, user-agent strings, proxy settings, or viewport sizes are perfect candidates. This is far cleaner than trying to manage a large JSON or YAML structure inside a single environment variable.
    *   *Example `browser.yaml`:*
        ```yaml
        launchOptions:
          headless: true
          args:
            - "--disable-gpu"
            - "--no-sandbox"
        defaultViewport:
          width: 1920
          height: 1080
        ```
*   **Avoids Runtime Insecurity:** Option C (runtime config via MCP) is dangerous. Allowing clients to pass arbitrary launch flags could create security vulnerabilities. Client-provided parameters should be treated as *arguments to tools* (e.g., the URL to navigate to), not as configuration for the service itself.

### 5. Docker Base Image

**Recommendation: A) `mcr.microsoft.com/playwright` (official, includes browsers).**

**Reasoning:**

*   **Reliability and Simplicity:** This is the path of least resistance and greatest stability. The official Playwright image is maintained by the Microsoft team and is guaranteed to have the correct versions of all browsers, codecs, and OS-level dependencies (`libnss3`, `libgbm-dev`, etc.).
*   **Avoids "Dependency Hell":** Trying to install browser dependencies correctly on a generic Linux image (Options B and C) is a common and frustrating source of errors. The official image completely solves this problem for you.
*   **Optimized for Purpose:** The image is built specifically for this use case. While it may be larger than a `-slim` image, the included dependencies are *required*, not optional. The time you save in debugging and maintenance will far outweigh any concerns about image size. Use this unless you have an extremely compelling corporate or security reason to build from a different base.

---

### Final Design Summary for Marco

1.  **Architecture:** A standalone WebSocket MCP server managing an internal Playwright subprocess.
2.  **Code:** Built using a new shared library for stdio-WebSocket bridging, which is also adopted by the existing MCP Relay.
3.  **Process:** Launches a single, persistent Playwright instance on container startup and monitors it, restarting on failure.
4.  **Config:** Uses environment variables for service settings and a mounted YAML file for detailed browser launch options.
5.  **Container:** Based on the official `mcr.microsoft.com/playwright` image for maximum reliability.
