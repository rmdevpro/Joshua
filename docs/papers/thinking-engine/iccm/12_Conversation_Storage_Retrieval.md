# Conversation Storage and Retrieval Infrastructure for Progressive CET Training

## Abstract

We present a comprehensive conversation storage and retrieval system designed specifically for the four-phase progressive training of Context Engineering Transformers. Built on Irina's 60TB+ tiered storage infrastructure, our system handles Phase 1 subject expertise conversations, Phase 2 context transformation pairs, Phase 3 interactive feedback loops, and Phase 4 production conversation histories. The architecture combines PostgreSQL with vector extensions for semantic search, implements intelligent data lifecycle management across fast and slow storage tiers, and provides specialized retrieval patterns optimized for each training phase. Our design handles an estimated 20TB of active training data plus 40TB+ of archived conversations while maintaining sub-100ms query latency for critical operations.

## 1. Introduction

The ICCM four-phase training methodology generates massive amounts of conversational data. Each phase produces distinct data types with different access patterns, retention requirements, and retrieval needs. An effective storage and retrieval system is essential for:

- **Phase 1**: Storing and indexing subject-specific conversations for Phase 2 transformation
- **Phase 2**: Maintaining context transformation pairs with quality gradients
- **Phase 3**: Recording interactive feedback loops with multi-LLM responses
- **Phase 4**: Providing fast access to conversation history for production inference

## 2. Infrastructure Foundation

### 2.1 Irina Storage Architecture

```yaml
irina_storage_platform:
  cpu: Intel Core i7-7700 @ 3.60GHz (4 cores, 8 threads)
  ram: 62GB + 8GB swap
  storage:
    fast_tier:
      config: 4x16TB RAID 5 (direct to board)
      throughput: 300+ MB/s
      latency: ~5ms
      use: Active training data, hot queries

    slow_tier:
      config: 4x16TB RAID 5 (PCIe Gen 3 1x card)
      throughput: 30 MB/s (bottlenecked)
      latency: ~20ms
      use: Archived conversations, long-term storage

    total_capacity: 60TB+ (usable ~48TB RAID 5)
```

### 2.2 Design Principles

1. **Phase-Specific Optimization**: Different storage and indexing for each phase
2. **Tiered Access**: Hot data on fast tier, archives on slow tier
3. **Semantic Retrieval**: Vector embeddings for similarity search
4. **Lifecycle Management**: Automatic archival based on age and access patterns
5. **Scalability**: Design for 100K+ conversations per phase

## 3. Design Decision: PostgreSQL + pgvector vs. Dedicated Vector Databases

### 3.1 Why PostgreSQL with Vector Extensions?

We chose PostgreSQL with the pgvector extension over dedicated vector databases (Pinecone, Weaviate, Milvus) for several critical reasons specific to ICCM's requirements:

#### 3.1.1 Hybrid Data Model Requirements

ICCM's conversation data is fundamentally **relational with vector components**, not purely vector-based:

```python
# Our actual data structure:
conversation_structure = {
    'relational_core': {
        'conversations': 'Phase metadata, timestamps, quality scores',
        'messages': 'Turn-by-turn dialogue with roles, models',
        'phase_specific_tables': 'Context pairs, feedback loops, production data',
        'complex_joins': '4-5 table joins are common'
    },
    'vector_component': {
        'embeddings': 'Single 1536-dim vector per message',
        'usage': 'Semantic similarity search within relational context'
    }
}
```

**Single Query in PostgreSQL:**
```sql
-- Combines relational filtering + vector search in one query
SELECT
    m.context_engineered,
    f.quality_metrics,
    p1.subject_tags,
    m.embedding <=> %s as similarity
FROM messages m
JOIN phase_3_feedback f ON m.conversation_id = f.conversation_id
JOIN phase_1_conversations p1 ON f.conversation_id = p1.conversation_id
WHERE f.learning_signal > 0.5
  AND p1.expertise_domain = 'software_development'
  AND m.embedding <=> %s < 0.4
ORDER BY f.learning_signal DESC, similarity
```

