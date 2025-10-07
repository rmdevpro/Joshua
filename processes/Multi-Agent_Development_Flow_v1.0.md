# Multi-Agent Development Flow v1.0

**Created**: 2025-10-07
**Status**: Draft - Defining Roles & Process

---

## Overview

A structured development process leveraging multiple AI agents with specialized roles to create documents and code through iterative generation, synthesis, and review cycles.

---

## Agent Roles

### 1. The Driver (Claude Code)

**Primary Responsibilities**:
- User interaction and communication
- Process orchestration and workflow management
- Requirements drift detection
- Team performance evaluation
- Context optimization (minimal content processing)

**Key Activities**:
- Interpret user requirements
- Assign tasks to appropriate agents
- Monitor progress against requirements
- Detect scope creep or requirements drift
- Rate team performance at each step
- Make go/no-go decisions for iterations
- Synthesize final deliverables

**Focus Areas**:
- Process adherence
- Requirements alignment
- Workflow efficiency
- Quality gates
- NOT content generation or detailed review

**Performance Metrics**:
- Requirements drift detection accuracy
- Process efficiency (iteration count)
- Team coordination effectiveness
- User satisfaction

---

### 2. The Trio (Generation Team)

**Composition**: 3 models selected for diversity
- **Standard Trio (std_trio)**: 1 premium + 1 standard + 1 open-source
  - Example: Gemini 2.5 Pro, GPT-4o, DeepSeek
- **Senior Trio (sr_trio)**: 3 premium models
  - Example: Gemini 2.5 Pro, GPT-5, Claude Opus
- **Junior Trio (jr_trio)**: 1 standard + 2 open-source
  - Example: GPT-4o-mini, DeepSeek, Llama

**Primary Responsibilities**:
- Initial content generation from requirements
- Parallel exploration of different approaches
- Diverse perspective generation

**Key Activities**:
- Receive requirements from Driver
- Generate independent implementations/drafts
- Provide rationale for design decisions
- Complete work within timeout limits

**Focus Areas**:
- Content creation
- Technical accuracy
- Completeness
- Innovation and alternatives

**Performance Metrics**:
- Generation speed
- Initial quality (pre-synthesis)
- Diversity of approaches
- Requirements coverage

---

### 3. The Senior Member (Synthesizer)

**Selection**: Most premium model from the trio
- Default: Gemini 2.5 Pro (from std_trio)
- For sr_trio: GPT-5 or Opus
- For jr_trio: GPT-4o-mini

**Primary Responsibilities**:
- Synthesize multiple implementations into unified solution
- Incorporate review feedback iteratively
- Maintain consistency and quality
- Address critical issues

**Key Activities**:
- Review all trio outputs
- Identify best elements from each approach
- Create unified implementation
- Respond to review feedback
- Iterate until consensus reached

**Focus Areas**:
- Code/document synthesis
- Consistency maintenance
- Quality improvement
- Issue resolution

**Performance Metrics**:
- Synthesis quality
- Iteration efficiency
- Issue resolution rate
- Consensus achievement time

---

### 4. The Junior Members (Review Team)

**Composition**: Remaining 2 members from trio (excluding Senior)
- Standard: GPT-4o + DeepSeek
- Senior: Gemini 2.5 Pro + Opus (if GPT-5 is synthesizer)
- Junior: DeepSeek + Llama

**Primary Responsibilities**:
- Review synthesized work for issues
- Identify critical blockers
- Provide actionable feedback
- Approve when ready

**Key Activities**:
- Conduct code/document reviews
- Flag security vulnerabilities
- Identify missing functionality
- Validate against requirements
- Provide specific, actionable feedback
- Vote APPROVED or NEEDS REVISION

**Focus Areas**:
- Quality assurance
- Security review
- Completeness validation
- Edge case identification

**Performance Metrics**:
- Issue detection rate
- False positive rate
- Review depth/thoroughness
- Time to consensus

---

### 5. Consensus Mechanism

**Key Principle**: Senior Member is always assenting (they created the content)

**Consensus Rules**:
- **APPROVED**: Both Junior Members approve (2/2)
  - Senior Member implicitly approves their own synthesis
  - Result: 3/3 consensus achieved
- **NEEDS REVISION**: Either Junior Member flags critical issues
  - Senior Member must address feedback in next iteration
  - Senior Member can reject feedback as out-of-scope (with rationale)
- **BLOCKED**: Senior Member and Junior Members fundamentally disagree
  - Driver validates scope per requirements
  - Driver decides or escalates to user

