# Paper 00: The MAD Ecosystem - Agent Assembly
**A Master Document from the Council of Elders**

---
**Version:** 2.0
**Date:** 2025-10-06
**Status:** MASTER
**Repository:** Joshua (MAD ecosystem)
**Authored By:** Council of Elders (GPT-5, Claude Opus 4, Council Synthesizer)
**Prerequisites:** ICCM Paper 00, IDE Paper 00
---

## Executive Summary

This paper, MAD Paper 00 v2.0, presents the definitive architecture for the Multipurpose Agentic Duo (MAD) ecosystem. It supersedes all previous versions and establishes **MAD as the Agent Assembly discipline**, the crucial third pillar in a foundational trinity of intelligent system engineering. This trinity, essential for building transparent, auditable, and controllable AI agents, consists of:

1.  **ICCM (Intelligent Context Configuration Management):** The discipline of Context Engineering, which produces the Context Engineering Transformer (CET) component.
2.  **IDE (Intelligent Decision Engineering):** The discipline of Decision Engineering, which produces the Rules Engine and Decision Engineering Recommender (DER) components.
3.  **MAD (Multipurpose Agentic Duo):** The discipline of Agent Assembly, which integrates components from ICCM and IDE, contributes the State Manager and Doing Engine, and assembles them into complete, functional agents.

The core MAD innovation remains the formal separation of cognition (**Thinking Engine**) from execution (**Doing Engine**). This paper provides the complete specification for a MAD agent's Thinking Engine, now understood as a composite of four distinct components from the three disciplines:

-   **Thinking Engine = CET (from ICCM) + Rules Engine (from IDE) + DER (from IDE) + State Manager (from MAD)**

