# MAD Architecture & Scaffolding Requirements

## Version: 1.0
## Status: Draft - Open Questions for Expert Guidance
## Created: 2025-10-09

---

## Overview

This document addresses the fundamental code architecture and scaffolding for MADs and eMADs, including inheritance, composition, and shared base classes.

---

## What We Know

### MAD Structure
```
MAD
├── Thought Engine
│   ├── LLM Client Library (common to all)
│   ├── Sequential Thinking access (common to all)
│   └── [MAD-specific components]
│       ├── Fiedler: Recommendation system
│       ├── Rogers: Routing logic (future)
│       └── Hopper: Workflow orchestration (future)
│
└── Action Engine
    ├── MAD CP Library (common to all)
    ├── Base MCP Server (common to all)
    ├── Error handling (common to all)
    └── [MAD-specific components]
        ├── Fiedler: LLM API orchestration
        ├── Rogers: Conversation storage
        └── Horace: File system operations
```

### eMAD Characteristics
- Ephemeral (temporary instances)
- Role-based (PM, Senior Dev, Junior Dev, etc.)
- Persistent learning (shared role-based models)
- Spawned on-demand, destroyed when done

---

## Open Questions for Expert Guidance

### Question 1: Inheritance vs. Composition?

**Option A: Inheritance**
```python
class MADBase:
    # Common components
    pass

class FiedlerMAD(MADBase):
    # Fiedler-specific additions
    pass
```

**Option B: Composition**
```python
class MAD:
    def __init__(self, thought_engine, action_engine):
        self.thought = thought_engine
        self.action = action_engine

fiedler = MAD(
    thought=FiedlerThoughtEngine(),
    action=FiedlerActionEngine()
)
```

**Need guidance on:** Which approach for MAD customization?

---

### Question 2: eMAD Relationship to MAD?

**Option A: eMAD inherits from MAD**
```python
class eMAD(MAD):
    # Adds lifecycle wrapper (spawn, destroy)
    # Adds shared model persistence
    pass
```

**Option B: eMAD is separate with shared components**
```python
class eMAD:
    # Reuses components but different base
    pass
```

**Option C: eMAD IS a MAD, just instantiated differently**
```python
# Same class, different lifecycle management
emad = MAD(ephemeral=True, role="SeniorDev")
```

**Need guidance on:** How should eMADs relate to MADs in code?

---

### Question 3: What Goes in Base Classes?

**Thought Engine Base:**
- LLM Client Library? (yes, common to all)
- Sequential Thinking access? (yes, common to all)
- Conversation interface? (probably yes)
- What else?

**Action Engine Base:**
- MAD CP Library? (yes, common to all)
- Base MCP Server framework? (yes, common to all)
- Error handling patterns? (probably yes)
- What else?

**Need guidance on:** Where to draw the line between base and customizable?

---

### Question 4: How Do Customizations Plug In?

**For MAD-specific components:**
- Override methods in subclass?
- Register plugins/modules?
- Dependency injection?

**Example:**
- Fiedler needs recommendation system in Thought Engine
- How does that get added to base Thought Engine?

**Need guidance on:** Extension mechanism for customizations?

---

## Related Dependencies

These questions affect:
- Fiedler V1 implementation
- Rogers V1 implementation
- LLM Client Library design
- Future Hopper implementation
- All eMAD implementations

**Need answers before starting implementation.**

---

## Success Criteria

Once answered, we should have:
- ✅ Clear MAD base class structure
- ✅ Clear eMAD relationship to MAD
- ✅ Clear extension points for customization
- ✅ Consistent architecture across all MADs

---

*Architecture questions v1.0 - Awaiting expert guidance on scaffolding approach*
