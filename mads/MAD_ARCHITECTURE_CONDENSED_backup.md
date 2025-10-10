# MAD Architecture v1.1 - Condensed Version

## Core Concept

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

### DTR (Decision Tree Router)

The DTR is a machine learning decision tree classifier that routes incoming conversation content to where it needs to go.  The DTR learns optimal routing based on features extracted from the message structure, syntax patterns, and content markers.  Measage content can be categorizes into three classes: *deterministic* such as commands and code to be executed; *fixed* such as data files or images, and *prose* which provides base guidance for routing.  As the system processes more messages, the decision tree refines its routing through incremental learning, improving routing accuracy. This allows the majority of structured content (deterministic and fixed) to bypass the computationally expensive LLM processing path.

### DER (Decision Engineering Recommender)

The DER is a recommendation system that learns from the Imperator's decision history. Using collaborative filtering techniques, it identifies patterns where similar input contexts lead to identical decisions. The DER builds a feature matrix of input characteristics and decision outcomes, employing methods like matrix factorization or deep learning embeddings to predict when a prose input can be safely converted to a deterministic route. This recommendation system operates autonomously, continuously updating its model as new decision patterns emerge.  It takes prose and turn is into decisions that are communicated to the Action Engine.  When deployed and trained, it takes contents off the Imperators hands that is better handled deterministocally rather than conextually.

### CET (Context Engineering Transformer)

The CET is a transformer neural network that builds optimized context from multiple sources. It assembles context by: (1) incorporating recent prompts and conversation content, (2) searching for relevant historical data within conversations when needed ("what was that code block we were working on last week?"), (3) using RAG-based retrieval to  fetch data from authoritative works and company documents, and (4) querying data sources within the ecosystem.

The CET's transformer architecture learns to predict exactly what context elements are needed for specific tasks, delivering the right context at the right time for the right purpose while minimizing unnecessary information. This embodies ICCM (Intelligent Conversation and Context Management), a new architectural discipline that treats context not as a system limitation but as a fundamental carrier of thought to be optimized within constraints. The CET learns these optimization patterns through attention mechanisms that identify which combinations of sources yield successful outcomes.

Conversation Flow

Incoming: Action Engine-> MCP Server-> DTR -> DER -> CET -> Imperator
Outgoing: Action Engine <- MCP Server <- CET <- Imperator

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

## Conversation as Memory and Action

Conversation is at the core of the MAD ecosystem.  We store conversations as an infinte stream (within storage limits) that represent most of the memories of the system.  MADs join and leave conversations as needed and are able to retrieve contents of any conversation they paricipated in.  This replicates the way humans remember with the added benefits of perfect recall and near infite memory.  These also provide the basis for conituned training of the intelligents systems within the ecosystem.

When MADs communicate, they use free-form conversations without strict protocols. For example, if Fiedler notices that GPT-5 is consistently failing, it might tell Marco about this observation. Marco could then check recent AI news and discover that the model has been renamed to GPT-5.1.6. Fiedler would update its configuration based on this information, all through conversation rather than formal API calls.

Another example: When unusual activity occurs, any MAD can mention it to Sentinel. Sentinel then correlates these observations across all MADs to identify patterns. If multiple MADs report similar anomalies, Sentinel coordinates a collective response, using conversation to describe the situation and coordinate action.

## Research Objectives

This architecture is designed for research lab environments where the goal is to explore how autonomous agents can effectively collaborate through conversation. The focus is on making it work and observing how the system behaves and evolves over time.

## Key Innovation

The primary innovation is the hybrid approach to communication. Rather than forcing everything through either rigid APIs or expensive LLM processing, the DTR enables efficient routing based on content type. This allows the system to maintain the flexibility of free-form conversation while achieving the efficiency of deterministic execution where appropriate.

As the system operates, it becomes more efficient without losing flexibility. Patterns that emerge through use gradually shift from prose to deterministic routing, reducing costs and latency while maintaining the ability to handle novel situations through semantic understanding.

---

*v1.1 - With DTR for hybrid communication*