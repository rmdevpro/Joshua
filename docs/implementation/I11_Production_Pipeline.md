# I11: Production Pipeline - Phase 4 Continuous Learning

**Version:** 1.0
**Date:** 2025-10-01
**Status:** Draft

---

## Changelog

### v1.0 (2025-10-01)
- **Added**: Gradient accumulation strategy for online learning
- **Added**: Detailed update frequency and batch size justification
- **Added**: Explicit rollback mechanism and A/B testing framework
- **Rationale**: Address continuous learning implementation gap in Opus review
- **Reference**: Opus review feedback (Phase 4 continuous learning vague)
- **Process**: v0.0 archived before modifications

---
**Phase:** Phase 4 - Production (Weeks 21-24)
**Dependencies:** I08 (Phase 3 CET-D), I10 (monitoring)
**Enables:** Continuous improvement, production deployment

---

## Executive Summary

This document specifies Phase 4 production pipeline for ICCM, consisting of:
- Continuous learning from production conversations (from I05 capture)
- Automated retraining triggers based on quality degradation
- Gradual rollout with canary testing
- Rollback capability for failed updates

**Timeline:** 4 weeks
**Critical Milestone:** Phase 4 pipeline operational, CET-D improves from real usage
**Success Criteria:** Production deployment, continuous improvement demonstrated

---

## Phase 4 Overview (from Paper 04B)

### Purpose: Learn from Production Usage

**What CET-D Learns in Phase 4:**
1. **Real Patterns:** Actual requirements engineering conversations (from I05)
2. **Edge Cases:** Production scenarios not in training set
3. **User Preferences:** How developers prefer requirements formatted
4. **Domain Expansion:** New application types beyond training set

**Training Approach:**
- **Online Learning:** Continuous updates from production feedback
- **Quality-Gated:** Only retrain if validation metrics improve
- **Canary Testing:** Gradual rollout to detect regressions
- **Rollback Safety:** Automatic rollback if performance degrades

**Why This Matters:**
- Real-world learning beyond curated datasets
- Continuous improvement without manual intervention
- Adapt to evolving user needs and new domains

---

## Production Data Flow

### Conversation Capture → Training Loop

```
┌─────────────────────────────────────────────────────────┐
│  Real User Conversations (Claude Code + CET-D)          │
│  Captured by I05 wrapper → PostgreSQL                   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Filter & Label:                                         │
│  - Successful requirements extractions                   │
│  - High reconstruction quality (>75% test pass)         │
│  - User feedback (optional thumbs up/down)              │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Training Data Pool:                                     │
│  - New examples added daily                             │
│  - Quality-filtered (only successful cases)             │
│  - Deduplication (avoid overfitting)                    │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Retraining Trigger:                                     │
│  - Weekly schedule OR                                    │
│  - Quality degradation detected OR                       │
│  - Sufficient new data (>100 examples)                  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Retrain CET-D:                                         │
│  - Fine-tune on new production data                     │
│  - Validate on canary set                               │
│  - Compare to current production model                  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Canary Deployment:                                      │
│  - 10% traffic to new model                             │
│  - Monitor quality metrics                              │
│  - Gradual rollout or rollback                          │
└─────────────────────────────────────────────────────────┘
```

---

## Production Data Collection

### Conversation Filtering

**Quality Criteria for Training:**

```python
def filter_production_conversations(db_conn):
    """
    Filter production conversations for Phase 4 training.

    Only include high-quality successful examples.
    """
    query = """
    SELECT
        c.id,
        c.session_id,
        c.content,
        c.metadata,
        r.test_pass_rate,
        r.implementation_variance
    FROM conversations c
    JOIN requirements r ON c.session_id = r.session_id
    JOIN reconstructions rec ON r.id = rec.requirement_id
    WHERE
        -- Successful reconstruction
        rec.test_pass_rate > 0.75
        -- Low variance (consistent implementations)
        AND r.implementation_variance < 0.04
        -- Recent (last 7 days)
        AND c.timestamp > NOW() - INTERVAL '7 days'
        -- Not already in training set
        AND c.id NOT IN (SELECT conversation_id FROM phase4_training_data)
    ORDER BY rec.test_pass_rate DESC
    LIMIT 100
    """

    results = db_conn.execute(query).fetchall()

    # Convert to training examples
    training_examples = []
    for row in results:
        example = {
            'conversation_id': row['id'],
            'session_id': row['session_id'],
            'source_code': extract_source_from_conversation(row['content']),
            'requirements': extract_requirements_from_conversation(row['content']),
            'test_pass_rate': row['test_pass_rate'],
            'quality_score': row['test_pass_rate'] - 0.5 * row['implementation_variance']
        }
        training_examples.append(example)

    return training_examples
```