**Same Query with Vector DB:**
```python
# Requires multiple round trips and application-layer joins:
# 1. Vector search (Pinecone)
vector_results = pinecone.query(query_vector, top_k=1000)
# 2. Fetch conversation metadata (PostgreSQL)
conversations = db.query("SELECT ... WHERE id IN (%s)", vector_results.ids)
# 3. Fetch feedback data (PostgreSQL)
feedback = db.query("SELECT ... WHERE conversation_id IN (%s)", vector_results.ids)
# 4. Join and filter in Python
# 5. Filter by learning_signal, domain, etc.
```

#### 3.1.2 Query Pattern Analysis

Our primary query patterns are NOT simple vector lookups:

| Query Type | Frequency | PostgreSQL | Vector DB |
|-----------|-----------|------------|-----------|
| Phase 1→2: Filter high-quality conversations by domain + tags | High | Single query with indices | Vector DB + metadata fetch |
| Phase 3: Similar contexts with feedback metrics + quality filters | Very High | Complex join with vector similarity | Multiple queries + app join |
| Phase 4: User history by time range + quality threshold | High | Time-series query with indices | Metadata-heavy, poor fit |
| Analytics: Aggregate quality metrics by phase/domain | Medium | Native SQL aggregations | Requires separate analytics DB |

**Key Insight:** 80% of our queries need relational filtering BEFORE or ALONGSIDE vector similarity. Vector DBs optimize for the inverse pattern.

#### 3.1.3 Operational Simplicity on Irina

**Infrastructure we already have:**
- PostgreSQL deployment expertise
- 62GB RAM for query caching and working memory
- Backup/restore procedures
- Monitoring with Prometheus/Grafana
- Query optimization experience

**Infrastructure we'd need for vector DB:**
- Pinecone: Cloud-only, not deployable on Irina (dealbreaker)
- Weaviate/Milvus: New service deployment, resource allocation, monitoring
- Data synchronization: Keep vector DB in sync with PostgreSQL source of truth
- Dual backup strategies: Vectors + metadata must stay consistent
- New query patterns and API learning curve

**Decision:** Minimize operational complexity by using existing PostgreSQL infrastructure.

#### 3.1.4 Performance Sufficient for Training Workloads

```python
our_requirements = {
    'scale': '~10M vectors (all phases)',
    'dimensions': 1536,
    'query_latency': '<100ms p99 (batch training, not real-time)',
    'queries_per_second': '10-50 during training',
    'primary_use': 'Training data retrieval, not production serving'
}

pgvector_performance = {
    'index_type': 'IVFFlat with 100 lists',
    'search_time': '20-50ms for k=10 on 10M vectors',
    'our_requirement': '<100ms',
    'verdict': '✅ Sufficient for training workloads'
}

dedicated_vector_db = {
    'search_time': '3-10ms (Pinecone, Weaviate)',
    'benefit': 'Faster, but unnecessary for batch training',
    'cost': '$70-200/month + operational overhead'
}
```

**Key Insight:** We're optimizing for training pipeline throughput, not production inference latency. pgvector's 20-50ms is perfectly adequate.

#### 3.1.5 Storage Tier Compatibility

Irina's tiered storage architecture favors PostgreSQL's access patterns:

```yaml
irina_storage_characteristics:
  fast_tier:
    throughput: 300+ MB/s sequential
    pattern: Direct-to-board RAID 5

  postgresql_benefits:
    - Sequential scans for bulk Phase 1→2 transformations
    - WAL (Write-Ahead Log) leverages sequential writes
    - VACUUM operations benefit from fast sequential I/O
    - Index files (B-tree, IVFFlat) perform well

  vector_db_patterns:
    - Often HNSW graphs requiring random I/O
    - Would work, but not optimized for our hardware
```

#### 3.1.6 Data Lifecycle Management

PostgreSQL simplifies our tiered archival strategy:

```sql
-- Simple tier movement while maintaining all relationships
UPDATE conversations
SET storage_tier = 'slow', archived_at = NOW()
WHERE created_at < NOW() - INTERVAL '30 days';

-- Physical data movement handled by storage layer
-- All foreign keys, indices, and relationships stay intact
```

With vector DB + PostgreSQL:
- Must archive vectors AND metadata in lockstep
- Complex consistency guarantees required
- Dual storage tier strategies (vectors in DB, metadata in Postgres)
- Potential desync issues during archival

