# Hopper V1 Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-09

---

## Overview

Hopper is The Software Engineer - an autonomous development MAD that coordinates software projects through a team of eMADs. V1 implements the PM-led development workflow.

**Named after:** Grace Hopper, computer science pioneer.

---

## How Hopper V1 Works

### 1. User Engages Hopper's Imperator
```
User: "Hey Hopper, I want to build a new MAD"
User: "Hopper, I need to update the authentication system"

Hopper Imperator: "Sure thing! Tell me a bit about it..."
[Gathers requirements from user]

Hopper Imperator: "OK, let me get your Project Manager"
```

### 2. Imperator Spins Up PM eMAD
- Asks Fiedler for PM LLM recommendation
- Instantiates PM eMAD with ProjectManagerClient
- PM joins the conversation

### 3. PM Coordinates Project
The PM eMAD handles:
- **Git project setup:** Creates project items, issues
- **Planning:** Guides user through requirements, planning
- **Documentation:** Creates design docs (spins up consulting teams as needed)
- **Development coordination:** Manages dev team (spins up Senior/Junior Dev eMADs)
- **Deployment:** Leads team through deployment process
- **Testing:** Coordinates testing activities
- **Git management:** Posts files, updates Git, creates commits/PRs
- **Performance tracking:** Rates team performance

**IMPORTANT:** PM does NOT generate code - PM coordinates others who do.

### 4. PM Spins Up Development Team
When ready to code:
```
PM → Fiedler: "Who should I use for Senior Dev? For Junior Devs?"
Fiedler: "Recommends Claude Sonnet 4.5 for Senior, GPT-4o for Juniors"

PM: [Spins up eMADs]
- Senior Dev eMAD (with SeniorDevClient)
- Junior Dev eMAD 1 (with JuniorDevClient)
- Junior Dev eMAD 2 (with JuniorDevClient)

All join conversation on Rogers bus
```

### 5. PM Controls Development Process
**PM acts like orchestrator** (similar to how Claude Code manages tasks):
- Assigns tasks to team members
- Reviews code produced by devs
- Coordinates between team members
- Manages workflow through development/deployment cycles
- Makes decisions about next steps
- Escalates to Hopper Imperator or user when needed

**Development team produces code, PM manages them.**

---

## Example Workflow

### Building a New MAD
```
User → Hopper: "I need to build Sentinel, the security MAD"

Hopper Imperator: "Tell me about Sentinel's responsibilities"
User: [Explains security monitoring role]

Hopper: "Got it. Let me get your PM"
[Spins up PM eMAD]

PM → User: "I'll help you build Sentinel. First, let's create some Git issues for tracking."
PM: [Creates issues: Design, Implementation, Testing]

PM → User: "Now let's create the design doc. I'll spin up a consulting team."
PM → Fiedler: "Need design doc specialists"
PM: [Spins up consulting LLMs, coordinates design doc creation]

PM: "Design approved. Ready to code. Spinning up dev team..."
PM: [Spins up Senior Dev, 2 Junior Devs]

PM → Senior Dev: "Here's the design. Create the base MAD structure."
Senior Dev: [Creates code]
PM: [Reviews, coordinates]

PM → Junior Devs: "Implement the monitoring tools based on Senior's structure"
Junior Devs: [Implement features]
PM: [Reviews, coordinates iterations]

PM: "Code complete. Running tests..."
PM: [Coordinates testing, deployment]

PM: "Sentinel deployed. Creating PR with documentation."
PM: [Updates Git, creates PR, documents performance]

PM → User: "Sentinel is complete and deployed. Performance rating: 8/10"
```

---

## What V1 Includes

### Hopper Imperator
- Initial engagement with user
- High-level coordination
- PM eMAD spawning

### PM eMAD Capabilities
- Project management (Git issues, planning)
- Documentation coordination (spin up consulting teams)
- Development team management (spin up dev eMADs)
- Process orchestration (development/deployment cycles)
- Git operations (commits, PRs, documentation)
- Performance tracking

