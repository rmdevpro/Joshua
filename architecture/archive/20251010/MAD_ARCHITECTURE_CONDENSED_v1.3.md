# MAD Architecture v1.3 - Condensed Version

## Core Concept

**MAD = Multipurpose Agentic Duo**

The MAD Architecture is comprised entirely of domain specific modular semi-autonomous components that interact through *Conversation* and provide *Capabilities* to the ecosystem. No element of the ecosystem sits outside of a MAD or communicates to other MADs outside of Conversations. The MAD is a virtual construct in that some MADs may be made up entirely of a monolithic piece of software, where others may include multiple elements that report to a controlling piece of software.

Each MAD consists of two engines working as a duo:

- **Thought Engine**: The cognitive system that understands and reasons
- **Action Engine**: The execution system that performs tasks

MADs communicate through free-form conversations that can contain deterministic commands, fixed data structures, or prose. This conversation-based approach maintains separation of concerns while allowing both structured efficiency and flexible expression when needed. Most importantly they facilitate the training of the intelligent systems within them which self-improve over time in nearly every way.

## Thought Engine

The Thought Engine is the brain of the system. It cannot act on its own. It needs the Action Engine for that. It is comprised of several intelligent components.

### Imperator (V1+)

The Imperator is an LLM that provides understanding and reasoning capabilities. Each MAD has its own Imperator instance, which processes the prose content that the DTR routes to it. The Imperator interprets intent, maintains context awareness, and generates appropriate responses. It handles the aspects of communication that require semantic understanding rather than pattern matching. Each Imperator is selected from the list of every LLM available to it, matched optimally to fit the domain of the MAD.

### Consulting LLMs (V1+)

While the Imperator is mandatory, MADs can request temporary consulting teams of additional LLMs through Fiedler. When the Imperator recognizes it needs specialized expertise, verification, or parallel processing, it sends a conversation request to Fiedler. Fiedler, knowing the entire LLM landscape (capabilities, availability, costs, recent updates), assembles the optimal consulting team and provisions them to the requesting MAD's Thinking Engine. These might be specialists for domains, validators for critical decisions, or simply additional instances for consensus. This creates dynamic resource allocation - consulting teams form on-demand and release when complete.

### LPPM - Learned Prose-to-Process Mapper (V2+)

The LPPM is a fine-tuned neural network that learns to map prose conversations to process orchestration patterns. Unlike a simple classifier, it understands the implicit processes that emerge from usage - learning that certain prose patterns trigger specific multi-step workflows. The LPPM sits between the lightning-fast DTR and the deliberative LLMs, handling learned patterns that don't need full reasoning but are too complex for simple routing. It orchestrates known processes like Development Cycles, determining when the Imperator needs to engage versus when steps can execute deterministically.

### DTR - Decision Tree Router (V3+)

The DTR is a machine learning decision tree classifier that routes incoming conversation content to where it needs to go. The DTR learns optimal routing based on features extracted from the message structure, syntax patterns, and content markers. Message content can be categorized into three classes: *deterministic* such as commands and code to be executed; *fixed* such as data files or images, and *prose* which provides base guidance for routing. As the system processes more messages, the decision tree refines its routing through incremental learning, improving routing accuracy. This allows the majority of structured content (deterministic and fixed) to bypass the computationally expensive LLM processing path.

### CET - Context Engineering Transformer (V4+)

The CET is a transformer neural network that builds optimized context from multiple sources. It assembles context by: (1) incorporating recent prompts and conversation content, (2) searching for relevant historical data within conversations when needed ("what was that code block we were working on last week?"), (3) using RAG-based retrieval to fetch data from authoritative works and company documents, and (4) querying data sources within the ecosystem.

The CET's transformer architecture learns to predict exactly what context elements are needed for specific tasks, delivering the right context at the right time for the right purpose while minimizing unnecessary information. This embodies ICCM (Intelligent Conversation and Context Management), a new architectural discipline that treats context not as a system limitation but as a fundamental carrier of thought to be optimized within constraints. The CET learns these optimization patterns through attention mechanisms that identify which combinations of sources yield successful outcomes.

