# MAD CP Interface Library Requirements

## Version: 1.0
## Status: Draft
## Created: 2025-10-09

---

## Overview

The MAD CP Interface Library provides the client library for MADs to connect to the Rogers conversation bus. This enables MADs to send/receive messages, join/leave conversations, and participate in the conversation-based architecture.

---

## Core Capabilities

### For MADs connecting to Rogers:
- Create conversations
- Join/leave conversations
- Send messages
- Receive messages (real-time)
- Query conversation history

### Integration:
- Works with Rogers V1 conversation bus
- Uses MAD CP Protocol Library for message parsing/formatting
- Accessible to all MADs via relay

---

## Library Retirement Plan

### Current Libraries Being Replaced:

**1. joshua_logger**
- **Current:** Sends logs to Godot asynchronously
- **Replacement:** Send messages to logging conversations with tags (#status, #error, #metric)
- **Why:** Logs ARE conversations in MAD architecture
- **Timeline:** Retire once Rogers + MAD CP operational

**2. joshua_network**
- **Current:** WebSocket JSON-RPC for MAD-to-MAD communication
- **Replacement:** Rogers conversation bus + MAD CP
- **Why:** MADs communicate via conversations, not direct RPC
- **Timeline:** Retire once all MADs converted to conversation-based communication

### Migration Strategy:
1. **Phase 1:** Keep both (backward compatibility)
2. **Phase 2:** Deprecate (warnings, migration guides)
3. **Phase 3:** Remove (all MADs converted)

---

## Open Questions

1. **API design** - REST? WebSocket? Both?
2. **State management** - Does library maintain connection state or delegate to Rogers?
3. **Error handling** - Retry logic? Reconnection?
4. **Real-time subscriptions** - How do MADs subscribe to conversation updates?

---

*Requirements v1.0 - Conversation bus client for MADs*