**Approval Criteria for Junior Members**:
- All critical issues resolved
- Quality meets production standards
- Completeness satisfies requirements
- No security vulnerabilities
- Ready for deployment

**Senior Member Escalation Path**:
- If Junior Member feedback is out of scope → Senior Member rejects with rationale
- If Junior Member feedback is valid → Senior Member addresses in iteration
- If circular changes detected → Senior Member escalates to Driver
- If fundamental disagreement → Driver arbitrates or consults user

---

## Development Flow

### Phase 1: Generation
```
Driver prepares inputs (outline, requirements, code, documents)
  ↓
Driver sends to Trio (via Fiedler)
  ↓
Trio generates 3 independent drafts (parallel)
  ↓
Driver reviews & rates (Quality, Completeness, Drift)
```

**Success Criteria**:
- All 3 drafts submitted
- Reasonable diversity in approaches
- Inputs addressed by all 3

**Driver Evaluation**:
- Coverage: Do all 3 address inputs?
- Diversity: Are approaches sufficiently different?
- Quality: Is baseline quality acceptable?

**Note**: Inputs vary by deliverable type:
- **Requirements doc**: Outline drafted with user
- **Code implementation**: Existing requirements/specs
- **README**: Existing code + requirements
- **Architecture doc**: Outline drafted with user
- **Refactoring**: Existing code + objectives

**Trio Selection Process**:
- Driver sends to Fiedler MCP with trio preset selection
- **Default**: `std_trio` (1 premium + 1 standard + 1 open-source)
  - Example: Gemini 2.5 Pro, GPT-4o, DeepSeek
- **User can request**: `sr_trio` (3 premium) or `jr_trio` (1 standard + 2 open-source)
- Fiedler uses randomization/selection within preset constraints
- Fiedler returns which 3 models were selected
- **Driver locks team composition** for entire cycle:
  - Most premium model → Senior Member (synthesis)
  - Other 2 models → Junior Members (review)
- Team remains consistent across all phases (no rotation mid-cycle)

---

### Phase 2: Synthesis
```
Driver sends to Senior Member
  ↓
Senior Member reviews all 3 drafts
  ↓
Senior Member creates unified solution + notes on disagreements
  ↓
Driver reviews & rates (Quality, Completeness, Drift)
```

**Success Criteria**:
- Unified draft created
- Best elements from all 3 incorporated
- Consistent style and architecture
- No drift from inputs

**Driver Evaluation**:
- Completeness: All features present?
- Quality: Improvement over individual outputs?
- Consistency: Unified voice/style?
- Drift: Still aligned with inputs?

---

### Phase 3: Review (Initial)
```
Driver sends to Junior Members
  ↓
Junior Members review in parallel
  ↓
Driver reviews & rates Junior performance
  ↓
Consensus? (2/2 approve)
  ↓
If NO → proceed to Iteration Loop
If YES → proceed to Final Approval
```

**Success Criteria**:
- Both reviews completed
- Specific, actionable feedback
- Critical issues identified (if any)

**Driver Evaluation** (per review response):
1. **Quality Score**: Is feedback technically sound?
2. **Completeness Score**: All areas covered?
3. **Drift Check**: Review against original inputs
4. **Circular Change Check**: Compare to previous iterations (if applicable)

---

### Phase 4: Iteration Loop (if needed)
```
[LOOP START]
Driver sends to Senior Member
  ↓
Senior Member generates + notes on disagreements
  ↓
Driver reviews & rates (Quality, Completeness, Drift)
  ↓
Driver sends to Junior Members
  ↓
Junior Members review
  ↓
Driver reviews & rates Junior performance
  ↓
Consensus? (2/2 approve)
  ↓
If YES → EXIT LOOP to Final Approval
If NO → Check loop count > 6?
  ↓
If loop count > 6 → STOP, consult user
If loop count ≤ 6 → CONTINUE LOOP
[LOOP END]
```

**Success Criteria**:
- Consensus reached (2/2 Junior Members approve)
- All critical issues resolved
- Inputs still met
- No circular changes

**Stop Conditions**:
- **SUCCESS**: Both Junior Members approve (2/2)
- **MAX ITERATIONS**: Loop count > 6 → Driver stops & consults user
- **CIRCULAR CHANGES**: 3rd occurrence → Driver stops & consults user
- **PERSISTENT DRIFT**: Red for 2+ iterations → Driver stops & consults user
- **BLOCKED**: Fundamental disagreement → Driver validates scope, then stops & consults user

