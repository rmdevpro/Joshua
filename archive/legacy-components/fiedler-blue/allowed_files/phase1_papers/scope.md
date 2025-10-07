# ICCM System Architecture - Scope Definition

## Project Context

Building implementation architecture for Intelligent Context and Conversation Management (ICCM) system based on 14 research papers defining theoretical framework.

**Primary Goal:** Transform research papers into concrete system architecture that runs on existing infrastructure.

---

## IN SCOPE - CET-D Proof of Concept

### Core System Components

**CET-D Training Pipeline:**

- Phase 1: Subject expertise acquisition (RAG-grounded training on domain knowledge)
- Phase 2: Context engineering skills (learning to transform context effectively)
- Phase 3: Interactive context optimization (feedback loops with LLM Orchestra)
- Phase 4: Minimal continuous self-improvement (offline self-critique, simulated production loops for proof-of-concept)
- **Note:** CET-D generates ONLY optimized context; LLM Orchestra generates actual outputs (requirements, code, tests)

**LLM Orchestra:**

- M5-based infrastructure (4x Tesla P40 GPUs) managing local model deployment
- Dynamic model loading/rotation (swap models every 4-12 hours for diversity)
- Local model library: Llama 3.1 70B, DeepSeek-R1 70B, Mistral Large, Qwen variants, etc.
- Model storage on Irina NAS (60TB capacity, stores 50+ models)
- Cloud API coordination: Together.AI, GPT-4o, Gemini 2.5 Pro, Claude (supplemental)
- Intelligent routing: prefer local ($0.003/M) over cloud ($0.88-15/M)
- Phase-specific model rotation strategy for training diversity
- Request batching, response caching, load balancing
- API cost guardrails: daily/monthly spend caps, fallback routing, alert thresholds
- **Role:** Generates actual outputs (requirements, code, tests) using CET-engineered context

**Requirements Engineering Domain:**

- Application analysis and understanding
- Engineering context that enables LLM Orchestra to extract requirements from applications
- Validation via reconstruction testing
- 50-application validation dataset (40 training / 10 hold-out)

**Test Lab Infrastructure:**

- Code execution environment
- Containerized isolation (Docker-based)
- Test execution and validation
- 600-1000 executions/day capacity

**Conversation Storage & Retrieval:**

- Training data persistence
- Conversation history management
- Phase transition data preservation

**RAG System:**

- Vector database (pgvector) for knowledge storage
- Embedding models for semantic search
- Retrieval logic (chunking, top-k selection, reranking)
- Knowledge base indexing from application codebases

**Reconstruction Testing Pipeline:**

- Orchestration of LLM Orchestra for multi-LLM implementations
- Test Lab execution coordination
- Pass rate calculation and analysis
- Comparison framework (CET-D vs RAG baseline vs Gold Standard)

**Validation & Metrics Framework:**

- Experiment runner for systematic evaluation
- Metrics collection (pass rates, compatibility scores, reconstruction success)
- Statistical testing (paired t-test, α=0.05, 80% power)
- Baseline comparisons and reporting

**Gold-Standard Protocol:**

- Two-reviewer independent requirements generation
- Third reviewer adjudication for disagreements
- Time budget: 6-10 hours per application
- Decision documentation and quality criteria

**Dataset Preparation & Management:**

- 50-application selection criteria (language, size bands, test coverage thresholds)
- License compliance verification
- Ingestion and code analysis pipeline
- Partitioning (40 training / 10 hold-out validation)

**Experiment Tracking:**

- Configuration versioning (Git-based)
- Dataset snapshot hashes for reproducibility
- Seed capture for deterministic runs
- Results storage (PostgreSQL/CSV)
- Re-run scripts for validation

**Model Management:**

- CET checkpoint storage and versioning
- Model deployment
- Performance monitoring

### Infrastructure Constraints

**Hardware (Owned/Operational):**

- **M5 Server**: LLM Orchestra primary deployment
  - 4x Tesla P40 (96GB VRAM) - Inference
  - Tesla V100 32GB - CET training
  - Optional expansion - 3 open GPU spots for either. Strong case will need to be made to find funding.
    - Telsa P40s - $260 ea
    - Telsa V100 - $1000 ea
- **Irina NAS**: 60TB storage - model library (50+ models) + backup/archive
  - Also contains 2x Tesla P4
- **Workstation**: Edge testing or inference
  - RTX 3050
- **Pharoh**: Orchestration Server
- **Scale**: Research lab (not production)

**Team:**

- 5-person research team
- Manual validation capability: ~50 applications
- Timeline: 10-16 weeks (2.5-4 months) for proof of concept
  - Weeks 1-3: Infrastructure setup + RAG baseline
  - Weeks 2-6: Gold standard + Phase 1/2 training
  - Weeks 5-10: Phase 3 training + reconstruction pipeline
  - Weeks 9-12: Minimal Phase 4 + statistical analysis
  - Weeks 13-16: Buffer for iterations and final validation