#### 3.1.7 Cost Analysis

```python
cost_comparison = {
    'postgresql_pgvector': {
        'infrastructure': '$0 (runs on Irina we already own)',
        'operational': '$0 (existing admin)',
        'total_monthly': '$0'
    },

    'pinecone_managed': {
        'infrastructure': '$70-200/month (10M vectors)',
        'egress': '$20-50/month (training queries)',
        'total_monthly': '$90-250'
    },

    'weaviate_self_hosted': {
        'infrastructure': 'Need dedicated VM/container',
        'operational': 'New service to manage',
        'learning_curve': 'GraphQL API, new query patterns',
        'total_monthly': '$50-100 equivalent effort'
    }
}

# Annual savings: $1,080 - $3,000 with PostgreSQL
```

#### 3.1.8 When We Would Reconsider

We would switch to a dedicated vector database if:

1. **Phase 4 Production Scaling:**
   - Real-time personalization requires <10ms p99 vector search
   - Query volume exceeds 1,000 QPS
   - Vector search becomes the primary bottleneck

2. **Scale Beyond Current Estimates:**
   - Conversations exceed 50M (>500M vectors)
   - pgvector's IVFFlat performance degrades
   - Need advanced indexing (HNSW, product quantization)

3. **Cloud Migration:**
   - Moving off Irina to cloud infrastructure
   - Pinecone's managed service becomes attractive
   - Operational simplicity outweighs integration complexity

4. **Advanced Vector Features:**
   - Hybrid sparse-dense search
   - Multi-vector representations
   - Cross-modal similarity (code + documentation embeddings)

### 3.2 Implementation Strategy

Given our decision for PostgreSQL + pgvector:

```sql
-- Install pgvector extension
CREATE EXTENSION vector;

-- Optimize for our scale
ALTER SYSTEM SET shared_buffers = '16GB';  -- Leverage Irina's 62GB RAM
ALTER SYSTEM SET effective_cache_size = '48GB';
ALTER SYSTEM SET maintenance_work_mem = '2GB';

-- Vector-specific tuning
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
```

**Monitoring strategy:**
- Track vector search latency (target <100ms p99)
- Monitor index size growth (IVFFlat indices)
- Alert if search times exceed 200ms (degradation threshold)
- Plan migration to dedicated vector DB if persistent >500ms queries

## 4. Database Schema Design

### 4.1 Core Conversation Tables

```sql
-- Primary conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase VARCHAR(20) NOT NULL CHECK (phase IN ('phase_1', 'phase_2', 'phase_3', 'phase_4')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    conversation_type VARCHAR(20) CHECK (conversation_type IN ('training', 'validation', 'production')),
    subject_tags TEXT[],  -- e.g., ['python', 'api_design', 'async']
    metadata JSONB,  -- Flexible metadata per phase
    storage_tier VARCHAR(10) DEFAULT 'fast' CHECK (storage_tier IN ('fast', 'slow')),
    archived_at TIMESTAMPTZ
);

-- Create indices for common queries
CREATE INDEX idx_conversations_phase ON conversations(phase);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);
CREATE INDEX idx_conversations_tags ON conversations USING GIN(subject_tags);
CREATE INDEX idx_conversations_metadata ON conversations USING GIN(metadata);

-- Messages/turns within conversations
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model_used VARCHAR(100),  -- Which LLM generated this
    embedding vector(1536),  -- For semantic search (OpenAI ada-002 dimension)
    context_engineered TEXT,  -- CET output if applicable
    quality_score FLOAT CHECK (quality_score BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(conversation_id, turn_number)
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, turn_number);
CREATE INDEX idx_messages_quality ON messages(quality_score DESC) WHERE quality_score IS NOT NULL;
CREATE INDEX idx_messages_embedding ON messages USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);  -- Vector similarity index
```

### 3.2 Phase 1: Subject Expertise Data