**Driver Evaluation** (per iteration):
1. **Quality Score**: Is revised work improving?
2. **Completeness Score**: Are issues being resolved?
3. **Drift Score**: Still aligned with inputs?
4. **Circular Change Check**: Any regressions or repeated issues?
5. **Scope Validation**: Are Senior rejections valid per inputs?

---

### Phase 5: Final Approval
```
Both Junior Members approve (2/2)
  ↓
Senior Member implicitly approves (their work)
  ↓
Driver final validation & Post-Mortem Report
  ↓
Driver updates:
  - Git projects & GitHub issues
  - Affected documents
  - Push to GitHub
  ↓
User reviews and approves
  ↓
Finished code or document
```

**Success Criteria**:
- 2/2 Junior Member approval (Senior always approves their own work)
- Final Quality score ≥ 4/5
- Final Completeness score = 5/5
- Final Drift score = 5/5 (Green)
- No unresolved critical issues
- Production ready

**Driver Final Evaluation**:
1. **Quality Score**: Professional standards met?
2. **Completeness Score**: All inputs satisfied?
3. **Drift Score**: Perfect alignment maintained?
4. **Overall Efficiency**: Iterations vs. value delivered
5. **Team Performance**: Individual and collective ratings

**Driver Deliverables**:
1. Finished code or document
2. Comprehensive post-mortem report
3. Process improvement recommendations
4. Documentation gap identification
5. Trio performance assessment

**Driver Post-Completion Actions**:
1. Save finished code/document to appropriate repository location
2. Update or close related GitHub issues (with `fixes #N` or `closes #N`)
3. Update affected documentation (README, architecture docs, etc.)
4. Commit all changes with descriptive message
5. Push to GitHub
6. Present post-mortem report to user

---

## Driver Evaluation Framework

### Core Metrics (1-5 scale, evaluated at each step)

**1. Quality Score**:
- Code/document meets professional standards
- Best practices followed
- Clear, maintainable, well-structured
- Security considerations addressed
- Edge cases handled

**2. Completeness Score**:
- All requirements addressed
- No missing functionality
- Adequate documentation
- Test coverage (for code)
- No gaps or TODOs left unresolved

**3. Drift Score**:
- ✅ **5/5 - Green**: Perfect alignment with requirements
- ⚠️ **3-4/5 - Yellow**: Minor beneficial clarifications or improvements
- 🔴 **1-2/5 - Red**: Scope creep, missing features, or wrong direction

### Drift Detection Process

**Driver monitors for**:
- **Feature drift**: New features not in requirements
- **Scope creep**: Expanding beyond original scope
- **Missing requirements**: Original features dropped
- **Direction drift**: Solving different problem than specified

**Drift Response Protocol**:
1. **Green (5/5)**: Continue normal process
2. **Yellow (3-4/5)**: Note improvement, flag to Senior Member as context
3. **Red (1-2/5)**:
   - STOP current iteration
   - Alert Senior Member with specific drift details
   - Senior Member must acknowledge and correct in next iteration
   - If drift persists: ESCALATE to user consultation

### Circular Change Detection

**Driver monitors for**:
- Same issue raised multiple times
- Previous fixes being reverted
- Reviewers contradicting each other
- Senior Member ignoring valid feedback
- Reviewers insisting on out-of-scope changes

**Circular Change Indicators**:
- Issue mentioned in Iteration N and Iteration N+2 (regression)
- Reviewers disagree on same issue across 2+ iterations
- Senior Member makes change, then reverts in next iteration
- Review focuses on style preferences vs. functional issues

**Response to Circular Changes**:
1. **First occurrence**: Flag to Senior Member
2. **Second occurrence**: Senior Member must explicitly address why
3. **Third occurrence**: STOP and consult user

### Senior Member Authority

**Scope Management**:
- Senior Member can reject reviewer feedback as "out of scope"
- Must provide rationale referencing requirements document
- Driver validates scope decision against requirements
- If Driver disagrees: ESCALATE to user

**Example Senior Member Responses**:
- "This optimization is out of scope per requirement 3.2"
- "Requirements specify mock implementation, not full provider"
- "This feature is explicitly deferred to v2.0 per requirements"

### Iteration Control

**Driver Stop Authority**:
- **STOP if**: Circular changes detected (3rd occurrence)
- **STOP if**: Drift score remains Red for 2+ iterations
- **STOP if**: Senior Member repeatedly ignores critical feedback
- **STOP if**: Reviewers insist on out-of-scope changes
- **STOP if**: Iteration count exceeds 6 without progress
- **STOP if**: Cost/time budget exceeded

