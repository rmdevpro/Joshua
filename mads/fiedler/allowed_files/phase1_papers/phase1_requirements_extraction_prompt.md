# Phase 1: Requirements Extraction from ICCM Research Papers

## Your Task

Extract concrete, implementable system requirements from 16 ICCM research papers. These requirements will inform the architecture design for a proof-of-concept implementation.

## Context

The ICCM (Intelligent Context and Conversation Management) system is being built to prove that:
1. A specialized model (CET-D) can learn to engineer context for LLMs
2. An LLM Orchestra can generate outputs using that engineered context
3. Progressive training (Phases 1-4) produces better results than naive approaches
4. The system works in a resource-constrained environment (small lab, limited GPUs)

**Scope:** CET-D proof-of-concept focused on requirements engineering domain
**Infrastructure:** Existing hardware (M5: 4x Tesla P40, M6: 2x Tesla P100, NAS storage)
**Out of Scope:** Production scaling, enterprise features, multi-domain generalization

## Requirements Extraction Guidelines

### 1. Focus on Implementation Requirements

**Extract:**
- Concrete functional requirements (what the system must do)
- Non-functional requirements (performance, scalability, resource limits)
- Component interfaces and interactions
- Data requirements (datasets, storage, formats)
- Infrastructure requirements (hardware, networking, storage)

**Avoid:**
- Theoretical concepts without implementation details
- Aspirational "nice-to-have" features
- Requirements that contradict the PoC scope
- Duplicate or redundant requirements

### 2. Organize by System Component

Group requirements into these categories:

**A. CET-D Training Pipeline**
- Phase 1: Subject expertise acquisition
- Phase 2: Context engineering skills
- Phase 3: Interactive optimization
- Phase 4: Minimal self-improvement
- Training infrastructure and data requirements

**B. LLM Orchestra**
- Local model management (M5 GPU server)
- Cloud API coordination (Together.AI, OpenAI, Google)
- Model rotation and diversity strategy
- Request routing and load balancing
- Cost control and monitoring

**C. Requirements Engineering Domain**
- Application analysis capabilities
- Context engineering for requirements extraction
- Validation via reconstruction testing
- Dataset: 50 applications (40 train / 10 holdout)

**D. Test Lab Infrastructure**
- Code execution environment
- Containerized isolation (Docker)
- Test execution and validation
- Capacity: 600-1000 executions/day

**E. Conversation Storage & Retrieval**
- Training conversation capture
- LLM Orchestra interaction logs
- Retrieval for training and analysis

**F. Foundation Layer**
- Authentication and access control
- Monitoring and observability
- Data management and backup
- Networking and connectivity

**G. Cross-Cutting Concerns**
- Security requirements
- Performance requirements
- Operational requirements
- Testing and validation requirements

### 3. Requirement Format

For each requirement, provide:

```
REQ-<COMPONENT>-<NUMBER>: <Brief Title>

Source: Paper <XX> - <Paper Name> (Section X.X)

Description:
<Clear, implementable description of what must be built>

Acceptance Criteria:
- <Testable criterion 1>
- <Testable criterion 2>
- <Testable criterion 3>

Priority: [Critical | High | Medium | Low]

Dependencies: [REQ-XXX-YYY, REQ-XXX-ZZZ] (if applicable)

Notes: <Any clarifications, constraints, or important context>
```

### 4. Traceability

Every requirement MUST:
1. Reference the source paper(s) by number and name
2. Include section references when possible
3. Note if requirement appears in multiple papers (shows importance)
4. Flag contradictions between papers (for later resolution)

### 5. Priority Assignment

**Critical:** System cannot function without this
**High:** Core functionality for PoC
**Medium:** Important but can be simplified/deferred
**Low:** Nice-to-have, can be cut if needed

Consider:
- Is this needed for minimal viable PoC?
- Does scope.md explicitly call this out as in-scope?
- Can this be deferred to future work?
- Is this dependency for other critical requirements?

## Special Instructions

