# DER (Decision Engineering Recommender) - Corrected Understanding

## The Real Purpose of DER

The DER is about **internal decision learning**, not external instructions. It learns patterns and makes recommendations based on accumulated experience.

---

## Perfect Example: Fiedler with DER

### Conversation:
```
Hopper: "Hey Fiedler, I'm building a new MAD focused on Law
Practice. Can you recommend which LLM I should use as a
driver and which LLMs I should use as senior and junior
members of the consultation team?"

Fiedler: "Yes, the best LLM for legal matters is GPT-5, so
that should be your Senior member. It's a bit slow, but when
you are making legal decisions you want your best.

I'd recommend Grok and Gemini 2.5 Pro as your junior members.
They are very rational and have a good general understanding
of what is out there on the internet and therefore Law. Grok
is important because he's better with current events.

For a driver I would recommend Claude Sonnet. It's good with
organizational tasks and rational thinking, but not too
expensive."
```

### What's Happening Under the Hood:

**Fiedler's DER has LEARNED**:
- GPT-5 excels at legal accuracy (from observing legal task outcomes)
- Grok is best for current events (from tracking news-related queries)
- Gemini 2.5 Pro has broad knowledge (from general task performance)
- Claude Sonnet balances cost/performance for orchestration (from usage metrics)
- Legal work needs accuracy over speed (from outcome analysis)

**This wasn't programmed** - Fiedler's DER learned these patterns from experience!

---

## Rogers with DER - Corrected Examples

### Phase 1 (No DER - Rule-based):
```python
# Hard-coded rule in rogers.md or code
if session.age > 7 and session.access_count == 0:
    archive_session()
```

### Phase 2 (With DER - Learned patterns):
```python
# DER has learned from thousands of sessions
decision = der.evaluate({
    'session_age': 8_days,
    'last_access': 3_days_ago,
    'user_type': 'premium',
    'session_size': '2GB',
    'related_sessions': 3,
    'historical_pattern': 'sporadic'
})

# DER recommends: "keep_warm"
# Because it LEARNED that:
# - Premium users often return after 10-12 days
# - Sessions with related sessions get reactivated 73% of time
# - 2GB sessions are expensive to rehydrate
# - This pattern matches previous successful keep-warm decisions
```

**The key**: Rogers doesn't say "Dewey told me to keep it warm" - Rogers' DER **internally learned** that keeping it warm is optimal!

---

## What DER Actually Learns (Per MAD)

### Rogers' DER learns:
- Session reactivation patterns
- Optimal storage tier transitions
- Cache eviction strategies
- Resource allocation priorities

### Fiedler's DER learns:
- Which LLMs excel at specific tasks
- Cost/performance tradeoffs
- Team composition patterns
- Model compatibility insights

### Dewey's DER learns:
- Conversation retrieval patterns
- Indexing strategies
- Compression tradeoffs
- Query optimization approaches

### Horace's DER learns:
- File access patterns
- Storage distribution strategies
- Backup priorities
- Cleanup timing

---

## The Learning Process

1. **Observation**: MAD performs actions, observes outcomes
2. **Pattern Recognition**: DER identifies successful patterns
3. **Model Training**: Updates its recommendation model
4. **Application**: Makes better decisions next time

Example for Fiedler:
```
Day 1: Uses GPT-4 for legal task → Okay result
Day 2: Uses GPT-5 for legal task → Excellent result
Day 3: Uses Claude for legal task → Poor result
...
Day 100: DER knows: Legal tasks → GPT-5 is optimal
```

---

## Key Distinction

### ❌ WRONG Understanding:
"DER helps MADs follow external instructions better"

### ✅ CORRECT Understanding:
"DER helps MADs make better internal decisions based on learned experience"

### The Difference:
- **External**: "Dewey says keep this warm" → Do it
- **Internal**: DER learned keeping similar sessions warm had 73% success rate → Recommend keeping warm

---

## Rogers Phase 2 with DER - Correct Example

### User Interaction:
```
Imperator: "Rogers, optimize our session storage"

Rogers: "I've analyzed our patterns over the past month.
I'm adjusting our storage strategy:

- Moving 15 sessions to cold storage (dormant >14 days,
  reactivation rate <5%)
- Keeping 8 sessions in warm tier despite age (belonging
  to power users with 82% monthly return rate)
- Pre-warming 3 sessions (detected weekly access pattern,
  next access predicted in 2 hours)

This should reduce costs by 30% while maintaining <100ms
retrieval for active patterns I've learned."
```

**Note**: These aren't rules Rogers was given - the DER LEARNED these patterns from experience!

---

## Summary

DER is about **autonomous learning** within each MAD:
- Learns from experience
- Makes intelligent recommendations
- Explains reasoning based on patterns
- Improves decision-making over time

It's not about following instructions better - it's about becoming genuinely smarter at its job through experience!