# I00: ICCM Implementation Master Document

**Version:** 1.2
**Date:** 2025-10-01
**Status:** Planning Phase

---

## Changelog

### v1.2 (2025-10-01)
- **Added**: I14 Model Architecture document to structure
- **Changed**: All documents updated to v1.0 incorporating Opus review feedback
- **Process**: v0.0 documents archived before modifications
- **Status**: All 14 implementation documents at v1.0, ready for review round 2

### v1.1 (2025-10-01)
- Added Phase 5 (Agentic Architecture) with I13
- Extended timeline to 28 weeks (7 months)

### v1.0 (2025-10-01)
- Initial master document created
- Added all-local LLM decision
- Added conversation capture as I05

---

---

## Purpose

This master document serves as the control center for the ICCM implementation, tracking:
- Overall implementation outline and structure
- Dependencies between implementation phases
- Status of each implementation document
- Change history and decision log
- Critical path and milestones

---

## Implementation Document Structure

### Core Documents
- **I00** - Master Implementation Document (this document)
- **I01** - Implementation Summary (executive overview)

### Phase 1: Foundation (Weeks 1-4)
- **I02** - Foundation Layer: Hardware, Database, Docker (Week 1-2)
- **I03** - LLM Infrastructure: Model Serving & Orchestra (Week 2-3)
- **I04** - Application Dataset: Curation & Test Harness (Week 3-4)
- **I05** - Conversation Capture System (Week 1-3, parallel)

### Phase 2: CET Training (Weeks 5-12)
- **I06** - Phase 1 Training: RAG & Subject Expertise (Week 5-6)
- **I07** - Phase 2 Training: Context Transformation (Week 7-8)
- **I08** - Phase 3 Training: Interactive Feedback Loop (Week 9-12)

### Phase 3: Validation (Weeks 13-16)
- **I09** - Validation Framework: Three Baselines & Statistical Tests

### Phase 4: Production (Weeks 17-24)
- **I10** - Monitoring & Observability Infrastructure (Week 17-20)
- **I11** - Production Pipeline: Phase 4 Continuous Learning (Week 21-24)

### Phase 5: Agentic Enhancement (Weeks 25-28)
- **I13** - Agentic Infrastructure Architecture (AutoGen + MCP) (Week 25-28)

### Supporting Infrastructure
- **I12** - Data Management & Backup Strategy (Continuous)
- **I14** - CET-D Model Architecture (Week 4-5)

---

## Implementation Timeline

| Phase | Duration | Documents | Critical Milestone |
|-------|----------|-----------|-------------------|
| **Foundation** | Weeks 1-4 | I02-I05 | Infrastructure ready, 10 apps curated |
| **CET Training** | Weeks 5-12 | I06-I08 | Phase 3 complete, first reconstruction results |
| **Validation** | Weeks 13-16 | I09 | Statistical proof: CET-D beats RAG (p<0.05) |
| **Production** | Weeks 17-24 | I10-I11 | Phase 4 deployed, 50-app validation complete |
| **Agentic Enhancement** | Weeks 25-28 | I13 | Agentic layer operational, first duo deployed |

**Total Duration:** 28 weeks (7 months)

---

## Critical Path Dependencies

```
I02 (Foundation) → I05 (Conversation Capture) → I04 (Dataset)
                 ↓                                    ↓
I03 (LLM Infra) → I06 (Phase 1) → I07 (Phase 2) → I08 (Phase 3)
                                                        ↓
                                    I09 (Validation) → I10 (Monitoring)
                                                        ↓
                                                   I11 (Production)
                                                        ↓
                                    I13 (Agentic Architecture)

I12 (Backup) runs continuously across all phases
```

---

## Document Status Tracking

