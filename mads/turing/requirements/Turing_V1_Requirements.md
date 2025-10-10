# Turing V1 Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-09

---

## Overview

Turing is The Secrets Manager - handles all cryptographic secrets, API keys, certificates, and credential lifecycle management for the MAD ecosystem.

**Named after:** Alan Turing, cryptography pioneer.

---

## What V1 Includes

### 1. Imperator
- LLM brain for Turing
- Conversational secrets management
- Uses LLM Client Library (ImperatorClient)

### 2. Conversation Capability
- New MCP tool: `turing_converse`
- Secret storage/retrieval requests
- Key rotation guidance
- Certificate management

### 3. Secrets Management
- **API key storage** - Encrypted storage (like current keyring)
- **Secrets retrieval** - Secure access for MADs
- **Key rotation** - Manage key lifecycle
- **Certificate management** - SSL/TLS certificates
- **Encryption/decryption** - Cryptographic operations

### 4. Example Usage
```
User: "Turing, store the OpenAI API key"
Turing: [Encrypts and stores securely]

Fiedler → Turing: "I need the OpenAI API key"
Turing: [Validates Fiedler's authorization, provides key]

User: "Turing, rotate all API keys older than 90 days"
Turing: [Identifies old keys, coordinates rotation, notifies affected MADs]

User: "Turing, what secrets do we have stored?"
Turing: [Lists secrets with metadata, NOT values]
```

---

## Success Criteria

- ✅ Securely stores API keys and secrets
- ✅ MADs can retrieve secrets they're authorized for
- ✅ Can rotate keys on schedule or request
- ✅ Conversational interface for secrets management
- ✅ Never exposes secrets in conversation logs

---

## Security Considerations

- **Conversation logging** - Secret values NEVER logged to Rogers
- **Authorization** - Only authorized MADs can access specific secrets
- **Encryption at rest** - All secrets encrypted in storage
- **Audit trail** - Who accessed what secrets, when (logged to McNamara)

---

*Requirements v1.0 - Turing as secrets management specialist*

---

## Conversation History

### Secrets Manager Discussion

(See McNamara conversation history for context on security vs. secrets separation)

**User:** That leaves the question of secrets I think, which really is separate from security i think. That can be Turing

**Assistant:** Perfect separation!
- **McNamara** - Security (pen testing, monitoring, threat analysis, audits)
- **Turing** - Secrets (API keys, encryption, certificates, credential lifecycle)

Named after Alan Turing, cryptography pioneer.

*Conversation captured: 2025-10-09*