**Stop Procedure**:
1. Driver documents issue
2. Driver presents situation to user
3. User decides: Continue with adjustment, or Abort cycle

### Per-Phase Ratings (1-5 scale)

**Generation Phase**:
- Coverage Score: % of requirements addressed
- Diversity Score: Variation in approaches
- Quality Score: Baseline implementation quality
- Speed Score: Time to complete

**Synthesis Phase**:
- Integration Score: How well elements combined
- Improvement Score: Quality gain vs. individual outputs
- Consistency Score: Unified style/architecture
- Drift Score: Alignment with original requirements

**Review Phase**:
- Thoroughness Score: Coverage of review areas
- Actionability Score: Specificity of feedback
- Accuracy Score: Valid issues vs. false positives
- Agreement Score: Reviewer consensus level

**Iteration Phase** (per iteration):
- Resolution Score: Issues fixed per iteration
- Responsiveness Score: Senior Member's adaptation
- Progress Score: Forward momentum
- Efficiency Score: Iteration cost vs. value

**Final Phase**:
- Consensus Score: Agreement level
- Completeness Score: Requirements coverage
- Quality Score: Production readiness
- Overall Efficiency: Total time/cost vs. value

## Post-Mortem Report (End of Cycle)

### Purpose
After each development cycle, Driver generates comprehensive post-mortem report for user review, capturing lessons learned and process improvements.

### Post-Mortem Report Template