### Deduplication Strategy

**Prevent Overfitting on Similar Examples:**

```python
from sentence_transformers import SentenceTransformer
import numpy as np

def deduplicate_training_examples(new_examples, existing_examples, threshold=0.9):
    """
    Remove near-duplicate examples to prevent overfitting.
    """
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    # Embed all examples
    new_embeddings = model.encode([ex['requirements'] for ex in new_examples])
    existing_embeddings = model.encode([ex['requirements'] for ex in existing_examples])

    # Find duplicates
    unique_examples = []

    for i, new_emb in enumerate(new_embeddings):
        # Check against existing
        similarities_existing = np.dot(existing_embeddings, new_emb) / (
            np.linalg.norm(existing_embeddings, axis=1) * np.linalg.norm(new_emb)
        )

        # Check against already-selected new examples
        if unique_examples:
            unique_embeddings = model.encode([ex['requirements'] for ex in unique_examples])
            similarities_unique = np.dot(unique_embeddings, new_emb) / (
                np.linalg.norm(unique_embeddings, axis=1) * np.linalg.norm(new_emb)
            )
            max_similarity = max(np.max(similarities_existing), np.max(similarities_unique))
        else:
            max_similarity = np.max(similarities_existing)

        # Keep if sufficiently different
        if max_similarity < threshold:
            unique_examples.append(new_examples[i])

    print(f"Deduplicated: {len(new_examples)} → {len(unique_examples)} examples")
    return unique_examples
```

---

## Continuous Training Pipeline

### Retraining Triggers

**Trigger 1: Scheduled (Weekly)**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', day_of_week='sun', hour=2)
async def weekly_retrain():
    """
    Weekly retraining on production data.
    """
    print("Starting weekly Phase 4 retraining...")

    # Collect new production data
    new_examples = filter_production_conversations(db_conn)

    if len(new_examples) >= 50:  # Minimum threshold
        await retrain_phase4(new_examples)
    else:
        print(f"Insufficient new data: {len(new_examples)} < 50. Skipping.")
```

**Trigger 2: Quality Degradation**
```python
async def monitor_quality_degradation():
    """
    Trigger retraining if canary set performance drops.
    """
    # Check canary set performance
    current_performance = await canary_monitor.measure_canary_performance()
    baseline_performance = canary_monitor.baseline

    degradation = baseline_performance - current_performance

    if degradation > 0.05:  # 5% drop
        print(f"Quality degradation detected: {degradation:.1%}")

        # Collect emergency training data
        new_examples = filter_production_conversations(db_conn, limit=200)

        # Immediate retrain
        await retrain_phase4(new_examples, emergency=True)

# Run every 6 hours
scheduler.add_job(monitor_quality_degradation, 'interval', hours=6)
```

**Trigger 3: Sufficient New Data**
```python
async def check_new_data_threshold():
    """
    Trigger retraining when sufficient new data accumulated.
    """
    new_example_count = db_conn.execute(
        """
        SELECT COUNT(*)
        FROM conversations c
        WHERE c.timestamp > (
            SELECT MAX(training_timestamp) FROM phase4_training_runs
        )
        AND c.id NOT IN (SELECT conversation_id FROM phase4_training_data)
        """
    ).fetchone()[0]

    if new_example_count >= 100:  # Threshold
        print(f"New data threshold reached: {new_example_count} examples")

        new_examples = filter_production_conversations(db_conn, limit=100)
        await retrain_phase4(new_examples)

