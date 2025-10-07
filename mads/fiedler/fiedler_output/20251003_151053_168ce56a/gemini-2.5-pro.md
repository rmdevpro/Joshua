Excellent. Based on the detailed `BUG_TRACKING.md`, here is a breakdown of the next diagnostic steps if Attempt #5 (`ws://127.0.0.1:9010`) fails, along with the reasoning behind them.

### Most Likely Reasons `127.0.0.1` Would Fail if `localhost` Failed

While often interchangeable, `localhost` and `127.0.0.1` can behave differently in specific scenarios, which is why testing both is a standard diagnostic step. If `127.0.0.1` also fails, it strongly suggests the problem is not a simple name resolution issue. The most likely reasons are:

1.  **Network Isolation (Still the Prime Suspect):** The core issue identified by the triplets remains the most probable cause. The "bare metal" Claude Code process and the Docker container environment are not on the same network loopback. Traffic sent to `127.0.0.1` from the host is not being correctly routed to the port published by the Docker container.
2.  **Host Firewall or Security Software:** A firewall (like `ufw` on Linux, Windows Defender Firewall, or third-party security software) could be blocking the connection from the Claude Code application to port 9010, even on the loopback interface.
3.  **Application-Level Issue:** There might be an issue within Claude Code itself—a networking library bug, a proxy configuration it's unexpectedly using, or a subtle configuration override—that prevents it from establishing any local WebSocket connections, regardless of the address.

---

### Next Diagnostic Steps (If 127.0.0.1 Fails)

Here is the recommended plan, moving from the most likely solutions to more in-depth diagnostics.

#### **Step 1: Immediate Verification (Crucial First Step)**

Before trying a new URL, we must gather data on *how* the `127.0.0.1` attempt failed.

1.  **Check Claude Code Debug Logs:** This is your highest priority. The application's own logs are the most direct source of truth. Look for errors like:
    *   `Connection refused`: The OS is actively rejecting the connection. This points to the Fiedler container not listening correctly or a firewall.
    *   `Connection timed out`: The request is being sent, but nothing is responding. This strongly suggests a network routing/namespace issue where the packets are going into a void.
    *   `Name or service not known`: Unlikely for an IP, but confirms a fundamental networking stack issue.

2.  **Check Fiedler Container Logs in Real-Time:** While Claude Code is starting up, monitor the Fiedler logs.
    ```bash
    docker logs -f fiedler-mcp
    ```
    If you see **no connection attempts at all**, it confirms the traffic from Claude Code is not reaching the container. This makes a network isolation or host-side blocking issue much more likely than a problem with Fiedler itself.

#### **Step 2: Try `host.docker.internal` (The Canonical Docker Solution)**

This is the next logical URL to try.

*   **Action:** Update the URL in both config files to `ws://host.docker.internal:9010`.
*   **Why:** `host.docker.internal` is a special DNS name that Docker provides for containers to resolve the IP address of the host machine. It is the officially recommended way to handle this exact scenario (a container needing to connect back to a service running on the host, or in this case, a host process connecting to a container's published port).
*   **Caveat:** This works out-of-the-box on Docker Desktop (Windows/Mac). On Linux, it may require a specific Docker version or an `extra_hosts` entry in your Docker Compose file, but it is the correct architectural pattern to attempt.

#### **Step 3: A Different Approach - Isolate the Problem with `wscat`**

If `host.docker.internal` also fails, we must stop changing the Claude Code config and prove that the WebSocket endpoint is accessible from the host *at all*.

*   **Action:** Install a command-line WebSocket client like `wscat` and run it from your bare-metal terminal (the same environment as Claude Code).
    ```bash
    # If you don't have it, install via npm
    # npm install -g wscat

    # Test the connection
    wscat -c ws://127.0.0.1:9010
    ```
*   **Interpreting the Results:**
    *   **If `wscat` connects successfully:** The problem is **100% isolated to the Claude Code application**. The network, Docker, and the Fiedler container are all working correctly. The focus must shift entirely to Claude Code's internal behavior (proxy settings, library versions, permissions, etc.).
    *   **If `wscat` fails with the same error:** The problem is **external to Claude Code**. It's a lower-level issue with Docker networking, a host firewall, or another system process interfering with the connection.

#### **Step 4: Use the Host's LAN IP Address**

This is a final check to bypass any loopback/localhost resolution quirks.

*   **Action:** Find your machine's actual network IP (e.g., `192.168.1.54`) and use that in the config: `ws://192.168.1.54:9010`.
*   **Why:** This forces the connection to go through the standard network stack. If this works and the others didn't, it points to a very strange configuration in the host's loopback interface or DNS resolution policies. If it fails, it reinforces the likelihood of a firewall issue.

---

### Summary Plan

| Step | Action                                                       | Primary Question Answered                                                                 |
| :--- | :----------------------------------------------------------- | :---------------------------------------------------------------------------------------- |
| **0**  | **Test `ws://127.0.0.1:9010` (Current Attempt)**             | Is the issue a simple `localhost` (IPv6 vs IPv4) name resolution problem?                 |
| **1**  | **Check Claude Code & Fiedler logs**                         | Is traffic being sent but rejected, or not sent at all? What is the specific error?       |
| **2**  | **Try `ws://host.docker.internal:9010`**                     | Can Docker's built-in host DNS bridge the network gap between the host and container?     |
| **3**  | **Use `wscat -c ws://127.0.0.1:9010`**                       | Is the WebSocket endpoint accessible from the host *outside* of the Claude Code application? |
| **4**  | **Try `ws://<HOST_LAN_IP>:9010`**                            | Is there a fundamental networking or firewall issue blocking the port?                    |

Start with Step 1 to analyze the failure of the current attempt. Based on those logs, proceed methodically through the subsequent steps. The `wscat` test (Step 3) is the most powerful diagnostic as it will definitively isolate the problem to either Claude Code or the underlying system/network configuration.
