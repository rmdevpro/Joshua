# Paper 00: The MAD Ecosystem - Master Document v2.0

**Title:** The MAD (Multipurpose Agentic Duo) Framework: Agent Assembly Architecture for Cognitive AI Systems

**Authors:** MAD Research Collective  
**Version:** 2.0  
**Date:** 2025-01-08  
**Repository:** Joshua/MAD  
**Status:** Complete Synthesis by Council of Elders

---

## Executive Summary

The MAD (Multipurpose Agentic Duo) framework represents the Agent Assembly discipline that completes the foundational trinity of AI agent engineering. While ICCM (Intelligent Context and Content Management) provides the Context Engineering discipline and IDE (Intelligent Decision Engineering) provides the Decision Engineering discipline, MAD integrates their components into complete, autonomous agents.

At its core, MAD introduces a dual-engine cognitive architecture that formally separates thinking (cognition) from doing (execution). The MAD Thinking Engine integrates four components: CET (Context Engineering Transformer) from ICCM, Rules Engine and DER (Decision Engineering Recommender) from IDE, and State Manager from MAD itself. This separation enables unprecedented transparency, auditability, and control in AI agent systems.

The MAD ecosystem consists of two types of agents:
- **Half-MADs**: Agents with minimal Thinking Engines that provide specialized capabilities to other MADs (Fiedler, Dewey, Godot, Marco, Horace, Gates, Playfair)
- **Full MADs**: Complete agents with full Thinking and Doing Engines (Hopper, Grace)

All MADs communicate through conversations (not service calls) and provide capabilities (not services) to each other. The Fiedler Half-MAD provides LLM Orchestra capability, enabling any component to consult multiple large language models when needed.

This paper proposes a hierarchical 14-paper structure for the MAD discipline, building upon the foundations established in ICCM Paper 00 and IDE Paper 00. The framework is validated through two reference implementations: Hopper (autonomous development) and Grace (intelligent system UI).

---

## Table of Contents