```sql
-- Phase 1 specific metadata
CREATE TABLE phase_1_conversations (
    conversation_id UUID PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,
    rag_sources JSONB[],  -- Documents/chunks retrieved for grounding
    supervising_models TEXT[],  -- LLMs that validated quality
    expertise_domain VARCHAR(100) NOT NULL,  -- e.g., 'software_development'
    subject_subtopics TEXT[],  -- Specific areas covered
    quality_validated BOOLEAN DEFAULT FALSE,
    validation_timestamp TIMESTAMPTZ
);

CREATE INDEX idx_phase1_domain ON phase_1_conversations(expertise_domain);
CREATE INDEX idx_phase1_validated ON phase_1_conversations(quality_validated);
```

### 3.3 Phase 2: Context Transformation Pairs

```sql
-- Context transformation pairs derived from Phase 1
CREATE TABLE phase_2_context_pairs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_conversation_id UUID REFERENCES conversations(id),
    source_turn_number INTEGER,
    poor_context TEXT NOT NULL,
    excellent_context TEXT NOT NULL,
    transformation_type VARCHAR(50),  -- 'noise_reduction', 'structure_improvement', etc.
    quality_gradient FLOAT NOT NULL,  -- Improvement measure
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_phase2_source ON phase_2_context_pairs(source_conversation_id);
CREATE INDEX idx_phase2_gradient ON phase_2_context_pairs(quality_gradient DESC);
CREATE INDEX idx_phase2_type ON phase_2_context_pairs(transformation_type);
```

### 3.4 Phase 3: Interactive Feedback Data

```sql
-- Phase 3 interactive optimization feedback
CREATE TABLE phase_3_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    iteration_number INTEGER NOT NULL,
    cet_context TEXT NOT NULL,  -- Context generated by CET
    llm_responses JSONB[] NOT NULL,  -- Array of {model, response, quality} objects
    quality_metrics JSONB NOT NULL,  -- Detailed feedback signals
    learning_signal FLOAT NOT NULL,  -- Aggregate training signal
    feedback_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_phase3_conversation ON phase_3_feedback(conversation_id, iteration_number);
CREATE INDEX idx_phase3_signal ON phase_3_feedback(learning_signal DESC);
CREATE INDEX idx_phase3_timestamp ON phase_3_feedback(feedback_timestamp DESC);
```

### 3.5 Phase 4: Production Conversation History

```sql
-- Phase 4 production deployment conversations
CREATE TABLE phase_4_production (
    conversation_id UUID PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,
    user_id VARCHAR(100),
    cet_variant VARCHAR(10) CHECK (cet_variant IN ('CET-D', 'CET-P', 'CET-T')),
    deployment_context JSONB,  -- User preferences, settings, etc.
    self_critique_data JSONB,  -- CET's self-evaluation
    actual_outcome_quality FLOAT,  -- Measured response quality
    improvement_applied BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_phase4_user ON phase_4_production(user_id);
CREATE INDEX idx_phase4_variant ON phase_4_production(cet_variant);
CREATE INDEX idx_phase4_outcome ON phase_4_production(actual_outcome_quality DESC);
```

## 4. Retrieval Patterns

### 4.1 Phase 1 → Phase 2: Conversation Transformation

```python
class Phase1ToPhase2Retrieval:
    """Retrieve Phase 1 conversations for Phase 2 transformation"""

    def get_high_quality_conversations(self,
                                       domain='software_development',
                                       quality_threshold=0.7,
                                       limit=1000):
        """Fetch validated Phase 1 conversations for transformation"""
        return self.db.query("""
            SELECT
                c.id,
                c.subject_tags,
                array_agg(
                    json_build_object(
                        'turn', m.turn_number,
                        'role', m.role,
                        'content', m.content,
                        'quality', m.quality_score
                    ) ORDER BY m.turn_number
                ) as messages
            FROM conversations c
            JOIN messages m ON c.id = m.conversation_id
            JOIN phase_1_conversations p1 ON c.id = p1.conversation_id
            WHERE c.phase = 'phase_1'
            AND c.storage_tier = 'fast'
            AND p1.expertise_domain = %s
            AND p1.quality_validated = TRUE
            AND m.quality_score > %s
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT %s
        """, [domain, quality_threshold, limit])

    def get_conversations_by_topic(self, topic_tags):
        """Retrieve conversations covering specific topics"""
        return self.db.query("""
            SELECT c.*, array_agg(m.*) as messages
            FROM conversations c
            JOIN messages m ON c.id = m.conversation_id
            WHERE c.phase = 'phase_1'
            AND c.subject_tags && %s  -- Array overlap operator
            GROUP BY c.id
        """, [topic_tags])
```