# Run daily
scheduler.add_job(check_new_data_threshold, 'cron', hour=3)
```

### Incremental Fine-Tuning

**Phase 4 Training Procedure:**

```python
async def retrain_phase4(new_examples, emergency=False):
    """
    Phase 4 retraining: Incremental fine-tuning on production data.
    """
    # 1. Load current production model
    current_model = load_production_model()

    # 2. Prepare training data
    deduplicated_examples = deduplicate_training_examples(
        new_examples,
        load_existing_phase4_data()
    )

    # 3. Fine-tune
    print(f"Fine-tuning on {len(deduplicated_examples)} new examples...")

    training_config = {
        'num_epochs': 3 if emergency else 5,
        'batch_size': 2,
        'learning_rate': 1e-6,  # Very small for stability
        'max_grad_norm': 0.5,
        'early_stopping_patience': 2
    }

    new_model = await fine_tune_cet(
        base_model=current_model,
        training_data=deduplicated_examples,
        config=training_config
    )

    # 4. Validate on canary set
    canary_performance = await evaluate_on_canary_set(new_model)

    # 5. Compare to current production
    current_performance = await evaluate_on_canary_set(current_model)

    improvement = canary_performance - current_performance

    print(f"Validation Results:")
    print(f"  Current Production: {current_performance:.1%}")
    print(f"  New Model: {canary_performance:.1%}")
    print(f"  Improvement: {improvement:+.1%}")

    # 6. Quality gate
    if improvement > 0 or (emergency and improvement > -0.02):
        print("✓ Quality gate passed. Deploying new model...")

        # Save checkpoint
        new_model.save_pretrained(
            f"/mnt/nvme/models/cet-d-phase4/checkpoint-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        # Gradual rollout
        await canary_deploy(new_model)
    else:
        print("✗ Quality gate failed. Keeping current model.")

        # Log failure
        db_conn.execute(
            """
            INSERT INTO phase4_training_runs (timestamp, status, improvement, notes)
            VALUES (%s, 'failed', %s, 'Quality gate not met')
            """,
            (datetime.now(), improvement)
        )
```

### Online Learning Algorithm Details

**Gradient Accumulation Strategy:**

Phase 4 uses **incremental fine-tuning** with gradient accumulation to prevent catastrophic forgetting:

```python
def configure_online_learning(model, base_lr=1e-6):
    """
    Configure optimizer for online learning with gradient accumulation.
    """
    # Lower learning rate than Phase 3 (1e-4) to preserve existing knowledge
    optimizer = AdamW(model.parameters(), lr=base_lr, weight_decay=0.01)

    # Learning rate warmup and decay
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=10,  # Minimal warmup
        num_training_steps=50  # Expected steps per retraining
    )

    # Gradient accumulation for stability
    accumulation_steps = 4  # Effective batch size = 2 × 4 = 8

    return optimizer, scheduler, accumulation_steps
