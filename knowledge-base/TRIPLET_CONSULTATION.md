# Triplet Consultation Process

**Last Updated:** 2025-10-03
**Purpose:** Standard process for consulting Fiedler's default LLM triplet on complex bugs and architecture decisions

---

## When to Consult the Triplet

Use triplet consultation when:
- Root cause of a bug is unclear after initial investigation
- Multiple solution approaches exist and you need expert comparison
- Architecture decision has significant long-term impact
- User explicitly requests triplet consultation
- You've exhausted obvious solutions and need fresh perspective

**Do NOT consult for:**
- Simple bugs with obvious solutions
- Routine implementation decisions
- Questions answered by existing documentation

---

## Consultation Package Format

### Required Structure

```markdown
# [Title - Brief Problem Statement]

## Executive Summary
[2-3 sentences describing the problem and why you're consulting]

## Problem Statement
[Detailed description of the issue, what's broken, what's expected]

## System Architecture & Context

### Architecture Overview
[Reference to architecture PNG and brief explanation]

**Key Documents for Context:**
Please read these documents to understand the environment:

1. **Architecture Diagram:** /mnt/projects/ICCM/architecture/General Architecture.PNG
   - Visual overview of entire system
   - Component relationships and data flows

2. **Current Architecture Overview:** /mnt/projects/ICCM/architecture/CURRENT_ARCHITECTURE_OVERVIEW.md
   - Immutable architecture principles
   - Current protocol implementation
   - Component details and connection flows

3. **Current Status:** /mnt/projects/ICCM/CURRENT_STATUS.md
   - What we're working on right now
   - Recent changes and current state
   - Next steps and test plans

4. **GitHub Issues:** https://github.com/rmdevpro/ICCM/issues (`gh issue list`)
   - Active bugs and investigations
   - What has been tried before
   - Root cause analysis findings

### Component Details
[Specific details about components involved in the issue]

## Investigation History

### What Has Been Tried
[List all attempts with:
- Configuration/approach used
- Expected result
- Actual result
- Why it failed
]

### Evidence Gathered
[Logs, test results, diagnostic output]

### What Works / What Doesn't
**What Works:**
- ✅ [Item 1]
- ✅ [Item 2]

**What Doesn't Work:**
- ❌ [Item 1]
- ❌ [Item 2]

## Configuration Files
[Include relevant config files with explanations]

## Critical Questions

1. [Specific question about root cause]
2. [Question about recommended approach]
3. [Question about implementation details]
4. [Question about potential risks/side effects]

## Constraints

- [Architecture constraints that must be respected]
- [Technology/infrastructure constraints]
- [Time/resource constraints]

## Expected Output

Please provide:
1. Root cause analysis
2. Recommended solution approach
3. Specific implementation steps or configuration changes
4. Potential risks and how to mitigate them
5. Any alternative approaches to consider
```

---

## Step-by-Step Process

### Step 1: Gather Information

Before creating the consultation package:

1. **Read the 4 key documents:**
   - `/mnt/projects/ICCM/architecture/General Architecture.PNG`
   - `/mnt/projects/ICCM/architecture/CURRENT_ARCHITECTURE_OVERVIEW.md`
   - `/mnt/projects/ICCM/CURRENT_STATUS.md`
   - GitHub Issues (`gh issue list`)

2. **Collect evidence:**
   - Relevant logs
   - Configuration files
   - Test results
   - Diagnostic output

3. **Document investigation:**
   - What has been tried
   - What worked/didn't work
   - Current hypotheses

### Step 2: Create Consultation Package

1. **Create package file:**
   ```bash
   # Use descriptive filename with date
   /tmp/triplet_consultation_[topic]_$(date +%Y%m%d).md
   ```

2. **Follow the standard format above**

3. **Include the 4 key documents inline or by reference:**
   - Embed critical sections directly in package
   - Reference full documents by path for complete context

4. **Be specific with questions:**
   - Ask actionable questions
   - Provide enough context for complete answers
   - Number questions for clear tracking

### Step 3: Send to Triplet

**Method 1: Via Fiedler MCP Tools (Preferred)**

If Fiedler MCP tools are available:

```bash
# Use mcp__fiedler__fiedler_send tool
# Omit models parameter to use Fiedler's default triplet
```

**Method 2: Via Docker Workaround (Fallback)**

If Fiedler MCP tools are NOT available, use the workaround:

See: `/mnt/projects/ICCM/architecture/FIEDLER_DOCKER_WORKAROUND.md`

```bash
# 1. Create consultation package
cat > /tmp/consultation.md << 'EOF'
[Your consultation package here]
EOF

# 2. Send via docker exec
docker exec -i fiedler-mcp python3 << 'PYTHON_EOF'
import sys
import json
sys.path.insert(0, '/app')

from fiedler.tools.send import fiedler_send

with open('/tmp/consultation.md', 'r') as f:
    consultation = f.read()

print("Sending to triplet...", file=sys.stderr)

result = fiedler_send(
    prompt=consultation
    # Omit models parameter to use Fiedler's default triplet
    # (configured in /app/fiedler/config/models.yaml)
)

print(json.dumps(result, indent=2))
PYTHON_EOF

# 3. Read responses from output directory
```

### Step 4: Save Responses