### 4.2 Phase 3: Semantic Context Search

```python
class Phase3SemanticRetrieval:
    """Semantic search for similar successful contexts"""

    def find_similar_contexts(self, query_embedding, k=10):
        """Vector similarity search for context examples"""
        return self.db.query("""
            SELECT
                m.content,
                m.context_engineered,
                m.quality_score,
                m.embedding <=> %s::vector as distance,
                f.quality_metrics,
                f.learning_signal
            FROM messages m
            JOIN phase_3_feedback f ON m.conversation_id = f.conversation_id
            WHERE m.quality_score > 0.8
            AND m.context_engineered IS NOT NULL
            ORDER BY m.embedding <=> %s::vector
            LIMIT %s
        """, [query_embedding, query_embedding, k])

    def get_feedback_patterns(self, context_pattern):
        """Retrieve feedback for similar context patterns"""
        return self.db.query("""
            SELECT
                f.cet_context,
                f.llm_responses,
                f.quality_metrics,
                f.learning_signal
            FROM phase_3_feedback f
            WHERE f.cet_context ILIKE %s
            AND f.learning_signal > 0.5
            ORDER BY f.learning_signal DESC
            LIMIT 100
        """, [f"%{context_pattern}%"])
```

### 4.3 Phase 4: Production History Retrieval

```python
class Phase4ProductionRetrieval:
    """Fast retrieval for production conversation history"""

    def __init__(self):
        self.db = PostgresDB('/mnt/irina/fast/')
        self.cache = RedisCache()  # In-memory cache for hot queries

    def get_user_conversation_history(self,
                                      user_id,
                                      lookback_hours=24,
                                      max_turns=50):
        """Retrieve recent conversation history for CET-P personalization"""

        # Check cache first
        cache_key = f"history:{user_id}:{lookback_hours}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Query database
        history = self.db.query("""
            SELECT
                c.id,
                c.created_at,
                array_agg(
                    json_build_object(
                        'turn', m.turn_number,
                        'role', m.role,
                        'content', m.content
                    ) ORDER BY m.turn_number
                ) as messages
            FROM conversations c
            JOIN messages m ON c.id = m.conversation_id
            JOIN phase_4_production p4 ON c.id = p4.conversation_id
            WHERE p4.user_id = %s
            AND c.created_at > NOW() - INTERVAL '%s hours'
            AND c.storage_tier = 'fast'
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT %s
        """, [user_id, lookback_hours, max_turns])

        # Cache for 5 minutes
        self.cache.set(cache_key, history, ttl=300)
        return history
```

## 5. Storage Capacity Planning

### 5.1 Size Estimates

```python
storage_estimates = {
    'phase_1_conversations': {
        'target_count': 100_000,
        'avg_turns_per_conversation': 10,
        'avg_tokens_per_turn': 500,
        'bytes_per_token': 4,
        'embedding_overhead': 6144,  # 1536 dimensions * 4 bytes
        'metadata_jsonb': 1024,
        'total_per_conversation': '(10 * 500 * 4) + (10 * 6144) + 1024 = ~82KB',
        'total_phase_1': '100K * 82KB = 8.2TB'
    },

    'phase_2_context_pairs': {
        'pairs_per_conversation': 10,
        'total_pairs': '100K * 10 = 1M pairs',
        'avg_pair_size': 2048,  # poor + excellent context
        'total_phase_2': '1M * 2KB = 2TB'
    },

    'phase_3_feedback': {
        'training_iterations': 1_000_000,
        'llm_responses_per_iteration': 15,
        'avg_response_size': 1024,
        'quality_metrics_size': 512,
        'total_per_iteration': '(15 * 1KB) + 512B = ~16KB',
        'total_phase_3': '1M * 16KB = 16TB'
    },

    'phase_4_production': {
        'continuous_growth': 'Variable',
        'daily_conversations': 10_000,
        'avg_size': '50KB',
        'daily_growth': '10K * 50KB = 500MB/day',
        'monthly_growth': '15GB/month'
    },

    'total_active_storage': '8.2TB + 2TB + 16TB = 26.2TB',
    'fast_tier_allocation': '30TB (with buffer)',
    'archived_slow_tier': '18TB+ (older data)',
    'irina_capacity': '48TB usable (60TB RAID 5)',
    'headroom': '~40% free for growth'
}
```

