# Paper 15: Ephemeral MADs and Persistent Learning Architecture

## Status: Concept Discussion (To be formalized later)

---

## The eMAD Concept - Initial Discussion

### Core Idea

**eMADs (Ephemeral MADs)** - On-demand workers that spin up based on a class, get used, then are destroyed.

**The Innovation:** Workers disappear, but their learning remains.

### Key Characteristics

1. **On-Demand Lifecycle**: Instantiated when needed → Execute task → Destroyed when done
2. **Role-Based**: Each eMAD represents a specific role (PM, Senior Dev, Junior Dev, Specialist LLM, etc.)
3. **Shared Learning**: All instances of a role type share the same underlying ML models
4. **Concurrent Instances**: Multiple instances of same role can run simultaneously
5. **Collective Intelligence**: Every instance contributes to training the shared model

### Contrast with Persistent MADs

| Aspect | Persistent MADs | eMADs |
|--------|----------------|-------|
| **Lifecycle** | Always running | On-demand, temporary |
| **Examples** | Rogers, Dewey, Fiedler, Horace | PM, Senior Dev, LLM Specialists |
| **Purpose** | Infrastructure/services | Role-based workers |
| **State** | Maintains session state | Stateless (model persists) |
| **Resource** | Continuous resources | Resources only when active |

### The Shared Model Innovation

- **PM Model** persists and improves over time
- **Senior Dev Model** persists and improves over time
- **Junior Dev Model** persists and improves over time
- Each instantiation gets the latest trained model
- All activities from all instances contribute to training
- Multiple simultaneous instances all benefit from collective learning

### Primary Use Case: LLM Development Teams

**Example:** Development cycle requires PM + Senior Dev + 2 Junior Devs

```
Imperator (persistent MAD) receives development request
    ↓
Instantiates development team:
    - PM (eMAD using pm model v2.1)
    - Senior Developer (eMAD using senior_dev model v3.4)
    - Junior Developer 1 (eMAD using junior_dev model v1.8)
    - Junior Developer 2 (eMAD using junior_dev model v1.8)
    ↓
Team collaborates via conversation bus
    ↓
Development cycle completes
    ↓
All eMADs contribute to their respective role models
    ↓
Team instances terminated
    ↓
Next development cycle gets benefit of improved models
```

### Potential Use Cases Beyond LLMs

**Note:** May be eMADs that are not the LLM use case. Can't think of specific examples right now, but the pattern is possible.

**The Key Pattern:** Like having workers, but instead of just disappearing entirely their learning remains.

#### Possible Non-LLM eMAD Examples:

1. **Data Processing eMADs**
   - Spin up to process batches of data
   - Learn patterns: data quality issues, transformation optimizations, anomaly detection
   - Model improves over time → faster, smarter processing
   - All instances contribute to the shared "Data Processor" model

2. **Test Execution eMADs**
   - Spin up to run test suites
   - Learn: which tests catch which bugs, optimal test ordering, flaky test patterns
   - Model gets better at predicting failures, prioritizing tests
   - Shared "Test Runner" model improves with every execution

3. **Code Analysis eMADs**
   - Spin up for code reviews/analysis
   - Learn: code smell patterns, architecture anti-patterns, team coding styles
   - Model improves at identifying issues specific to the codebase
   - Shared "Code Analyzer" model benefits from all analysis

4. **Security Scanning eMADs**
   - Spin up for security audits
   - Learn: vulnerability patterns, false positive signatures, attack vectors
   - Collective security intelligence across all scans
   - Shared "Security Scanner" model improves detection

5. **Document Processing eMADs**
   - Spin up to extract/transform documents
   - Learn: document structure patterns, extraction rules, edge cases
   - Model improves accuracy over time
   - Shared "Doc Processor" model benefits all processing

### The Key Differentiator

| Traditional Workers | eMADs |
|---------------------|-------|
| Stateless | Models persist |
| No learning | Continuous learning |
| Each execution independent | Each execution trains the model |
| No improvement over time | Constant improvement |
| Instance-specific experience | Collective role-based intelligence |

### Architectural Requirements (Initial Thoughts)

- **Model Storage**: Role-based model repository (e.g., `/models/senior_dev/`, `/models/test_runner/`)
- **Versioning**: Instances always get latest trained model
- **Training Pipeline**: Activities feed back to continuous model training
- **Concurrent Access**: Multiple instances can use same model simultaneously
- **Hot Updates**: Model updates without downtime

---

## To Be Developed

This concept needs to be formalized into a proper academic paper covering:

- Detailed architecture
- Implementation considerations
- Performance metrics
- Comparison with related work
- Future directions
- Empirical validation

**Target**: Q1 2026

---

*Concept captured: 2025-10-09*
*To be formalized later*