### Handle Ambiguities
If papers are unclear or contradictory:
- Note the ambiguity in the requirement
- Propose a reasonable interpretation
- Flag for user decision

### Respect Infrastructure Constraints
All requirements must be achievable with:
- M5: 4x Tesla P40 (24GB VRAM each, 96GB total)
- M6: 2x Tesla P100 (16GB VRAM each, 32GB total)
- Irina NAS: 60TB storage
- M5 CPU: AMD Ryzen 9 5900X (12-core, 64GB RAM)
- Existing Docker/networking setup

### Consider the 50-Application Dataset
Requirements engineering domain needs:
- 40 training applications
- 10 holdout applications
- Mix of complexity levels
- Real-world applications (not toy examples)

If papers specify dataset characteristics, extract those as requirements.

### Progressive Training Phases
CET-D training has 4 phases (Papers 01, 02):
- Phase 1: RAG-grounded domain knowledge
- Phase 2: Context transformation skills
- Phase 3: Interactive feedback loops
- Phase 4: Self-improvement

Extract phase-specific requirements separately.

## Deliverable Format

Organize your output as:

```markdown
# ICCM System Requirements - Extracted from Research Papers

## Executive Summary
- Total requirements extracted: <N>
- Requirements by component: <breakdown>
- Critical requirements: <N>
- Key dependencies identified: <brief summary>
- Ambiguities requiring user decision: <N>

## Requirements by Component

### A. CET-D Training Pipeline
[Requirements REQ-CET-001 through REQ-CET-XXX]

### B. LLM Orchestra
[Requirements REQ-ORC-001 through REQ-ORC-XXX]

### C. Requirements Engineering Domain
[Requirements REQ-REQ-001 through REQ-REQ-XXX]

### D. Test Lab Infrastructure
[Requirements REQ-LAB-001 through REQ-LAB-XXX]

### E. Conversation Storage & Retrieval
[Requirements REQ-CONV-001 through REQ-CONV-XXX]

### F. Foundation Layer
[Requirements REQ-FOUND-001 through REQ-FOUND-XXX]

### G. Cross-Cutting Concerns
[Requirements REQ-CROSS-001 through REQ-CROSS-XXX]

## Traceability Matrix

| Requirement ID | Source Papers | Priority | Status |
|----------------|---------------|----------|--------|
| REQ-CET-001    | 01, 02        | Critical | New    |
| REQ-CET-002    | 02, 05        | High     | New    |
| ...            | ...           | ...      | ...    |

## Ambiguities and Questions

1. **<Topic>:** Papers XX and YY have conflicting statements about <issue>
   - Paper XX says: <quote>
   - Paper YY says: <quote>
   - Recommendation: <suggested resolution>

## Dependencies and Ordering

1. **Foundation requirements** must be satisfied before:
   - <list dependent components>

2. **CET-D Phase 1** requires:
   - <list prerequisites>

3. **Critical path:** <identify critical dependency chain>

## Implementation Recommendations

Based on requirements extraction:
1. <Suggested component build order>
2. <Suggested early prototyping targets>
3. <Suggested validation checkpoints>
```

## Questions to Guide Your Analysis

As you read each paper, ask:
1. What must be built for this to work?
2. What data does this component need?
3. How does this interact with other components?
4. What are the performance/resource requirements?
5. What can go wrong, and how is it detected/handled?
6. How is success measured?
7. What infrastructure is needed?
8. What are the security/privacy requirements?
9. What operational requirements exist (monitoring, logging, backup)?
10. What testing/validation is needed?

## Remember

- **Be concrete:** "System shall support 600 test executions/day" not "System shall be fast"
- **Be testable:** Every requirement should have clear acceptance criteria
- **Be honest:** If papers are vague, say so
- **Be practical:** Focus on PoC, not production-scale system
- **Be thorough:** Extract ALL implementation requirements, not just the interesting ones

You are creating the foundation for the entire system architecture. Completeness and accuracy matter more than brevity.