### 5.2 Tier Distribution

```yaml
tier_allocation:
  fast_tier:  # 4x16TB RAID 5 direct (~26TB usable)
    - Active Phase 1 conversations (last 30 days): ~3TB
    - Active Phase 2 pairs (last 60 days): ~2TB
    - Active Phase 3 feedback (current training): ~16TB
    - Phase 4 recent history (last 7 days): ~3.5GB
    - Indices and overhead: ~2TB
    - Total: ~23TB

  slow_tier:  # 4x16TB RAID 5 bottlenecked (~22TB usable)
    - Archived Phase 1 (older than 30 days): ~5TB compressed
    - Archived Phase 2 (older than 60 days): ~1TB compressed
    - Archived Phase 3 (completed training runs): ~8TB compressed
    - Phase 4 long-term history: ~5TB
    - Total: ~19TB
```

## 6. Data Lifecycle Management

### 6.1 Automatic Archival Policy

```python
class DataLifecycleManager:
    """Manage data movement between fast and slow tiers"""

    def __init__(self):
        self.fast_tier = '/mnt/irina/fast/conversations/'
        self.slow_tier = '/mnt/irina/slow/conversations/'

    def archive_old_conversations(self):
        """Move aged conversations to slow tier"""

        # Phase 1: Archive after 30 days
        self.db.execute("""
            UPDATE conversations
            SET storage_tier = 'slow',
                archived_at = NOW()
            WHERE phase = 'phase_1'
            AND created_at < NOW() - INTERVAL '30 days'
            AND storage_tier = 'fast'
        """)

        # Phase 2: Archive after 60 days
        self.db.execute("""
            UPDATE conversations
            SET storage_tier = 'slow',
                archived_at = NOW()
            WHERE phase = 'phase_2'
            AND created_at < NOW() - INTERVAL '60 days'
            AND storage_tier = 'fast'
        """)

        # Phase 3: Archive completed training runs
        self.db.execute("""
            UPDATE conversations c
            SET storage_tier = 'slow',
                archived_at = NOW()
            FROM phase_3_feedback f
            WHERE c.id = f.conversation_id
            AND c.phase = 'phase_3'
            AND f.feedback_timestamp < NOW() - INTERVAL '90 days'
            AND c.storage_tier = 'fast'
        """)

        # Phase 4: Archive old production conversations
        self.db.execute("""
            UPDATE conversations
            SET storage_tier = 'slow',
                archived_at = NOW()
            WHERE phase = 'phase_4'
            AND created_at < NOW() - INTERVAL '7 days'
            AND storage_tier = 'fast'
        """)

    def compress_archived_data(self):
        """Compress old conversations for space savings"""
        # Compress message content for archived conversations
        # Use JSONB compression, embedding quantization
        pass
```

### 6.2 Retention Policies

```yaml
retention_policies:
  phase_1:
    fast_tier: 30 days
    slow_tier: 2 years
    after_2_years: Delete if not referenced by Phase 2

  phase_2:
    fast_tier: 60 days
    slow_tier: 1 year
    after_1_year: Keep top 10% by quality gradient

  phase_3:
    fast_tier: 90 days (active training)
    slow_tier: Indefinite (training history)
    compression: After 180 days

  phase_4:
    fast_tier: 7 days
    slow_tier: 90 days
    user_data_retention: Per privacy policy
    delete_on_request: Immediate compliance
```

## 7. Performance Optimization

### 7.1 Query Optimization

