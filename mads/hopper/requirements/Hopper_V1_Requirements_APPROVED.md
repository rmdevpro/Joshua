# Hopper V1 - Autonomous Development Coordinator Requirements
| **Version:** 1.0 | **Status:** Approved | **Date:** 2025-10-09 |
| :--- | :--- | :--- |

**1. Overview**

Hopper V1 is an autonomous software engineering MAD that coordinates development projects. V1 implements a **Project Manager (PM)-led workflow**. A user engages Hopper's Imperator with a development goal, which then spawns a dedicated PM eMAD. This PM eMAD orchestrates an entire team of developer eMADs to plan, design, build, test, and deploy the software.

**2. Key Features & Functional Requirements**

*   **FR1: PM-Led Workflow:**
    *   The user initiates a project by making a request to Hopper's main Imperator (e.g., "I need to build a new MAD").
    *   The Imperator gathers initial requirements and then spawns a persistent Project Manager eMAD to lead the project.
*   **FR2: Autonomous Project Management:** The PM eMAD is responsible for the entire development lifecycle:
    *   **Planning:** Creates project structure and issues in Git.
    *   **Design:** Spins up a "consulting team" of eMADs to create design documents.
    *   **Development:** Spins up a "development team" (e.g., Senior and Junior Dev eMADs) to write the code.
    *   **Testing & Deployment:** Manages the team through testing and deployment cycles.
    *   **Documentation:** Updates Git with all code, documentation, and creates a final Pull Request.
*   **FR3: Orchestration, Not Implementation:** The PM eMAD's primary role is to coordinate and manage the specialist eMADs. It does not write production code itself but reviews and directs the work of the dev team.

**3. Technical & Integration Requirements**

*   **TR1: Rogers Conversation Bus:** All communication between the PM and its eMAD team members must occur on the Rogers bus.
*   **TR2: Fiedler Integration:** The PM eMAD must query Fiedler to get recommendations for the best LLMs for specific roles (e.g., Senior Dev, consultant).
*   **TR3: eMAD Framework:** Requires a robust framework for spawning, managing, and terminating ephemeral MADs.
*   **TR4: Git Integration:** Deep integration with a Git provider is required for all project management, code commits, and documentation tasks.
*   **TR5: LLM Client Library:** Requires specialized clients from the library for different roles (e.g., `ProjectManagerClient`, `SeniorDevClient`).

**4. Out of Scope for V1**

*   Fully autonomous architectural decisions (the PM will escalate to the user for guidance).
*   Managing multiple, concurrent development projects.
*   Advanced, automated testing strategies (V1 will focus on basic testing).

**5. Success Criteria**

*   ✅ A user can provide a high-level development request to Hopper.
*   ✅ Hopper successfully spawns a PM eMAD that autonomously assembles a team and manages the project.
*   ✅ A complete, documented, and functional software project is delivered and committed to Git without the user writing any code.