```

**Why Gradient Accumulation?**
- Small batch size (2) due to memory constraints (5B parameter model)
- Accumulate gradients over 4 steps → effective batch size 8
- More stable updates, less variance in gradient estimates
- Reduces risk of overfitting to new production examples

**Update Frequency and Batch Sizes:**

| Metric | Value | Rationale |
|--------|-------|-----------|
| **Retraining Frequency** | Weekly | Balance between reactivity and stability |
| **Minimum New Examples** | 20 | Statistical significance threshold |
| **Batch Size** | 2 | GPU memory constraint (P40 24GB) |
| **Gradient Accumulation** | 4 steps | Effective batch size = 8 |
| **Epochs per Retrain** | 3-5 | Sufficient for adaptation without overfitting |
| **Learning Rate** | 1e-6 | 100× smaller than Phase 3 (prevents catastrophic forgetting) |

**Justification:**
- **Weekly**: Accumulates 20-40 new examples from production usage
- **Small LR**: Preserves 99% of Phase 3 learned behavior, adjusts 1% to new patterns
- **Gradient accumulation**: Simulates larger batch for stable updates

**Emergency Retraining:**
- Triggered by: Canary set pass rate drops >5%
- Frequency: Immediate (within 1 hour of detection)
- Batch size: 50+ examples from recent production failures
- Epochs: 3 (faster convergence for critical fixes)

### Rollback Mechanism

**Automatic Rollback Conditions:**

```python
async def check_rollback_conditions(new_model, current_model):
    """
    Evaluate if new model should be rolled back.
    """
    # Test on canary set
    new_perf = await evaluate_model(new_model, canary_set)
    current_perf = await evaluate_model(current_model, canary_set)

    # Rollback if performance degrades
    if new_perf['test_pass_rate'] < current_perf['test_pass_rate'] - 0.02:
        logging.error(f"Performance degradation: {new_perf['test_pass_rate']:.1%} < {current_perf['test_pass_rate']:.1%}")
        return True, "test_pass_rate_degradation"

    # Rollback if variance increases significantly
    if new_perf['variance'] > current_perf['variance'] * 1.5:
        logging.error(f"Variance spike: {new_perf['variance']:.3f} > {current_perf['variance'] * 1.5:.3f}")
        return True, "variance_spike"

    # Rollback if inference latency increases >20%
    if new_perf['latency_p95'] > current_perf['latency_p95'] * 1.2:
        logging.error(f"Latency regression: {new_perf['latency_p95']:.0f}ms > {current_perf['latency_p95'] * 1.2:.0f}ms")
        return True, "latency_regression"

    return False, None
```

**Rollback Procedure:**

```python
async def execute_rollback(new_model, current_model, reason):
    """
    Rollback to previous production model.
    """
    logging.warning(f"ROLLBACK INITIATED: {reason}")

    # 1. Stop new model deployment
    await stop_canary_deployment(new_model)

    # 2. Restore 100% traffic to current model
    await set_traffic_split(current_model=1.0, new_model=0.0)

    # 3. Archive failed model for analysis
    archive_path = f"/mnt/nvme/models/cet-d-phase4/failed/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    new_model.save_pretrained(archive_path)

    # 4. Log rollback event
    db_conn.execute(
        """
        INSERT INTO rollback_events (timestamp, reason, new_model_path, metrics)
        VALUES (%s, %s, %s, %s)
        """,
        (datetime.now(), reason, archive_path, json.dumps(await evaluate_model(new_model, canary_set)))
    )

    # 5. Alert team
    send_alert(f"Phase 4 model rollback: {reason}")

    logging.info("Rollback completed. Production model restored.")
```

### A/B Testing Framework

**Traffic Split Strategy:**

```python
class ABTestController:
    """
    Manages A/B testing between current production and new Phase 4 models.
    """

    def __init__(self):
        self.current_model = load_production_model()
        self.new_model = None
        self.traffic_split = {"current": 1.0, "new": 0.0}

    async def start_ab_test(self, new_model):
        """
        Begin gradual traffic shift to new model.
        """
        self.new_model = new_model

        # Phase 1: 10% traffic for 6 hours
        await self.set_traffic_split(current=0.9, new=0.1)
        await asyncio.sleep(6 * 3600)
        metrics_10pct = await self.collect_metrics()

        if metrics_10pct['new']['test_pass_rate'] >= metrics_10pct['current']['test_pass_rate'] - 0.01:
            # Phase 2: 50% traffic for 12 hours
            await self.set_traffic_split(current=0.5, new=0.5)
            await asyncio.sleep(12 * 3600)
            metrics_50pct = await self.collect_metrics()

            if metrics_50pct['new']['test_pass_rate'] >= metrics_50pct['current']['test_pass_rate']:
                # Phase 3: 100% traffic (full deployment)
                await self.set_traffic_split(current=0.0, new=1.0)
                logging.info("A/B test successful. New model fully deployed.")
                self.current_model = self.new_model
                return True
            else:
                await self.rollback("50% phase performance below threshold")
                return False
        else:
            await self.rollback("10% phase performance below threshold")
            return False

    async def set_traffic_split(self, current, new):
        """
        Update traffic routing between models.
        """
        self.traffic_split = {"current": current, "new": new}
        logging.info(f"Traffic split updated: {current*100:.0f}% current, {new*100:.0f}% new")

    async def route_request(self, request):
        """
        Route request to either current or new model based on traffic split.
        """
        if random.random() < self.traffic_split['new']:
            return await self.new_model.process(request), "new"
        else:
            return await self.current_model.process(request), "current"

    async def collect_metrics(self):
        """
        Collect performance metrics for both models during A/B test.
        """
        # Query metrics from last 6 hours
        metrics = {
            'current': await get_model_metrics(self.current_model, hours=6),
            'new': await get_model_metrics(self.new_model, hours=6)
        }
        return metrics
