# [Project Name] - Design Principles

**Version:** 1.0
**Date:** [YYYY-MM-DD]
**Project:** [Project Name]
**Target Deployment:** [Lab/Enterprise/Edge/etc.]

---

## Purpose

This document captures the fundamental design principles that must be followed throughout the [Project Name] development. These principles serve as anchors to prevent architectural drift during the Multi-Agent Development process.

**Use this document when:**
- Creating initial requirements
- Synthesizing design documents
- Reviewing code implementations
- Evaluating architectural decisions

---

## 1. Architectural Principles

### 1.1. Core Architectural Pattern

**Principle:** [State the primary architectural pattern]

**Example:** "Embed reasoning capabilities within each service rather than creating centralized reasoning services."

**Rationale:** [Why this pattern was chosen]

**Example:** "Centralized reasoning creates single points of failure, tight coupling, and scaling bottlenecks. Embedded reasoning provides autonomy, resilience, and independent evolution of each service."

**Application:**
- [How this applies to your project]
- [Specific services/components this affects]
- [What to avoid]

**Example:**
- Each MAD that requires reasoning must have its own embedded Imperator
- Sequential Thinking must NOT be implemented as a separate service
- Avoid shared LLM pools or centralized orchestration layers

---

### 1.2. Service Boundaries

**Principle:** [How services should be decomposed]

**Example:** "Services should be decomposed by business capability, not technical layer."

**Rationale:** [Why]

**Application:**
- [Guidelines for service creation]
- [When to split vs. combine services]
- [Communication patterns between services]

---

### 1.3. State Management

**Principle:** [How state should be managed]

**Example:** "Each service owns its own state. Shared state must be explicitly justified and minimized."

**Rationale:** [Why]

**Application:**
- [Where state lives (databases, files, memory)]
- [State persistence requirements]
- [State synchronization patterns (if any)]

---

### 1.4. [Additional Architectural Principles]

**Principle:**

**Rationale:**

**Application:**

---

## 2. Security Principles

### 2.1. Security Posture

**Context:** [Lab/Enterprise/Public-facing/etc.]

**Example:** "5-person trusted research lab on internal network"

**Threat Model:** [What threats are in scope vs. out of scope]

**Example:**
- **IN SCOPE:** Accidental secret exposure, credential leakage, audit logging
- **OUT OF SCOPE:** Sophisticated attacks, DDoS, zero-day exploits, physical security

**Rationale:** "Security measures must be proportionate to the threat model. Lab environments can accept higher trust assumptions and focus security effort on operational safety rather than adversarial defense."

---

### 2.2. Authentication & Authorization

**Principle:** [How auth should be handled]

**Example:** "Implement authentication at all service boundaries. Defer fine-grained authorization to v2+."

**Rationale:** [Why]

