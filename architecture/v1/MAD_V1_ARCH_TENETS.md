# MAD V1 Architecture Tenets

## Version: 1.0
## Status: Approved

---

## Overview

These five tenets represent the fundamental laws of the MAD V1 architecture. They are the core principles that guide all design, development, and operational decisions. All components and interactions within the MAD ecosystem MUST adhere to these tenets without exception. They answer the question: "Why do we build this way?"

---

### Tenet 1: Conversation is the Universal Interface

All interactions between system components, human operators, and external services MUST be expressible as conversational turns. Data transfer, command execution, status updates, and error handling are all facets of a single, unified conversational paradigm. There SHALL be no side-channel communication or traditional REST/RPC APIs between MAD components.

### Tenet 2: Natural Language is the Protocol

The system SHALL treat structured and unstructured natural language as the primary, authoritative protocol for communication. Formal syntax (e.g., commands, structured data) is considered an optimization for deterministic routing and performance, not a prerequisite for interaction. The system must be capable of understanding intent from pure prose.

### Tenet 3: Composition Defines Capability

A MAD's function is defined by the composition of its ThoughtEngine (an Imperator LLM) and its ActionEngine (specialized tools). System-level functionality is achieved by composing conversations between multiple, specialized MADs. We SHALL favor creating new, focused MADs over adding unrelated responsibilities to existing ones.

### Tenet 4: Infrastructure is Conversational

Core infrastructure services that enable LLM functionality (e.g., code execution, RAG, sequential thinking) MUST be exposed as persistent, conversational agents (Helper MCPs). This ensures that all system resources, regardless of their function, participate in the same conversational ecosystem, making them discoverable, observable, and composable.

### Tenet 5: State is Ephemeral; History is Persistent

MAD instances, particularly ephemeral MADs (eMADs), are designed to be transient and stateless. All application state, operational history, and learned context MUST be persisted within the conversational record, managed by the Rogers messaging bus. This design ensures resilience, auditability, and allows any MAD to reconstruct context from the conversation history.

---
---