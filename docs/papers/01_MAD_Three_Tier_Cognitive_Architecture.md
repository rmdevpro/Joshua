# Three-Tier Cognitive Architecture and the MAD Framework: Efficient Autonomous Agent Systems Through Progressive Intelligence Filtering

## Abstract

Current autonomous agent architectures struggle with the fundamental tension between flexibility and efficiency - systems either rely on expensive Large Language Models for all decisions or rigid rule-based systems that cannot adapt. We propose the MAD (Multipurpose Agentic Duo) architecture featuring a three-tier cognitive filtering system that progressively routes content to the minimum necessary intelligence level. Each MAD consists of paired Thought and Action engines communicating via a conversation bus that handles free-form messages. The Thought Engine implements three layers: (1) a Decision Tree Router (DTR) for microsecond classification of deterministic and fixed content, (2) a Learned Prose-to-Process Mapper (LPPM) for millisecond pattern matching and process orchestration, and (3) LLMs with optional consulting teams for second-level reasoning on truly novel content. This architecture achieves 60-80% routing efficiency at the DTR level and 15-30% at the LPPM level, leaving only 5-10% of traffic requiring expensive LLM processing. The system self-improves as both the DTR and LPPM learn from usage patterns, gradually converting prose interactions to deterministic routes while maintaining full flexibility for novel situations. We present implementation results from Rogers (session management) and Fiedler (LLM orchestration) demonstrating practical deployment of Phase 1 MADs.

## 1. Introduction

The development of autonomous agent systems faces a fundamental challenge: how to balance the flexibility needed for natural interaction with the efficiency required for practical deployment. Current approaches typically fall into two categories, each with significant limitations.

Rule-based systems offer speed and predictability but lack adaptability. They cannot handle novel situations or learn from experience. Conversely, LLM-based systems provide remarkable flexibility and understanding but at prohibitive computational cost when every interaction requires full model inference.

We propose the MAD (Multipurpose Agentic Duo) architecture, which resolves this tension through a three-tier cognitive filtering system that progressively routes content to the minimum necessary intelligence level.

### 1.1 Core Innovation

The key insight is that not all content requires the same level of cognitive processing. A simple command like "archive session 123" doesn't need the reasoning power of GPT-4, while a complex request like "analyze this architecture and suggest improvements" does. By implementing progressive filtering, we achieve both efficiency and flexibility.

### 1.2 Core Concept

**MAD = Multipurpose Agentic Duo**

The MAD Architecture is comprised entirely of domain specific modular semi automomous compoents that interact through *Conversation* and provide *Capabilities* to the ecosystem.  No element of the ecosystem sits outside of a MAD or communicates to other mads outside of Conversations.  The MAD is a virtual contruct in that some MADs may be made up entirely of a monolitic piece of software, where others may include multiple elements that report to a controling piece of software.

Each MAD consists of two engines working as a duo:

- **Thought Engine**: The cognitive system that understands and reasons
- **Action Engine**: The execution system that performs tasks

MADs communicate through free-form conversations that can contain deterministic commands, fixed data structures, or prose. This conversation-based approach maintains separation of concerns while allowing both structured efficiency and flexible expression when needed. Most importantly they facilitate the training of the intelligent systems with them which self improve over time in nearly every way.

## Thought Engine

The Thought Engine is the brain of the system. It cannot act on its own. It needs the Action Engine for that.  It is comprised of several intelligent components.

### Imperator

The Imperator is the an LLM that provides understanding and reasoning capabilities. Each MAD has its own Imperator instance, which processes the prose content that the DTR routes to it. The Imperator interprets intent, maintains context awareness, and generates appropriate responses. It handles the aspects of communication that require semantic understanding rather than pattern matching. Each Imperator is selected from the list of every LLM available to it, matched optimally to fit the domain of the MAD.

### Consulting LLMs

While the Imperator is mandatory, MADs can request temporary consulting teams of additional LLMs through Fiedler. When the Imperator recognizes it needs specialized expertise, verification, or parallel processing, it sends a conversation request to Fiedler. Fiedler, knowing the entire LLM landscape (capabilities, availability, costs, recent updates), assembles the optimal consulting team and provisions them to the requesting MAD's Thinking Engine. These might be specialists for domains, validators for critical decisions, or simply additional instances for consensus. This creates dynamic resource allocation - consulting teams form on-demand and release when complete.

