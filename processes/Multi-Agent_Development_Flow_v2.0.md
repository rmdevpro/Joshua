# Multi-Agent Development Flow v2.0

**Created**: 2025-10-11
**Status**: Active
**Supersedes**: v1.0
**Based on**: V1 MAD Group v2.0 process post-mortem

---

## Overview

A streamlined development process leveraging multiple AI agents with specialized roles, optimized for large-context models. This version collapses progressive synthesis into complete ecosystem synthesis followed by comprehensive review.

**Key Changes from v1.0:**
- **Simplified Flow**: Requirements → Complete Synthesis → Extended Review → Deploy
- **Larger Quorum**: 6+ reviewers for major projects (vs. 2 in v1.0)
- **Complete Synthesis**: Senior creates all deliverables in one pass (not progressively)
- **Anchor Documents**: Design Principles added as critical drift prevention

**IMPORTANT: LLM Communication Format**:
- All code transmitted between LLMs MUST be in Markdown format (code blocks in .md files)
- LLMs cannot directly read/write .py or other code files - only markdown
- Driver (Claude Code) extracts actual code files from markdown for deployment
- Storage locations:
  - **Development outputs**: `/mnt/projects/Joshua/docs/implementation/{feature}/`
  - **Final code extraction**: Deployment phase converts MD → Python files in codebase

---

## Agent Roles

### 1. The Driver (Claude Code)

**Primary Responsibilities**:
- User interaction and communication
- Process orchestration and workflow management
- Requirements drift detection
- Team performance evaluation
- Context optimization

**Key Activities**:
- Interpret user requirements
- Prepare synthesis packages (requirements + context)
- Send to appropriate agents (trio or senior)
- Monitor review progress
- Make go/no-go decisions
- Synthesize final deliverables

**Focus Areas**:
- Process adherence
- Requirements alignment
- Workflow efficiency
- Quality gates
- NOT content generation or detailed review

---

### 2. The Trio (Requirements Generation Team)

**Composition**: 3 models selected for diversity
- **Standard Trio (std_trio)**: 1 premium + 1 standard + 1 open-source
  - Example: Gemini 2.5 Pro, GPT-4o, DeepSeek-R1
- **Senior Trio (sr_trio)**: 3 premium models
  - Example: Gemini 2.5 Pro, GPT-5, Claude Opus
- **Junior Trio (jr_trio)**: 1 standard + 2 open-source
  - Example: GPT-4o-mini, DeepSeek-R1, Llama 3.3 70B

**Primary Responsibilities** (Requirements Phase Only):
- Initial requirements generation from user needs
- Parallel exploration of different approaches
- Diverse perspective generation

**Key Activities**:
- Receive high-level needs from Driver
- Generate independent requirements documents
- Provide rationale for design decisions
- Complete work within timeout limits

**Focus Areas**:
- Requirements completeness
- Technical accuracy
- Innovation and alternatives
- Edge case identification

**Performance Metrics**:
- Generation speed
- Initial quality (pre-synthesis)
- Diversity of approaches
- Requirements coverage

---

### 3. The Senior Member (Complete Ecosystem Synthesizer)

**Selection**: Highest-context, most capable model
- **Default**: Gemini 2.5 Pro (2M token context window)
- **Alternatives**: GPT-5 (when available), Claude Opus (future)

**Primary Responsibilities**:
- Synthesize requirements from trio outputs (if using trio)
- **NEW:** Create complete ecosystem in ONE PASS:
  - Complete Design Document
  - Complete Code Implementation
  - Complete Testing Plan
  - Complete Implementation Plan
- Incorporate review feedback iteratively (if needed)
- Maintain consistency and quality

**Key Activities**:
- Review all inputs (requirements, context, design principles)
- Create unified, comprehensive solution
- Ensure architectural consistency across all documents
- Address critical issues from reviews
- Iterate until approval achieved

**Focus Areas**:
- Complete ecosystem synthesis
- Cross-document consistency
- Quality improvement
- Issue resolution
- Holistic architectural vision

