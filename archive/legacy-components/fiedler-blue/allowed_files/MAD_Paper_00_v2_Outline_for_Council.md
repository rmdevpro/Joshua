# Paper 00: The MAD Ecosystem - Master Document v2.0 Outline

**Version:** Draft v2.0 for Council of Elders Review
**Date:** 2025-10-06
**Status:** OUTLINE - Awaiting Council Synthesis
**Repository:** Joshua (MAD ecosystem)
**Purpose:** Update MAD Paper 00 to reflect corrected trinity understanding and integrate ICCM Paper 00 and IDE Paper 00

---

## Context for Council of Elders

You are being asked to review and synthesize an UPDATED version of the MAD Ecosystem Master Document (Paper 00). Since the original v1.0 synthesis, significant clarifications have emerged:

**Critical Corrections from v1.0:**

1. **Trinity Corrected:**
   - **ICCM** ≠ Infrastructure; ICCM = Context Engineering discipline producing **CET component** of MAD Thinking Engine
   - **IDE** = NEW discipline (Decision Engineering) producing **Rules Engine + DER components** of MAD Thinking Engine
   - **MAD** = Agent Assembly discipline integrating all components into complete agents

2. **Terminology Corrections:**
   - MADs communicate via **conversations** (NOT "service calls" or "API requests")
   - MADs provide **capabilities** (NOT "services" or "functions")
   - **Half-MADs** = MADs with minimal Thinking Engines (Fiedler, Dewey, Godot, Marco, Horace, Gates, Playfair)
   - **Full MADs** = Complete Thinking + Doing Engines (Hopper, Grace)
   - NO "Infrastructure Classical" - Fiedler/Dewey/etc are Half-MADs, not infrastructure

3. **Thinking Engine Composition:**
   ```
   Thinking Engine = CET (from ICCM) + Rules Engine (from IDE) + DER (from IDE) + State Manager (from MAD)
   ```

4. **LLM Orchestra:**
   - Fiedler MAD is a **Half-MAD** providing LLM Orchestra **capability**
   - Available to ALL components (Thinking Engine, Doing Engine) via **conversations**
   - NOT owned exclusively by any discipline

**Your Task:**
Update the MAD Paper 00 v1.0 to reflect these corrections while preserving its excellent structure, theoretical foundation, and hierarchical paper organization. Produce a comprehensive Paper 00 v2.0 that:

1. Correctly positions MAD as the **Agent Assembly** discipline
2. Integrates ICCM Paper 00 (Context Engineering) and IDE Paper 00 (Decision Engineering) as prerequisite disciplines
3. Clarifies the complete MAD Thinking Engine architecture
4. Uses correct terminology (conversations, capabilities, Half-MADs, Full MADs)
5. Updates all examples, diagrams, and references
6. Maintains the excellent 14-paper hierarchical structure

---

## Key Architectural Facts (MUST BE REFLECTED)

**The Trinity:**
| Discipline | Repository | Output | Thinking Engine Contribution |
|------------|-----------|--------|------------------------------|
| **ICCM** | ICCM | CET | Component #1: Context transformation |
| **IDE** | Joshua | Rules Engine + DER | Components #2-3: Decision-making |
| **MAD** | Joshua | Complete agents | Component #4 (State Manager) + Doing Engine + assembly |

**MAD Thinking Engine = CET + Rules Engine + DER + State Manager**

**Correct Terminology:**
- **Conversation:** Communication between MADs (not "service call," "API request," or "RPC")
- **Capability:** What a MAD provides (not "service" or "function")
- **Half-MAD:** MAD with minimal/incomplete Thinking Engine (current: Fiedler, Dewey, Godot, Marco, Horace, Gates, Playfair)
- **Full MAD:** Complete Thinking + Doing Engine (Hopper, Grace being built)
- **LLM Orchestra:** Capability provided by Fiedler Half-MAD, accessible to all components

**What Changed Since v1.0:**
- ICCM Paper 00 completed (defines Context Engineering discipline and CET)
- IDE Paper 00 completed (defines Decision Engineering discipline, Rules Engine, and DER)
- Terminology standardized across all papers
- Trinity clarified: ICCM + IDE + MAD (not ICCM as infrastructure)

---

## Proposed Updated Outline Structure

### Executive Summary (UPDATED)