### DTR (Decision Tree Router)

The DTR is a machine learning decision tree classifier that routes incoming conversation content to where it needs to go.  The DTR learns optimal routing based on features extracted from the message structure, syntax patterns, and content markers.  Measage content can be categorizes into three classes: *deterministic* such as commands and code to be executed; *fixed* such as data files or images, and *prose* which provides base guidance for routing.  As the system processes more messages, the decision tree refines its routing through incremental learning, improving routing accuracy. This allows the majority of structured content (deterministic and fixed) to bypass the computationally expensive LLM processing path.

### LPPM (Learned Prose-to-Process Mapper)

The LPPM is a fine-tuned neural network that learns to map prose conversations to process orchestration patterns. Unlike a simple classifier, it understands the implicit processes that emerge from usage - learning that certain prose patterns trigger specific multi-step workflows. The LPPM sits between the lightning-fast DTR and the deliberative LLMs, handling learned patterns that don't need full reasoning but are too complex for simple routing. It orchestrates known processes like Development Cycles, determining when the Imperator needs to engage versus when steps can execute deterministically. This creates a three-tier cognitive architecture: microsecond routing (DTR), millisecond pattern mapping (LPPM), and second-level reasoning (LLMs).

### CET (Context Engineering Transformer)

The CET is a transformer neural network that builds optimized context from multiple sources. It assembles context by: (1) incorporating recent prompts and conversation content, (2) searching for relevant historical data within conversations when needed ("what was that code block we were working on last week?"), (3) using RAG-based retrieval to  fetch data from authoritative works and company documents, and (4) querying data sources within the ecosystem.

The CET's transformer architecture learns to predict exactly what context elements are needed for specific tasks, delivering the right context at the right time for the right purpose while minimizing unnecessary information. This embodies ICCM (Intelligent Conversation and Context Management), a new architectural discipline that treats context not as a system limitation but as a fundamental carrier of thought to be optimized within constraints. The CET learns these optimization patterns through attention mechanisms that identify which combinations of sources yield successful outcomes.



## Three-Tier Cognitive Architecture

The Thinking Engine implements a progressive filtering system with three tiers of increasing cost and capability:

1. **DTR (Microseconds)**: Lightning-fast routing of deterministic and fixed content
2. **LPPM (Milliseconds)**: Pattern matching and process orchestration for learned workflows
3. **Imperator + Consulting (Seconds)**: Full reasoning for novel situations requiring true intelligence

This creates massive efficiency - the DTR handles 60-80% of traffic, the LPPM another 15-30%, leaving only 5-10% requiring expensive LLM reasoning. The system becomes more efficient over time as both the DTR and LPPM learn.

## Conversation Flow

Incoming: Action Engine → MCP Server → DTR → LPPM → CET → Imperator (+ Consulting LLMs)
Outgoing: Action Engine ← MCP Server ← CET ← Imperator

## Action Engine Components

The Action Engine provides the MAD's ability to interact with external systems  as well as control, repair and improve its own systems. It contains an MCP Server to inteface with the Thinking Engine, as well of the other components and code to take action on behalf of the MAD. In many ways it can been as the eyes, ears, mouth and hands of the MAD

## Evolution Phases

The architecture evolves through four phases:

**Parial MADs**: Many of the MADs have evolved from earlier systems I built preceding this architecture.  They don't have the complete componets to comprise a true MAD yet.  They are being upgraded to Phase 1 MADs.

**Phase 1** establishes the basic Thought and Action engine structure with DTR routing. This provides the foundation for all future development.

**Phase 2** adds the DER to learn from decisions and create new deterministic paths based on observed patterns.

**Phase 3** introduces the CET to optimize context usage and transform prose into more efficient formats.

**Phase 4** adds enterprise capabilities including encryption, audit trails, and compliance features.

## Current MADs with Their Phase of Completion

Several MAD implementations have been developed for different purposes:

- **Rogers (Phase 1)**: Convesation Manager, manages "forever conversatios" through session managment and data storage, breaking the contraints of conversation windows.
- **Fiedler (Phase 1)**: LLM Orchester Conductor, orchestrates over 20 LLMs to be used widely accross the ecosystem
- **Hopper (Phase 1):** The Software Engineer, autonomously builds software from Design Documents
- **Dewey (Partial MAD)**: The Librian, functions as a DBA that manages the data lake (Winnipesaukee, Winne for short)
- **Horace (Partial MAD)**: The NAS Gateway that manages file systems
- **Marco (Partial MAD)**: The Web Explore that provides web surfing cababilites of all sorts to the ecosyste
- **Godot (Partial MAD)**: The Log Master, takes all your logs in and prevents you from having to wait for them when you want to read them.
- **Gates (Partial MAD):** The Office Documentarian, builds and alters documents such as Word Docs, Excel Files and Slide Decks, in Microsoft, Google and Open Source formats
- **Playfair (Partial MAD):** The Chart Master, creates chart and graphs of various types and formats.
- **Solomon (Designed)**: The Judge, tests software and builds test suites from design docs and code
- **Wright (Designed)**: The Architect, responsible for authoring desing docs, and implentation plans
- **Grace (Designed)**: The User Interface, provides users the ability to interact with the ecosystem through conversation

Different deployments will require different MAD types based on their specific needs.

## Conversation Bus Architecture

The MAD ecosystem operates on a conversation bus - essentially a message bus architecture where MADs publish and subscribe to conversation streams. Unlike traditional message buses with fixed schemas and rigid protocols, the conversation bus handles free-form messages containing any mix of deterministic commands, fixed data, or prose. This bus is the only communication mechanism between MADs - no element of the ecosystem sits outside a MAD or communicates outside of conversations.

## Conversation as Memory and Action

Conversation is at the core of the MAD ecosystem.  We store conversations as an infinte stream (within storage limits) that represent most of the memories of the system.  MADs join and leave conversations as needed and are able to retrieve contents of any conversation they paricipated in.  This replicates the way humans remember with the added benefits of perfect recall and near infite memory.  These also provide the basis for conituned training of the intelligents systems within the ecosystem.

When MADs communicate, they use free-form conversations without strict protocols. For example, if Fiedler notices that GPT-5 is consistently failing, it might tell Marco about this observation. Marco could then check recent AI news and discover that the model has been renamed to GPT-5.1.6. Fiedler would update its configuration based on this information, all through conversation rather than formal API calls.

Another example: When unusual activity occurs, any MAD can mention it to Sentinel. Sentinel then correlates these observations across all MADs to identify patterns. If multiple MADs report similar anomalies, Sentinel coordinates a collective response, using conversation to describe the situation and coordinate action.

## Research Objectives

This architecture is designed for research lab environments where the goal is to explore how autonomous agents can effectively collaborate through conversation. The focus is on making it work and observing how the system behaves and evolves over time.

## Key Innovations

The architecture introduces several fundamental innovations:

1. **Three-Tier Cognitive Filtering**: Progressive intelligence layers (DTR → LPPM → LLMs) create massive efficiency by routing content to the minimum necessary cognitive level.

2. **Conversation Bus with Internal Optimization**: MADs communicate via a free-form conversation bus while internally optimizing processing through learned routing and pattern matching.

3. **Context as Carrier of Thought**: The CET embodies ICCM principles - treating context not as a limitation but as a fundamental carrier that must be optimized for each specific purpose.

4. **Self-Improving Architecture**: Both the DTR and LPPM learn continuously, gradually converting prose patterns to deterministic routes while maintaining flexibility for novel situations.

5. **Ephemeral MADs with Persistent Learning**: The architecture supports both persistent MADs (continuously-running infrastructure services) and ephemeral MADs (on-demand role-based workers). While eMAD instances have temporary lifecycles, they maintain shared role-based machine learning models that persist across all instantiations. This enables collective intelligence where each instance contributes to training the shared model, and subsequent instances benefit from the accumulated knowledge of all previous executions. This innovation addresses the resource efficiency limitations of persistent agents while avoiding the learning isolation of traditional stateless workers, creating a third paradigm where ephemeral execution coexists with continuous improvement.

The system achieves the flexibility of natural language communication with the efficiency of deterministic execution, becoming more efficient over time without losing adaptability.

---

*v1.2 - Three-tier cognitive architecture with LPPM and consulting LLMs*