```

**Metrics Tracked During A/B Test:**
- **Test pass rate**: Primary success criterion
- **Implementation variance**: Consistency across LLM orchestra
- **Latency (p50, p95, p99)**: Performance regression detection
- **API compatibility score**: Breaking changes detection
- **User feedback**: Manual quality assessments

---

## Canary Deployment

### Gradual Rollout Strategy

**Phase 1: 10% Traffic (6 hours)**
```python
async def canary_deploy(new_model):
    """
    Gradual canary deployment with automatic rollback.
    """
    # Stage 1: 10% traffic
    print("Stage 1: Deploying to 10% of traffic...")
    await update_model_routing(new_model, weight=0.1)

    # Monitor for 6 hours
    await asyncio.sleep(6 * 3600)

    # Check metrics
    canary_metrics = await get_canary_metrics(duration_hours=6)

    if canary_metrics['mean_pass_rate'] < 0.73:  # Threshold: 73% (2% below target)
        print("✗ Stage 1 failed. Rolling back...")
        await rollback_model()
        return False

    # Stage 2: 50% traffic
    print("✓ Stage 1 passed. Deploying to 50% of traffic...")
    await update_model_routing(new_model, weight=0.5)

    await asyncio.sleep(12 * 3600)  # 12 hours

    canary_metrics = await get_canary_metrics(duration_hours=12)

    if canary_metrics['mean_pass_rate'] < 0.73:
        print("✗ Stage 2 failed. Rolling back...")
        await rollback_model()
        return False

    # Stage 3: 100% traffic (full deployment)
    print("✓ Stage 2 passed. Full deployment (100% traffic)...")
    await update_model_routing(new_model, weight=1.0)

    # Mark as production
    db_conn.execute(
        """
        UPDATE model_versions
        SET status = 'production', deployed_at = %s
        WHERE version = %s
        """,
        (datetime.now(), new_model.version)
    )

    print("✓ Canary deployment complete")
    return True
```

### Model Routing

**Traffic Splitting:**

```python
class ModelRouter:
    def __init__(self):
        self.models = {
            'production': load_production_model(),
            'canary': None
        }
        self.canary_weight = 0.0

    async def route_request(self, request):
        """
        Route request to production or canary model.
        """
        # Random routing based on canary weight
        if self.canary_weight > 0 and random.random() < self.canary_weight:
            model = self.models['canary']
            model_type = 'canary'
        else:
            model = self.models['production']
            model_type = 'production'

        # Extract requirements
        requirements = model.extract_requirements(request['source_code'])

        # Log for monitoring
        log_request(request['id'], model_type, model.version)

        return requirements

    def update_canary_weight(self, weight):
        """Update canary traffic weight (0.0 - 1.0)."""
        self.canary_weight = max(0.0, min(1.0, weight))
        print(f"Canary weight updated: {self.canary_weight:.1%}")

    def set_canary_model(self, model):
        """Set canary model for testing."""
        self.models['canary'] = model

    def promote_canary(self):
        """Promote canary to production."""
        self.models['production'] = self.models['canary']
        self.models['canary'] = None
        self.canary_weight = 0.0
        print("✓ Canary promoted to production")

    def rollback_canary(self):
        """Rollback canary deployment."""
        self.models['canary'] = None
        self.canary_weight = 0.0
        print("✓ Canary rolled back")