- **MAD = Agent Assembly discipline** completing the trinity
- Produces **complete agents** by integrating components from ICCM and IDE
- **Thinking Engine** = CET (ICCM) + Rules Engine (IDE) + DER (IDE) + State Manager (MAD)
- **Doing Engine** = Domain-specific execution capabilities
- **Half-MADs** provide capabilities to other MADs via conversations
- **Full MADs** (Hopper, Grace) demonstrate complete Thinking + Doing architecture
- Proposed 14-paper hierarchical structure for MAD discipline

### 1. Introduction: The MAD Ecosystem (UPDATED)

#### 1.1 What is the MAD Ecosystem?

- Definition of Multipurpose Agentic Duo (MAD) as cognitive architecture
- **Key Innovation:** Formal separation of Thinking (cognition) from Doing (execution)
- MAD as **Agent Assembly discipline** (NOT infrastructure provider)
- The MAD ecosystem enables building agents that are transparent, auditable, controllable

#### 1.2 The Trinity of Disciplines (NEW SECTION)

**Complete the foundational trinity:**

1. **ICCM (Context Engineering):**
   - Repository: ICCM
   - Discipline: How to transform raw input into optimized, decision-ready context
   - Output: CET (Context Engineering Transformer)
   - Papers: ICCM Paper 00 + Papers 01-14
   - Contributes to MAD: Component #1 of Thinking Engine

2. **IDE (Intelligent Decision Engineering):**
   - Repository: Joshua/IDE
   - Discipline: How to make transparent, auditable, hybrid decisions
   - Output: Rules Engine (deterministic) + DER (synthesis)
   - Papers: IDE Paper 00 + Papers 01-13
   - Contributes to MAD: Components #2-3 of Thinking Engine