| Doc | Title | Status | Owner | Last Updated |
|-----|-------|--------|-------|--------------|
| I00 | Master Document | ✅ v1.2 | - | 2025-10-01 |
| I01 | Implementation Summary | ✅ v1.0 | - | 2025-10-01 |
| I02 | Foundation Layer | ✅ v1.0 | - | 2025-10-01 |
| I03 | LLM Infrastructure | ✅ v1.0 | - | 2025-10-01 |
| I04 | Application Dataset | ✅ v1.0 | - | 2025-10-01 |
| I05 | Conversation Capture | ✅ v1.0 | - | 2025-10-01 |
| I06 | Phase 1 Training | ✅ v1.0 | - | 2025-10-01 |
| I07 | Phase 2 Training | ✅ v1.0 | - | 2025-10-01 |
| I08 | Phase 3 Training | ✅ v1.0 | - | 2025-10-01 |
| I09 | Validation Framework | ✅ v1.0 | - | 2025-10-01 |
| I10 | Monitoring & Observability | ✅ v1.0 | - | 2025-10-01 |
| I11 | Production Pipeline | ✅ v1.0 | - | 2025-10-01 |
| I12 | Data Management | ✅ v1.0 | - | 2025-10-01 |
| I13 | Agentic Infrastructure (AutoGen + MCP) | ✅ v1.0 | - | 2025-10-01 |
| I14 | Model Architecture | ✅ v1.0 | - | 2025-10-01 |

**Status Legend:**
- 📝 Pending - Not started
- 🔨 In Progress - Actively being written
- 👁️ Review - Ready for AI review
- ✅ Approved - Reviewed and approved
- 🚀 Implemented - Actually built
- ✔️ Validated - Tested and working

---

## Success Criteria (from AI Reviews)

### Primary Metrics
- **Test Pass Rate:** >75% average on hold-out set
- **Statistical Significance:** CET-D beats RAG by ≥15% (p<0.05)
- **Implementation Variance:** <20% across LLM orchestra

### Secondary Metrics
- **Inference Speed:** <5s for requirements extraction
- **Context Compression:** >50% token reduction
- **Human Agreement:** >80% match with gold standard

### Infrastructure Targets
- **Uptime:** >99% for execution environment
- **Cost:** <$100/month operational (all-local LLMs)
- **Throughput:** 600-1,000 test executions/day

---

## Key Architectural Decisions

### Decision Log

**2025-10-01: All-Local LLM Orchestra**
- **Decision:** Use 6 local models instead of paid APIs (GPT-4, Claude, Gemini)
- **Rationale:**
  - Zero monthly API costs ($0 vs $300-500)
  - Better diversity through different model families
  - Unlimited inference for training
  - Full reproducibility
- **Models:** DeepSeek-Coder-33B, CodeLlama-34B, Llama-3.1-70B, Mistral-7B, Qwen-2.5-14B, Phi-3-mini
- **Reference:** Conversation with Claude (Sonnet 4.5), 2025-10-01

**2025-10-01: Conversation Capture Priority**
- **Decision:** Add conversation capture as first-class component (I05)
- **Rationale:**
  - Captures real requirements engineering conversations
  - Training data for future CET-P (personalization)
  - Essential for learning from actual usage patterns
- **Implementation:** Wrapper around Claude Code → PostgreSQL
- **Reference:** User requirement, 2025-10-01

**2025-10-01: 50-App Quality-Over-Quantity Dataset**
- **Decision:** 50 high-quality apps (40 train, 10 hold-out) instead of 3,000+
- **Rationale:**
  - Enables 100% manual validation
  - Rigorous statistical testing still valid
  - Feasible for 5-person lab
  - Addresses v2.1 reviewer concerns about scale
- **Reference:** Papers v3 updates, AI reviewer consensus

**2025-10-01: Agentic Architecture with AutoGen + MCP**
- **Decision:** Adopt AutoGen for multi-agent coordination, MCP for tool interfaces
- **Rationale:**
  - "Agent sits in front of every function" design principle
  - AutoGen handles multi-LLM orchestration naturally (6-model orchestra)
  - MCP provides standardized tool interfaces
  - Enables Modular Agentic Duos (CET + Agent pairing)
  - CETs become optional learning enhancements for agents
- **Architecture:** 6 core agents (Data, LLM Orchestrator, Execution, Validation, Training, Monitoring)
- **Reference:** Conversation with Claude (Sonnet 4.5), 2025-10-01

---

## Resource Allocation

### Hardware (Already Available - Paper 08)
- 4-6× P40 GPUs (96-144GB VRAM)
- 256GB RAM (with $200 upgrade for caching)
- 4TB NVMe storage
- **Total Cost:** $7,840 (one-time, already spent)

### Software/Services
- PostgreSQL 15+ with pgvector (open source)
- Docker Compose (open source)
- vLLM for model serving (open source)
- Local LLM models (open source)
- **Monthly Cost:** ~$50 (electricity only)

### Team (5 people assumed)
- Implementation lead
- ML engineer (CET training)
- Infrastructure engineer (Docker, DB)
- Dataset curator / QA
- Domain expert (requirements validation)

