# McNamara V1 Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-09

---

## Overview

McNamara is The Security Specialist - coordinates security operations across the MAD ecosystem through security eMAD teams and basic monitoring.

**Named after:** Ed McNamara, famous police chief.

---

## What V1 Includes

### 1. Imperator
- LLM brain for McNamara
- Security conversations and guidance
- Uses LLM Client Library (ImperatorClient)

### 2. Conversation Capability
- New MCP tool: `mcnamara_converse`
- Security questions, threat discussions, policy guidance

### 3. Basic Security Monitoring
- Track who's accessing what across MADs
- Anomaly detection (unusual patterns)
- Security event logging (via conversation bus with #security tag)
- Alert generation

### 4. Security eMAD Team Coordination
Can spin up specialized security teams:
- **Penetration Testing Team** - Find vulnerabilities
- **Code Security Audit Team** - Review code for security issues
- **Threat Analysis Team** - Analyze potential threats
- **Compliance Checking Team** - Verify regulatory compliance

### 5. Example Usage
```
User: "McNamara, are there any security anomalies today?"
User: "McNamara, I need a pen test on the new authentication system"
McNamara: [Spins up pen testing eMAD team, coordinates test, reports results]

User: "McNamara, audit the file access patterns"
McNamara: [Reviews logs, identifies unusual access, reports findings]
```

---

## What V1 Does NOT Include (Deferred to V2+)

- Advanced automated scanning across all MADs
- Complex policy enforcement automation
- Deep integration hooks in all MADs
- Automated threat response/remediation
- Security policy generation
- Intrusion prevention systems

---

## Success Criteria

- ✅ Can answer security questions conversationally
- ✅ Monitors basic access patterns and detects anomalies
- ✅ Can spin up security eMAD teams
- ✅ Coordinates security audits and pen tests
- ✅ Generates security alerts via conversation bus

---

## Dependencies

- **Rogers** - Conversation bus for security event logging
- **Fiedler** - LLM recommendations for security eMAD roles
- **LLM Client Library** - Security-specialized clients for eMADs
- **eMAD framework** - Ephemeral security team lifecycle

---

*Requirements v1.0 - McNamara as security coordinator*

---

## Conversation History

### Security MAD Discussion

**User:** I think Sentinel (needs better name) is a one stop shop for all things security that can spin up a variety of eMAD teams and may have persisent functions within it

**Assistant:** Ah! Sentinel is a real persistent MAD! [Showed capabilities: pen testing, threat analysis, monitoring, etc.]

Name suggestions: Turing, Diffie, Rivest, Schneier

**User:** Ill figure out the name, we just need to figure out what he does. I think you are right about that. That leaves the question of secrets I think, which really is separate from security i think. That can be Turing

**Assistant:** Perfect separation!
- Sentinel for security (pen testing, monitoring, audits)
- Turing for secrets (API keys, encryption, certificates)

**User:** McNamara

**Assistant:** McNamara - perfect! (Robert McNamara, Secretary of Defense)

**User:** nope Ed McNamara famous police chief

**Assistant:** Even better! Ed McNamara, famous police chief - perfect for security.

**User:** It think it would have those things eventually, the question is how much to put in v1.

**Assistant:** McNamara V1 - minimal but functional:
- Imperator for security conversations
- Basic security monitoring (access tracking, anomaly detection)
- Can spin up security eMAD teams
- Defer advanced scanning/automation to V2+

**User:** yeah I think so

*Conversation captured: 2025-10-09*