## Progressive Cognitive Architecture

The Thinking Engine implements a progressive filtering system with increasing cost and capability as versions advance:

**V1-V2:** Imperator + Consulting (Seconds) - Full reasoning for all tasks requiring intelligence

**V3+:** DTR (Microseconds) + LPPM (Milliseconds) + Imperator (Seconds) - Progressive filtering creates massive efficiency. The DTR handles 60-80% of traffic, the LPPM another 15-30%, leaving only 5-10% requiring expensive LLM reasoning. The system becomes more efficient over time as both the DTR and LPPM learn.

## Conversation Flow

Incoming:
Conversation Bus → Action Engine → MCP Server → [DTR → LPPM →] CET → Imperator

Outgoing:
Conversation Bus ← Action Engine ← MCP Server ← CET ← Imperator

*Note: DTR and LPPM only present in V3+*

## Action Engine Components

The Action Engine provides the MAD's ability to interact with external systems as well as control, repair and improve its own systems. It contains an MCP Server to interface with the Thinking Engine, as well as the other components and code to take action on behalf of the MAD. In many ways it can be seen as the eyes, ears, mouth and hands of the MAD.

## MAD Evolution Versions

The architecture evolves through versions, with each MAD progressing at its own pace:

**V0 - Partial MADs**: Many of the MADs have evolved from earlier systems preceding this architecture. They don't have the complete components to comprise a true MAD yet. They are being upgraded to V1.

**V1 - Conversational**: Adds Imperator to enable MAD-to-MAD conversation. This provides the foundation for collaborative intelligence.

**V2 - Process Learning**: Adds LPPM to learn process patterns and decision-making from observed workflows.

**V3 - Speed Optimization**: Adds DTR to route deterministic content quickly through learning, bypassing expensive LLM processing for routine operations.

**V4 - Context Optimization**: Adds CET to optimize context usage through learning and transform prose into more efficient formats.

**V5 - Enterprise Ready**: Adds scalability features, encryption, audit trails, compliance, and enterprise-grade security.

## Current MADs with Their Versions

Several MAD implementations exist at various stages of evolution:

**Infrastructure MADs:**
- **Rogers (V0 → V1)**: Conversation Manager - manages "forever conversations" through session management and data storage, breaking the constraints of conversation windows
- **Fiedler (V0 → V1)**: LLM Orchestra Conductor - orchestrates over 20 LLMs to be used widely across the ecosystem
- **Grace (V0 → V1)**: User Interface - provides users the ability to interact with the ecosystem through conversation

**Service MADs:**
- **Dewey (V0 → V1)**: The Librarian - functions as a DBA that manages the data lake (Winnipesaukee, Winne for short)
- **Horace (V0 → V1)**: The NAS Gateway - manages file systems and storage operations
- **Marco (V0 → V1)**: The Web Explorer - provides web surfing capabilities of all sorts to the ecosystem

**Document MADs:**
- **Brin (V0 → V1)**: Google Docs Specialist - creates and manipulates Google Workspace documents
- **Gates (V0 → V1)**: Microsoft Office Specialist - creates and manipulates Word, Excel, and PowerPoint documents
- **Stallman (V0 → V1)**: OpenDocument Specialist - creates and manipulates LibreOffice and open source document formats
- **Playfair (V0 → V1)**: The Chart Master - creates charts and graphs of various types and formats

**Development & Operations MADs:**
- **Hopper (V0 → V1)**: The Software Engineer - coordinates autonomous software development through PM-led teams
- **McNamara (V0 → V1)**: Security Operations Coordinator - provides security monitoring and coordinates security eMAD teams
- **Turing (V0 → V1)**: Secrets Manager - manages cryptographic secrets, API keys, and credentials

Different deployments will require different MAD types based on their specific needs.

## MAD Lifecycle Patterns: Persistent and Ephemeral

The MAD architecture supports two distinct lifecycle models, each optimized for different resource and intelligence patterns:

**Persistent MADs** (Rogers, Dewey, Fiedler, Horace) run continuously as infrastructure services, maintaining session state and providing always-available capabilities to the ecosystem. These consume constant resources but enable immediate response and persistent context management.

**Ephemeral MADs (eMADs)** instantiate on-demand for specific tasks and terminate upon completion, achieving massive resource efficiency by existing only when needed. The architectural innovation is that while eMAD instances are temporary, they maintain persistent role-based ML models shared across all instances of that role type. When a PM eMAD spins up, it loads the latest PM model trained by all previous PM instances. Its execution contributes training data back to the model, then the instance terminates while the improved model persists. This enables unlimited concurrent instances (e.g., 50 simultaneous Senior Dev eMADs during high load), collective learning across all instances, and resource costs that scale precisely with actual workload rather than anticipated capacity.

## Conversation Bus Architecture

The MAD ecosystem operates on a conversation bus - essentially a message bus architecture where MADs publish and subscribe to conversation streams. Unlike traditional message buses with fixed schemas and rigid protocols, the conversation bus handles free-form messages containing any mix of deterministic commands, fixed data, or prose. This bus is the only communication mechanism between MADs - no element of the ecosystem sits outside a MAD or communicates outside of conversations.

## Conversation as Memory and Action

Conversation is at the core of the MAD ecosystem. We store conversations as an infinite stream (within storage limits) that represent most of the memories of the system. MADs join and leave conversations as needed and are able to retrieve contents of any conversation they participated in. This replicates the way humans remember with the added benefits of perfect recall and near infinite memory. These also provide the basis for continued training of the intelligent systems within the ecosystem.

When MADs communicate, they use free-form conversations without strict protocols. For example, if Fiedler notices that GPT-5 is consistently failing, it might tell Marco about this observation. Marco could then check recent AI news and discover that the model has been renamed to GPT-5.1.6. Fiedler would update its configuration based on this information, all through conversation rather than formal API calls.

Another example: When unusual activity occurs, any MAD can mention it to McNamara. McNamara then correlates these observations across all MADs to identify patterns. If multiple MADs report similar anomalies, McNamara coordinates a collective response, using conversation to describe the situation and coordinate action.

## Research Objectives

This architecture is designed for research lab environments where the goal is to explore how autonomous agents can effectively collaborate through conversation. The focus is on making it work and observing how the system behaves and evolves over time.

## Key Innovations

The architecture introduces several fundamental innovations:

1. **MADs**: Modular domain-specific semi-autonomous components that form the basis of the ecosystem. They not only have the power to act within their domain, but to think, learn and continuously improve.

2. **Progressive Cognitive Filtering** (V3+): Progressive intelligence layers (DTR → LPPM → LLMs) create massive efficiency by routing content to the minimum necessary cognitive level.

3. **Conversation Bus with Internal Optimization**: MADs communicate via a free-form conversation bus while internally optimizing processing through learned routing and pattern matching.

4. **Context as Carrier of Thought** (V4+): The CET embodies ICCM principles - treating context not as a limitation but as a fundamental carrier that must be optimized for each specific purpose.

5. **Self-Improving Architecture** (V2+): Both the LPPM and DTR learn continuously, gradually converting prose patterns to deterministic routes while maintaining flexibility for novel situations.

6. **LLM Usage**: LLMs are used throughout the system as managers, creators, testers, translators, decipherers, and many other uses to super-power the thinking portion of the infrastructure.

7. **LLM Teaming**: We team LLMs together in multiple ways to reduce hallucination, increase speed, provide better judgment and improve content. They act as true teams very much in the human sense.

8. **Conversation Bus**: A universal carrier of all messaging in the system from human chat to logging.

9. **Ephemeral Intelligence with Persistent Learning**: eMADs provide on-demand cognitive resources with collective learning across instances.

The system achieves the flexibility of natural language communication with the efficiency of deterministic execution, becoming more efficient over time without losing adaptability.

---

*v1.3 - Clarified version progression (V0-V5), updated MAD list, removed phase terminology*
