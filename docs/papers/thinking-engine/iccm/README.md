# ICCM Papers Directory Structure

## Current Papers (Main Directory)

### Primary Paper
- **00_ICCM_Primary_Paper_v1.md** - Main theoretical paper (submitted for review)

### Sub-Papers (Complete Drafts)
- **01_Progressive_Training_Methodology_v1.md** - Four-phase training approach
- **02_CET_Architecture_Specialization_v1.md** - CET-P/T/D variants
- **03A_Code_Execution_Feedback_v1.md** - Interactive code feedback mechanisms
- **03B_Production_Learning_Pipeline_v1.md** - Production training pipeline
- **04_CET_D_Software_Implementation_v1.md** - Software domain implementation
- **05_Automated_Validation_Framework_v2.md** - Validation methodology
- **06A_Self_Bootstrapping_Development_v1.md** - Self-bootstrapping (partial)
- **06B_Continuous_Self_Improvement_v1.md** - Continuous improvement
- **07_Test_Lab_Infrastructure_v2.md** - Hardware/network infrastructure
- **08_Containerized_Code_Execution_for_Small_Labs_v3.md** - **UNIFIED: Docker-based execution + security for small labs**
- **09_LLM_Orchestra_v1.md** - Multi-LLM coordination (outline)
- **10_Testing_Infrastructure_v1.md** - Testing framework (outline)
- **11_Conversation_Storage_Retrieval_v1.md** - Conversation management

### Future Work Papers
- **F01_Bidirectional_Processing_v1.md** - Input/output processing (outline)
- **F02_Edge_CET_P_v1.md** - Edge deployment (outline)
- **F03_Requirements_Reverse_Engineering_v4.md** - Requirements extraction

### Master Document
- **ICCM_Master_Document_v11.md** - Current tracker for all papers

## Archive Directory Structure

### `/archive/old_versions/`
Superseded v1 versions of papers that have been rewritten:
- 03_Interactive_Learning_Code_Feedback_v1.md
- 06_Self_Bootstrapping_v1.md
- 07_Test_Lab_Infrastructure_v1.md
- 08_Containerized_Execution_v1.md
- 08B_Security_Hardening_Incident_Response_v1.md

### `/archive/master_document_versions/`
Historical master document versions (v3-v6):
- ICCM_Master_Document_v3.md through v6.md

### `/archive/session_docs/`
Session summaries and reality check documents:
- SESSION_SUMMARY_2025-10-01.md
- SESSION_SUMMARY_2025-10-01_B.md
- REALITY_CHECK_2025-10-01.md (Paper 08B over-engineering)
- REALITY_CHECK_08A_2025-10-01.md (Paper 08A over-engineering)

### `/archive/v1_enterprise_overkill/`
Paper 08A v1 - Enterprise Kubernetes architecture (over-engineered for small lab)

### `/archive/v2_enterprise_overkill/`
Paper 08B v2 - Enterprise security (over-engineered for small lab)

### `/archive/v2_split_papers/`
Papers 08A v2 and 08B v3 - Split architecture/security papers (recombined into Paper 08 v3)

### `/archive/v1/` through `/archive/v6/`
Master document version history

### Other archived files
- Various conversation backups
- Historical academic reviews
- Old paper outlines and structure documents

## Key Changes Log

### Paper 08 Evolution (2025-10-01)
1. **v1**: Enterprise Kubernetes architecture (1,465 lines) - OVER-ENGINEERED
2. **v2 Split**: 08A (architecture 3,500 words) + 08B (security 3,000 words) - RIGHT-SIZED
3. **v3 Unified**: Recombined into single paper (6,500 words) - CURRENT

**Rationale for recombination:** Both papers told the same story for the same context (simple Docker execution for 5-person labs). Combined length (6,500 words) = ideal conference paper.

### Reality Checks (2025-10-01)
- **Paper 08B**: v2 enterprise security → v3 pragmatic security
- **Paper 08A**: v1 Kubernetes (100k executions/day) → v2 Docker Compose (600-1k executions/day)
- **Paper 07**: Added TP-Link ER7206 router and TL-SG1428PE switch, simplified network architecture

## Current Status (as of v11)

**Complete Drafts:** 12 papers
- Papers 00, 01, 02, 03A, 03B, 04, 05, 06B, 07, 08, 11, F03

**Partial Draft:** 1 paper
- Paper 06A (sections 1-5 complete)

**Outlines Ready:** 4 papers
- Papers 09, 10, F01, F02

**Total Papers:** 17 papers in ICCM suite

---

*Last updated: 2025-10-01*
*Maintained by: Claude Sonnet 4.5*