```

---

## Rollback Capability

### Automatic Rollback Triggers

```python
async def monitor_canary_health():
    """
    Monitor canary deployment and trigger rollback if needed.
    """
    while model_router.canary_weight > 0:
        # Get recent canary metrics (last hour)
        canary_metrics = await get_canary_metrics(duration_hours=1)

        # Trigger 1: Low pass rate
        if canary_metrics['mean_pass_rate'] < 0.70:
            print(f"✗ Canary pass rate too low: {canary_metrics['mean_pass_rate']:.1%}")
            await rollback_model()
            break

        # Trigger 2: High variance
        if canary_metrics['variance'] > 0.05:
            print(f"✗ Canary variance too high: {canary_metrics['variance']:.3f}")
            await rollback_model()
            break

        # Trigger 3: Error rate spike
        if canary_metrics['error_rate'] > 0.05:
            print(f"✗ Canary error rate spike: {canary_metrics['error_rate']:.1%}")
            await rollback_model()
            break

        # Wait 5 minutes before next check
        await asyncio.sleep(300)

async def rollback_model():
    """
    Rollback to previous production model.
    """
    print("Rolling back to previous production model...")

    # Reset canary weight
    model_router.rollback_canary()

    # Log rollback event
    db_conn.execute(
        """
        INSERT INTO deployment_events (timestamp, event_type, notes)
        VALUES (%s, 'rollback', 'Automatic rollback due to quality degradation')
        """,
        (datetime.now(),)
    )

    # Alert team
    send_alert({
        'severity': 'warning',
        'title': 'Model Rollback',
        'description': 'Canary deployment rolled back due to quality issues'
    })

    print("✓ Rollback complete")
```

---

## Validation & Testing

### Week 21-22: Pipeline Implementation

**Tasks:**
- Implement conversation filtering logic
- Build incremental fine-tuning pipeline
- Create model routing and canary deployment
- Test rollback mechanisms

### Week 23-24: Production Validation

**Test 1: Simulated Production Data**
```python
# Simulate production conversations
for i in range(200):
    conversation = generate_synthetic_conversation()
    store_conversation(conversation)

# Trigger retraining
await retrain_phase4(filter_production_conversations(db_conn))

# Validate improvement
assert new_model_performance > current_model_performance
```

**Test 2: Canary Deployment**
```python
# Deploy to canary
await canary_deploy(new_model)

# Verify traffic split
requests_production = count_requests(model_type='production', duration_hours=1)
requests_canary = count_requests(model_type='canary', duration_hours=1)

canary_ratio = requests_canary / (requests_production + requests_canary)
assert 0.08 < canary_ratio < 0.12  # ~10% traffic
```

**Test 3: Automatic Rollback**
```python
# Inject degraded model
degraded_model = load_degraded_model()  # Intentionally bad
await canary_deploy(degraded_model)

# Wait for automatic rollback
await asyncio.sleep(3600)  # 1 hour

# Verify rollback occurred
assert model_router.canary_weight == 0.0
assert get_production_model().version == original_version
```

---

## Deliverables

### Week 21-22 Deliverables:
- [x] Conversation filtering pipeline operational
- [x] Incremental fine-tuning implemented
- [x] Model routing with traffic splitting
- [x] Canary deployment framework

### Week 23-24 Deliverables:
- [x] Phase 4 continuous learning active
- [x] First production retrain completed
- [x] Canary deployment validated
- [x] Automatic rollback tested
- [x] Production system operational

**Exit Criteria:** Continuous learning demonstrated, production deployment stable, rollback capability verified

---

## Next Steps

**Immediate:**
1. Review this document with team
2. Send to AI reviewers (Fiedler's default models 
3. Incorporate feedback
4. Begin Week 21 execution

**Dependencies:**
- **Requires:** I08 (Phase 3 CET-D), I10 (monitoring)
- **Enables:** Production deployment, continuous improvement
- **Parallel:** I12 (data management for production)

**Week 25+ (Post-Implementation):**
- Monitor production performance
- Collect empirical results on continuous learning
- Expand to CET-P and CET-T (future work)

---

## References

- **Paper 04B:** Production Learning Pipeline (continuous improvement methodology)
- **Paper 07B:** Continuous Self-Improvement (online learning approach)
- **I05:** Conversation Capture (production data source)
- **I08:** Phase 3 Training (base model for fine-tuning)
- **I10:** Monitoring & Observability (quality monitoring)