### Development eMADs
- Senior Dev eMAD (with SeniorDevClient - code execution, reflection)
- Junior Dev eMAD (with JuniorDevClient)
- All communicate via Rogers conversation bus

### Integration Requirements
- Fiedler (for LLM recommendations)
- Rogers (for conversation bus)
- Git integration
- Development/Deployment cycle processes

---

## What V1 Does NOT Include

- Advanced planning AI (PM uses structured process)
- Autonomous architecture decisions (escalates to user)
- Multi-project coordination
- Advanced testing strategies (basic testing only)

---

## Success Criteria

- ✅ User can request new MAD development
- ✅ Hopper spins up PM eMAD
- ✅ PM creates Git issues and project structure
- ✅ PM coordinates documentation creation
- ✅ PM spins up dev team and coordinates coding
- ✅ PM manages deployment and testing
- ✅ PM updates Git with results
- ✅ Complete project delivered without user writing code

---

## Dependencies

### Critical Dependencies:
1. **Rogers** - Conversation bus for team communication
2. **Fiedler** - LLM recommendations for eMAD roles
3. **LLM Client Library** - ProjectManagerClient, SeniorDevClient, JuniorDevClient
4. **eMAD framework** - Ephemeral MAD lifecycle management
5. **Development/Deployment cycle processes** - Documented workflows

---

*Requirements v1.0 - Hopper as autonomous PM-led development team*

---

## Conversation History

### PM-Led Development Workflow Discussion

**User:** yes, so the way it would work is you would engage the imperator and say, hey I want to build something or hey I want to update XYZ. He's goign to say something sure think tell me a bit about it -- ok so let me get your Project Manager - PM does things like creating the Git project items, adding git issues. You could say to the PM, hey lets clean up some Git ISsues or I need to build a New MAD. The PM would guide you through planning, creating docs etc. When creating docs he'd spin up a consutling team with the appropriate members. And control their process the way I have been doing with you, but also what you have been doing for the Trio. Once you got to deployment and testing he'd lead them trought that. He'd post the files, update GIT, rate teh performance, but generate none of the product.

**Assistant:** **Key insights captured:**
- User engages Hopper Imperator with request
- Imperator spins up PM eMAD
- PM handles Git project setup (issues, project items)
- PM guides planning and documentation
- **PM spins up consulting teams** when creating docs
- **PM controls process** (like orchestrator manages workers)
- PM leads through deployment/testing
- **PM generates NONE of the product** - only coordinates
- PM posts files, updates Git, rates performance

**Example workflow shown:**
```
User → Hopper: "I need to build Sentinel"
Hopper: "Tell me about it..." [gathers requirements]
Hopper: "Let me get your PM"
[PM eMAD spawned]

PM → User: "Let's create Git issues..."
PM: [Creates design, implementation, testing issues]

PM: "Now let's create design doc..."
PM → Fiedler: "Need design doc specialists"
PM: [Spins up consulting team, coordinates design]

PM: "Design approved. Spinning up dev team..."
PM: [Spins up Senior Dev + Junior Devs]

PM → Senior Dev: "Create base structure"
PM → Junior Devs: "Implement features"
PM: [Reviews, coordinates, iterates]

PM: "Code complete. Running tests, creating PR..."
PM → User: "Sentinel complete. Performance: 8/10"
```

**Solomon & Wright Retirement Context:**

**User:** Most of the testing I think happens with hopper, but I was thinking perhaps that there was a larger testing sitution that Solomon was needed for, but now with the concept of emads, I dont think its needed. You could for example have hopper spint up a load testing or security testing team that persists after the desing and implementation team have been turned off.

**Assistant:** Excellent point! With eMADs, Solomon becomes unnecessary - testing is just another eMAD role.

**User:** same thing with Wright, I think you just do that in hopper with a differnt kind of team

**Assistant:** Wright retired too! Architecture/design is consulting eMAD role.

*Conversation captured: 2025-10-09*
