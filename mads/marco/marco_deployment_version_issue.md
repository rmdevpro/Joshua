# Marco Deployment - Package Version Issue

## Context
Deploying Marco Internet Gateway (approved by triplet in previous session). Build failed due to package version mismatch.

## Issue
**Package:** `@playwright/mcp`
**Specified in REQUIREMENTS.md (line 236):** `1.43.0` (pinned)
**Reality:** Version `1.43.0` does not exist in npm registry

## Available Versions
**Latest stable:** `0.0.41`
**Latest alpha:** `0.0.41-alpha-2025-10-04`

**All available versions:**
```
npm view @playwright/mcp versions
```
Shows versions ranging from 0.0.1 to 0.0.41, plus various alpha builds. No 1.x versions exist.

## Current Implementation
**File:** `/mnt/projects/ICCM/marco/package.json`
```json
{
  "dependencies": {
    "@playwright/mcp": "1.43.0",
    "ws": "^8.17.0"
  }
}
```

**File:** `/mnt/projects/ICCM/marco/server.js` (line 99)
```javascript
playwrightProcess = spawn('npx', ['@playwright/mcp@1.43.0'], {
```

**Dockerfile:** Uses `mcr.microsoft.com/playwright:v1.43.0-jammy` as base image

## Question for Triplet
The requirements specified `@playwright/mcp@1.43.0` to match the Playwright Docker image version (v1.43.0-jammy), but the npm package doesn't use matching version numbers.

**Which version should we use?**

Option 1: Latest stable (`0.0.41`)
- Pros: Most stable, production-ready
- Cons: May not match Playwright 1.43.0 image capabilities

Option 2: Latest alpha (`0.0.41-alpha-2025-10-04`)
- Pros: Most recent features, current date
- Cons: Alpha release, potentially unstable

Option 3: Pin to latest stable with caret (`^0.0.41`)
- Pros: Allows patch updates, maintains stability
- Cons: Same as Option 1

Option 4: Different approach entirely
- Question: Should we reconsider the architecture?

## Files to Update
If approved:
1. `/mnt/projects/ICCM/marco/package.json` - Update dependency version
2. `/mnt/projects/ICCM/marco/server.js` (line 99) - Update spawn command
3. `/mnt/projects/ICCM/marco/REQUIREMENTS.md` (line 236) - Document correct version

## Request
Please review the @playwright/mcp version mismatch and recommend:
1. Which version to use (0.0.41, alpha, or other)
2. Whether version pinning strategy needs adjustment
3. Any architectural concerns with the version selection