1. **Create response directory:**
   ```bash
   mkdir -p /tmp/triplet_[topic]_responses
   ```

2. **Save each response:**
   ```bash
   # Save responses with model names from Fiedler output
   /tmp/triplet_[topic]_responses/[model1]_Response.md
   /tmp/triplet_[topic]_responses/[model2]_Response.md
   /tmp/triplet_[topic]_responses/[model3]_Response.md
   ```

3. **Create summary:**
   ```bash
   /tmp/triplet_[topic]_responses/SUMMARY.md
   ```

### Step 5: Analyze Responses

1. **Read all three responses**

2. **Identify consensus:**
   - What do all 3 LLMs agree on?
   - Where do they disagree?
   - Which recommendations appear most frequently?

3. **Document findings:**
   - Create/update GitHub Issue with triplet consensus
   - Update CURRENT_STATUS.md with recommended next steps
   - Note any dissenting opinions and why

### Step 6: Update Documentation

1. **GitHub Issue:**
   - Add comment: "Triplet Consultation [Date]"
   - Record consensus diagnosis
   - List top recommendations
   - Note response times and success rate

2. **CURRENT_STATUS.md:**
   - Update next steps based on triplet recommendations
   - Adjust current work plan if needed
   - Add critical reminders from triplet insights

3. **Archive consultation:**
   - Move consultation package to archive if valuable for future reference
   - Keep responses accessible for implementation phase

---

## The Triplet - Default Models

**Always use Fiedler's default triplet** for consultations by omitting the `models` parameter in `fiedler_send()`. This ensures consistency across all consultations.

**Default configuration location:** `/app/fiedler/config/models.yaml` in the Fiedler container

**To check current triplet:**
```bash
docker exec fiedler-mcp grep "defaults:" -A 2 /app/fiedler/config/models.yaml
```

**Why use defaults:**
- Ensures consistency across all consultations
- Triplet is curated for complementary strengths
- Easy to update all consultations by changing one config file
- Different training data and perspectives provide comprehensive analysis

---

## Success Criteria

A successful consultation provides:

1. ✅ **Clear root cause** - All 3 LLMs agree on what's broken
2. ✅ **Actionable steps** - Specific configuration or code changes
3. ✅ **Risk assessment** - Potential issues and mitigations
4. ✅ **Architecture alignment** - Solutions respect existing architecture
5. ✅ **Implementable** - Can be executed immediately

---

## Common Pitfalls to Avoid

1. **Insufficient context** - Always include the 4 key documents
2. **Vague questions** - Be specific and actionable
3. **Missing investigation history** - Show what you've already tried
4. **No constraints** - State what must be preserved (architecture, etc.)
5. **Ignoring dissent** - Pay attention when LLMs disagree
6. **Not updating docs** - Consultation is wasted if findings aren't documented

---

## Example: Real Consultation (2025-10-03)

**Problem:** Fiedler MCP tools not loading after 8 configuration attempts

**Package Created:** `/tmp/triplet_mcp_diagnosis/consultation_package.md`

**Included:**
- 4 key documents (inline excerpts + full path references)
- 8 configuration attempts with results
- Network diagnostics (wscat, port checks)
- Configuration files (both mcp.json files)
- 7 specific questions

**Results:**
- All 3 default LLMs responded successfully (76 seconds total)
- Unanimous diagnosis: Silent MCP initialization failure
- Top recommendation: Enable debug logging, check for stale state
- Led to process tree analysis discovering ZERO MCP child processes

**Outcome:**
- Root cause identified (MCP subsystem not starting)
- Next steps clear (restart Claude, check for initialization)
- Documented in GitHub Issue for future reference

---

## Templates Location

**Consultation Package Template:** This document (copy structure above)

**Response Summary Template:**
```markdown
# Triplet Consultation Summary - [Topic] - [Date]

## Consultation Details
- **Date:** [YYYY-MM-DD]
- **Models:** [Fiedler's default triplet - check config for current models]
- **Duration:** [Total time in seconds]
- **Success Rate:** [X/3 models responded]

## Consensus Diagnosis
[What all 3 LLMs agree on]

## Top Recommendations
1. [Recommendation 1 - mentioned by X/3 LLMs]
2. [Recommendation 2 - mentioned by X/3 LLMs]
3. [Recommendation 3 - mentioned by X/3 LLMs]

## Dissenting Opinions
[Where LLMs disagreed and why it matters]

## Next Steps
Based on triplet analysis:
1. [Action 1]
2. [Action 2]
3. [Action 3]

## Response Files
- [Model 1]: [path]
- [Model 2]: [path]
- [Model 3]: [path]
```

---

## Related Documentation

- `/mnt/projects/ICCM/architecture/FIEDLER_DOCKER_WORKAROUND.md` - Docker exec method when MCP unavailable
- `/mnt/projects/ICCM/fiedler/README.md` - Fiedler MCP server documentation
- GitHub Issues (https://github.com/rmdevpro/ICCM/issues) - Bug investigation and tracking
- `/mnt/projects/ICCM/CURRENT_STATUS.md` - Current work and status

---

## Maintenance Notes

**Last Updated:** 2025-10-03
**Process Owner:** ICCM Development Team
**Review Frequency:** After each major consultation to refine process

**Update History:**
- 2025-10-03: Initial documentation based on successful MCP consultation