```markdown
## Development Cycle Post-Mortem

**Date**: YYYY-MM-DD
**Project**: [Project Name]
**Trio**: [Model 1, Model 2, Model 3]
**Senior Member**: [Model]
**Total Iterations**: [Count]
**Final Status**: ✅ APPROVED / 🔴 STOPPED / ⚠️ ESCALATED

---

## Executive Summary

[2-3 sentence summary of cycle outcome]

---

## Core Metrics

| Iteration | Quality | Completeness | Drift | Issues Raised | Issues Resolved |
|-----------|---------|--------------|-------|---------------|-----------------|
| Generation | X/5 | X/5 | X/5 | - | - |
| Synthesis | X/5 | X/5 | X/5 | - | - |
| Review 1 | X/5 | X/5 | X/5 | X | - |
| Iteration 1 | X/5 | X/5 | X/5 | - | X |
| Review 2 | X/5 | X/5 | X/5 | X | - |
| Iteration 2 | X/5 | X/5 | X/5 | - | X |
| Final | X/5 | X/5 | X/5 | X total | X total |

**Final Scores**:
- **Quality**: X/5
- **Completeness**: X/5
- **Drift**: X/5 (✅ Green / ⚠️ Yellow / 🔴 Red)

---

## Timeline & Cost

- **Total Time**: XX hours XX minutes
- **Estimated Cost**: $XX.XX
- **Average Iteration Time**: XX minutes
- **Cost per Iteration**: $XX.XX

---

## Issue Analysis

### Critical Issues Identified: [Count]

1. **[Issue Name]** (Iteration [N])
   - Reported by: [Junior Member]
   - Severity: CRITICAL / HIGH / MEDIUM
   - Resolution: [How addressed]
   - Iterations to fix: [N]

2. **[Issue Name]** (Iteration [N])
   - ...

### Drift Incidents: [Count]

1. **[Drift Type]** (Iteration [N])
   - Description: [What drifted]
   - Detection: [How caught]
   - Resolution: [How corrected]
   - Impact: [Minimal / Moderate / Significant]

### Circular Changes Detected: [Count]

1. **[Issue]** (Iterations [N, M, P])
   - Description: [What kept coming back]
   - Root cause: [Why it happened]
   - Resolution: [How broken]

### Out-of-Scope Rejections: [Count]

1. **[Feedback Item]** (Iteration [N])
   - Requested by: [Junior Member]
   - Rejected by: Senior Member
   - Rationale: [Reference to requirements]
   - Driver validation: ✅ Correct / 🔴 Incorrect

---

## Team Performance

### Senior Member ([Model])

**Strengths**:
- [Specific positive behaviors]
- [Quality of synthesis]
- [Responsiveness to feedback]

**Areas for Improvement**:
- [Specific issues]
- [Patterns to address]

**Overall Rating**: X/5

### Junior Member 1 ([Model])

**Strengths**:
- [Review thoroughness]
- [Issue detection accuracy]
- [Feedback quality]

**Areas for Improvement**:
- [False positives]
- [Out-of-scope requests]

**Overall Rating**: X/5

### Junior Member 2 ([Model])

**Strengths**:
- [Specific strengths]

**Areas for Improvement**:
- [Specific issues]

**Overall Rating**: X/5

### Team Dynamics

- **Best collaboration**: [Example]
- **Friction points**: [Example]
- **Communication quality**: X/5

---

## Process Observations

### What Worked Well

1. [Specific process element that was effective]
2. [Another success]
3. [Another success]

### What Didn't Work

1. [Specific process failure or inefficiency]
   - Impact: [How it affected cycle]
   - Recommendation: [How to fix]

2. [Another failure]
   - Impact: [How it affected cycle]
   - Recommendation: [How to fix]

### Driver Interventions

- **Stop Events**: [Count]
  1. [Reason for stop, outcome]

- **Scope Challenges**: [Count]
  1. [Challenge, resolution]

- **Escalations to User**: [Count]
  1. [Issue, user decision]

---

## Recommendations

### Immediate Actions

1. **[Action Item]**
   - Rationale: [Why needed]
   - Owner: [Who should do it]
   - Priority: HIGH / MEDIUM / LOW

2. **[Action Item]**
   - ...

### Process Improvements

1. **[Process Change]**
   - Problem it solves: [What current pain]
   - Implementation: [How to adopt]
   - Expected impact: [Benefit]

2. **[Process Change]**
   - ...

### Documentation Needs

1. **[New Document Needed]**
   - Purpose: [Why needed]
   - Content: [What to include]
   - Owner: [Who creates it]

2. **[Existing Document to Update]**
   - Gap: [What's missing]
   - Update: [What to add]

### Trio Selection

- **Current Trio Performance**: X/5
- **Recommendation**: KEEP / ROTATE [Model] / CHANGE COMPOSITION
- **Rationale**: [Why]
- **Alternative Trio**: [Suggested composition if change recommended]

### Senior Member Selection

- **Current Senior Performance**: X/5
- **Recommendation**: KEEP / ROTATE TO [Model]
- **Rationale**: [Why]

---

## Key Learnings

### Technical Insights

1. [Something learned about the technology/domain]
2. [Another technical insight]
3. [Another technical insight]

### Process Insights

1. [Something learned about the development process]
2. [Another process insight]
3. [Another process insight]

### Team Insights

1. [Something learned about model performance/behavior]
2. [Another team insight]
3. [Another team insight]

---

## Success Criteria Met

- ✅ / 🔴 All requirements implemented
- ✅ / 🔴 Quality standards met
- ✅ / 🔴 No requirements drift
- ✅ / 🔴 Both Junior Members approved
- ✅ / 🔴 Production ready
- ✅ / 🔴 Within iteration budget (6 max)
- ✅ / 🔴 Within cost budget

---

## User Review Questions

1. Do you agree with the drift assessments?
2. Were the right issues prioritized?
3. Should any rejected feedback have been in scope?
4. Are you satisfied with the final quality?
5. Do you approve the recommended process changes?
6. Should we rotate the trio composition for next cycle?

---

## Appendix: Aggregated Review Summaries

### Generation Phase
- [Brief summary of each trio member's approach]

### Review Round 1
- **Junior Member 1**: [Key points from review]
- **Junior Member 2**: [Key points from review]

### Review Round 2 (if applicable)
- **Junior Member 1**: [Key points from review]
- **Junior Member 2**: [Key points from review]

[... etc for each review round]

---

**Report Generated by**: Driver (Claude Code)
**Report Date**: YYYY-MM-DD HH:MM
```

---

## Requirements Drift Detection

### Driver Responsibilities

**Continuous Monitoring**:
- Compare outputs to original requirements at each phase
- Flag deviations immediately
- Distinguish between:
  - **Beneficial drift**: Natural improvements/clarifications
  - **Harmful drift**: Scope creep, missing features, wrong direction

**Drift Indicators**:
- ✅ **Green**: Perfect alignment
- ⚠️ **Yellow**: Minor clarifications (beneficial)
- 🔴 **Red**: Scope creep or missing requirements (harmful)

**Drift Response**:
- Green: Continue
- Yellow: Note for user, continue if beneficial
- Red: STOP, consult user, realign before proceeding

---

## Context Optimization for Driver

### Driver Context Budget

