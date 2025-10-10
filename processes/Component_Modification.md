# Component Modification Process

## Overview
This process ensures production systems are never broken when making changes. Use blue/green deployment to safely modify working components.

---

## Critical Principle

**NEVER BREAK WORKING SYSTEMS**

If it works, get user approval before changing it.

---

## Before Modification

### Step 1: Read Documentation

**Required reading:**
- Component README.md
- Requirements/specifications
- Architecture documents
- Recent git history

**Verify understanding:**
- How does it currently work?
- What are the dependencies?
- What's the deployment model?

---

### Step 2: Verify Current System Works

**Test the existing system:**
```bash
# Run existing tests
# Check health endpoints
# Verify expected behavior
```

**Document current state:**
- What works?
- What's the baseline performance?
- What are known limitations?

---

### Step 3: Get User Approval

**Present proposed changes:**
- What will change?
- Why is it needed?
- What's the risk?
- What's the rollback plan?

**Wait for approval before proceeding.**

---

## During Modification

### Blue/Green Deployment Strategy

**Build changes in separate copy:**

```bash
# Example: Modifying fiedler-mcp

# Don't modify existing: fiedler-mcp (BLUE - production)
# Create new version: fiedler-mcp-green (GREEN - staging)

# Work on GREEN
docker-compose -f docker-compose.green.yml up -d

# Test GREEN thoroughly
# Keep BLUE running
```

**Advantages:**
- Zero downtime
- Easy rollback
- Safe testing
- Original intact

---

### Testing GREEN Version

**Comprehensive testing:**
1. Unit tests pass
2. Integration tests pass
3. Manual smoke tests
4. Performance comparable to BLUE
5. All features working

**Keep BLUE running until GREEN verified.**

---

### Cutover

**Only after GREEN fully verified:**

```bash
# Stop BLUE
docker stop fiedler-mcp

# Promote GREEN to production
docker rename fiedler-mcp-green fiedler-mcp

# Or update routing/config to point to GREEN
```

**Monitor closely after cutover.**

---

## After Modification

### Step 1: Update Documentation

**Update all relevant docs:**
- README.md (usage changes)
- Requirements (if specs changed)
- Architecture docs (if design changed)
- Configuration examples

**Verify docs match reality.**

---

### Step 2: Final System Test

**Verify production system:**
- All tests still pass
- Performance acceptable
- No regressions
- Users not impacted

---

### Step 3: Clean Up

**Only after success confirmed:**
```bash
# Archive old BLUE version
# Remove temporary GREEN artifacts
# Update deployment scripts
```

---

## Rollback Plan

**If GREEN fails:**

```bash
# GREEN is broken, BLUE still running
# Just delete GREEN
docker stop fiedler-mcp-green
docker rm fiedler-mcp-green

# BLUE never stopped, no user impact
```

**If GREEN promoted but issues found:**

```bash
# BLUE was archived, not deleted
# Restore BLUE
docker stop fiedler-mcp
docker rename fiedler-mcp-blue fiedler-mcp
docker start fiedler-mcp
```

---

## Working System Examples

**These are working systems - require approval to modify:**
- MCP Relay
- Production containers (dewey-mcp, fiedler-mcp, etc.)
- Core libraries (joshua_network, joshua_logger)
- Any deployed service

**Modification checklist:**
- [ ] Read documentation
- [ ] Verify current system works
- [ ] Get user approval
- [ ] Use blue/green deployment
- [ ] Test GREEN thoroughly
- [ ] Keep BLUE running until verified
- [ ] Update documentation
- [ ] Final system test
- [ ] Have rollback plan

---

## Common Mistakes

**DON'T:**
- ❌ Modify production directly
- ❌ Skip testing
- ❌ Delete old version immediately
- ❌ Assume it works without testing
- ❌ Change without approval

**DO:**
- ✅ Build in parallel (blue/green)
- ✅ Test exhaustively
- ✅ Keep rollback option
- ✅ Update docs
- ✅ Get approval first

---

## Quick Reference

| Phase | Action | Result |
|-------|--------|--------|
| Before | Read docs, verify works, get approval | Understanding + permission |
| During | Build GREEN, test, keep BLUE running | Safe staging |
| Cutover | Promote GREEN only after verification | Zero downtime |
| After | Update docs, test, clean up | Production ready |
| If failed | Rollback to BLUE | No user impact |

---

## See Also

- `/mnt/projects/Joshua/knowledge-base/TROUBLESHOOTING_WORKING_SYSTEMS.md` - Diagnosis without changes
- `/mnt/projects/Joshua/processes/Deployment_Flow_v1.0.md` - Deployment process

---

*Last Updated: 2025-10-10*