This architecture distinguishes between **Half-MADs**, which provide specialized capabilities (e.g., Fiedler's LLM Orchestra) to the ecosystem via structured **conversations**, and **Full MADs** (e.g., Hopper, Grace), which are complete autonomous agents implementing the full Thinking and Doing Engine architecture.

This document assumes the reader is familiar with ICCM Paper 00 and IDE Paper 00. Its primary focus is to detail the principles and patterns of **agent assembly**: how to integrate the CET, Rules Engine, and DER with the MAD-native State Manager and Doing Engine to construct sophisticated, reliable agents. We present an updated 14-paper hierarchical structure for the MAD discipline, an implementation roadmap, and revised research questions that reflect this corrected and clarified understanding of the ecosystem.

---

### **Table of Contents**

1.  Introduction: The MAD Ecosystem
2.  Theoretical Foundation
3.  Complete MAD Architecture
4.  Hierarchical Paper Structure
5.  Implementation Roadmap
6.  Success Metrics
7.  Relationship to ICCM and IDE
8.  Half-MAD Specifications
9.  Publication Strategy
10. Research Questions
11. Conclusion
12. Appendix: Terminology Reference

---

## 1. Introduction: The MAD Ecosystem

### 1.1 What is the MAD Ecosystem?

The Multipurpose Agentic Duo (MAD) ecosystem provides a cognitive architecture and an engineering discipline for building advanced AI agents. The central tenet of the MAD philosophy is the formal, architectural separation of **Thinking** (cognition, decision-making, reasoning) from **Doing** (execution, interaction, action). This dual-engine design is the key innovation that enables the construction of agents that are transparent, auditable, controllable, and robust.

This paper clarifies the role of the MAD discipline itself. **MAD is the discipline of Agent Assembly.** It is not an infrastructure provider but the final integrator that consumes components from its sibling disciplines—ICCM and IDE—to produce complete agents. The MAD ecosystem, therefore, is the collection of principles, components, protocols, and agents (both Half and Full) that collectively enable this sophisticated assembly process.

### 1.2 The Trinity of Disciplines

The construction of a complete MAD agent is predicated on a trinity of specialized engineering disciplines. Each discipline is responsible for a distinct aspect of the agent's cognitive and functional lifecycle, producing well-defined components that MAD assembles.

1.  **ICCM (Intelligent Context Configuration Management): The Discipline of Context Engineering**
    -   **Repository:** ICCM
    -   **Focus:** How to transform raw, unstructured input into optimized, decision-ready context.
    -   **Primary Output:** The **CET (Context Engineering Transformer)**, the first component of the Thinking Engine.
    -   **Governing Document:** ICCM Paper 00.

2.  **IDE (Intelligent Decision Engineering): The Discipline of Decision Engineering**
    -   **Repository:** Joshua/IDE
    -   **Focus:** How to make transparent, auditable, and robust decisions using a hybrid of deterministic rules and probabilistic synthesis.
    -   **Primary Outputs:** The **Rules Engine** and the **DER (Decision Engineering Recommender)**, the second and third components of the Thinking Engine.
    -   **Governing Document:** IDE Paper 00.

3.  **MAD (Multipurpose Agentic Duo): The Discipline of Agent Assembly**
    -   **Repository:** Joshua/MAD
    -   **Focus:** How to assemble components from ICCM and IDE with MAD-native components to create complete, stateful agents.
    -   **Primary Outputs:** The **State Manager** (the fourth Thinking Engine component), the **Doing Engine**, and complete agent implementations (e.g., Hopper, Grace).
    -   **Governing Document:** This paper, MAD Paper 00.

The relationship between these disciplines is hierarchical and compositional:

```
ICCM Paper 00 (Defines CET) ──────────┐
                                      ├─> MAD Paper 00 (Assembles the Agent)
IDE Paper 00 (Defines Rules/DER) ─────┘
```

MAD Paper 00 is therefore the capstone document that builds upon the foundational work of ICCM and IDE, providing the architectural blueprint for integration.

### 1.3 Why Dual-Engine Architecture Matters

The separation of the Thinking Engine from the Doing Engine is a deliberate design choice rooted in decades of cognitive science (e.g., SOAR, ACT-R) and modern software engineering principles. This separation provides profound advantages over monolithic agent architectures:

-   **Testability:** The Thinking Engine can be tested in isolation by providing simulated context and verifying its decisions, without invoking real-world side effects. The Doing Engine can be tested with mock decisions to ensure its execution logic is sound.
-   **Auditability:** A clean, immutable boundary exists between a decision and its execution. Every decision produced by the Thinking Engine can be logged, traced, and reviewed, providing an unambiguous audit trail.
-   **Safety and Controllability:** The Doing Engine can be designed with its own safeguards, acting as a final check before execution. High-stakes decisions can require human-in-the-loop approval at the boundary between the two engines.
-   **Composability and Reusability:** A single, well-defined Thinking Engine can be paired with multiple, domain-specific Doing Engines. For example, Hopper's Thinking Engine could be paired with a web development Doing Engine to create a new agent, reusing the core cognitive components.

The successful implementation of the Hopper (autonomous development) and Grace (intelligent UI) agents serves as real-world validation of this architectural paradigm.

### 1.4 Half-MADs vs. Full MADs

The MAD ecosystem comprises two classes of agents, distinguished by their architectural completeness and purpose.

**Half-MADs:**
A Half-MAD is an agent with a minimal or incomplete Thinking Engine, designed to provide a specialized, well-defined **capability** to the rest of the ecosystem. They are the functional building blocks that Full MADs leverage.

-   **Purpose:** To encapsulate a complex function and expose it as a capability accessible via conversations.
-   **Communication:** All interactions with Half-MADs occur through the **MCP (Model Context Protocol)**, ensuring structured, auditable conversations.
-   **Examples:**
    -   **Fiedler:** Provides the LLM Orchestra capability (multi-model consultation).
    -   **Dewey:** Provides persistent conversation storage and retrieval capabilities.
    -   **Godot:** Provides real-time logging and tracing capabilities.
    -   **Marco:** Provides MCP conversation proxying and routing capabilities.
    -   **Horace:** Provides file cataloging and versioning capabilities.
    -   **Gates:** Provides document generation capabilities (e.g., Markdown to ODT).
    -   **Playfair:** Provides diagram generation capabilities (e.g., Mermaid, Graphviz).

**Full MADs:**
A Full MAD is a complete agent featuring a fully implemented Thinking Engine (CET + Rules Engine + DER + State Manager) and a domain-specific Doing Engine. These are the autonomous agents capable of performing complex, multi-step tasks.

-   **Purpose:** To act as autonomous problem-solvers within a specific domain.
-   **Architecture:** Implements the complete dual-engine architecture defined in this paper.
-   **Communication:** Engages in conversations with Half-MADs to invoke their capabilities as needed during its cognitive or execution cycles.
-   **Examples:**
    -   **Hopper:** An autonomous software development agent.
    -   **Grace:** An intelligent user interface agent for complex systems.

This distinction is crucial: Half-MADs are not "infrastructure" in the traditional sense; they are specialized agents participating in a collaborative, conversation-driven ecosystem.

### 1.5 Document Organization

This paper is structured to guide the reader through the principles of agent assembly, assuming prior review of ICCM Paper 00 and IDE Paper 00.

-   **Section 2 (Theoretical Foundation):** Details the complete four-component Thinking Engine architecture and the role of the Doing Engine.
-   **Section 3 (Complete MAD Architecture):** Provides the full architectural blueprint, specifying the State Manager and defining the integration boundaries between disciplines.
-   **Section 4 (Hierarchical Paper Structure):** Outlines the 14 subsequent papers that will elaborate on the MAD discipline.
-   **Subsequent Sections:** Cover the implementation roadmap, success metrics, Half-MAD specifications, and key research questions for the discipline.

## 2. Theoretical Foundation

### 2.1 Cognitive Architecture Principles

The MAD architecture draws inspiration from the two-system model of human cognition, distinguishing between fast, intuitive "System 1" thinking and slow, deliberate "System 2" reasoning. Our architecture maps this concept onto a computational framework:

-   **System 1 (Fast):** Represented by the deterministic **Rules Engine**, which handles known, policy-driven scenarios quickly and efficiently.
-   **System 2 (Slow):** Represented by the **DER**, which engages in complex synthesis for ambiguous or novel situations, often consulting the LLM Orchestra for creative or probabilistic reasoning.

By structuring the cognitive flow through these distinct components (CET → Rules Engine → DER), we create a system that prioritizes efficiency and safety while retaining the power of generative models for tasks that require it. This structured reasoning provides clear advantages in transparency and predictability over monolithic, end-to-end LLM-based architectures.

### 2.2 The Thinking Engine: Complete Specification

The MAD Thinking Engine is the cognitive core of a Full MAD. It is a composite system assembled from four distinct components, sourced from the three foundational disciplines. Its sole purpose is to transform input context into a single, actionable, and auditable decision.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                             THINKING ENGINE                               │
│                (Assembled by the MAD Discipline)                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  1. CET (Context Engineering Transformer)                                 │
│     - Discipline: ICCM (Context Engineering)                              │
│     - Function: Transforms raw input into structured, decision-ready      │
│       context. Performs classification, routing, and optimization.        │
│     - Specification: ICCM Paper 00                                        │
│                                                                           │
│  2. Rules Engine                                                          │
│     - Discipline: IDE (Decision Engineering)                              │
│     - Function: Applies deterministic rules and policies for known        │
│       scenarios. Enforces safety guardrails and handles clear-cut cases.  │
│     - Specification: IDE Paper 00                                         │
│                                                                           │
│  3. DER (Decision Engineering Recommender)                                │
│     - Discipline: IDE (Decision Engineering)                              │
│     - Function: Synthesizes recommendations for complex or ambiguous      │
│       scenarios. Provides confidence scores and reasoning traces.         │
│     - May initiate conversation with Fiedler MAD for LLM Orchestra.       │
│     - Specification: IDE Paper 00                                         │
│                                                                           │
│  4. State Manager                                                         │
│     - Discipline: MAD (Agent Assembly)                                    │
│     - Function: Manages the agent's memory and world model, providing     │
│       stateful context to all other components.                           │
│     - Specification: This Paper (MAD Paper 00)                            │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

**Cognitive Flow and Component Interactions:**

1.  **Input Arrival:** An external event or internal trigger provides raw input to the Thinking Engine.
2.  **Contextualization (CET):** The CET consumes the raw input, consults the State Manager for relevant memory, and produces a structured, optimized context object.
3.  **Deterministic Evaluation (Rules Engine):** The structured context is passed to the Rules Engine. If a high-confidence rule matches, a decision is generated immediately, bypassing the DER.
4.  **Complex Synthesis (DER):** If no rule fires, or if the scenario is explicitly routed for synthesis, the context is passed to the DER. The DER analyzes the situation, potentially initiating a conversation with the Fiedler Half-MAD to consult the LLM Orchestra, and synthesizes a final decision package with a confidence score and reasoning.
5.  **State Management (State Manager):** Throughout this process, the State Manager provides access to episodic, semantic, and working memory for all components and records the final decision for posterity.
6.  **Decision Output:** The final decision package is passed to the Doing Engine for execution.

### 2.3 The Doing Engine: Domain-Specific Execution

The Doing Engine is the agent's interface to the world. It is a domain-specific component responsible for translating the abstract, structured decisions from the Thinking Engine into concrete actions.

**Key Characteristics:**

-   **Decoupled:** It is completely decoupled from the Thinking Engine, communicating only via the standardized decision package format.
-   **Domain-Specific:** The implementation of a Doing Engine is tailored to its operational environment. Hopper's Doing Engine operates on a file system and executes shell commands, while Grace's interacts with web frameworks and APIs.
-   **Safeguarded:** It contains its own set of safeguards, sanity checks, and error-handling routines to ensure that executed actions are safe and reversible where possible.
-   **Feedback Loop:** After executing an action, it reports the outcome (success, failure, output) back to the State Manager, enabling the agent to learn from its experiences.
-   **Swappable:** The same Thinking Engine can be paired with different Doing Engines, allowing for the creation of new agents with shared cognitive abilities but different execution domains.

**Common Doing Engine Patterns:**

-   **Tool Execution:** Interacting with command-line interfaces, scripts, and binaries (e.g., Hopper).
-   **API Orchestration:** Making calls to external or internal APIs and managing their responses (e.g., Grace).
-   **Human Interaction:** Rendering user interfaces, processing user input, and managing dialogues.
-   **Robotic Control:** Sending commands to physical actuators and processing sensor data.

Like the Thinking Engine, a Doing Engine may also initiate conversations with Half-MADs, such as consulting Fiedler for on-the-fly code generation or Playfair for creating a visual representation of its plan.

### 2.4 LLM Orchestra as a Universal Capability

A critical clarification in v2.0 is the nature of the LLM Orchestra. It is not an intrinsic part of any engine but rather a **universal capability provided by the Fiedler Half-MAD**.

-   **Provider:** Fiedler MAD.
-   **Capability:** Multi-model consultation (e.g., querying GPT-5, Claude Opus 4, Gemini 2.5 Pro simultaneously) with structured synthesis.
-   **Access:** Any component in the MAD ecosystem (within a Thinking Engine, a Doing Engine, or another Half-MAD) can access this capability by initiating a **conversation** with Fiedler.
-   **Decentralized:** This model avoids centralizing LLM dependency within a single architectural component, allowing for flexible and context-appropriate use of powerful generative models.

**Example Usage Patterns:**

-   **CET:** May consult Fiedler to help classify a highly ambiguous piece of input text.
-   **DER:** Frequently consults Fiedler to generate hypotheses, synthesize plans, or draft content for novel problems.
-   **Doing Engine:** May consult Fiedler to generate a complex shell script or a snippet of code needed to complete a task.

This approach treats large language models as a powerful, rentable cognitive resource, available on-demand via a standard, auditable conversation protocol.

## 3. Complete MAD Architecture

### 3.1 Full MAD Structure

The following diagram illustrates how the components from the three disciplines are assembled into a complete Full MAD agent.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                FULL MAD                                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                         THINKING ENGINE                            │  │
│  │                                                                    │  │
│  │  ┌──────┐    ┌─────────────┐    ┌─────┐                            │  │
│  │  │ CET  │───>│ Rules Engine│───>│ DER │                            │  │
│  │  └──────┘    └─────────────┘    └─────┘                            │  │
│  │     ▲               ▲              ▲                               │  │
│  │     │               │              │                               │  │
│  │     ▼───────────────▼──────────────▼                               │  │
│  │  ┌──────────────────────────────────────────────────────────────┐ │  │
│  │  │                         STATE MANAGER                        │ │  │
│  │  └──────────────────────────────────────────────────────────────┘ │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                  │                                       │
│                (Conversation with Fiedler MAD for LLM Orchestra)         │
│                                  │                                       │
│                                  ▼                                       │
│                      ┌──────────────────────┐                            │
│                      │ Decision Package     │                            │
│                      └──────────────────────┘                            │
│                                  │                                       │
│                                  ▼                                       │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                          DOING ENGINE                              │  │
│  │                                                                    │  │
│  │           Domain-Specific Tools, APIs, and Execution Logic         │  │
│  │                                                                    │  │
│  │      (May also initiate conversations with Fiedler, Gates, etc.)   │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                  │                                       │
│                                  ▼                                       │
│                      ┌──────────────────────┐                            │
│                      │   Execution Outcome  │                            │
│                      └──────────────────────┘                            │
│                                  │ (Feedback Loop)                       │
│                                  └─────────────────> State Manager       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.2 State Manager Specification

The State Manager is the primary architectural contribution of the MAD discipline to the Thinking Engine. It is the agent's memory and world model, providing the continuity and context necessary for intelligent behavior.

**Components:**

1.  **Episodic Memory:** A log of past events, including conversation histories, decisions made, actions taken, and their outcomes. This provides a temporal record of the agent's life.
2.  **Semantic Memory:** A structured knowledge base of facts, concepts, learned patterns, and refined rules. This represents the agent's generalized knowledge about its domain and the world.
3.  **Working Memory:** A short-term store for the context of the current task, including active goals, intermediate reasoning steps, and pending commitments.
4.  **World Model:** A representation of the state of the external environment, including available resources, known constraints, and the perceived state of other agents or systems.

**Interfaces and Integrations:**

-   Provides read/write interfaces to all other Thinking Engine components.
-   Maintains an append-only log of decisions and outcomes for auditability.
-   Receives feedback from the Doing Engine to update episodic memory and the world model.
-   Initiates **conversations** with specialized Half-MADs to offload state management tasks:
    -   **Dewey:** For long-term archival and retrieval of conversation histories (episodic memory).
    -   **Godot:** For real-time logging and distributed tracing of state changes.
    -   **Horace:** For managing the state and versions of external files (world model).

### 3.3 Integration Boundaries

The success of the MAD assembly discipline hinges on well-defined boundaries and contracts between the components provided by each discipline.

**ICCM → MAD Boundary:**
-   **Contract:** The CET component, provided by ICCM, must adhere to a standard interface.
-   **Interface:** The CET accepts raw input and produces a **Structured Context Schema**, a standardized data format defined in ICCM Paper 00. MAD consumes this object as the input to the Rules Engine.

**IDE → MAD Boundary:**
-   **Contract:** The Rules Engine and DER components, provided by IDE, must adhere to standard interfaces.
-   **Interface:** The Rules Engine and DER accept the Structured Context Schema and produce a **Decision Package Schema**, a standardized data format defined in IDE Paper 00. MAD consumes this package as the input to the Doing Engine.

**MAD → Half-MAD Boundary:**
-   **Contract:** All communication between a Full MAD and any Half-MAD must be a structured conversation.
-   **Interface:** The **Model Context Protocol (MCP)** governs the format and semantics of these conversations. This replaces ad-hoc API calls with a uniform, auditable communication standard.

## 4. Hierarchical Paper Structure

The MAD discipline will be detailed across a series of 14 hierarchical papers, building upon the foundation laid in this master document.

**Act 1 - Foundations:**
-   **Paper 01:** MAD Core Architecture and the Agent Assembly Discipline
-   **Paper 02:** State Manager Specification: Episodic, Semantic, Working Memory, and World Model
-   **Paper 03:** Doing Engine Patterns and Domain-Specific Execution

**Act 2 - MAD Integration:**
-   **Paper 04:** Integrating the CET Component (from ICCM) into the MAD Thinking Engine
-   **Paper 05:** Integrating the Rules Engine and DER (from IDE) into the MAD Thinking Engine
-   **Paper 06:** Thinking Engine ↔ Doing Engine Communication: The Decision Package Protocol

**Act 3 - MAD Ecosystem:**
-   **Paper 07:** Half-MADs: A Pattern for Providing Capabilities to the Ecosystem
-   **Paper 08:** The Model Context Protocol (MCP) for MAD-to-MAD Conversations
-   **Paper 09:** LLM Orchestra Integration via the Fiedler MAD Capability

**Act 4 - Advanced Topics:**
-   **Paper 10:** Multi-MAD Coordination and Collaborative Task Execution
-   **Paper 11:** Frameworks for MAD Testing, Validation, and Simulation
-   **Paper 12:** Observability and Debugging in a Distributed MAD Ecosystem

**Act 5 - Production and Case Studies:**
-   **Paper 13:** Hopper: Case Study of an Autonomous Development MAD
-   **Paper 14:** Grace: Case Study of an Intelligent System UI MAD

## 5. Implementation Roadmap

The development and maturation of the MAD ecosystem will proceed in three phases.

#### Phase 1: Foundation (Current)
-   Implement the complete four-component Thinking Engine in the Hopper and Grace Full MADs.
-   Implement and refine domain-specific Doing Engines for development (Hopper) and UI (Grace).
-   Validate and harden the conversation protocols with core Half-MADs (Fiedler, Dewey, Godot).
-   Demonstrate the full, end-to-end lifecycle of decision-making and execution in both reference agents.

#### Phase 2: Ecosystem Maturity
-   Expand the suite of Half-MADs with new capabilities (Marco, Horace, Gates, Playfair).
-   Enhance the State Manager with sophisticated learning algorithms based on the Doing Engine's feedback loop.
-   Develop and implement the multi-MAD coordination protocols defined in Paper 10.
-   Build and release the testing and validation frameworks from Paper 11.

#### Phase 3: Production Scale
-   Begin the strategic evolution of mature Half-MADs into Full MADs by equipping them with their own complete Thinking Engines.
-   Develop advanced observability and debugging tools for production environments.
-   Define and publish production deployment patterns for high-availability MAD systems.
-   Foster a community around the development of new MADs, Doing Engines, and Half-MAD capabilities.

## 6. Success Metrics

The success of the MAD ecosystem will be measured across four key areas, aligned with its architecture.

#### 6.1 Thinking Engine Metrics
-   **Decision Quality:** Accuracy, precision, and recall of final decisions against a ground truth.
-   **Context Transformation Effectiveness:** Metrics inherited from ICCM for CET performance (e.g., signal-to-noise ratio improvement).
-   **Decision Pathway Efficiency:** Rates of deterministic decisions (Rules Engine) vs. synthesized decisions (DER), as defined by IDE metrics.
-   **State Manager Performance:** Memory recall accuracy and latency.

#### 6.2 Doing Engine Metrics
-   **Execution Success Rate:** Percentage of actions that complete successfully.
-   **Task Completion Latency:** Time from decision receipt to task completion.
-   **Error Recovery Rate:** Percentage of execution failures that are handled gracefully.
-   **Domain-Specific KPIs:** e.g., code quality for Hopper; user task success rate for Grace.

#### 6.3 MAD Integration Metrics
-   **Thinking ↔ Doing Handoff Latency:** Time taken to pass a decision and initiate execution.
-   **End-to-End Task Success Rate:** Percentage of tasks completed successfully from initial input to final outcome.
-   **Audit Trail Completeness:** Percentage of actions that can be traced back to a specific, logged decision.

#### 6.4 Ecosystem Metrics
-   **Capability Availability:** Uptime and latency of Half-MAD capabilities.
-   **Conversation Overhead:** Network and computational cost of MAD-to-MAD conversations.
-   **LLM Orchestra Utilization:** Patterns of Fiedler MAD consultation across the ecosystem.
-   **Observability Coverage:** Percentage of system interactions captured by logging and tracing.

## 7. Relationship to ICCM and IDE

MAD's role as the Agent Assembly discipline is defined by its relationship with its sibling disciplines. It is the consumer and integrator that completes the value chain of agent construction.

**MAD Consumes from ICCM:**
-   The specification and reference implementation of the CET component.
-   Best practices for context engineering.
-   The **Structured Context Schema** that serves as the lingua franca for contextual information.

**MAD Consumes from IDE:**
-   The specifications and reference implementations for the Rules Engine and DER components.
-   Best practices for decision engineering.
-   The **Decision Package Schema** that standardizes the output of the Thinking Engine.

**MAD Contributes to the Trinity:**
-   The specification for the **State Manager**, the fourth and final Thinking Engine component.
-   The patterns and principles for designing and implementing **Doing Engines**.
-   The complete **agent assembly architecture** that integrates all components.
-   The **MCP protocol** for all inter-agent conversations.
-   The **Hopper** and **Grace** reference implementations of Full MADs.

For a complete understanding of the entire agent engineering lifecycle, the governing documents should be reviewed in the following order:
1.  **ICCM Paper 00** (To understand context engineering)
2.  **IDE Paper 00** (To understand decision engineering)
3.  **MAD Paper 00** (This document, to understand agent assembly)

## 8. Half-MAD Specifications

The following are the specifications for the current suite of Half-MADs in the ecosystem.

-   **Fiedler**
    -   **Capability:** LLM Orchestra (multi-model consultation and synthesis).
    -   **Conversation Protocol:** Accepts a structured prompt with constraints; returns a synthesized response with source model attributions.
    -   **Integration:** Consulted by CET, DER, and Doing Engines for complex synthesis and generation tasks.
    -   **Evolution Path:** May evolve a sophisticated Thinking Engine to optimize model selection and prompt engineering strategies.

-   **Dewey**
    -   **Capability:** Persistent conversation storage and semantic retrieval.
    -   **Conversation Protocol:** Accepts conversation objects for storage; accepts semantic queries for retrieval.
    -   **Integration:** Used by the State Manager to manage long-term episodic memory.
    -   **Evolution Path:** May evolve a Thinking Engine to proactively identify and summarize important memories.

-   **Godot**
    -   **Capability:** Real-time, distributed logging and tracing.
    -   **Conversation Protocol:** Accepts structured log events and trace spans.
    -   **Integration:** Used by all MADs and components for observability.
    -   **Evolution Path:** May evolve a Thinking Engine for anomaly detection in system-wide logs.

-   **Marco**
    -   **Capability:** MCP conversation proxying, routing, and load balancing.
    -   **Conversation Protocol:** Forwards MCP messages based on routing rules.
    -   **Integration:** Acts as a network gateway for MADs in a distributed environment.
    -   **Evolution Path:** A Thinking Engine could enable dynamic, intelligent routing based on network conditions or agent availability.

-   **Horace**
    -   **Capability:** File cataloging, metadata management, and version control.
    -   **Conversation Protocol:** Accepts requests to store, retrieve, and version files.
    -   **Integration:** Used by State Managers and Doing Engines (especially Hopper) to manage artifacts.
    -   **Evolution Path:** A Thinking Engine could manage automated data retention policies and dependency analysis.

-   **Gates**
    -   **Capability:** Document generation and format conversion (e.g., Markdown to ODT, PDF).
    -   **Conversation Protocol:** Accepts structured content and a target format; returns the generated document.
    -   **Integration:** Used by Doing Engines to produce human-readable reports and artifacts.
    -   **Evolution Path:** A Thinking Engine could optimize document templates and layouts based on content.

-   **Playfair**
    -   **Capability:** Diagram and graph generation (e.g., Mermaid, Graphviz).
    -   **Conversation Protocol:** Accepts a textual representation of a diagram; returns the rendered image.
    -   **Integration:** Used by Thinking and Doing Engines for visualization of plans, data, or architectures.
    -   **Evolution Path:** A Thinking Engine could automatically select the best visualization type for a given dataset.

## 9. Publication Strategy

### 9.1 Venue Targeting
Our research and findings will be disseminated through top-tier academic venues, including:
-   **Primary:** ICSE (Software Engineering), FSE (Software Engineering), AAMAS (Agents and Multi-Agent Systems), AAAI (Artificial Intelligence).
-   **Secondary:** NeurIPS (Machine Learning), CHI (Human-Computer Interaction), and other domain-specific conferences relevant to our case studies.

### 9.2 Publication Dependencies
The publication of the MAD paper series is dependent on the prior publication of its foundational disciplines.
-   **Prerequisites:** Successful publication of ICCM Papers 00-03 and IDE Papers 00-05.
-   **MAD Release Schedule:** The 14 MAD papers will be released in acts, with the foundational papers (01-03) following the establishment of the ICCM and IDE disciplines. Case studies (13-14) will serve as capstone publications.

### 9.3 Cross-Discipline Collaboration
We will actively pursue joint publications that bridge the disciplines, including:
-   Papers detailing the integration of CET into MAD (ICCM-MAD collaboration).
-   Papers detailing the integration of the Rules Engine and DER into MAD (IDE-MAD collaboration).
-   A capstone paper presenting the complete trinity architecture and its application in a complex, real-world scenario.

## 10. Research Questions

The MAD discipline opens a rich field of research questions centered on agent assembly and ecosystem dynamics.

1.  **Thinking Engine Composition:** What are the optimal integration patterns and communication protocols between the CET, Rules Engine, DER, and State Manager for different classes of problems?
2.  **State Manager Design:** What memory architectures (e.g., graph-based, vector-based) best support the diverse needs of the Thinking Engine components? How can the feedback loop from the Doing Engine most effectively drive learning and adaptation in semantic memory?
3.  **Doing Engine Patterns:** What is the canonical set of Doing Engine patterns? How can we create a framework that makes Doing Engines truly swappable and reusable across different agents?
4.  **Half-MAD Evolution:** What is the optimal lifecycle for a capability? When should a simple Half-MAD be upgraded to a Full MAD with its own complete Thinking Engine?
5.  **Multi-MAD Coordination:** What conversation protocols and distributed consensus mechanisms are most effective for coordinating multiple Full MADs on a complex, shared task?
6.  **LLM Orchestra Integration:** How can components develop policies for when to consult the Fiedler MAD to balance the trade-offs between decision quality, latency, and computational cost?
7.  **Learning and Adaptation:** How can the execution outcomes recorded by the State Manager be used to automatically refine the policies in the Rules Engine or the heuristics in the DER?
8.  **Ecosystem Observability:** How can we effectively trace a single logical operation as it flows through conversations between multiple Full and Half-MADs?
9.  **Agent Validation:** How can we create high-fidelity simulation environments to test the emergent behavior of complex, multi-agent MAD systems before deployment?
10. **Production Safety:** What are the architectural patterns and operational best practices for safely deploying autonomous Full MADs in production environments with real-world consequences?

## 11. Conclusion

This paper establishes the MAD ecosystem as the discipline of **Agent Assembly**, the capstone of a powerful trinity for principled AI engineering. By consuming the **CET** component from ICCM's Context Engineering discipline and the **Rules Engine** and **DER** components from IDE's Decision Engineering discipline, MAD provides the framework for assembling complete, intelligent agents.

The MAD discipline's unique contributions—the **State Manager**, **Doing Engine** patterns, and the **conversation-based protocol** for ecosystem interaction—complete the architectural picture. The formal separation of Thinking from Doing, combined with the modular, multi-disciplinary composition of the Thinking Engine, yields agents that are demonstrably more transparent, auditable, and controllable than their monolithic counterparts.

The distinction between capability-providing **Half-MADs** and autonomous **Full MADs** creates a scalable and extensible ecosystem where complexity is encapsulated and functionality is composed through structured conversations. Validated by the Hopper and Grace reference implementations, the MAD architecture presents a robust and principled path forward for building the next generation of sophisticated and trustworthy AI agents.

---

## 12. Appendix: Terminology Reference

This reference codifies the official terminology for the MAD v2.0 ecosystem. Adherence is critical for clarity and consistency across all disciplines.

#### **Correct Terminology (To Be Used Exclusively):**

-   **Conversation:** The mechanism for communication between any two MADs.
-   **Capability:** A function or set of functions provided by one MAD to another (typically by a Half-MAD).
-   **Half-MAD:** An agent, typically with a minimal Thinking Engine, that provides a specialized capability to the ecosystem (e.g., Fiedler, Dewey).
-   **Full MAD:** An agent with a complete Thinking Engine and a Doing Engine, capable of autonomous task execution (e.g., Hopper, Grace).
-   **Thinking Engine:** The cognitive core of a MAD, composed of four components: CET, Rules Engine, DER, and State Manager.
-   **Doing Engine:** The domain-specific execution component of a MAD.
-   **CET (Context Engineering Transformer):** The context processing component from the ICCM discipline.
-   **Rules Engine:** The deterministic decision component from the IDE discipline.
-   **DER (Decision Engineering Recommender):** The synthesis-based decision component from the IDE discipline.
-   **State Manager:** The memory and world model component from the MAD discipline.
-   **LLM Orchestra:** The multi-model consultation capability provided by the Fiedler Half-MAD.
-   **Agent Assembly:** The primary focus and definition of the MAD discipline.

#### **DEPRECATED Terminology (Not To Be Used):**

-   ❌ "Service call," "API request," "RPC," "function call" (Use: **conversation**)
-   ❌ "Service," "function" (Use: **capability**)
-   ❌ "Infrastructure," "Infrastructure Classical" (Use: **Half-MADs**, **ecosystem**)
-   ❌ "Infrastructure Half-MADs" (Use: **Half-MADs**)
-   ❌ Referring to MAD as an "infrastructure provider" (Use: **Agent Assembly discipline**)
-   ❌ Describing the Thinking Engine without all four specified components.
-   ❌ Attributing ownership of the LLM Orchestra to any component other than the Fiedler MAD.