```sql
-- Materialized view for common Phase 1 queries
CREATE MATERIALIZED VIEW phase_1_quality_conversations AS
SELECT
    c.id,
    c.subject_tags,
    c.created_at,
    p1.expertise_domain,
    AVG(m.quality_score) as avg_quality,
    COUNT(m.id) as turn_count
FROM conversations c
JOIN messages m ON c.id = m.conversation_id
JOIN phase_1_conversations p1 ON c.id = p1.conversation_id
WHERE c.phase = 'phase_1'
AND p1.quality_validated = TRUE
GROUP BY c.id, p1.expertise_domain;

CREATE INDEX idx_p1_quality_domain ON phase_1_quality_conversations(expertise_domain, avg_quality DESC);

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY phase_1_quality_conversations;
```

### 7.2 Caching Strategy

```python
class ConversationCache:
    """Multi-tier caching for hot queries"""

    def __init__(self):
        self.l1_cache = {}  # In-process memory (62GB available on Irina)
        self.l2_cache = RedisCache()  # Redis for shared cache

    cache_policies = {
        'phase_1_conversations': {
            'ttl': 3600,  # 1 hour
            'size_limit': '10GB',
            'eviction': 'LRU'
        },
        'phase_3_embeddings': {
            'ttl': 7200,  # 2 hours
            'size_limit': '20GB',
            'eviction': 'LRU'
        },
        'phase_4_user_history': {
            'ttl': 300,  # 5 minutes
            'size_limit': '5GB',
            'eviction': 'LRU'
        }
    }
```

## 8. Integration with Training Pipeline

### 8.1 Phase 1: Conversation Generation

```python
def store_phase_1_conversation(conversation_data):
    """Store RAG-grounded subject expertise conversation"""

    # Insert conversation
    conv_id = db.insert("""
        INSERT INTO conversations (phase, conversation_type, subject_tags, metadata)
        VALUES ('phase_1', 'training', %s, %s)
        RETURNING id
    """, [conversation_data['tags'], conversation_data['metadata']])

    # Insert messages with embeddings
    for turn in conversation_data['turns']:
        embedding = generate_embedding(turn['content'])
        db.insert("""
            INSERT INTO messages
            (conversation_id, turn_number, role, content, model_used, embedding, quality_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, [conv_id, turn['number'], turn['role'], turn['content'],
              turn['model'], embedding, turn['quality']])

    # Store Phase 1 metadata
    db.insert("""
        INSERT INTO phase_1_conversations
        (conversation_id, rag_sources, supervising_models, expertise_domain)
        VALUES (%s, %s, %s, %s)
    """, [conv_id, conversation_data['rag_sources'],
          conversation_data['validators'], conversation_data['domain']])
```

### 8.2 Phase 3: Feedback Storage

```python
def store_phase_3_feedback(cet_context, llm_responses, quality_metrics):
    """Store interactive feedback loop data"""

    # Store CET-generated context and LLM responses
    feedback_id = db.insert("""
        INSERT INTO phase_3_feedback
        (conversation_id, iteration_number, cet_context, llm_responses,
         quality_metrics, learning_signal)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, [conv_id, iteration, cet_context, llm_responses,
          quality_metrics, calculate_learning_signal(quality_metrics)])

    return feedback_id
```

## 9. Monitoring and Observability

### 9.1 Storage Metrics

```yaml
monitoring_dashboards:
  storage_usage:
    - Fast tier usage percentage
    - Slow tier usage percentage
    - Daily growth rate
    - Archival queue depth

  query_performance:
    - Average query latency by phase
    - Cache hit rates
    - Slow query log
    - Vector search performance

  data_quality:
    - Phase 1 validation rate
    - Phase 2 quality gradient distribution
    - Phase 3 learning signal trends
    - Phase 4 outcome quality
```

## 10. Conclusion

Our conversation storage and retrieval system provides a robust foundation for ICCM's four-phase training methodology. By leveraging Irina's tiered storage architecture, implementing phase-specific data models, and optimizing for both semantic and temporal queries, we enable efficient training data management while maintaining sub-100ms latency for critical retrieval operations.

The system's design accommodates the estimated 26TB of active training data plus 18TB+ of archives within Irina's 48TB usable capacity, with 40% headroom for growth. Automatic lifecycle management ensures hot data remains on the fast tier while older conversations are compressed and archived to the slow tier.

## References

[To be added]
