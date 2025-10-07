Designing your containerized service "Marco" requires careful consideration of both architecture and implementation details. Below are the recommendations for each of your design questions:

### 1. **Architecture Pattern**
**Recommendation: B) Build Marco as a full WebSocket MCP server that manages Playwright internally.**

**Reasoning:**
Creating Marco as a full WebSocket MCP server allows it to offer browser automation directly to clients without relying on additional layers presenting potential performance bottlenecks. This encapsulation of Playwright's logic enables better management of state, better error handling, and specific optimizations tailored to the use cases you’re targeting. It also aligns well with your goal of making services available not just to Claude but to the whole ICCM ecosystem.

### 2. **Code Reuse**
**Recommendation: C) Create a shared library for stdio-WebSocket bridging and use it in both.**

**Reasoning:**
By creating a shared library, you not only promote code reuse and reduce duplicative work but also ensure that any improvements to the bridging logic can be consistently applied across multiple projects (Marco and MCP Relay). This leverages the existing functionality of MCP Relay while allowing Marco to focus specifically on the nuances of browser automation without unnecessary complexity.

### 3. **Process Management**
**Recommendation: A) Launch Playwright on startup, restart if it crashes.**

**Reasoning:**
Launching Playwright on startup provides a single, persistent instance that serves multiple clients, which generally leads to better resource management and lower latency in handling requests. Also, process status can be managed effectively, as you can implement restart logic to handle unexpected crashes. This solution balances resource usage and responsiveness, particularly important in an automation context.

### 4. **Configuration**
**Recommendation: A) Environment variables in docker-compose.yml.**

**Reasoning:**
Using environment variables in your Docker configuration allows for flexible and easy configuration management without needing to modify internal files. This approach is also standard and consistent with how services are managed in container orchestrations. It simplifies deployment and scaling processes as configuration can be easily updated or injected at runtime. 

### 5. **Docker Base Image**
**Recommendation: A) mcr.microsoft.com/playwright (official, includes browsers).**

**Reasoning:**
The official Playwright base image provides a quick and efficient start, as it is configured with all necessary dependencies, including various browsers and their corresponding drivers. This minimizes setup time and reduces the risk of errors during manual installations. It also ensures that you have a correctly configured environment for utilizing Playwright right out of the box. Using an official image maintains consistency with other developers' setups and aligns with Playwright's recommendations.

### Summary:
Following the recommendations above should provide a cohesive and efficient architecture for Marco as an internet gateway for browser automation within your ICCM system. Prioritizing a robust design with a focus on scalability and maintainability will serve you well as your system evolves.