**Application:**
- [Authentication mechanisms to use]
- [What requires auth, what doesn't]
- [How to handle service-to-service auth]

---

### 2.3. Secrets Management

**Principle:** [How secrets should be handled]

**Example:** "All secrets must be managed by a centralized secrets manager. No secrets in environment variables, config files, or version control."

**Rationale:** [Why]

**Application:**
- [Where secrets are stored]
- [How services retrieve secrets]
- [Secret rotation procedures]
- [Bootstrap process]

---

### 2.4. [Additional Security Principles]

**Principle:**

**Rationale:**

**Application:**

---

## 3. Complexity Principles

### 3.1. Complexity Budget

**Context:** [Team size, resources, operational capacity]

**Example:** "5-person team, limited DevOps resources, research lab budget"

**Complexity Ceiling:** [What complexity is acceptable vs. too much]

**Example:**
- **ACCEPTABLE:** Docker Compose, SQLite, single-server deployment, manual scaling
- **TOO COMPLEX:** Kubernetes, microservices mesh, distributed databases, auto-scaling

**Rationale:** "Complexity must be justified by actual requirements, not potential future needs. Over-engineering increases maintenance burden and reduces development velocity for small teams."

---

### 3.2. Technology Selection

**Principle:** [How to choose technologies]

**Example:** "Prefer boring, proven technologies over cutting-edge solutions. Optimize for operational simplicity over theoretical performance."

**Rationale:** [Why]

**Application:**
- [Approved technology stack]
- [Technologies to avoid]
- [When exceptions are acceptable]

**Example:**
- **APPROVED:** Python 3.11+, SQLite, Redis, Docker, OpenSSH
- **AVOID:** NoSQL databases, message queues beyond Redis, service meshes, observability platforms
- **EXCEPTIONS:** Can consider when proven inadequacy of approved tech

---

### 3.3. Premature Optimization

**Principle:** [When to optimize]

**Example:** "Do not optimize for scale, performance, or reliability beyond demonstrated requirements."

**Rationale:** [Why]

**Application:**
- [What to build first (MVP)]
- [What to defer to later versions]
- [Metrics that trigger optimization work]

**Example:**
- **V1:** Single instance, no load balancing, manual failover
- **V2:** Add high availability if uptime <99%
- **V3:** Add horizontal scaling if single instance saturated

---

### 3.4. [Additional Complexity Principles]

**Principle:**

**Rationale:**

**Application:**

---

## 4. Development Principles

### 4.1. Testing Strategy

**Principle:** [What testing is required]

**Example:** "Integration tests > unit tests. Test the system as users will use it."

**Rationale:** [Why]

**Application:**
- [Types of tests required]
- [Test coverage expectations]
- [When to write tests (TDD, after implementation, etc.)]

---

### 4.2. Documentation Standards

**Principle:** [What documentation is required]

**Example:** "Document the 'why' not the 'what'. Code documents itself, comments explain rationale."

**Rationale:** [Why]

**Application:**
- [Required documentation artifacts]
- [Documentation maintenance process]
- [When documentation is optional]

---

### 4.3. Code Standards

**Principle:** [Coding standards to follow]

**Example:** "Follow PEP 8 for Python. Prefer explicit over clever. Optimize for readability."

**Rationale:** [Why]

**Application:**
- [Language-specific standards]
- [Naming conventions]
- [Code review requirements]

---

### 4.4. [Additional Development Principles]

**Principle:**

**Rationale:**

**Application:**

---

## 5. Operational Principles

### 5.1. Deployment Model

**Principle:** [How the system deploys]

**Example:** "Single-server deployment using Docker Compose. No distributed systems in V1."

**Rationale:** [Why]

**Application:**
- [Deployment automation requirements]
- [Rollback procedures]
- [Configuration management]

---

### 5.2. Monitoring & Observability

**Principle:** [What to monitor and how]

**Example:** "Logs to stdout, metrics to Redis. No external observability platforms in V1."

**Rationale:** [Why]

**Application:**
- [What to log (and what not to log)]
- [Log aggregation approach]
- [Alerting thresholds]

---

### 5.3. Failure Handling

**Principle:** [How the system handles failures]

**Example:** "Fail loudly, recover automatically. No silent failures. Automatic reconnection with exponential backoff."

**Rationale:** [Why]

**Application:**
- [Retry policies]
- [Circuit breaker patterns]
- [Data loss tolerance]

---

### 5.4. [Additional Operational Principles]

**Principle:**

**Rationale:**

**Application:**

---

## 6. Data Principles

### 6.1. Data Storage

**Principle:** [How data should be stored]

**Example:** "Each service owns its database. Use SQLite with WAL mode for all persistent state."

**Rationale:** [Why]

**Application:**
- [Database technology choices]
- [Schema management]
- [Data migration approach]

---

### 6.2. Data Retention

**Principle:** [How long to keep data]

**Example:** "Retain conversation logs for 90 days. Retain audit logs for 1 year. No automatic purging in V1."

**Rationale:** [Why]

**Application:**
- [What data to keep]
- [Retention periods by data type]
- [Archival vs. deletion policies]

---

### 6.3. Data Privacy

**Principle:** [How to handle sensitive data]

**Example:** "Secrets encrypted at rest. Conversation data unencrypted (lab environment). No PII collection."

**Rationale:** [Why]

**Application:**
- [What data is sensitive]
- [Encryption requirements]
- [Access controls]

---

### 6.4. [Additional Data Principles]

**Principle:**

**Rationale:**

**Application:**

---

## 7. Communication Principles

### 7.1. Inter-Service Communication

**Principle:** [How services communicate]

**Example:** "Asynchronous pub/sub via Redis for inter-MAD communication. Synchronous MCP for client-to-MAD communication."

**Rationale:** [Why]

**Application:**
- [Communication protocols]
- [Message formats]
- [Error handling in communication]

---

### 7.2. API Design

**Principle:** [How APIs should be designed]

**Example:** "MCP tools are the API. Keep tool interfaces stable, version imperatively if breaking changes required."

**Rationale:** [Why]

**Application:**
- [API versioning strategy]
- [Backward compatibility requirements]
- [Deprecation policy]

---

### 7.3. [Additional Communication Principles]

**Principle:**

**Rationale:**

**Application:**

---

## 8. Evolution Principles

### 8.1. Versioning Strategy

**Principle:** [How the system evolves]

**Example:** "Major versions (v1, v2) for architectural changes. Minor versions (v1.1, v1.2) for feature additions. Patches (v1.1.1) for bug fixes."

**Rationale:** [Why]

**Application:**
- [When to increment versions]
- [Backward compatibility requirements]
- [Migration paths between versions]

---

### 8.2. Feature Prioritization

**Principle:** [What to build first]

**Example:** "Ship minimal viable functionality first. Add features based on actual usage patterns, not hypothetical needs."

**Rationale:** [Why]

**Application:**
- [MVP definition]
- [What to defer to later versions]
- [Feature request evaluation criteria]

---

### 8.3. Technical Debt

**Principle:** [How to manage technical debt]

**Example:** "Accept technical debt to ship faster. Document all known debt. Address debt when it blocks new features or causes operational pain."

**Rationale:** [Why]

**Application:**
- [Acceptable vs. unacceptable debt]
- [Debt tracking mechanism]
- [Debt repayment triggers]

---

### 8.4. [Additional Evolution Principles]

**Principle:**

**Rationale:**

**Application:**

---

## 9. Constraints & Assumptions

### 9.1. Hard Constraints

**These cannot be violated:**

1. [Constraint 1]
   - **Example:** "Must operate on single server with 16GB RAM"
   - **Reason:** [Why this constraint exists]

2. [Constraint 2]

3. [Constraint 3]

---

### 9.2. Soft Constraints

**These can be violated with explicit justification:**

1. [Constraint 1]
   - **Example:** "Prefer open-source technologies"
   - **Reason:** [Why this is preferred]
   - **Acceptable violations:** [When it's okay to violate]

2. [Constraint 2]

3. [Constraint 3]

---

### 9.3. Key Assumptions

**The design assumes:**

1. [Assumption 1]
   - **Example:** "All team members have trusted access to all systems"
   - **Impact if wrong:** [What breaks if this assumption is false]

2. [Assumption 2]

3. [Assumption 3]

---

## 10. Anti-Patterns to Avoid

### 10.1. Architectural Anti-Patterns

**DO NOT:**

1. **[Anti-pattern name]**
   - **Example:** "Creating centralized services for cross-cutting concerns"
   - **Why it's bad:** [Explanation]
   - **What to do instead:** [Alternative]

2. **[Anti-pattern name]**

3. **[Anti-pattern name]**

---

### 10.2. Security Anti-Patterns

**DO NOT:**

1. **[Anti-pattern name]**
   - **Example:** "Storing secrets in environment variables or config files"
   - **Why it's bad:** [Explanation]
   - **What to do instead:** [Alternative]

2. **[Anti-pattern name]**

3. **[Anti-pattern name]**

---

### 10.3. Operational Anti-Patterns

**DO NOT:**

1. **[Anti-pattern name]**
   - **Example:** "Silent failure handling without logging"
   - **Why it's bad:** [Explanation]
   - **What to do instead:** [Alternative]

2. **[Anti-pattern name]**

3. **[Anti-pattern name]**

---

## 11. Decision Log

**Use this section to document major design decisions and their rationale.**

### Decision #1: [Decision Title]
- **Date:** [YYYY-MM-DD]
- **Context:** [What prompted this decision]
- **Decision:** [What was decided]
- **Alternatives Considered:** [What else was considered]
- **Rationale:** [Why this decision was made]
- **Impact:** [What this affects]

---

### Decision #2: [Decision Title]

---

## 12. Review Checklist

**Use this checklist when reviewing designs against these principles:**

- [ ] Architecture follows core pattern (Section 1.1)
- [ ] Security posture matches threat model (Section 2.1)
- [ ] Complexity is justified by requirements (Section 3.1)
- [ ] No anti-patterns present (Section 10)
- [ ] Hard constraints not violated (Section 9.1)
- [ ] Soft constraint violations are justified (Section 9.2)
- [ ] Key assumptions remain valid (Section 9.3)
- [ ] Evolution path is clear (Section 8)

---

## Appendix: How to Use This Document

### For Requirements Definition
- Reference Section 1 (Architecture), 3 (Complexity), and 9 (Constraints)
- Ensure requirements align with architectural pattern
- Don't create requirements that violate hard constraints

### For Design Synthesis
- Include this entire document in the synthesis package
- Reference specific sections when making design decisions
- Use Section 10 (Anti-patterns) as a negative checklist
- Document major decisions in Section 11

### For Code Review
- Check that implementation follows Section 4 (Development) principles
- Verify no anti-patterns from Section 10
- Ensure complexity stays within budget (Section 3.1)

### For Deployment
- Verify deployment matches Section 5 (Operational) principles
- Follow monitoring/observability guidelines (Section 5.2)
- Ensure failure handling aligns with principles (Section 5.3)

---

*Template Version: 1.0*
*Last Updated: 2025-10-11*
*Created by: Joshua Project (Claude Code)*
