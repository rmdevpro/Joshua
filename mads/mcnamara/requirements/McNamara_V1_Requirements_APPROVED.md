# McNamara V1 - Security Operations Coordinator Requirements
| **Version:** 1.0 | **Status:** Approved | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

McNamara V1 is the security specialist MAD for the ecosystem. This version acts as a central point for security operations, providing a conversational interface for security inquiries, performing basic monitoring, and coordinating specialized security eMAD teams for tasks like penetration testing.

**2. Key Features & Functional Requirements**

*   **FR1: Add Imperator:** Integrate an LLM brain into McNamara for conversational security guidance and operations.
*   **FR2: Conversational Interface:** Introduce a tool (`mcnamara_converse`) for users to ask security questions or request security tasks.
    *   *Examples:* "Are there any security anomalies today?" or "I need a penetration test on the new authentication system."
*   **FR3: Basic Security Monitoring:**
    *   Monitor the Rogers conversation bus for security-related events (e.g., messages with a `#security` tag).
    *   Track high-level access patterns across MADs to detect simple anomalies.
    *   Generate alerts by posting messages to a dedicated security conversation.
*   **FR4: Security eMAD Team Coordination:** McNamara must be able to spin up and coordinate ephemeral security teams for specialized tasks, such as a Penetration Testing Team or a Code Security Audit Team.

**3. Technical & Integration Requirements**

*   **TR1: Rogers Integration:** Must be able to monitor messages and participants on the Rogers conversation bus.
*   **TR2: Fiedler Integration:** Must query Fiedler to get recommendations for appropriate LLMs for security eMAD roles.
*   **TR3: eMAD Framework:** Requires the ability to spawn, manage, and terminate security-focused eMADs.

**4. Out of Scope for V1**

*   Automated threat response or remediation.
*   Advanced, deep automated scanning of all MADs and infrastructure.
*   Automated security policy enforcement.

**5. Success Criteria**

*   ✅ A user can ask McNamara security-related questions and receive a helpful response.
*   ✅ McNamara can successfully orchestrate a security task (e.g., a penetration test) by spawning an eMAD team and reporting the results.
*   ✅ McNamara detects basic access anomalies and generates a corresponding alert on the conversation bus.