**Performance Metrics**:
- Synthesis quality
- Architectural consistency
- Issue resolution rate
- Consensus achievement time
- Token efficiency (fit within context window)

---

### 4. The Review Quorum (Extended Validation Team)

**Composition**: 6+ diverse models (for major projects)
- **Standard Quorum (std_quorum)**: 6 models
  - Example: GPT-4o, Grok-4, Llama 3.3 70B, Qwen 2.5 72B, DeepSeek-R1, GPT-4o-mini
- **Senior Quorum (sr_quorum)**: 6-8 premium models
  - Use for critical projects requiring highest confidence
- **Junior Quorum (jr_quorum)**: 4-6 cost-efficient models
  - Use for smaller projects or iteration reviews

**Primary Responsibilities**:
- Review complete ecosystem for issues
- Identify critical blockers
- Provide actionable feedback
- Approve when ready

**Key Activities**:
- Conduct comprehensive reviews of all documents
- Flag security vulnerabilities
- Identify missing functionality
- Validate against requirements AND design principles
- Check cross-document consistency
- Provide specific, actionable feedback
- Vote APPROVED or NEEDS REVISION

**Focus Areas**:
- Quality assurance
- Security review
- Completeness validation
- Consistency across documents
- Edge case identification
- Architectural soundness

**Performance Metrics**:
- Issue detection rate
- False positive rate
- Review depth/thoroughness
- Time to consensus
- Diversity of perspectives

---

### 5. Consensus Mechanism (NEW)

**Approval Rules**:
- **APPROVED**: ≥80% of quorum approves
  - For 6 reviewers: 5/6 or 6/6
  - For 4 reviewers: 4/4 (small projects)
  - For 8 reviewers: 7/8 or 8/8 (critical projects)
- **NEEDS MINOR REVISION**: 60-79% approve
  - Senior Member addresses issues from dissenters only
  - Re-review by dissenters only (not full quorum)
- **NEEDS MAJOR REVISION**: <60% approve
  - Significant architectural or requirements issues
  - Senior Member must revise and re-submit to full quorum

**Approval Criteria**:
- All critical issues resolved
- Quality meets production standards
- Completeness satisfies requirements
- No security vulnerabilities
- Architectural consistency maintained
- Design principles followed
- Ready for deployment

**Senior Member Escalation Path**:
- If reviewer feedback is out of scope → Senior Member rejects with rationale (referencing requirements/design principles)
- If reviewer feedback is valid → Senior Member addresses in revision
- If fundamental disagreement → Driver validates scope and arbitrates
- If persistent blocking issues → Driver consults user

---

## Development Flow v2.0

### Phase 1: Requirements Definition

**Option A: Using Trio (Complex Projects)**
```
Driver prepares inputs (outline, user needs, architecture context)
  ↓
Driver sends to Trio (via Fiedler)
  ↓
Trio generates 3 independent requirements documents (parallel)
  ↓
Driver sends all 3 to Senior Member
  ↓
Senior Member synthesizes unified requirements document
  ↓
User reviews and approves
  ↓
Requirements Document (APPROVED)
```

**Option B: Direct Senior (Simple Projects)**
```
Driver prepares inputs (outline, user needs, architecture context)
  ↓
Driver sends directly to Senior Member
  ↓
Senior Member generates requirements document
  ↓
User reviews and approves
  ↓
Requirements Document (APPROVED)
```

**Success Criteria**:
- All user needs addressed
- Requirements complete and unambiguous
- Design principles referenced
- Ready for complete synthesis

**Inputs to Senior Member**:
- User needs outline
- High-level architecture diagrams
- Deployment context document
- Design principles document
- Any existing related documentation

---

### Phase 2: Complete Ecosystem Synthesis (NEW)

