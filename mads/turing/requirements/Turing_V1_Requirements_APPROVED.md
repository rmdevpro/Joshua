# Turing V1 - Secrets Manager Requirements
| **Version:** 1.0 | **Status:** Approved | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Turing V1 is the dedicated secrets management MAD for the ecosystem. It is responsible for the secure storage, retrieval, and lifecycle management of all cryptographic secrets, including API keys, certificates, and other credentials.

**2. Key Features & Functional Requirements**

*   **FR1: Imperator for Guidance:** Integrate an LLM brain into Turing for conversational guidance on secrets management best practices.
*   **FR2: Secure Storage & Retrieval:** Provide a secure, encrypted storage mechanism for secrets. A programmatic interface will allow authorized MADs to retrieve the secrets they need to function.
*   **FR3: Lifecycle Management:** Support operations for managing the lifecycle of secrets, such as key rotation, either on a schedule or upon user request via a conversational interface (`turing_converse`).
*   **FR4: Security and Auditing:**
    *   **Zero-Trust Logging:** Secret values must **never** be exposed in plain text in any conversation log on the Rogers bus.
    *   **Audit Trail:** All secret access events (who accessed what, and when) must be logged to a secure conversation, which can be monitored by McNamara.

**3. Technical & Integration Requirements**

*   **TR1: Encryption:** All secrets must be encrypted at rest using a strong, industry-standard cryptographic method.
*   **TR2: Authorization:** The system must implement a robust, identity-based authorization mechanism to enforce access controls.
*   **TR3: Client Integration:** All MADs that require secrets (e.g., Fiedler, Marco) will be clients of Turing.
*   **TR4: McNamara Integration:** Turing must forward all audit logs to McNamara for security monitoring.

**4. Out of Scope for V1**

*   Complex, dynamic policy-based access control.
*   Hardware Security Module (HSM) integration.

**5. Success Criteria**

*   ✅ MADs can securely and programmatically retrieve the API keys they are authorized to access.
*   ✅ A user can conversationally request the rotation of an API key, and Turing successfully completes the action.
*   ✅ No secret value is ever logged to the Rogers conversation bus.
*   ✅ A complete and accurate audit trail of all secret access is available to McNamara.