1. [Introduction: The MAD Ecosystem](#1-introduction-the-mad-ecosystem)
2. [Theoretical Foundation](#2-theoretical-foundation)
3. [Complete MAD Architecture](#3-complete-mad-architecture)
4. [Half-MAD Specifications](#4-half-mad-specifications)
5. [Implementation Roadmap](#5-implementation-roadmap)
6. [Success Metrics](#6-success-metrics)
7. [Hierarchical Paper Structure](#7-hierarchical-paper-structure)
8. [Research Questions](#8-research-questions)
9. [Case Studies](#9-case-studies)
10. [Related Work](#10-related-work)
11. [Publication Strategy](#11-publication-strategy)
12. [Conclusion](#12-conclusion)
13. [References](#references)
14. [Appendix: Terminology Reference](#appendix-terminology-reference)

---

## 1. Introduction: The MAD Ecosystem

### 1.1 What is the MAD Ecosystem?

The MAD (Multipurpose Agentic Duo) ecosystem represents a groundbreaking approach to building AI agents through formal separation of cognitive and execution concerns. Unlike monolithic architectures where reasoning and action are intertwined, MAD introduces a dual-engine architecture that cleanly separates thinking from doing.

**Definition:** A MAD is an AI agent composed of two distinct engines:
- **Thinking Engine**: Handles perception, reasoning, planning, and decision-making
- **Doing Engine**: Executes decisions and interacts with the external world

This separation is not merely organizational—it represents a fundamental architectural principle that enables:
- **Transparency**: Every decision can be traced through explicit reasoning steps
- **Auditability**: Complete decision logs with reasoning traces
- **Controllability**: Clear intervention points for human oversight
- **Composability**: Engines can be independently developed and tested
- **Swappability**: Same Thinking Engine can pair with different Doing Engines

MAD serves as the **Agent Assembly discipline** within the foundational trinity of AI agent engineering. It provides the frameworks, patterns, and architectures needed to integrate components from Context Engineering (ICCM) and Decision Engineering (IDE) into complete, functional agents.

### 1.2 The Trinity of Disciplines

The development of sophisticated AI agents requires three complementary disciplines, each addressing a critical aspect of agent construction:

#### 1.2.1 ICCM (Intelligent Context and Content Management)
- **Repository**: ICCM
- **Discipline**: Context Engineering - the science of transforming raw, unstructured input into optimized, decision-ready context
- **Primary Output**: CET (Context Engineering Transformer) component
- **Paper Structure**: ICCM Paper 00 + Papers 01-14
- **Contribution to MAD**: Provides Component #1 of the Thinking Engine

ICCM addresses the fundamental challenge of context transformation. Raw inputs from users, sensors, or systems are often noisy, incomplete, or ambiguously structured. The CET component systematically transforms these inputs into clean, classified, and enriched context that downstream decision-making components can process effectively.

#### 1.2.2 IDE (Intelligent Decision Engineering)
- **Repository**: Joshua/IDE
- **Discipline**: Decision Engineering - the science of making transparent, auditable, hybrid decisions combining deterministic rules with AI synthesis
- **Primary Outputs**: Rules Engine (deterministic) + DER (synthesis)
- **Paper Structure**: IDE Paper 00 + Papers 01-13
- **Contribution to MAD**: Provides Components #2-3 of the Thinking Engine

IDE tackles the core challenge of decision-making in AI systems. It introduces a hybrid approach where deterministic rules handle known scenarios with guaranteed outcomes, while the DER component synthesizes decisions for novel or ambiguous situations. This dual approach ensures both reliability and adaptability.

#### 1.2.3 MAD (Multipurpose Agentic Duo)
- **Repository**: Joshua/MAD
- **Discipline**: Agent Assembly - the science of integrating cognitive components into complete, autonomous agents
- **Primary Outputs**: Complete MAD implementations (Hopper, Grace, etc.)
- **Paper Structure**: MAD Paper 00 + Papers 01-14 (this document)
- **Contribution**: State Manager (Component #4 of Thinking Engine) + Doing Engine patterns + integration architecture

MAD completes the trinity by providing the assembly discipline. It defines how to integrate CET from ICCM, Rules Engine and DER from IDE, add the State Manager component, create domain-specific Doing Engines, and orchestrate all components into agents capable of autonomous operation.

**Relationship Diagram:**
```
Context Engineering (ICCM) ─────┐
                                ├───> Agent Assembly (MAD)
Decision Engineering (IDE) ─────┘     └─> Complete Agents
```

This trinity represents a natural factorization of concerns:
- ICCM: "How do we understand what's happening?"
- IDE: "How do we decide what to do?"
- MAD: "How do we build agents that act autonomously?"

### 1.3 Why Dual-Engine Architecture Matters

The separation of thinking from doing is not a new concept—it has deep roots in both cognitive science and AI research. However, MAD's implementation of this principle in the context of modern AI systems, particularly those leveraging large language models, represents a significant advance.

#### 1.3.1 Cognitive Architecture Heritage

MAD builds upon decades of research in cognitive architectures:

**SOAR (State, Operator, And Result)**:
- Introduced problem spaces and universal subgoaling
- Demonstrated the power of separating reasoning from execution
- MAD adopts: Clear separation of cognitive cycles from action execution

**ACT-R (Adaptive Control of Thought—Rational)**:
- Modeled human cognition with separate declarative and procedural memory
- Showed how symbolic and subsymbolic processes can be integrated
- MAD adopts: Multiple memory types in State Manager, hybrid reasoning

**Modern Integration**:
MAD extends these classical architectures by incorporating:
- Large Language Models for synthesis and generation
- Deterministic rules engines for guaranteed behaviors
- Structured context transformation from modern NLP
- Distributed capability access through conversations

#### 1.3.2 Advantages of Separation

**1. Testability**
- Thinking Engine can be tested with simulated inputs and expected decisions
- Doing Engine can be tested with mock decisions and expected actions
- Integration testing validates the handoff between engines
- Each component has clear contracts and boundaries

**2. Auditability**
- Every decision includes a complete reasoning trace
- State changes are logged with causal chains
- Execution outcomes link back to originating decisions
- Compliance and safety requirements can be systematically verified

**3. Safety**
- Thinking Engine can be constrained by rules and policies
- Doing Engine can have execution safeguards
- Clear intervention points for human oversight
- Graceful degradation when components fail

**4. Composability**
- Different Thinking Engines can share Doing Engines
- Same Thinking Engine can use different Doing Engines
- Components can be upgraded independently
- New capabilities can be added without full system changes

#### 1.3.3 Real-World Validation

The MAD architecture is not theoretical—it has been validated through two significant implementations:

**Hopper**: An autonomous development agent that can:
- Understand development tasks from natural language
- Plan multi-step implementation strategies
- Execute bash commands, write code, run tests
- Learn from execution outcomes and adapt

**Grace**: An intelligent system UI that can:
- Understand user intent across multiple interaction modes
- Dynamically generate appropriate interfaces
- Execute complex workflows on behalf of users
- Maintain context across extended interactions

Both systems demonstrate that the dual-engine architecture can handle real-world complexity while maintaining the transparency and control that traditional monolithic approaches lack.

### 1.4 Half-MADs vs Full MADs

The MAD ecosystem recognizes that not all agents require complete cognitive architectures. This insight led to the distinction between Half-MADs and Full MADs.

#### 1.4.1 Half-MADs: Specialized Capability Providers

**Definition**: A Half-MAD is an agent with a minimal or incomplete Thinking Engine, designed to provide specific capabilities to other MADs in the ecosystem.

**Characteristics**:
- Minimal Thinking Engine (often just simple routing logic)
- Focused on providing one or few capabilities efficiently
- Communicate via conversations using MCP protocol
- Designed for high-performance, specialized tasks
- Lower resource requirements than Full MADs

**Current Half-MADs in the Ecosystem**:

1. **Fiedler**: LLM Orchestra capability
   - Provides multi-model consultation
   - Manages prompts across Gemini, GPT, Claude, Grok, etc.
   - Returns synthesized responses with confidence scores

2. **Dewey**: Conversation storage and retrieval
   - Persistent storage for all MAD conversations
   - Efficient retrieval by various criteria
   - Maintains conversation indices and metadata

3. **Godot**: Real-time logging and tracing
   - Collects logs from all MAD components
   - Provides real-time log streaming
   - Maintains trace correlation across conversations

4. **Marco**: MCP conversation proxy
   - Routes conversations between MADs
   - Handles protocol translation if needed
   - Provides conversation monitoring and metrics

5. **Horace**: File catalog and versioning
   - Maintains catalog of all files in the system
   - Tracks versions and changes
   - Provides efficient file search and retrieval

6. **Gates**: Document generation
   - Transforms Markdown to various formats (ODT, PDF, etc.)
   - Maintains document templates
   - Handles complex document assembly

7. **Playfair**: Diagram generation
   - Creates diagrams from textual descriptions
   - Supports Mermaid, Graphviz, PlantUML
   - Provides diagram caching and optimization

**Evolution Path**: Half-MADs are designed to eventually upgrade to Full MADs as requirements grow. This upgrade involves:
- Adding complete Thinking Engine components
- Implementing State Manager for memory
- Expanding capability set
- Maintaining backward compatibility for existing conversations

#### 1.4.2 Full MADs: Complete Autonomous Agents

**Definition**: A Full MAD implements the complete dual-engine architecture with all four Thinking Engine components and a domain-specific Doing Engine.

**Characteristics**:
- Complete Thinking Engine (CET + Rules + DER + State Manager)
- Domain-specific Doing Engine
- Autonomous operation capability
- Can handle complex, multi-step tasks
- Maintains memory and learns from experience

**Architecture of a Full MAD**:
```
┌─────────────────────────────────────────────┐
│              FULL MAD                       │
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │        THINKING ENGINE                  │ │
│ │                                         │ │
│ │  Input → CET → Rules → DER → Decision  │ │
│ │            ↕      ↕      ↕              │ │
│ │         State Manager                   │ │
│ └─────────────────────────────────────────┘ │
│                    ↓                        │
│ ┌─────────────────────────────────────────┐ │
│ │         DOING ENGINE                    │ │
│ │                                         │ │
│ │   Domain-Specific Execution             │ │
│ │   (Tools, APIs, Interfaces)             │ │
│ └─────────────────────────────────────────┘ │
│                    ↓                        │
│              Execution Results              │
│                    ↓                        │
│           State Manager Update              │
└─────────────────────────────────────────────┘
```

**Current Full MADs**:

1. **Hopper**: Autonomous Development Agent
   - Thinking Engine: Full implementation with development-focused rules
   - Doing Engine: Bash execution, file operations, code generation
   - Capabilities: Can complete complex development tasks autonomously

2. **Grace**: Intelligent System UI
   - Thinking Engine: Full implementation with UI/UX-focused rules
   - Doing Engine: Web framework integration, dynamic UI generation
   - Capabilities: Can create and adapt user interfaces dynamically

#### 1.4.3 MAD-to-MAD Interactions

All interactions between MADs, whether Half or Full, follow consistent patterns:

**Communication Protocol**: MCP (Model Context Protocol)
- Structured conversation format
- Request-response with streaming support
- Built-in error handling and retries
- Conversation correlation and tracing

**Conversation Patterns**:
1. **Capability Discovery**: MADs can query what capabilities others provide
2. **Capability Invocation**: Structured requests for specific capabilities
3. **Streaming Responses**: For long-running operations
4. **Event Notification**: Asynchronous updates about state changes

**Example Conversation Flow**:
```
Grace (Full MAD) → Fiedler (Half-MAD):
  "I need multi-model consensus on this UI design decision"
  
Fiedler → Grace:
  "Consulting Gemini, GPT-5, Claude..."
  [Streaming responses]
  "Synthesis: 85% confidence in approach A"

Grace → Dewey (Half-MAD):
  "Store this conversation with tags: ui-design, decision-2024-01-08"
  
Dewey → Grace:
  "Stored with ID: conv-12345, retrievable by tags"
```

### 1.5 Document Organization

This Paper 00 serves as the master document for the MAD discipline, completing the foundational trinity of AI agent engineering. It is organized to provide both theoretical grounding and practical implementation guidance.

**Prerequisites**: Readers should first review:
1. **ICCM Paper 00**: Understanding Context Engineering and the CET component
2. **IDE Paper 00**: Understanding Decision Engineering, Rules Engine, and DER

**This Document's Focus**:
- Agent Assembly: Integrating components from ICCM and IDE
- State Manager: The fourth Thinking Engine component unique to MAD
- Doing Engine Patterns: Domain-specific execution architectures
- MAD Ecosystem: How Half-MADs and Full MADs work together
- Implementation Examples: Hopper and Grace as reference architectures

**Document Structure**:
- **Sections 1-3**: Core concepts and architecture
- **Sections 4-6**: Implementation details and patterns
- **Section 7**: Proposed 14-paper hierarchical structure
- **Sections 8-12**: Research directions and strategy
- **Appendices**: Reference materials and terminology

The hierarchical paper structure (detailed in Section 7) provides a roadmap for deep exploration of each aspect of the MAD framework, from theoretical foundations to production deployments.

---

## 2. Theoretical Foundation

### 2.1 Cognitive Architecture Principles

The MAD framework's theoretical foundation rests on well-established principles from cognitive science and AI, adapted for modern autonomous agent systems.

#### 2.1.1 Two-System Model

Drawing from Kahneman's dual-process theory, MAD implements a computational analog of System 1 and System 2 thinking:

**System 1 (Fast, Automatic)**:
- Implemented primarily in Rules Engine
- Handles routine decisions with deterministic rules
- Provides immediate responses for known scenarios
- Low computational cost, high speed

**System 2 (Slow, Deliberative)**:
- Implemented primarily in DER with LLM Orchestra consultation
- Handles novel, complex, or ambiguous decisions
- Provides reasoned responses with uncertainty quantification
- Higher computational cost, but more flexible

**MAD's Innovation**: Unlike human cognition where these systems compete, MAD orchestrates them cooperatively:
```
Input → CET → Rules Engine (System 1 attempt)
                ↓
         [If no confident rule]
                ↓
              DER (System 2 deliberation)
                ↓
            Decision
```

This cooperative approach ensures that:
- Simple decisions are fast and efficient
- Complex decisions receive appropriate deliberation
- All decisions are traceable through the system
- Resource usage is optimized

#### 2.1.2 Structured Reasoning with Clean Boundaries

MAD enforces strict boundaries between components to ensure predictable, auditable behavior:

**1. Input Boundary (External → CET)**:
- Raw input must be transformed before reasoning
- No direct access to decision components
- Ensures consistent context representation

**2. Context Boundary (CET → Rules/DER)**:
- Structured context with defined schema
- No raw data passes this boundary
- Enables component testing in isolation

**3. Decision Boundary (Thinking → Doing)**:
- Decisions are structured packages
- Include reasoning traces and confidence
- Doing Engine cannot modify decisions

**4. Execution Boundary (Doing → External)**:
- Actions are logged before execution
- Results are captured systematically
- Failures are handled gracefully

**5. Feedback Boundary (Results → State Manager)**:
- Execution outcomes update memory
- Learning happens through structured feedback
- No direct modification of rules or components

These boundaries enable:
- **Component Independence**: Each component has clear inputs/outputs
- **Testing in Isolation**: Components can be tested separately
- **Progressive Enhancement**: Components can be improved independently
- **Audit Trails**: Every boundary crossing is logged

#### 2.1.3 Advantages Over Monolithic Architectures

Traditional monolithic AI agents suffer from several fundamental issues that MAD addresses:

**Problem 1: Opaque Decision-Making**
- Monolithic: Decisions emerge from black-box processes
- MAD: Every decision has a traceable path through components

**Problem 2: Difficult Testing**
- Monolithic: Must test entire system end-to-end
- MAD: Each component can be unit tested

**Problem 3: Poor Maintainability**
- Monolithic: Changes risk breaking unrelated functionality
- MAD: Components can be modified independently

**Problem 4: Limited Reusability**
- Monolithic: Agent capabilities are tightly coupled
- MAD: Thinking Engines can be reused with different Doing Engines

**Problem 5: Scaling Challenges**
- Monolithic: Entire system must scale together
- MAD: Components can scale independently based on load

### 2.2 The Thinking Engine: Complete Specification

The MAD Thinking Engine represents a sophisticated integration of four components from three disciplines, creating a cognitive system capable of perception, reasoning, decision-making, and learning.

#### 2.2.1 Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        THINKING ENGINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CET (Context Engineering Transformer)                      │
│     Source: ICCM Discipline                                    │
│     Function: Transform raw input → structured context         │
│     • Classification and routing                               │
│     • Context enrichment and optimization                      │
│     • Ambiguity resolution                                     │
│     • Feature extraction                                       │
│                                                                 │
│  2. Rules Engine                                               │
│     Source: IDE Discipline                                     │
│     Function: Deterministic decision-making                    │
│     • Policy enforcement                                       │
│     • Safety guardrails                                       │
│     • Known scenario handling                                  │
│     • Fast-path decisions                                      │
│                                                                 │
│  3. DER (Decision Engineering Recommender)                     │
│     Source: IDE Discipline                                     │
│     Function: Synthesis for complex decisions                  │
│     • Novel scenario handling                                  │
│     • Multi-criteria optimization                              │
│     • Uncertainty quantification                               │
│     • LLM Orchestra consultation via Fiedler                   │
│                                                                 │
│  4. State Manager                                              │
│     Source: MAD Discipline                                     │
│     Function: Memory and world model                          │
│     • Episodic memory (conversation history)                  │
│     • Semantic memory (learned patterns)                       │
│     • Working memory (active context)                          │
│     • World model (external state)                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.2.2 Component Interactions

The Thinking Engine components interact through well-defined protocols:

**1. Input Processing Flow**:
```
Raw Input → CET
    ↓
Structured Context
    ↓
Rules Engine (with State Manager consultation)
    ↓
[If high-confidence rule found]
    ↓                          
Decision Package              
    
[If no confident rule]
    ↓
DER (with State Manager + Fiedler consultation)
    ↓
Decision Package
```

**2. State Manager Integration**:
The State Manager provides memory services to all components:

- **To CET**: Previous context patterns, entity recognition data
- **To Rules Engine**: Rule activation history, policy updates
- **To DER**: Past decisions, learned preferences, outcome feedback
- **From all**: Updates to respective memory stores

**3. LLM Orchestra Access Pattern**:
When components need LLM assistance, they initiate conversations with Fiedler:

```
Component → Fiedler MAD:
  {
    "capability": "multi_model_consultation",
    "context": { ... },
    "constraints": { ... },
    "models_requested": ["gemini-2", "gpt-5", "claude-3"]
  }

Fiedler → Component:
  {
    "synthesis": "...",
    "individual_responses": { ... },
    "confidence": 0.85,
    "reasoning_trace": [ ... ]
  }
```

#### 2.2.3 Component Specifications

**1. CET (Context Engineering Transformer)**
- **Specification**: ICCM Paper 00, Papers 01-03
- **Inputs**: Raw text, structured data, multimodal inputs
- **Outputs**: Structured context objects with classification
- **Key Functions**:
  - Intent classification
  - Entity extraction
  - Context normalization
  - Ambiguity flagging
- **Integration Points**:
  - Receives raw input from external sources
  - Consults State Manager for context history
  - May consult Fiedler for ambiguous classification
  - Outputs to Rules Engine

**2. Rules Engine**
- **Specification**: IDE Paper 00, Papers 01-02
- **Inputs**: Structured context from CET
- **Outputs**: Decisions (if confident) or delegation to DER
- **Key Functions**:
  - Policy evaluation
  - Constraint checking
  - Fast-path optimization
  - Confidence scoring
- **Integration Points**:
  - Receives context from CET
  - Consults State Manager for rule state
  - Outputs decisions or delegates to DER

**3. DER (Decision Engineering Recommender)**
- **Specification**: IDE Paper 00, Papers 03-05
- **Inputs**: Context + Rules Engine analysis
- **Outputs**: Decision packages with reasoning
- **Key Functions**:
  - Multi-criteria decision synthesis
  - Uncertainty handling
  - Reasoning trace generation
  - Confidence calibration
- **Integration Points**:
  - Receives from Rules Engine when needed
  - Consults State Manager for decision history
  - Initiates conversations with Fiedler for LLM assistance
  - Outputs complete decision packages

**4. State Manager**
- **Specification**: This paper (MAD Paper 00), Papers 02-03
- **Inputs**: Updates from all components
- **Outputs**: Memory retrievals, state queries
- **Key Functions**:
  - Memory management (episodic, semantic, working)
  - World model maintenance
  - Learning integration
  - State persistence via Dewey conversations
- **Integration Points**:
  - Provides read/write access to all Thinking Engine components
  - Receives execution feedback from Doing Engine
  - Conversations with Dewey for persistence
  - Conversations with Godot for logging

#### 2.2.4 Decision Package Structure

All Thinking Engine outputs follow a standardized Decision Package format:

```json
{
  "decision_id": "uuid",
  "timestamp": "iso8601",
  "decision_type": "action|response|planning",
  "content": {
    "primary_action": { ... },
    "parameters": { ... },
    "constraints": { ... }
  },
  "reasoning": {
    "path": ["CET", "Rules", "DER"],
    "rule_evaluation": { ... },
    "synthesis_trace": [ ... ],
    "alternatives_considered": [ ... ]
  },
  "confidence": {
    "overall": 0.0-1.0,
    "components": {
      "context": 0.0-1.0,
      "decision": 0.0-1.0,
      "execution": 0.0-1.0
    }
  },
  "metadata": {
    "processing_time_ms": 123,
    "llm_consultations": 0,
    "memory_accesses": 5
  }
}
```

### 2.3 The Doing Engine: Domain-Specific Execution

While the Thinking Engine provides domain-agnostic cognitive capabilities, the Doing Engine implements domain-specific execution logic. This separation allows the same Thinking Engine to be paired with different Doing Engines for different applications.

#### 2.3.1 Doing Engine Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         DOING ENGINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Decision Interpreter                                           │
│    ↓                                                           │
│  Execution Planner                                             │
│    ↓                                                           │
│  Resource Manager                                              │
│    ↓                                                           │
│  Action Executors                                              │
│    ├─> Tool Executor                                           │
│    ├─> API Orchestrator                                        │
│    ├─> UI Renderer                                             │
│    └─> External Integrations                                   │
│    ↓                                                           │
│  Result Collector                                              │
│    ↓                                                           │
│  Feedback Generator                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.3.2 Core Components

**1. Decision Interpreter**
- Parses decision packages from Thinking Engine
- Validates decisions against current capabilities
- Translates abstract actions to concrete operations

**2. Execution Planner**
- Decomposes complex actions into steps
- Orders operations for optimal execution
- Handles dependencies between actions

**3. Resource Manager**
- Tracks available resources (files, connections, etc.)
- Manages resource allocation and cleanup
- Prevents resource conflicts

**4. Action Executors**
- Domain-specific execution modules
- Examples:
  - **Tool Executor**: Runs CLI commands, scripts
  - **API Orchestrator**: Manages external API calls
  - **UI Renderer**: Generates user interfaces
  - **External Integrations**: Connects to third-party systems

**5. Result Collector**
- Gathers execution outcomes
- Captures errors and exceptions
- Assembles comprehensive result packages

**6. Feedback Generator**
- Transforms results into learning feedback
- Identifies patterns in successes/failures
- Sends structured updates to State Manager

#### 2.3.3 Doing Engine Patterns

**Pattern 1: Tool Execution (Hopper)**
```python
class ToolExecutionEngine(DoingEngine):
    def __init__(self):
        self.executors = {
            'bash': BashExecutor(),
            'python': PythonExecutor(),
            'file_ops': FileOperationsExecutor()
        }
    
    def execute_decision(self, decision):
        tool = decision.content.primary_action.tool
        if tool not in self.executors:
            return ErrorResult("Unknown tool")
        
        executor = self.executors[tool]
        result = executor.execute(decision.content.parameters)
        
        return self.generate_feedback(decision, result)
```

**Pattern 2: API Orchestration (Grace)**
```python
class APIOrchestrationEngine(DoingEngine):
    def __init__(self):
        self.api_clients = {
            'database': DatabaseClient(),
            'web_framework': WebFrameworkClient(),
            'auth_service': AuthServiceClient()
        }
    
    def execute_decision(self, decision):
        orchestration = self.plan_api_calls(decision)
        results = []
        
        for step in orchestration:
            client = self.api_clients[step.service]
            result = await client.execute(step.params)
            results.append(result)
            
            if result.failed and step.critical:
                return self.handle_failure(results)
        
        return self.aggregate_results(results)
```

**Pattern 3: Human Interaction**
```python
class HumanInteractionEngine(DoingEngine):
    def __init__(self):
        self.ui_generator = DynamicUIGenerator()
        self.feedback_collector = FeedbackCollector()
    
    def execute_decision(self, decision):
        if decision.content.primary_action.type == "render_ui":
            ui = self.ui_generator.generate(decision.content.parameters)
            return self.display_and_collect(ui)
        
        elif decision.content.primary_action.type == "request_input":
            return self.feedback_collector.collect(
                decision.content.parameters.prompt,
                decision.content.parameters.constraints
            )
```

**Pattern 4: Hybrid Execution**
```python
class HybridExecutionEngine(DoingEngine):
    def __init__(self):
        self.tool_engine = ToolExecutionEngine()
        self.api_engine = APIOrchestrationEngine()
        self.ui_engine = HumanInteractionEngine()
    
    def execute_decision(self, decision):
        execution_type = decision.content.execution_type
        
        if execution_type == "tool":
            return self.tool_engine.execute(decision)
        elif execution_type == "api":
            return self.api_engine.execute(decision)
        elif execution_type == "ui":
            return self.ui_engine.execute(decision)
        elif execution_type == "composite":
            return self.execute_composite(decision)
```

#### 2.3.4 Doing Engine Integration with MAD Ecosystem

Doing Engines may need to consult other MADs for specialized capabilities:

**Example: Code Generation via Fiedler**
```python
def generate_code(self, specification):
    # Initiate conversation with Fiedler
    response = self.mad_conversation(
        target="fiedler",
        capability="code_generation",
        params={
            "language": specification.language,
            "requirements": specification.requirements,
            "constraints": specification.constraints,
            "examples": specification.examples
        }
    )
    
    # Process multi-model synthesis
    if response.confidence > 0.8:
        return self.validate_and_execute(response.synthesis)
    else:
        return self.request_human_review(response)
```

**Example: File Operations via Horace**
```python
def find_related_files(self, pattern):
    # Conversation with Horace for file catalog
    response = self.mad_conversation(
        target="horace",
        capability="file_search",
        params={
            "pattern": pattern,
            "include_versions": True,
            "max_results": 50
        }
    )
    
    return response.files
```

### 2.4 LLM Orchestra as Universal Capability

The LLM Orchestra, provided by the Fiedler Half-MAD, represents a unique architectural pattern in the MAD ecosystem—a capability that is universally accessible but owned by no single component.

#### 2.4.1 Architecture of LLM Orchestra

```
┌─────────────────────────────────────────────────────────────────┐
│                     FIEDLER HALF-MAD                            │
│                   (LLM Orchestra Provider)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Capability Router                                              │
│    ↓                                                           │
│  Multi-Model Manager                                           │
│    ├─> Gemini 2.0 Interface                                   │
│    ├─> GPT-5 Interface                                        │
│    ├─> Claude 3 Interface                                      │
│    ├─> Grok 4 Interface                                        │
│    └─> [Extensible for new models]                            │
│    ↓                                                           │
│  Prompt Optimizer                                              │
│    ↓                                                           │
│  Parallel Executor                                             │
│    ↓                                                           │
│  Response Synthesizer                                          │
│    ↓                                                           │
│  Confidence Calibrator                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.4.2 Universal Access Pattern

Any component in any MAD can access LLM Orchestra:

**From CET (Context Classification)**:
```python
# When CET encounters ambiguous input
if context_confidence < threshold:
    orchestra_response = self.conversation(
        target="fiedler",
        capability="context_disambiguation",
        params={
            "raw_input": ambiguous_input,
            "possible_intents": candidate_intents,
            "domain_context": domain_info
        }
    )
    return self.integrate_orchestra_insight(
        orchestra_response,
        original_analysis
    )
```

**From DER (Decision Synthesis)**:
```python
# When DER needs multi-model consensus
def synthesize_complex_decision(self, context, constraints):
    orchestra_response = self.conversation(
        target="fiedler",
        capability="decision_synthesis",
        params={
            "context": context.to_dict(),
            "constraints": constraints,
            "alternatives": self.generate_alternatives(),
            "evaluation_criteria": self.criteria
        }
    )
    
    return self.build_decision_package(
        orchestra_response,
        confidence=orchestra_response.aggregate_confidence
    )
```

**From Doing Engine (Code Generation)**:
```python
# When Doing Engine needs to generate code
def generate_implementation(self, spec):
    orchestra_response = self.conversation(
        target="fiedler",
        capability="code_generation",
        params={
            "specification": spec,
            "language": "python",
            "style_guide": self.coding_standards,
            "test_requirements": True
        }
    )
    
    return self.validate_code(orchestra_response.synthesis)
```

#### 2.4.3 Orchestra Capabilities

Fiedler provides several specialized capabilities:

**1. Multi-Model Consultation**
- Queries multiple LLMs in parallel
- Aggregates responses with voting mechanisms
- Identifies consensus and disagreements
- Returns confidence-weighted synthesis

**2. Prompt Optimization**
- Adapts prompts for each model's strengths
- Handles model-specific formatting
- Optimizes token usage
- Maintains prompt libraries

**3. Response Synthesis**
- Combines multiple model outputs
- Resolves contradictions
- Extracts best elements from each
- Produces coherent unified response

**4. Confidence Calibration**
- Tracks model agreement levels
- Adjusts confidence based on consensus
- Identifies high-uncertainty areas
- Provides confidence breakdowns

#### 2.4.4 Cost and Performance Management

The LLM Orchestra includes sophisticated management:

**Cost Controls**:
```python
class CostManager:
    def should_consult_expensive_model(self, request):
        if request.priority == "critical":
            return True
        
        if self.budget_remaining < threshold:
            return False
            
        if request.estimated_tokens > limit:
            return self.request_approval(request)
        
        return True
```

**Performance Optimization**:
```python
class PerformanceOptimizer:
    def optimize_consultation(self, request):
        # Parallel execution for independent queries
        if request.queries_independent:
            return self.parallel_execute(request)
        
        # Sequential with early termination
        if request.needs_consensus:
            return self.sequential_consensus(request)
        
        # Cached response reuse
        if cached := self.cache.get(request.signature):
            return cached
```

---

## 3. Complete MAD Architecture

### 3.1 Full MAD Structure

A Full MAD represents the complete implementation of the dual-engine architecture, integrating all components from the trinity of disciplines into a cohesive autonomous agent.

#### 3.1.1 Architectural Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                           FULL MAD                                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  External Input                                                    │
│       ↓                                                           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    THINKING ENGINE                          │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  CET (ICCM) ──> Rules Engine (IDE) ──> DER (IDE)          │  │
│  │       ↕                ↕                    ↕               │  │
│  │                 State Manager (MAD)                         │  │
│  │                        ↕                                    │  │
│  │              [Conversations with Half-MADs]                 │  │
│  │                                                             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            ↓                                      │
│                     Decision Package                              │
│                            ↓                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    DOING ENGINE                            │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  Decision      Execution     Action      Result            │  │
│  │  Interpreter ──> Planner ──> Executors ──> Collector       │  │
│  │                                  ↕                          │  │
│  │                        [Conversations with                  │  │
│  │                         Half-MADs for capabilities]         │  │
│  │                                                             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            ↓                                      │
│                    Execution Results                              │
│                            ↓                                      │
│                    State Manager Update                           │
│                    (Learning Feedback)                            │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 Component Integration

The Full MAD architecture carefully orchestrates component interactions:

**1. Input Processing Pipeline**:
```
External Input (user, system, sensor)
    ↓
Input Validation & Sanitization
    ↓
CET Transformation
    ↓
Structured Context with Metadata
    ↓
Rules Engine Evaluation
    ↓
[High Confidence Path]     [Low Confidence Path]
    ↓                           ↓
Direct Decision            DER Synthesis
    ↓                           ↓
    └───────────┬───────────────┘
                ↓
         Decision Package
```

**2. State Management Integration**:
- **Continuous Read Access**: All components can query state
- **Controlled Write Access**: Only through defined update protocols
- **Versioned Updates**: Every state change is versioned
- **Rollback Capability**: Can revert to previous states

**3. Half-MAD Conversation Management**:
```python
class ConversationManager:
    def __init__(self):
        self.active_conversations = {}
        self.conversation_history = []
        
    async def initiate_conversation(self, target, capability, params):
        conversation_id = self.generate_id()
        
        # Track conversation
        self.active_conversations[conversation_id] = {
            'target': target,
            'capability': capability,
            'initiated': datetime.now(),
            'status': 'active'
        }
        
        # Execute conversation
        response = await self.mcp_client.request(
            target=target,
            method=f"capability.{capability}",
            params=params
        )
        
        # Log for audit
        self.log_conversation(conversation_id, response)
        
        return response
```

#### 3.1.3 Operational Modes

Full MADs operate in several modes:

**1. Autonomous Mode**:
- Operates independently on assigned tasks
- Makes decisions within defined boundaries
- Escalates only when encountering novel situations
- Example: Hopper completing a development task

**2. Interactive Mode**:
- Engages with human users
- Requests clarification when needed
- Provides explanations for decisions
- Example: Grace helping design a UI

**3. Collaborative Mode**:
- Works with other Full MADs
- Coordinates on complex tasks
- Shares context and decisions
- Example: Multiple Hoppers on large project

**4. Learning Mode**:
- Focuses on improving performance
- Analyzes past decisions and outcomes
- Updates semantic memory
- Refines decision patterns

### 3.2 State Manager Specification

The State Manager is the MAD discipline's unique contribution to the Thinking Engine, providing sophisticated memory and world model capabilities.

#### 3.2.1 Memory Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       STATE MANAGER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │ Episodic Memory │  │ Semantic Memory │  │ Working Memory │ │
│  │                 │  │                 │  │                │ │
│  │ • Conversations │  │ • Domain Facts  │  │ • Active Tasks │ │
│  │ • Decisions     │  │ • Learned Rules │  │ • Current Goal │ │
│  │ • Outcomes      │  │ • Patterns      │  │ • Temp Data    │ │
│  │ • Temporal Seq  │  │ • Preferences   │  │ • Attention    │ │
│  └─────────────────┘  └─────────────────┘  └────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     World Model                          │  │
│  │                                                          │  │
│  │ • External State  • Resource Status  • Entity Tracking  │  │
│  │ • Constraints     • Dependencies     • Change History   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Memory Controller                       │  │
│  │                                                          │  │
│  │ • Read/Write APIs  • Indexing      • Garbage Collection │  │
│  │ • Versioning       • Persistence   • Recovery           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.2.2 Memory Component Details

**1. Episodic Memory**

Purpose: Stores sequential experiences and their outcomes

Structure:
```python
class EpisodicMemory:
    def __init__(self):
        self.episodes = []  # Chronological list
        self.index = {}     # Fast lookup indices
        
    def add_episode(self, episode):
        episode_entry = {
            'id': generate_uuid(),
            'timestamp': datetime.now(),
            'type': episode.type,  # conversation, decision, execution
            'content': episode.content,
            'participants': episode.participants,
            'outcome': episode.outcome,
            'metadata': episode.metadata
        }
        
        self.episodes.append(episode_entry)
        self.update_indices(episode_entry)
        
    def recall_similar(self, context, limit=5):
        # Find episodes with similar context
        similarities = []
        for episode in self.episodes:
            score = self.compute_similarity(context, episode.content)
            similarities.append((score, episode))
        
        return sorted(similarities, reverse=True)[:limit]
```

Key Features:
- Temporal ordering preservation
- Similarity-based retrieval
- Causal chain tracking
- Conversation with Dewey for long-term storage

**2. Semantic Memory**

Purpose: Stores general knowledge and learned patterns

Structure:
```python
class SemanticMemory:
    def __init__(self):
        self.facts = KnowledgeGraph()
        self.rules = RuleSet()
        self.patterns = PatternLibrary()
        
    def add_fact(self, subject, predicate, object, confidence):
        self.facts.add_triple(
            subject=subject,
            predicate=predicate,
            object=object,
            metadata={'confidence': confidence, 'source': context}
        )
        
    def learn_pattern(self, examples, outcome_labels):
        pattern = self.pattern_learner.extract(examples, outcome_labels)
        if pattern.confidence > threshold:
            self.patterns.add(pattern)
            self.notify_rules_engine(pattern)
    
    def query(self, query_type, params):
        if query_type == "fact":
            return self.facts.query(params)
        elif query_type == "rule":
            return self.rules.match(params)
        elif query_type == "pattern":
            return self.patterns.find(params)
```

Key Features:
- Knowledge graph for facts
- Pattern recognition and storage
- Rule refinement suggestions
- Confidence tracking

**3. Working Memory**

Purpose: Maintains active context and temporary state

Structure:
```python
class WorkingMemory:
    def __init__(self, capacity=100):
        self.active_items = OrderedDict()
        self.capacity = capacity
        self.attention_weights = {}
        
    def add(self, key, value, importance=1.0):
        # Remove LRU item if at capacity
        if len(self.active_items) >= self.capacity:
            self.evict_lru()
            
        self.active_items[key] = {
            'value': value,
            'added': datetime.now(),
            'accessed': datetime.now(),
            'access_count': 1,
            'importance': importance
        }
        
        self.update_attention(key, importance)
    
    def get(self, key):
        if key in self.active_items:
            item = self.active_items[key]
            item['accessed'] = datetime.now()
            item['access_count'] += 1
            return item['value']
        return None
    
    def get_focus_items(self, n=5):
        # Return highest attention items
        sorted_items = sorted(
            self.attention_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [self.active_items[k] for k, _ in sorted_items[:n]]
```

Key Features:
- Limited capacity with LRU eviction
- Attention-based prioritization
- Fast access for active data
- Automatic cleanup

**4. World Model**

Purpose: Represents external state and constraints

Structure:
```python
class WorldModel:
    def __init__(self):
        self.entities = {}      # Tracked external entities
        self.resources = {}     # Available resources
        self.constraints = {}   # Active constraints
        self.dependencies = Graph()  # Dependency relationships
        
    def update_entity(self, entity_id, properties):
        if entity_id not in self.entities:
            self.entities[entity_id] = Entity(entity_id)
            
        entity = self.entities[entity_id]
        old_state = entity.get_state()
        entity.update(properties)
        
        # Track state changes
        self.record_state_change(entity_id, old_state, entity.get_state())
        
        # Check constraint violations
        violations = self.check_constraints(entity_id)
        if violations:
            self.handle_violations(violations)
    
    def add_dependency(self, from_entity, to_entity, dep_type):
        self.dependencies.add_edge(
            from_entity,
            to_entity,
            type=dep_type,
            created=datetime.now()
        )
        
    def get_entity_state(self, entity_id):
        return self.entities.get(entity_id, None)
    
    def get_available_resources(self, resource_type):
        return [r for r in self.resources.values() 
                if r.type == resource_type and r.available]
```

Key Features:
- Entity state tracking
- Resource availability monitoring
- Constraint enforcement
- Dependency graph maintenance

#### 3.2.3 Memory Controller Operations

The Memory Controller provides unified access to all memory components:

**1. Read Operations**:
```python
class MemoryController:
    def read(self, query):
        results = []
        
        # Query across memory types based on request
        if query.include_episodic:
            episodic_results = self.episodic.recall(query)
            results.extend(episodic_results)
            
        if query.include_semantic:
            semantic_results = self.semantic.query(query)
            results.extend(semantic_results)
            
        if query.include_working:
            working_results = self.working.search(query)
            results.extend(working_results)
            
        if query.include_world:
            world_results = self.world.query(query)
            results.extend(world_results)
            
        # Rank and filter results
        ranked_results = self.rank_results(results, query)
        return ranked_results[:query.limit]
```

**2. Write Operations**:
```python
def write(self, write_request):
    # Validate write permission
    if not self.authorize_write(write_request):
        raise PermissionError("Unauthorized write attempt")
    
    # Version current state
    version_id = self.create_version()
    
    try:
        # Execute write based on target
        if write_request.target == "episodic":
            self.episodic.add(write_request.content)
        elif write_request.target == "semantic":
            self.semantic.update(write_request.content)
        elif write_request.target == "working":
            self.working.set(write_request.key, write_request.value)
        elif write_request.target == "world":
            self.world.update(write_request.entity, write_request.changes)
            
        # Log write for audit
        self.audit_log.record_write(write_request, version_id)
        
    except Exception as e:
        # Rollback on failure
        self.rollback_to_version(version_id)
        raise e
```

**3. Persistence via Dewey**:
```python
async def persist_to_dewey(self):
    # Prepare memory snapshot
    snapshot = {
        'mad_id': self.mad_id,
        'timestamp': datetime.now(),
        'episodic': self.episodic.serialize(),
        'semantic': self.semantic.serialize(),
        'world': self.world.serialize()
        # Working memory is not persisted (temporary by design)
    }
    
    # Conversation with Dewey
    response = await self.conversation_manager.initiate(
        target='dewey',
        capability='store_snapshot',
        params={
            'snapshot': snapshot,
            'compression': 'gzip',
            'encryption': 'aes256'
        }
    )
    
    return response.snapshot_id
```

**4. Learning Integration**:
```python
def integrate_execution_feedback(self, execution_result):
    # Update episodic memory
    self.episodic.add_episode({
        'type': 'execution',
        'decision_id': execution_result.decision_id,
        'outcome': execution_result.outcome,
        'metrics': execution_result.metrics
    })
    
    # Extract patterns for semantic memory
    if execution_result.success:
        pattern = self.pattern_extractor.extract(
            decision=execution_result.decision,
            context=execution_result.context,
            outcome=execution_result.outcome
        )
        
        if pattern.confidence > 0.7:
            self.semantic.add_pattern(pattern)
    
    # Update world model
    for state_change in execution_result.state_changes:
        self.world.update_entity(
            state_change.entity_id,
            state_change.new_properties
        )
```

### 3.3 Integration Boundaries

The MAD framework defines clear boundaries between disciplines and components, ensuring clean integration and maintainability.

#### 3.3.1 ICCM → MAD Boundary

The boundary between ICCM (Context Engineering) and MAD (Agent Assembly) is defined by the CET component interface:

**Interface Specification**:
```python
# From ICCM Paper 00
class CETInterface:
    """
    Standard interface for CET components provided by ICCM
    """
    
    def transform(self, raw_input: RawInput) -> StructuredContext:
        """
        Transform raw input into structured context
        
        Args:
            raw_input: Unprocessed input from external sources
            
        Returns:
            StructuredContext with classification and metadata
        """
        pass
    
    def get_confidence(self) -> float:
        """Return confidence in transformation"""
        pass
    
    def get_ambiguities(self) -> List[Ambiguity]:
        """Return detected ambiguities requiring resolution"""
        pass

# MAD integration
class ThinkingEngineIntegration:
    def __init__(self, cet_implementation: CETInterface):
        self.cet = cet_implementation
        
    def process_input(self, raw_input):
        # Use CET through standard interface
        context = self.cet.transform(raw_input)
        
        # Handle ambiguities if needed
        if context.confidence < 0.7:
            resolved_context = self.resolve_ambiguities(
                context,
                self.cet.get_ambiguities()
            )
            return resolved_context
            
        return context
```

**Data Contracts**:
```python
# Structured Context (CET output, Rules/DER input)
@dataclass
class StructuredContext:
    classification: str
    intent: Intent
    entities: List[Entity]
    metadata: Dict[str, Any]
    confidence: float
    processing_trace: List[ProcessingStep]
    ambiguities: List[Ambiguity]
    timestamp: datetime
```

**Integration Guidelines**:
1. MAD never modifies CET internals
2. CET doesn't access MAD State Manager directly
3. All communication through defined interfaces
4. Version compatibility managed through interface versioning

#### 3.3.2 IDE → MAD Boundary

The boundary between IDE (Decision Engineering) and MAD involves two components:

**Rules Engine Interface**:
```python
# From IDE Paper 00
class RulesEngineInterface:
    """
    Standard interface for Rules Engine from IDE
    """
    
    def evaluate(self, context: StructuredContext) -> RuleEvaluation:
        """
        Evaluate context against rule set
        
        Returns:
            RuleEvaluation with matched rules and confidence
        """
        pass
    
    def get_applicable_rules(self, context: StructuredContext) -> List[Rule]:
        """Get all rules that could apply to context"""
        pass
    
    def update_rules(self, rule_updates: List[RuleUpdate]) -> bool:
        """Apply rule updates (additions, modifications, deletions)"""
        pass

# DER Interface
class DERInterface:
    """
    Standard interface for Decision Engineering Recommender
    """
    
    def synthesize(self, 
                   context: StructuredContext,
                   rule_evaluation: RuleEvaluation,
                   constraints: List[Constraint]) -> DecisionPackage:
        """
        Synthesize decision from context and rules
        
        Returns:
            Complete DecisionPackage with reasoning trace
        """
        pass
    
    def set_llm_orchestra_client(self, client: ConversationClient):
        """Configure LLM Orchestra access"""
        pass
```

**MAD Integration Pattern**:
```python
class ThinkingEngineIDEIntegration:
    def __init__(self, 
                 rules_engine: RulesEngineInterface,
                 der: DERInterface):
        self.rules = rules_engine
        self.der = der
        
    def make_decision(self, structured_context):
        # First try rules engine
        rule_eval = self.rules.evaluate(structured_context)
        
        if rule_eval.confidence > 0.9:
            # High confidence rule match
            return self.create_decision_from_rules(rule_eval)
        
        # Need DER synthesis
        decision = self.der.synthesize(
            context=structured_context,
            rule_evaluation=rule_eval,
            constraints=self.get_active_constraints()
        )
        
        return decision
```

**Decision Package Contract**:
```python
@dataclass
class DecisionPackage:
    decision_id: str
    decision_type: DecisionType
    content: DecisionContent
    reasoning: ReasoningTrace
    confidence: ConfidenceMetrics
    metadata: DecisionMetadata
    
    def to_doing_engine_format(self) -> DoingEngineInput:
        """Convert to format expected by Doing Engine"""
        pass
```

#### 3.3.3 MAD → Half-MAD Boundary

All MAD to Half-MAD communication follows the conversation protocol:

**Conversation Protocol**:
```python
class ConversationProtocol:
    """
    Standard protocol for MAD conversations
    """
    
    async def initiate_conversation(self,
                                   target_mad: str,
                                   capability: str,
                                   params: Dict[str, Any]) -> ConversationResponse:
        """
        Start conversation with another MAD
        
        Args:
            target_mad: Identifier of target MAD
            capability: Capability being requested
            params: Parameters for the capability
            
        Returns:
            ConversationResponse with results
        """
        
        # Create conversation context
        context = ConversationContext(
            initiator=self.mad_id,
            target=target_mad,
            capability=capability,
            correlation_id=generate_correlation_id()
        )
        
        # Send via MCP
        response = await self.mcp_client.request(
            method=f"{target_mad}.{capability}",
            params=params,
            context=context
        )
        
        return response
```

**Capability Discovery**:
```python
async def discover_capabilities(self, target_mad: str) -> List[Capability]:
    """
    Discover what capabilities a MAD provides
    """
    response = await self.initiate_conversation(
        target_mad=target_mad,
        capability="list_capabilities",
        params={}
    )
    
    return response.capabilities
```

**Example Integration Patterns**:

1. **Fiedler (LLM Orchestra)**:
```python
async def consult_llm_orchestra(self, query):
    response = await self.initiate_conversation(
        target_mad="fiedler",
        capability="multi_model_consultation",
        params={
            "query": query,
            "models": ["gemini-2", "gpt-5", "claude-3"],
            "voting_method": "weighted_confidence",
            "timeout_ms": 5000
        }
    )
    return response
```

2. **Dewey (Storage)**:
```python
async def store_conversation(self, conversation):
    response = await self.initiate_conversation(
        target_mad="dewey",
        capability="store",
        params={
            "data": conversation.serialize(),
            "tags": conversation.tags,
            "retention": "permanent",
            "indexing": ["participants", "timestamp", "topic"]
        }
    )
    return response.storage_id
```

3. **Godot (Logging)**:
```python
async def log_event(self, event):
    # Fire and forget pattern for logging
    await self.initiate_conversation(
        target_mad="godot",
        capability="log",
        params={
            "level": event.level,
            "message": event.message,
            "context": event.context,
            "correlation_id": self.correlation_id
        }
    )
```

---

## 4. Half-MAD Specifications

Half-MADs represent a key architectural innovation in the MAD ecosystem—specialized agents that provide focused capabilities without the overhead of full cognitive architectures. Each Half-MAD is designed to excel at specific tasks while maintaining the conversation-based integration pattern.

### 4.1 Fiedler: LLM Orchestra Provider

**Purpose**: Provides multi-model LLM consultation as a capability to all MAD components

**Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│                    FIEDLER HALF-MAD                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Minimal Thinking Engine:                               │
│    • Capability Router                                  │
│    • Request Validator                                  │
│    • Response Formatter                                 │
│                                                         │
│  Specialized Components:                                │
│    • Model Registry                                     │
│    • Prompt Library                                     │
│    • Model Interfaces:                                  │
│      - Gemini 2.0 Experimental                         │
│      - GPT-5                                           │
│      - Claude 3 Opus                                   │
│      - Grok 4                                          │
│    • Response Synthesizer                              │
│    • Cost Tracker                                      │
│    • Performance Monitor                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Capabilities Provided**:
1. `multi_model_consultation`: Query multiple models and synthesize responses
2. `single_model_query`: Query specific model directly
3. `prompt_optimization`: Optimize prompts for specific models
4. `cost_estimation`: Estimate token usage and costs
5. `model_selection`: Recommend best models for specific tasks

**Conversation Interface**:
```python
# Request format
{
    "capability": "multi_model_consultation",
    "params": {
        "query": "Complex question requiring synthesis",
        "context": { /* relevant context */ },
        "models": ["gemini-2", "gpt-5", "claude-3"],
        "constraints": {
            "max_tokens": 2000,
            "temperature": 0.7,
            "voting_method": "weighted_confidence"
        }
    }
}

#