**Single-Pass Comprehensive Synthesis:**
```
Driver prepares complete package:
  - Requirements document (approved)
  - Architecture diagrams
  - Deployment context
  - Design principles
  - Any existing code/docs for reference
  ↓
Driver sends to Senior Member
  ↓
Senior Member creates in ONE PASS:
  1. Complete Design Document
  2. Complete Code Implementation
  3. Complete Testing Plan
  4. Complete Implementation Plan
  ↓
Driver reviews for completeness (not quality)
  ↓
Complete Ecosystem Package
```

**Why This Works**:
- Senior Member has ALL context in one synthesis
- No information loss between synthesis rounds
- Holistic architectural consistency
- Gemini 2.5 Pro can handle ~2M tokens (we typically use <100K)

**Success Criteria**:
- All 4 documents present
- Architectural consistency across documents
- Requirements fully addressed
- Design principles followed
- No placeholders or TODOs
- Implementation ready

**Driver Validation**:
- Check all 4 documents are present
- Verify no obvious placeholders
- Confirm reasonable size/completeness
- NOT detailed quality review (that's Phase 3)

**Package Size Guidelines**:
- Typical package: 50-100KB (15-30K tokens)
- Large package: 100-300KB (30-100K tokens)
- Maximum package: 500KB (~150K tokens)
- If exceeding 500KB: Consider breaking into sub-projects

---

### Phase 3: Extended Review (NEW)

**Comprehensive Quorum Review:**
```
Driver prepares review package:
  - Complete ecosystem (all 4 documents)
  - Requirements document
  - Design principles
  - Deployment context
  - Structured evaluation checklist (7-10 points)
  ↓
Driver sends to Review Quorum (6+ reviewers) in PARALLEL
  ↓
All reviewers evaluate independently using checklist
  ↓
Driver collects all reviews
  ↓
Driver calculates consensus:
  - ≥80% approve → APPROVED (proceed to Phase 5)
  - 60-79% approve → MINOR REVISION (proceed to Phase 4a)
  - <60% approve → MAJOR REVISION (proceed to Phase 4b)
```

**Review Checklist Template** (customize per project):
1. [ ] Architecture consistent across all documents
2. [ ] All requirements addressed
3. [ ] Critical fixes/features applied correctly
4. [ ] No new contradictions introduced
5. [ ] Design principles followed
6. [ ] Implementation ready (no placeholders)
7. [ ] Security posture appropriate (from deployment context)
8. [ ] No architectural regressions
9. [ ] Testing plan comprehensive
10. [ ] Deployment plan complete and executable

**Success Criteria**:
- ≥80% of quorum approves
- All critical issues identified
- Specific, actionable feedback from dissenters

**Quorum Selection**:
- **Small projects (<50KB)**: 4 reviewers (jr_quorum)
- **Standard projects (50-200KB)**: 6 reviewers (std_quorum)
- **Large/critical projects (>200KB)**: 8 reviewers (sr_quorum or expanded std_quorum)
- **Favor diversity**: Mix of premium, standard, open-source models

---

### Phase 4a: Minor Revision (60-79% Approval)

**Targeted Revision:**
```
Driver sends to Senior Member:
  - Original package
  - Feedback from DISSENTERS ONLY
  - Approvals noted (for context)
  ↓
Senior Member addresses dissenter issues
  ↓
Driver sends revised package to DISSENTERS ONLY
  ↓
Dissenters re-review
  ↓
If all dissenters now approve → ≥80% achieved → APPROVED
If dissenters still dissent → Check revision count:
  - If count ≤ 3 → Return to Phase 4a
  - If count > 3 → Escalate to user
```

**Success Criteria**:
- Dissenter issues addressed
- ≥80% total approval achieved
- No new issues introduced

---

### Phase 4b: Major Revision (<60% Approval)

**Comprehensive Revision:**
```
Driver sends to Senior Member:
  - Original package
  - ALL reviewer feedback
  - Summary of common issues
  ↓
Senior Member performs major revision
  ↓
Driver sends revised package to FULL QUORUM
  ↓
Full quorum re-reviews
  ↓
Driver calculates new consensus:
  - ≥80% approve → APPROVED (proceed to Phase 5)
  - 60-79% approve → MINOR REVISION (proceed to Phase 4a)
  - <60% approve → Check revision count:
      - If count ≤ 2 → Return to Phase 4b
      - If count > 2 → STOP and consult user
```

**Stop Conditions**:
- **SUCCESS**: ≥80% approval achieved
- **MAX MAJOR REVISIONS**: Count > 2 → Driver stops & consults user
- **PERSISTENT BLOCKING ISSUES**: Same critical issue raised 3+ times → Driver stops & consults user
- **REQUIREMENTS DRIFT**: Significant scope change detected → Driver stops & consults user
- **COST/TIME BUDGET**: Budget exceeded → Driver stops & consults user

---

### Phase 5: Final Approval & Deployment

**Final Validation:**
```
≥80% Quorum approval achieved
  ↓
Senior Member implicitly approves (their work)
  ↓
Driver final validation:
  - All documents present and complete
  - Architectural consistency confirmed
  - No unresolved critical issues
  - Requirements alignment maintained
  ↓
Driver prepares Final Approval Package:
  - Complete ecosystem (approved)
  - Approval summary with vote counts
  - All review files
  - Process summary
  ↓
Driver updates repository:
  - Create FINAL_APPROVED_DOCUMENTS_vX.X/ directory
  - Save all documents
  - Create README.md
  - Update CURRENT_STATUS.md
  - Commit and push to git
  ↓
User reviews and approves for deployment
  ↓
Deployment Phase (follow Implementation Plan)
```

**Success Criteria**:
- ≥80% quorum approval (typically 100% at this stage)
- All critical issues resolved
- Quality meets production standards
- Requirements coverage complete
- No architectural drift
- Production ready

**Driver Deliverables**:
1. Complete approved ecosystem (4 documents)
2. Approval summary with review statistics
3. All individual review files
4. Process summary and lessons learned
5. Updated git repository

---

## Anchor Documents (Critical for Drift Prevention)

### Document Set
1. **High-Level Architecture Diagrams**
   - Visual system overview
   - Service boundaries and interactions
   - Key technology choices

2. **Deployment Context Document**
   - Team size and resources
   - Security posture (lab vs. enterprise)
   - Budget constraints
   - Operational capacity
   - Scale requirements

3. **Design Principles Document** (NEW - see template)
   - Architectural patterns to follow
   - Security guidelines
   - Complexity constraints
   - Technology choices
   - Anti-patterns to avoid

4. **Requirements Document**
   - Functional requirements
   - Non-functional requirements
   - Explicit deferred features

### How Anchor Documents Prevent Drift

**Requirements Drift Prevention**:
- Requirements document is immutable reference
- All synthesis and review refers back to requirements
- Changes to requirements require user approval

**Architectural Drift Prevention**:
- Architecture diagrams show intended structure
- Design principles document patterns to follow
- Reviews explicitly check against principles

**Complexity Drift Prevention**:
- Deployment context defines constraints
- Design principles set complexity ceiling
- Reviews flag over-engineering

**Security Drift Prevention**:
- Deployment context defines threat model
- Design principles document security posture
- Reviews validate proportionate security

---

## Driver Evaluation Framework

### Core Metrics (evaluated at key phases)

**1. Synthesis Quality Score (1-5)**:
- Architectural consistency across documents
- Requirements coverage
- Design principles adherence
- Code/implementation quality
- No placeholders or TODOs

**2. Review Quality Score (1-5)**:
- Issue detection accuracy
- Feedback specificity and actionability
- Review thoroughness
- False positive rate
- Diversity of perspectives

**3. Consensus Efficiency Score (1-5)**:
- Approval percentage achieved
- Iterations required
- Time to consensus
- Cost efficiency
- Forward progress per iteration

**4. Requirements Alignment Score (1-5)**:
- Perfect alignment with requirements (5/5)
- Minor beneficial improvements (4/5)
- Scope creep or missing features (1-2/5)

### Performance Tracking

**Per Phase**:
- **Requirements Phase**: Coverage, Completeness, Clarity
- **Synthesis Phase**: Quality, Consistency, Completeness
- **Review Phase**: Thoroughness, Accuracy, Agreement
- **Revision Phase**: Resolution Rate, Progress, Efficiency

**Overall Cycle**:
- Total time requirements → approval
- Total cost (estimated LLM API calls)
- Approval percentage achieved
- Iterations required
- Critical issues identified/resolved

---

## Post-Mortem Report (Simplified for v2.0)

### Template

```markdown
## Development Cycle Post-Mortem

**Date**: YYYY-MM-DD
**Project**: [Project Name]
**Review Quorum**: [6 models listed]
**Senior Member**: [Model]
**Total Revisions**: [Count]
**Final Status**: ✅ APPROVED / 🔴 STOPPED / ⚠️ ESCALATED

---

## Executive Summary

[2-3 sentence summary of cycle outcome]

---

## Core Metrics

| Phase | Quality | Completeness | Consensus | Time | Cost |
|-------|---------|--------------|-----------|------|------|
| Requirements | X/5 | X/5 | Approved | XXm | $X |
| Synthesis | X/5 | X/5 | - | XXm | $X |
| Review 1 | X/5 | X/5 | X/Y approve | XXm | $X |
| Revision 1 | X/5 | X/5 | X/Y approve | XXm | $X |
| FINAL | X/5 | X/5 | X/Y approve | XXh | $XX |

**Final Scores**:
- **Synthesis Quality**: X/5
- **Review Quality**: X/5
- **Consensus Efficiency**: X/5
- **Requirements Alignment**: X/5

---

## Approval Results

**Final Vote**: X/Y (XX% approval)

| Reviewer | Model | Vote | Key Issues Raised |
|----------|-------|------|-------------------|
| 1 | Model | ✅ APPROVED | None |
| 2 | Model | ✅ APPROVED | None |
| 3 | Model | ❌ REVISE | [Issue summary] |
| 4 | Model | ✅ APPROVED | Minor: [summary] |
| 5 | Model | ✅ APPROVED | None |
| 6 | Model | ✅ APPROVED | None |

---

## Critical Issues

### Issues Identified: [Count]

1. **[Issue Name]** (Revision [N])
   - Reported by: [Reviewer(s)]
   - Severity: CRITICAL / HIGH / MEDIUM
   - Resolution: [How addressed]
   - Status: ✅ RESOLVED / 🔴 DEFERRED

---

## Strengths of v2.0 Process

1. [What worked well]
2. [Another success]
3. [Another success]

---

## Issues with v2.0 Process

1. [What didn't work]
   - Impact: [Effect on cycle]
   - Recommendation: [How to fix]

---

## Recommendations

### Immediate Actions
1. [Action item with owner and priority]

### Process Improvements
1. [Process change with rationale]

### Documentation Needs
1. [New/updated docs needed]

---

## Key Learnings

### Technical Insights
1. [Technical learning]

### Process Insights
1. [Process learning]

### Model Performance
1. [Model behavior observation]

---

## Next Steps

1. ✅ / ⏭️ [Next action]
2. ✅ / ⏭️ [Next action]

---

**Report Generated by**: Driver (Claude Code)
**Report Date**: YYYY-MM-DD HH:MM
```

---

## Comparison: v1.0 vs. v2.0

| Aspect | v1.0 | v2.0 |
|--------|------|------|
| **Requirements** | Trio → Senior synthesis | Same (KEPT) |
| **Design** | Trio → Senior synthesis | Senior direct synthesis |
| **Code** | Trio → Senior synthesis | Part of complete synthesis |
| **Testing Plan** | Separate phase | Part of complete synthesis |
| **Implementation Plan** | Separate phase | Part of complete synthesis |
| **Review Team** | 2 junior members | 6+ diverse quorum |
| **Review Scope** | Per-document | Complete ecosystem |
| **Consensus Rule** | 2/2 junior approve | ≥80% quorum approve |
| **Synthesis Phases** | 4-5 separate | 1 complete |
| **Context Usage** | Fragmented | Complete (single pass) |
| **Anchor Documents** | Architecture only | +Deployment Context +Design Principles |
| **Approval Confidence** | Medium (2 reviewers) | High (6+ reviewers) |
| **Time to Approval** | Multiple sessions | Single session (typical) |
| **LLM API Calls** | 12-15+ calls | 8-10 calls |

---

## Benefits of v2.0

### 1. Complete Context Synthesis
- Senior Member has ALL information at once
- No information loss between phases
- Holistic architectural vision
- Cross-document consistency assured

### 2. Higher Approval Confidence
- 6+ diverse reviewers catch more issues
- Model diversity reduces groupthink
- Higher consensus threshold (80% vs. 100%)
- Allows for dissent without blocking

### 3. Simpler Process
- Fewer phases (5 vs. 11 in v1.0)
- Less process management overhead
- Clearer decision points
- Faster time to approval (typical)

### 4. Better Drift Prevention
- Design Principles document guides all work
- Deployment Context prevents over-engineering
- All anchor documents in every package
- Explicit checklist items for principles/context

### 5. Cost Efficiency
- ~40% fewer LLM calls
- Parallel review (6 models in seconds via Fiedler)
- Less iteration typical (better first-pass quality)

---

## When to Use v1.0 vs. v2.0

### Use v2.0 (Default)
- Standard projects (<500KB package size)
- Clear requirements available
- Architectural patterns established
- Senior model has adequate context window (2M+ tokens)

### Use v1.0 (Exceptions)
- Extremely large projects (>500KB package size)
- Highly exploratory projects (unclear requirements)
- Need progressive consensus-building
- Limited context window models

### Hybrid Approach
- Use v2.0 for core synthesis
- Use v1.0 trio for specific sub-components if needed
- Driver decides based on project size and complexity

---

## Context Window Considerations

### Current Model Context Windows (as of 2025-10)
- Gemini 2.5 Pro: 2M tokens (~6MB text)
- GPT-5: 256K tokens (~1MB text)
- Claude Opus: 200K tokens (~800KB text)
- DeepSeek-R1: 128K tokens (~512KB text)

### Practical Limits
- **Typical v2.0 Package**: 50-100KB (15-30K tokens)
- **Large v2.0 Package**: 100-300KB (30-100K tokens)
- **Maximum v2.0 Package**: 500KB (~150K tokens)
- **Beyond 500KB**: Consider breaking into sub-projects or using v1.0

### Optimization Tips
- Use file references instead of inline code for existing systems
- Summarize lengthy requirements
- Extract design principles into separate document (reference, don't repeat)
- Use architecture diagrams instead of lengthy descriptions

---

## Open Questions for Future Versions

1. **Optimal Quorum Size**: Is 6 reviewers optimal? Test 4, 6, 8, 10
2. **Model Specialization**: Should different models handle different document types?
3. **Approval Threshold**: Is 80% the right threshold? Test 75%, 80%, 85%
4. **Cost Optimization**: Can we reduce quorum for iteration reviews?
5. **Automated Synthesis**: Can Driver automatically prepare packages without manual input?

---

## Migration from v1.0

### For Existing Projects
- **Ongoing v1.0 projects**: Complete using v1.0
- **New projects**: Use v2.0
- **Next version of existing project**: Migrate to v2.0

### Process Updates Needed
1. Create Design Principles template (DONE - see `/mnt/projects/Joshua/templates/`)
2. Update Driver workflows to use v2.0 flow
3. Train on Fiedler quorum mode (6+ parallel LLM calls)
4. Update post-mortem template

---

**Status**: v2.0 - Active, based on V1 MAD Group v2.0 learnings
**Next Review**: After 3 projects completed using v2.0