3. **MAD (Intelligent Agentic Engineering):**
   - Repository: Joshua/MAD
   - Discipline: How to assemble complete agents from components
   - Output: Complete MAD implementations (Hopper, Grace, etc.)
   - Papers: MAD Paper 00 + Papers 01-14 (this document)
   - Contributes: State Manager (Component #4 of Thinking Engine) + Doing Engine + integration

**Relationship:**
```
ICCM Paper 00 ──┐
                 ├──> MAD Paper 00 (Agent Assembly)
IDE Paper 00 ───┘
```

MAD Paper 00 assumes familiarity with ICCM Paper 00 and IDE Paper 00, which define the components MAD assembles.

#### 1.3 Why Dual-Engine Architecture Matters (KEEP FROM v1.0, UPDATE EXAMPLES)

- Separation of Concerns: Thinking vs Doing
- Cognitive Architecture Heritage (SOAR, ACT-R) + Modern LLM frameworks
- Advantages: testability, auditability, safety, composability
- Real-world validation: Hopper and Grace implementations

#### 1.4 Half-MADs vs Full MADs (NEW SECTION)

**Half-MADs:**
- Definition: MADs with minimal/incomplete Thinking Engines
- Purpose: Provide specialized capabilities to other MADs
- Examples: Fiedler (LLM Orchestra), Dewey (conversation retrieval), Godot (logging), Marco (MCP proxy), Horace (file catalog), Gates (document generation), Playfair (diagram generation)
- Communication: Via conversations (MCP protocol)
- Evolution path: Will eventually upgrade to Full MADs

**Full MADs:**
- Definition: Complete Thinking Engine (CET + Rules + DER + State Manager) + Doing Engine
- Purpose: Autonomous agents capable of complex multi-step tasks
- Examples: Hopper (autonomous development), Grace (intelligent system UI)
- Communication: Have conversations with Half-MADs to access capabilities
- Architecture: This paper defines how to build Full MADs

**MAD-to-MAD Interactions:**
- All interactions are **conversations** (not service calls)
- MADs **invoke capabilities** (not call services)
- Protocol: MCP (Model Context Protocol)
- Fiedler MAD provides LLM Orchestra capability accessible to all

#### 1.5 Document Organization (UPDATE)

- This Paper 00 assumes readers have reviewed ICCM Paper 00 and IDE Paper 00
- Focuses on **Agent Assembly**: how to integrate CET, Rules, DER, State Manager, and Doing Engine
- Defines the State Manager component (the 4th Thinking Engine component)
- Specifies Doing Engine patterns for different domains
- Proposes 14-paper hierarchical structure for MAD discipline

### 2. Theoretical Foundation (UPDATE)

#### 2.1 Cognitive Architecture Principles (KEEP FROM v1.0, MINOR UPDATES)

- Two-System Model (System 1 vs System 2)
- Structured Reasoning with clean boundaries
- Advantages over monolithic architectures

#### 2.2 The Thinking Engine: Complete Specification (MAJOR UPDATE)

**The MAD Thinking Engine integrates four components from three disciplines:**

```
Thinking Engine Architecture:

┌─────────────────────────────────────────────────────────────┐
│                    THINKING ENGINE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CET (from ICCM - Context Engineering)                  │
│     • Transforms raw input → structured context           │
│     • Classification, routing, optimization                │
│     • Paper: ICCM Paper 00                                 │
│                                                             │
│  2. Rules Engine (from IDE - Decision Engineering)         │
│     • Deterministic decision-making for known scenarios    │
│     • Policy enforcement, safety guardrails                │
│     • Paper: IDE Paper 00                                  │
│                                                             │
│  3. DER (from IDE - Decision Engineering)                  │
│     • Synthesis for complex/ambiguous decisions           │
│     • Confidence scoring, reasoning traces                │
│     • Optional LLM Orchestra consultation                  │
│     • Paper: IDE Paper 00                                  │
│                                                             │
│  4. State Manager (from MAD - Agent Assembly)              │
│     • Memory and world model management                    │
│     • Episodic + semantic + working memory                │
│     • This paper                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Component Interactions:**

1. **Input arrives** → CET transforms into structured context
2. **CET output** → Rules Engine evaluates against policies
3. **Rules output** → DER synthesizes (may consult LLM Orchestra via Fiedler MAD conversation)
4. **State Manager** → Provides memory/world state to all components, receives updates
5. **DER output** → Final decision delivered to Doing Engine

**Each component is separately specified:**
- **CET:** Defined in ICCM Paper 00, Papers 01-03
- **Rules Engine:** Defined in IDE Paper 00, Papers 01-02
- **DER:** Defined in IDE Paper 00, Papers 03-05
- **State Manager:** Defined in this paper (MAD Paper 00), Papers 02-03

#### 2.3 The Doing Engine: Domain-Specific Execution (UPDATE)

**Definition:** The Doing Engine is the domain-specific component that executes decisions from the Thinking Engine and interacts with the external world.

**Key Characteristics:**
- Receives structured decisions from DER
- Executes actions with safeguards
- Reports outcomes back to State Manager for learning
- Domain-specific (CLI for Hopper, web dev for Grace, etc.)
- Swappable: Same Thinking Engine can pair with different Doing Engines

**Doing Engine Patterns:**
- Tool Execution (Hopper: bash, file ops, code execution)
- API Orchestration (Grace: web frameworks, databases)
- Human Interaction (UI rendering, feedback collection)
- Hybrid (combine multiple patterns)

**May consult LLM Orchestra:** Doing Engines can have conversations with Fiedler MAD for code generation, complex transformations, etc.

#### 2.4 LLM Orchestra as Universal Capability (NEW SECTION)

**Fiedler MAD provides LLM Orchestra capability:**
- Multi-model consultation (Gemini, GPT, Claude, Grok, etc.)
- Accessible to ANY component via conversation
- NOT owned by Thinking Engine or Doing Engine
- Examples of usage:
  - CET: May consult for ambiguous classification
  - Rules Engine: Generally doesn't need it (deterministic)
  - DER: Frequently consults for novel/ambiguous decisions
  - Doing Engine: May consult for code generation, transformation

**Protocol:**
- DER (or other component) initiates conversation with Fiedler MAD
- Sends structured query with context and constraints
- Fiedler returns multi-model synthesis
- Requesting component synthesizes results with other inputs

### 3. Complete MAD Architecture (MAJOR UPDATE)

#### 3.1 Full MAD Structure

```
┌──────────────────────────────────────────────────────────┐
│                    FULL MAD                               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │         THINKING ENGINE                        │    │
│  │                                                │    │
│  │  CET ──> Rules Engine ──> DER                 │    │
│  │    ↕           ↕            ↕                  │    │
│  │         State Manager                          │    │
│  │            ↕                                   │    │
│  │     (may consult Fiedler MAD for              │    │
│  │      LLM Orchestra capability)                │    │
│  └────────────────────────────────────────────────┘    │
│                      ↓                                  │
│                 Decision                                │
│                      ↓                                  │
│  ┌────────────────────────────────────────────────┐    │
│  │         DOING ENGINE                           │    │
│  │                                                │    │
│  │  Domain-specific execution                    │    │
│  │  (CLI tools, web frameworks, APIs, etc.)      │    │
│  │                                                │    │
│  │  (may also consult Fiedler MAD for            │    │
│  │   code generation, transformations)           │    │
│  └────────────────────────────────────────────────┘    │
│                      ↓                                  │
│                 Execution                               │
│                  Outcome                                │
│                      ↓                                  │
│               State Manager                             │
│            (learning feedback)                          │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

#### 3.2 State Manager Specification (EXPAND FROM v1.0)

**Responsibility:** Memory and world model management for the Thinking Engine

**Components:**
1. **Episodic Memory:** Conversation history, decision logs, execution outcomes
2. **Semantic Memory:** Domain knowledge, learned patterns, rules refinements
3. **Working Memory:** Active context, current task state, pending commitments
4. **World Model:** External state representation, resource availability, constraints

**Interfaces:**
- Read/Write for CET, Rules Engine, DER
- Append-only decision logs for auditability
- Feedback loop from Doing Engine (execution outcomes)
- Time-travel reads for reproducibility
- Conversations with Dewey Half-MAD for persistent storage
- Conversations with Godot Half-MAD for logging

**Integration with Half-MADs:**
- **Dewey:** Long-term conversation storage and retrieval
- **Godot:** Real-time logging and tracing
- **Marco:** MCP conversation proxying
- **Horace:** File catalog and versioning

#### 3.3 Integration Boundaries (NEW SECTION)

**ICCM → MAD Boundary:**
- ICCM provides: CET component specification (ICCM Papers 00-03)
- MAD consumes: Integrates CET as Component #1 of Thinking Engine
- Interface: Structured context schema (defined in ICCM Paper 00)

**IDE → MAD Boundary:**
- IDE provides: Rules Engine + DER component specifications (IDE Papers 00-05)
- MAD consumes: Integrates as Components #2-3 of Thinking Engine
- Interface: Decision package schema (defined in IDE Paper 00)

**MAD → Half-MAD Boundary:**
- MAD defines: Conversation protocols, capability invocation patterns
- Half-MADs provide: Specialized capabilities (logging, storage, LLM Orchestra, etc.)
- Interface: MCP protocol (conversations, not service calls)

### 4. Hierarchical Paper Structure (UPDATE)

Update the 14-paper structure to reflect the trinity and remove "infrastructure" language.

**Act 1 - Foundations:**
- **Paper 01:** MAD Core Architecture and Agent Assembly Discipline
- **Paper 02:** State Manager Specification (Episodic, Semantic, Working Memory, World Model)
- **Paper 03:** Doing Engine Patterns and Domain-Specific Execution

**Act 2 - MAD Integration:**
- **Paper 04:** Integrating CET (from ICCM) into MAD Thinking Engine
- **Paper 05:** Integrating Rules Engine and DER (from IDE) into MAD Thinking Engine
- **Paper 06:** Thinking Engine ↔ Doing Engine Communication Protocols

**Act 3 - MAD Ecosystem:**
- **Paper 07:** Half-MADs: Providing Capabilities to the Ecosystem
- **Paper 08:** MAD-to-MAD Conversations and Capability Invocation
- **Paper 09:** LLM Orchestra Integration Patterns (Fiedler MAD)

**Act 4 - Advanced Topics:**
- **Paper 10:** Multi-MAD Coordination and Collaboration
- **Paper 11:** MAD Testing and Validation Frameworks
- **Paper 12:** MAD Observability and Debugging

**Act 5 - Production and Case Studies:**
- **Paper 13:** Hopper: Autonomous Development MAD Case Study
- **Paper 14:** Grace: Intelligent System UI MAD Case Study

### 5. Implementation Roadmap (UPDATE)

#### Phase 1: Foundation (Hopper/Grace)
- Implement complete Thinking Engine (CET + Rules + DER + State Manager)
- Implement domain-specific Doing Engines
- Validate Half-MAD conversations (Fiedler, Dewey, Godot)
- Demonstrate full MAD lifecycle

#### Phase 2: Ecosystem Maturity
- Expand Half-MAD capabilities (Marco, Horace, Gates, Playfair)
- Enhance State Manager with learning feedback loops
- Implement multi-MAD coordination protocols
- Build MAD testing/validation frameworks

#### Phase 3: Production Scale
- Upgrade Half-MADs to Full MADs (give them complete Thinking Engines)
- Advanced observability and debugging tools
- Production deployment patterns
- Community templates and best practices

### 6. Success Metrics (UPDATE)

#### 6.1 Thinking Engine Metrics
- Decision quality (accuracy, confidence calibration)
- Context transformation effectiveness (CET metrics from ICCM)
- Rule coverage and DER invocation rates (IDE metrics)
- State Manager memory efficiency and recall accuracy

#### 6.2 Doing Engine Metrics
- Execution success rates
- Task completion latency
- Error recovery effectiveness
- Domain-specific KPIs (code quality for Hopper, UI quality for Grace)

#### 6.3 MAD Integration Metrics
- Thinking ↔ Doing handoff latency
- Decision-to-execution success rate
- End-to-end task completion rates
- Audit trail completeness

#### 6.4 Ecosystem Metrics
- Half-MAD capability availability
- MAD-to-MAD conversation overhead
- LLM Orchestra utilization patterns
- System-wide observability coverage

### 7. Relationship to ICCM and IDE (NEW SECTION)

**MAD's Role in the Trinity:**

MAD is the **Agent Assembly** discipline that completes the trinity. It:

1. **Consumes from ICCM:**
   - CET specification and implementation
   - Context transformation patterns
   - Integration guidelines for Component #1

2. **Consumes from IDE:**
   - Rules Engine specification and implementation
   - DER specification and implementation
   - Decision-making patterns
   - Integration guidelines for Components #2-3

3. **Contributes:**
   - State Manager specification (Component #4)
   - Doing Engine patterns
   - Complete agent assembly architecture
   - MAD-to-MAD conversation protocols
   - Hopper and Grace reference implementations

**Reading Order for Complete Understanding:**
1. **ICCM Paper 00** → Understand Context Engineering discipline
2. **IDE Paper 00** → Understand Decision Engineering discipline
3. **MAD Paper 00** (this document) → Understand Agent Assembly discipline

### 8. Half-MAD Specifications (EXPAND FROM v1.0)

For each Half-MAD, specify:

**Current Half-MADs:**
- **Fiedler:** LLM Orchestra (multi-model consultation)
- **Dewey:** Conversation storage and retrieval
- **Godot:** Real-time logging and tracing
- **Marco:** MCP conversation proxy
- **Horace:** File catalog and versioning
- **Gates:** Document generation (Markdown → ODT)
- **Playfair:** Diagram generation (Mermaid, Graphviz)

**For each:**
- Current capabilities provided
- Conversation protocol
- Integration patterns
- Evolution path to Full MAD (future Thinking Engine design)

### 9. Publication Strategy (UPDATE)

#### 9.1 Venue Targeting (KEEP FROM v1.0)

**Primary venues:** ICSE, FSE, AAMAS, AAAI

**Secondary venues:** Domain-specific (NeurIPS for ML, CHI for HCI, etc.)

#### 9.2 Publication Dependencies (NEW)

**Prerequisites:**
- ICCM Papers 00-03 (Context Engineering foundation)
- IDE Papers 00-05 (Decision Engineering foundation)

**MAD Paper Release Schedule:**
- Papers 01-03 (MAD foundations) after ICCM/IDE foundations published
- Papers 04-06 (Integration) after both disciplines mature
- Papers 07-09 (Ecosystem) alongside IDE multi-agent papers
- Papers 10-12 (Advanced) after Hopper/Grace validation
- Papers 13-14 (Case studies) as capstone publications

#### 9.3 Cross-Discipline Collaboration (NEW)

- Joint papers bridging ICCM ↔ MAD (CET integration)
- Joint papers bridging IDE ↔ MAD (Rules/DER integration)
- Joint papers across all three (complete agent architecture)

### 10. Research Questions (UPDATE)

Update to reflect corrected architecture and remove "infrastructure" questions:

1. **Thinking Engine Composition:** What are the optimal integration patterns for CET + Rules + DER + State Manager?

2. **State Manager Design:** What memory architectures best support the Thinking Engine's needs? How to balance episodic, semantic, and working memory?

3. **Doing Engine Patterns:** What are the canonical Doing Engine patterns across different domains? How to make them swappable?

4. **Half-MAD Evolution:** What's the optimal upgrade path from Half-MAD to Full MAD? When should capabilities get full Thinking Engines?

5. **MAD-to-MAD Coordination:** How should multiple Full MADs coordinate on complex tasks? What conversation protocols ensure consistency?

6. **LLM Orchestra Integration:** How should components decide when to consult Fiedler MAD? How to balance cost vs. quality?

7. **Learning and Adaptation:** How should State Manager incorporate execution outcomes? How do Full MADs improve over time?

8. **Observability:** How to trace decisions and actions across distributed MAD conversations? What debugging tools are needed?

9. **Testing and Validation:** How to validate complete MAD systems? What are the testing anti-patterns to avoid?

10. **Production Deployment:** What are the operational patterns for running Full MADs in production? How to ensure reliability and safety?

### 11. Conclusion (UPDATE)

The MAD ecosystem completes the trinity of disciplines required to build sophisticated, trustworthy AI agents:

- **ICCM** provides the discipline of Context Engineering, producing the CET component
- **IDE** provides the discipline of Decision Engineering, producing the Rules Engine and DER components
- **MAD** provides the discipline of Agent Assembly, integrating all components into complete agents

By formally separating these concerns, the trinity enables:
- Specialized development of each component
- Clear integration boundaries and contracts
- Systematic evaluation and improvement
- Principled approach to building agents that are transparent, auditable, and effective

The MAD framework, validated through Hopper and Grace implementations, demonstrates that cognitive architectures can successfully integrate symbolic AI (Rules Engine), modern LLMs (via LLM Orchestra), and structured reasoning (CET + DER + State Manager) into agents that are both capable and controllable.

### Appendix: Terminology Reference (COMPLETE UPDATE)

**Correct Terminology (CRITICAL):**
- **Conversation:** Communication between MADs (NEVER "service call," "API request," "RPC," or "function call")
- **Capability:** What a MAD provides to others (NEVER "service" or "function")
- **Half-MAD:** MAD with minimal Thinking Engine providing specialized capabilities
- **Full MAD:** Complete Thinking Engine + Doing Engine
- **Thinking Engine:** CET + Rules Engine + DER + State Manager (4 components from 3 disciplines)
- **Doing Engine:** Domain-specific execution component
- **CET:** Context Engineering Transformer (from ICCM)
- **Rules Engine:** Deterministic decision component (from IDE)
- **DER:** Decision Engineering Recommender (from IDE)
- **State Manager:** Memory and world model component (from MAD)
- **LLM Orchestra:** Multi-model consultation capability provided by Fiedler MAD

**DEPRECATED Terminology (DO NOT USE):**
- ❌ "Infrastructure" or "Infrastructure Classical"
- ❌ "Service calls" or "API requests" (use "conversations")
- ❌ "Services" or "functions" (use "capabilities")
- ❌ "Infrastructure Half-MADs" (just "Half-MADs")

---

## Council Instructions

**Output Format:**
Please provide a comprehensive **MAD Paper 00 v2.0** that:

1. Correctly positions MAD as Agent Assembly discipline completing the trinity
2. Integrates ICCM and IDE as prerequisite disciplines
3. Defines complete Thinking Engine (CET + Rules + DER + State Manager)
4. Specifies Doing Engine patterns
5. Uses correct terminology throughout (conversations, capabilities, Half-MADs)
6. Maintains excellent hierarchical 14-paper structure with updates
7. Provides updated implementation roadmap
8. Includes comprehensive case studies (Hopper, Grace)

**Target Length:** ~1,000-1,200 lines (similar to ICCM and IDE Paper 00)

**Key Requirement:** This paper should be readable by someone who has already reviewed ICCM Paper 00 and IDE Paper 00. It should focus on **Agent Assembly** - how to integrate components from both disciplines into complete MADs.

**Critical Changes from v1.0:**
- Remove all "infrastructure" language
- Correct the trinity (ICCM = context, IDE = decisions, MAD = agents)
- Standardize terminology (conversations, capabilities, Half-MADs)
- Integrate IDE components (Rules Engine, DER) into Thinking Engine specification
- Clarify LLM Orchestra as Fiedler MAD capability, not owned by any discipline
- Update all diagrams and examples

---

## References

- **ICCM Paper 00:** Defines Context Engineering discipline and CET component
- **IDE Paper 00:** Defines Decision Engineering discipline, Rules Engine, and DER components
- **MAD Paper 00 v1.0:** Original synthesis (needs corrections per this outline)
- **MAD Architecture v1.1:** Triplet-approved architecture (Gemini 2.5 Pro, GPT-5, Grok 4)