**Reserved for**:
- Original requirements (immutable reference)
- Current phase outputs (minimal, just metadata)
- Team performance scores
- Drift detection summary
- User interaction history

**NOT for**:
- Full content of generations (use file references)
- Detailed code/document review (delegate to agents)
- Implementation details (track at summary level)

### Context Management Strategy

1. **Requirements**: Always in context (reference document)
2. **Outputs**: File paths + metadata only (not full content)
3. **Reviews**: Summary of issues (not full reviews)
4. **Iterations**: Change log (not full diffs)
5. **Performance**: Rolling scores (not full history)

---

## Example Workflow

### Case: Fiedler Multimodal Implementation (completed 2025-10-07)

**Phase 1: Generation**
- Trio: Gemini 2.5 Pro, GPT-4o, DeepSeek
- Outputs: 48KB, 5.6KB, 32KB
- Driver Rating: Coverage 5/5, Diversity 4/5, Quality 4/5

**Phase 2: Synthesis**
- Senior: Gemini 2.5 Pro
- Output: 9,175 tokens
- Driver Rating: Integration 5/5, Consistency 5/5, Drift 5/5

**Phase 3: Review Round 1**
- Reviewers: GPT-4o, DeepSeek
- Critical Issues: 4 (IPv6 SSRF, estimate_only, config, HEAD request)
- Driver Rating: Thoroughness 5/5, Actionability 5/5

**Phase 4: Iteration 1**
- Senior revised: 9,421 tokens
- Issues resolved: 4/4
- Driver Rating: Resolution 5/5, Progress 5/5

**Phase 5: Review Round 2**
- GPT-4o: APPROVED
- DeepSeek: 1 critical (redirect validation)
- Consensus: NO

**Phase 6: Iteration 2**
- Senior revised: 6,975 tokens
- Driver Rating: Responsiveness 5/5

**Phase 7: Review Round 3**
- GPT-4o: APPROVED
- DeepSeek: 1 critical (stream exhaustion)
- Consensus: NO

**Phase 8: Iteration 3**
- Senior revised: 2,023 tokens
- Driver Rating: Efficiency 4/5

**Phase 9: Review Round 4**
- GPT-4o: APPROVED
- DeepSeek: 1 critical (URL size limit)
- Consensus: NO

**Phase 10: Iteration 4**
- Senior revised: 2,899 tokens
- Driver Rating: Final push 5/5

**Phase 11: Final Consensus**
- GPT-4o: APPROVED ✅
- DeepSeek: APPROVED ✅
- Consensus: YES (3/3 implicit with senior)

**Overall Performance**:
- Total iterations: 4
- Time: ~2 hours
- All critical issues resolved
- Zero requirements drift
- **SUCCESS** ✅

---

## Next Steps

1. **Document Refinement**: Review this flow with user
2. **Tool Integration**: Build Driver evaluation tools
3. **Template Creation**: Standardize performance reports
4. **Workflow Automation**: Script common Driver tasks
5. **Metric Tracking**: Build dashboard for team performance

---

## Resolved Design Decisions

1. ✅ **Driver Stop Authority**: YES - Driver can stop and consult user when:
   - Circular changes (3rd occurrence)
   - Persistent drift (Red for 2+ iterations)
   - Max iterations exceeded (6)
   - Senior Member ignoring valid feedback
   - Cost/time budget exceeded

2. ✅ **Max Iteration Count**: 6 iterations before driver stops and consults user

3. ✅ **Consensus Mechanism**: Senior Member always approves (their work), only 2 Junior Members need to agree (2/2 for approval)

4. ✅ **Evaluation Metrics**: Three core scores
   - Quality (1-5)
   - Completeness (1-5)
   - Drift (1-5, with Green/Yellow/Red flagging)

5. ✅ **Drift Alerting**: Driver alerts Senior Member when drift detected in any review

6. ✅ **Circular Change Detection**: Driver monitors and flags after 3rd occurrence

7. ✅ **Senior Member Authority**: Can reject feedback as out-of-scope with rationale

8. ✅ **Post-Mortem Required**: Driver generates comprehensive report at end of every cycle

---

## Open Questions

1. Should Driver maintain a "lessons learned" database across projects?
2. How to optimize trio selection based on task type (code vs. docs vs. architecture)?
3. Should there be different iteration limits for different project types?
4. How to handle situations where Senior Member repeatedly rejects valid feedback?
5. Should post-mortem include automatic GitHub issue creation for process improvements?

---

**Status**: v1.0 - Ready for pilot implementation