**Validation Dataset:**

- 50 high-quality applications
- 40 training / 10 hold-out validation
- 100% manual validation
- Quality over quantity

### Quality Standards

**Statistical Rigor:**

- Paired t-test validation (α = 0.05)
- 80% power to detect 15% improvement
- Comparison against RAG baseline + manual gold standard

**Performance Targets:**

- > 75% test pass rate on reconstructed applications
- > 15% improvement over RAG baseline (p<0.05)
- Reconstruction success validates requirements completeness

---

## OUT OF SCOPE - Future Work

### CET Variants Not in Initial Implementation

**CET-P (Personal Context Engineering):**

- Edge deployment architecture
- Privacy-preserving federated learning
- 1-3B parameter model compression
- Cross-device synchronization
- Deferred to future work per Paper 14

**CET-T (Team Context Engineering):**

- Team collaboration features
- Shared context optimization
- Multi-user coordination
- Deferred to future work per Paper 01

### Advanced Features

**Bidirectional Processing:**

- Response adaptation in reverse pass
- Full pipeline control
- Deferred to future work per Paper 13 (F01)

**Production Deployment:**

- Production-scale continuous learning (Phase 4)
- Real-time deployment adaptation
- Enterprise scaling
- Cloud deployment
- Production-grade security hardening
- Enterprise monitoring and observability
- Note: Minimal Phase 4 (offline self-critique, simulated loops) IS in scope for PoC validation

**Large-Scale Training:**

- 500+ application datasets
- 3,000+ application datasets
- Automated quality filtering
- Deferred per Paper 05 scaling roadmap

---

## DECISION RULES

### When Evaluating New Requirements:

**Include if:**

1. ✅ Explicitly mentioned in research papers 01, 02, 04, 05, 09, 10, 11
2. ✅ Required for CET-D proof of concept
3. ✅ Feasible with 5-person team and $7,840 infrastructure
4. ✅ Needed for 50-app validation

**Defer if:**

1. ❌ Related to CET-P or CET-T variants
2. ❌ Production/enterprise features beyond proof of concept
3. ❌ Requires infrastructure beyond current budget
4. ❌ Not traceable to research papers
5. ❌ "Nice to have" vs. "must have" for validation

### Scope Change Process:

1. Document proposed addition in planning_log.md
2. Justify against decision rules
3. Identify source paper citation
4. User approval required
5. Update this scope.md if approved

---

## Key Architectural Boundaries

### What We're Building:

**Research validation system** that proves:

- Context engineering can be learned through progressive training
- CET-D (5B params) outperforms general LLMs (70B+) for requirements domain
- Reconstruction testing validates requirements quality
- Four-phase training methodology works

### What We're NOT Building:

- Production SaaS platform
- Consumer applications
- Multi-tenant systems
- Enterprise-grade security infrastructure
- Horizontal scaling infrastructure (Kubernetes, etc.)

---

## Success Criteria

**Architecture is successful if:**

1. All components trace to research papers
2. System runs on existing infrastructure (M5, Irina, Pharoh, Workstation)
3. Supports 50-app validation workflow (40 training / 10 hold-out)
4. Enables statistical validation (paired t-test, α=0.05, 80% power)
5. Implements all 4 training phases for CET-D (Phase 4 minimal for PoC)
6. Provides reconstruction testing pipeline
7. Manual validation feasible for 5-person team
8. **CET-D outputs only optimized context, verifiably distinct from LLM Orchestra's actual requirement specifications**
9. CET-D + LLM Orchestra ensemble outperforms RAG baseline and approaches gold standard on requirements extraction
10. Demonstrates that CET-engineered context enables smaller/faster systems to match or exceed generalist 70B+ baseline performance within requirements engineering domain

**Architecture has drifted if:**

1. Components appear not mentioned in papers
2. Workflow assumes >50 applications
3. CET-P or CET-T features creep in
4. Production features overshadow research validation
5. Complexity exceeds research lab capability

---

## Document Control

**Version:** 1.0 - Triplet Validated
**Date:** 2025-10-02
**Status:** Awaiting User Final Approval
**Triplet Validation:** Gemini 2.5 Pro (25/25), GPT-5 (25/25), Grok 4 (11/25)
**Key Corrections Applied:**

- Clarified CET generates context only; LLM Orchestra generates outputs
- Corrected infrastructure to actual owned hardware
- Added 7 missing critical components (RAG, Reconstruction Testing, Validation Framework, etc.)
- Clarified Phase 4 as minimal PoC (not production deployment)
- Added detailed timeline (10-16 weeks)
- Enhanced success criteria to reflect architectural boundaries

---

## Notes

This scope definition will be validated by sending to Gemini 2.5 Pro, GPT-5, and Grok 4 for independent review. Their feedback will be synthesized and this document updated before architecture work begins.