---

## Risk Register

| Risk | Impact | Likelihood | Mitigation | Owner |
|------|--------|------------|------------|-------|
| Dataset curation bottleneck | High | Medium | Start with 10 apps, automate where possible | Dataset curator |
| Model serving VRAM constraints | Medium | Low | Proven rotation strategy (Paper 08) | Infra engineer |
| Conversation capture performance | Medium | Low | Async writes, batch embeddings | ML engineer |
| Statistical significance not achieved | High | Medium | Iterate on Phase 3 training, expand dataset | ML lead |
| Catastrophic forgetting in Phase 4 | Medium | Low | Canary set monitoring, rollback capability | ML engineer |

---

## Integration with Papers

This implementation directly realizes the theoretical framework from:

| Paper | Implemented By | Notes |
|-------|----------------|-------|
| Paper 01 (Primary) | I06-I08 | Four-phase training methodology |
| Paper 02 (Progressive Training) | I06-I08 | Phase 1-3 detailed implementation |
| Paper 03 (CET Architecture) | I06-I08 | CET-D training specifics |
| Paper 04A (Reconstruction Testing) | I08, I09 | Core validation loop |
| Paper 04B (Production Learning) | I11 | Phase 4 continuous improvement |
| Paper 05 (CET-D Implementation) | I04, I08 | Requirements engineering focus |
| Paper 06 (Validation Framework) | I09 | Statistical tests, baselines |
| Paper 08 (Test Lab Infrastructure) | I02 | Hardware specs and optimizations |
| Paper 09 (Containerized Execution) | I02 | Docker Compose setup |
| Paper 10 (LLM Orchestra) | I03 | Local model serving (revised) |
| Paper 11 (Testing Infrastructure) | I04, I10 | Test harness and monitoring |
| Paper 12 (Conversation Storage) | I02, I05 | PostgreSQL + pgvector |
| Papers 07A/07B, 13, 14 | Future work | Deferred post-PoC |

---

## Next Steps

### Immediate (This Week)
1. Complete I01 (Implementation Summary)
2. Draft I02 (Foundation Layer)
3. Draft I05 (Conversation Capture) - **Critical for data collection**
4. Set up implementation directory structure

### Week 1 Goals
1. All foundation documents (I02-I05) drafted
2. AI review of foundation docs
3. Begin infrastructure setup (I02 execution)

### Month 1 Goals
1. Foundation complete (I02-I05 implemented)
2. Training documents (I06-I08) drafted and reviewed
3. First 10 apps curated (I04 execution)
4. Conversation capture operational

---

## Review Process

### AI Review Protocol (mirroring papers)
1. Complete implementation document draft
2. Package for review (same format as papers)
3. Send to AI reviewers:
   - Gemini 2.5 Pro
   - GPT-5
   - Grok 4
   - (GPT-4.1 optional for comparison)
4. Synthesize feedback
5. Iterate on document
6. Mark as approved when ready for implementation

### Review Focus Areas
- **Completeness:** All steps clearly defined?
- **Feasibility:** Can this actually be built?
- **Dependencies:** Are prerequisites identified?
- **Metrics:** How do we measure success?
- **Risks:** What could go wrong?

---

## Change History

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2025-10-01 | 1.0 | Initial master document created | Claude (Sonnet 4.5) |
| 2025-10-01 | 1.0 | Added all-local LLM decision | Claude (Sonnet 4.5) |
| 2025-10-01 | 1.0 | Added conversation capture as I05 | Claude (Sonnet 4.5) |
| 2025-10-01 | 1.1 | Added Phase 5 (Agentic Architecture) with I13 | Claude (Sonnet 4.5) |
| 2025-10-01 | 1.1 | Extended timeline to 28 weeks (7 months) | Claude (Sonnet 4.5) |
| 2025-10-01 | 1.2 | Archived v0.0, updated all docs to v1.0 with Opus feedback | Claude (Sonnet 4.5) |
| 2025-10-01 | 1.2 | Added I14 Model Architecture document | Claude (Sonnet 4.5) |

---

## Notes

- This implementation plan realizes the v3 paper suite's theoretical framework
- All four AI reviewers (Gemini, GPT-4.1, GPT-5, Grok) emphasized: **build the PoC first**
- Critical path: Foundation → Phase 3 training → Statistical validation
- Success = empirical results that can be added to papers for publication
