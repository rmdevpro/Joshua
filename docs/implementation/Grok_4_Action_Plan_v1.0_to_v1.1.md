# Action Plan for Updating ICCM Implementation Documents from v1.0 to v1.1

This action plan synthesizes feedback from all three AI reviews (Fiedler's default models and the Claude Sonnet 4.5 synthesis. It prioritizes fixes to address critical blockers (e.g., hardware feasibility, timeline realism, model inconsistencies) while maintaining the core PoC focus on CET-D validation. The plan assumes a 5-person team and aims for v1.1 to be "build-ready" with 85-90% success confidence, per reviewer estimates. Changes emphasize simplification, de-risking, and adding operational details without expanding scope.

## 1. Critical Path Fixes (Top 5 Must-Fix Items)

These are the highest-priority issues that could block implementation entirely if unaddressed, ranked by severity (based on consensus across reviews: hardware mismatches and timeline risks are most cited as "impossible" or "high risk"). Each includes the change needed, affected documents, and a concrete action.

1. **Hardware/Model Mismatch for LLM Ensemble**  
   - **What needs to change**: Replace 33B/70B models with 7B-class quantized models to fit P40 GPUs (96-144GB VRAM) without OOM errors or unacceptable latency (>10s per inference). Add quantization (AWQ/GPTQ) and engine benchmarks for Pascal compatibility.  
   - **Document(s)**: I03 (LLM Infrastructure), I14 (Model Architecture).  
   - **Concrete action**: In I03, update the model list to 6 quantized 7B models (e.g., Qwen2.5-Coder-7B-AWQ, DeepSeek-Coder-6.7B-GPTQ, Mistral-7B-Instruct-AWQ, CodeLlama-7B-Instruct-AWQ, StarCoder2-7B-AWQ, Phi-3-medium-4k-instruct-AWQ). Add a new "Quantization and Benchmark" subsection with code for downloading quantized checkpoints (e.g., via Hugging Face) and a Python script to benchmark tokens/sec on P40 (e.g., using vLLM or exllamaV2). In I14, reference this list for consistency in training estimates.

2. **Unrealistic Phase 3 Training Timeline and Compute**  
   - **What needs to change**: Revise estimates from 4 weeks to 8-10 weeks, incorporating aggressive caching, reduced iterations (e.g., 5 epochs instead of 15), and starting with 3 models before scaling to 6. Add compute budgets (e.g., max 500 GPU-hours).  
   - **Document(s)**: I08 (Phase 3 Training), I00 (Master Timeline).  
   - **Concrete action**: In I08, update the training script to include a caching mechanism (e.g., add `cache_reconstructions(app_id, llm_id)` function using PostgreSQL to store/retrieve prior results, targeting 90% hit rate). Reduce steps to 2,000 (20 apps * 10 iterations * 10 epochs). In I00, reallocate Weeks 9-18 to Phase 3 (see revised timeline below).

3. **Model Architecture Inconsistency**  
   - **What needs to change**: Unify on adapter-based finetuning (LoRA/QLoRA) of existing 1.5-7B code models, dropping bespoke CodeT5 scaling to 5B (unfeasible for lab compute).  
   - **Document(s)**: I06 (Phase 1), I07 (Phase 2), I08 (Phase 3), I14 (Model Architecture).  
   - **Concrete action**: In I14, replace CodeT5 progression with "Start with Qwen2.5-Coder-7B base + LoRA (rank=16, alpha=32); scale adapters if needed." Update I06-I08 training scripts to use this base (e.g., add `from peft import get_peft_model; model = get_peft_model(base_model, lora_config)`). Remove 5B references and add memory estimates for 7B (e.g., 28GB training on 2 P40s).

4. **Incomplete RL Training Math in Phases 2-3**  
   - **What needs to change**: Formalize REINFORCE-style loop as SCST or DPO with precise equations, reward normalization, and stability aids (e.g., baseline subtraction, gradient clipping).  
   - **Document(s)**: I07 (Phase 2), I08 (Phase 3).  
   - **Concrete action**: In I07 and I08, add a "RL Algorithm Details" subsection with code: For SCST, implement `advantage = reward - baseline; loss = -advantage * log_prob.detach();` with moving-average baseline update. Include sampling params (temperature=0.7, top-p=0.9) and normalization (rewards to [0,1]). Test with a small example (1 app, 1 epoch).

5. **Lack of Failure Recovery and Error Handling**  
   - **What needs to change**: Add standardized error handling, retries, and recovery procedures across components to prevent cascading failures.  
   - **Document(s)**: I03, I05, I07, I08, I11.  
   - **Concrete action**: In each document, add an "Error Handling and Recovery" subsection with code (e.g., in I08: `try: impl = llm.generate() except TimeoutError: retry(3) or fallback_to_cached()`). In I11, add rollback script triggered by metrics (e.g., if pass_rate < 0.7, revert to previous checkpoint).

## 2. Document-by-Document Action Items

For each document (I00-I14), prioritized changes (highest first) based on reviewer consensus. Priorities: 1=Blocker, 2=High impact, 3=Polish.

- **I00 (Master Document)**:  
  1. Add go/no-go gates (e.g., Week 6: Foundation stable; Week 12: Phase 3 >65% pass rate).  
  2. Include revised timeline with buffers (see Section 3 below).  
  3. Add new "API Specifications" appendix with OpenAPI YAML for inter-component communication.

- **I02 (Foundation Layer)**:  
  1. Fix DDL syntax (change "INDEX ..." to "CREATE INDEX ON ...").  
  2. Add dependency management for isolated Docker (e.g., local PyPI mirror script).  
  3. Include security hardening (e.g., AppArmor profiles, cgroup limits in Docker Compose YAML).

- **I03 (LLM Infrastructure)**:  
  1. Downsize models to 7B quantized and add benchmarks (as in Critical Fix #1).  
  2. Add error handling for vLLM failures (e.g., retry logic in rotation controller).  
  3. Simplify rotation: Start with 3 concurrent models, defer to 6.

- **I04 (Application Dataset)**:  
  1. Add pytest-json-report to Dockerfile.  
  2. Include synthetic data generation script (e.g., mutate_app function).  
  3. Add staffing buffer for manual gold standard creation (e.g., 20% time contingency).

- **I05 (Conversation Capture)**:  
  1. Add non-Claude MCP fallback (e.g., editor plugin script).  
  2. Fix schema consistency (add FKs for session_id linking).  
  3. Include error handling for DB writes (e.g., queue to disk on failure).

- **I06 (Phase 1 Training)**:  
  1. Unify base model to Qwen2.5-Coder-7B + LoRA (align with I14).  
  2. Add checkpointing for training state (e.g., save optimizer/scheduler).  
  3. Include reward normalization in data prep script.

- **I07 (Phase 2 Training)**:  
  1. Formalize RL math as SCST (as in Critical Fix #4).  
  2. Add caching for reconstructions to reduce compute.  
  3. Include debugging dashboard snippet (e.g., Streamlit UI for failed runs).

- **I08 (Phase 3 Training)**:  
  1. Revise compute estimates and add caching (as in Critical Fix #2).  
  2. Formalize RL math and stability aids (as in Critical Fix #4).  
  3. Add error handling for inference failures (as in Critical Fix #5).

- **I09 (Validation)**: No major changes needed (already "Complete" across reviews).  
  1. Add human inter-rater agreement metric (e.g., Cohen's kappa).  
  2. Include staging plan (e.g., smoke tests on 3 apps).

- **I10 (Monitoring)**:  
  1. Add runbooks for alerts (e.g., "If GPU OOM, restart vLLM").  
  2. Include full Prometheus YAML and SLOs (e.g., p95 latency <10s).  
  3. Add log aggregation (e.g., Loki integration).

- **I11 (Production Pipeline)**:  
  1. Expand rollback triggers with code (as in Critical Fix #5).  
  2. Fix schema FKs for session_id joins.  
  3. Add deployment script for canary rollout.

- **I12 (Data Management)**: No major changes needed (rated "Complete").  
  1. Add auto-cleanup script for storage overflow.  
  2. Include DVC for model versioning.

- **I13 (Agentic Architecture)**:  
  1. Defer to v2.0 (as in De-Scoping below).  
  2. If kept, add performance guardrails (e.g., bypass switch).  
  3. Simplify to 3 agents initially.

- **I14 (Model Architecture)**:  
  1. Unify on 7B adapters, drop 5B scaling (as in Critical Fix #3).  
  2. Add DeepSpeed config for tensor parallelism.  
  3. Update memory estimates for quantized models.

## 3. Timeline Revisions

Revised 28-week timeline reallocates time from de-scoped elements (e.g., Agentic Phase) to buffers and extended training, per Gemini/GPT-5 feedback. Total remains 28 weeks but adds 4 buffer weeks (1 per major phase) for debugging/convergence. Critical path: Foundation → Training → Validation.

- **Weeks 1-6: Foundation (I02-I05)** (Extended from 4 weeks; add buffer for curation delays).  
- **Weeks 7-18: CET Training (I06-I08)** (Extended from 8 weeks; 4 for Phases 1-2, 6 for Phase 3, 2 buffer).  
- **Weeks 19-22: Validation (I09)** (Same as original; add 1 buffer week).  
- **Weeks 23-28: Production (I10-I11)** (Shortened from 8 weeks; focus on core pipeline, add 1 buffer).  
- **Agentic (I13) deferred**: No allocation; move to post-28 weeks.

Milestones: Week 6 gate (infrastructure stable), Week 12 gate (Phase 2 >50% pass), Week 18 gate (Phase 3 >75% pass).

## 4. De-Scoping Recommendations

To reduce complexity and fit realistic timeline/hardware, defer non-core elements. This aligns with all reviews' emphasis on simplification for PoC success.

- **Remove/Defer to v1.2**: Scaling LLM orchestra from 3 to 6 models (I03; start with 3, add in v1.2 after stability proven). Full multi-objective reward (I08; start with mean pass rate only, add variance/API terms in v1.2). Dataset expansion to full 50 apps (I04; target 20-30 for PoC, curate remaining in v1.2).  
- **Defer to v2.0**: Agentic Infrastructure (I13; entire document/Phase 5 as post-PoC extension). Scaling beyond 50 apps (I04/I12; add synthetic generation and automation in v2.0). CET-P/T variants (I00; focus on CET-D only). Bidirectional processing (I00; unidirectional sufficient for PoC). Custom 5B model training (I14; stick to 7B adapters).

## 5. New Sections to Add

These are entirely new content blocks to address consensus gaps, written as subsections in existing documents unless noted.

- **Error Handling and Recovery** (Add to I03, I05, I07, I08, I11): 1-2 pages per doc with code snippets for retries, fallbacks, and logging (e.g., using try-except and custom exceptions).  
- **API Specifications Appendix** (New in I00): 3-5 pages with OpenAPI YAML schemas for inter-component calls (e.g., /generate_impl endpoint).  
- **Quantization and Benchmark Matrix** (New in I03): 1-page table with model benchmarks on P40 (tokens/sec, VRAM usage) and quantization scripts.  
- **RL Algorithm Details** (New in I07 and I08): 2 pages per doc with equations, pseudocode, and stability techniques (e.g., SCST implementation).  
- **Security Hardening** (New in I02): 1 page with Docker security configs (e.g., seccomp profiles, ulimits) and runbooks.  
- **Debugging Dashboard** (New in I10): 1-page spec for a Streamlit/Gradio UI to inspect failed reconstructions (input code, requirements, LLM outputs, test logs).
