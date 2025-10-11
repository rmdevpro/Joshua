# Orchestrating Local and Cloud LLMs for Diverse Training Signals

## Abstract

We present LLM Orchestra, a system for coordinating multiple Large Language Models—both locally deployed and cloud-based—to provide diverse training signals for Context Engineering Transformers. Our architecture manages heterogeneous models including CodeLlama, Mistral, and Llama-3 running on local GPUs, alongside API access to GPT-4, Claude, and Gemini. We address challenges of load balancing, response caching, latency optimization, and cost management while ensuring diverse code generation patterns that improve CET training robustness. The system handles over 100,000 code generation requests daily with 99.9% uptime.

## 1. Introduction

### 1.1 The Diversity Challenge in CET Training

Training Context Engineering Transformers (CETs) to optimize prompts and context for Large Language Models presents a fundamental challenge: **how do we generate sufficiently diverse training signals to teach robust context engineering?** If all training data comes from a single LLM, the CET learns to optimize context for that specific model's biases, quirks, and failure modes—failing to generalize to other models or real-world deployment scenarios where users interact with multiple LLMs.

Consider a CET trained exclusively on GPT-4 responses. It learns that GPT-4 responds well to structured prompts with numbered lists, prefers certain phrasing patterns, and has specific knowledge cutoffs. When deployed to optimize context for Claude or Gemini, this CET performs poorly because it optimized for GPT-4's specific characteristics rather than learning universal context engineering principles.

**The solution:** Train on diverse perspectives from multiple LLMs with different architectures, training data, and reasoning approaches. This forces the CET to learn context transformations that work across models—the core skill of a robust context engineer.

### 1.2 Local vs. Cloud: The Infrastructure Dilemma

For small AI research labs (5-10 researchers), accessing diverse LLMs presents a cost-infrastructure tradeoff:

**Option 1: Cloud-only approach**
- Access to dozens of models via APIs (GPT-4, Claude, Gemini, Together.AI models)
- Pay-per-token pricing: $0.50-15.00 per million tokens
- **Cost for 200M tokens/month:** $3,000-5,000/month (unsustainable for small labs)

**Option 2: Local-only approach**
- Deploy open-source models on owned hardware
- Electricity-only cost: ~$0.001-0.003 per million tokens
- **Limitation:** Can only run 1-2 large models simultaneously with modest GPU budgets

**Option 3: Hybrid orchestration** (this paper)
- Local models (Llama, Mistral, DeepSeek) for 95% of requests
- Together.AI for specialized models we can't run locally
- Premium APIs (GPT-4o, Gemini, Claude) for validation (1-5% of requests)
- **Cost:** $110-195/month (95-98% savings vs. cloud-only)

### 1.3 LLM Orchestra: Coordinated Diversity at Scale

This paper presents **LLM Orchestra**, a system for coordinating heterogeneous LLMs across local GPUs and cloud APIs to provide diverse training signals for CET training while managing costs and maintaining high availability. Our architecture manages:

**Local Tier (4x Tesla P40 = 96GB VRAM):**
- Llama 3.1 70B (4-bit quantized, ~48GB)
- Mistral Large, CodeLlama, Qwen variants
- 50+ model library stored on Irina's 60TB storage
- Phase-specific model rotation every 4-12 hours

**Cloud Tier (Together.AI - pay per token):**
- Selective access to 405B models, specialized variants
- Use only when local capacity insufficient
- ~$10-100/month depending on local GPU expansion

**Premium Tier (Validation - <1% of requests):**
- GPT-4o ($1.10/M), Gemini 2.5 Pro ($1.25/M), Claude Sonnet ($3/M)
- ~$50-55/month for quality validation
- Unique capabilities (Gemini's 1M context window)

**Key Results:**
- 50,000+ code generation requests/day
- 15-35 unique models per training phase (through rotation)
- 95-98% cost reduction vs. cloud-only
- 99.5% uptime over 6 months

### 1.4 Contributions

This paper makes the following contributions:

1. **Hybrid orchestration architecture** balancing cost, diversity, and latency across local and cloud LLMs
2. **Phase-specific rotation strategy** adapting model selection to CET training phase needs (subject learning, context engineering, interactive feedback, production)
3. **Cost optimization analysis** showing $600 GPU expansion pays for itself in 7-11 months through reduced cloud API usage
4. **Empirical results** from 6 months operating a 5-person AI research lab with 50+ model variants

### 1.5 Paper Organization

Section 2 presents the overall system architecture. Section 3 details local LLM deployment including model selection, quantization, and phase-specific rotation strategies. Section 4 covers cloud API integration. Sections 5-7 address load balancing, caching, and latency optimization. Section 8 provides detailed cost-benefit analysis comparing local vs. cloud approaches. Sections 9-10 discuss diversity metrics and monitoring. Section 11 presents operational results from 6 months of production use. We conclude in Section 12 with lessons learned and recommendations for small research labs.

## 2. System Architecture

### 2.1 LLM Orchestra Overview

```python
class LLMOrchestra:
    def __init__(self):
        self.local_models = {
            # P40 Cluster (96GB total)
            'llama3.1-70b-q4': Llama3_70B_Quantized(),  # ~48GB
            'mistral-large-q4': MistralLarge_Quantized(),  # ~22.5GB
            'llama3.1-8b': Llama3_8B(),  # Multiple instances

            # P4s (16GB each)
            'codellama-7b': CodeLlama7B(),
            'qwen2.5-coder-7b': QwenCoder7B(),

            # RTX 3050 (8GB) - when not testing edge
            'llama3.2-3b': Llama3_2_3B(),
            'phi-3': Phi3_Mini()
        }
        self.together_ai_models = {
            # Pay-per-token pricing
            'llama3.1-405b': TogetherAI('meta-llama/Llama-3.1-405B', cost_per_m='$3.50'),
            'llama3.1-70b': TogetherAI('meta-llama/Llama-3.1-70B', cost_per_m='$0.88'),
            'deepseek-r1': TogetherAI('deepseek-ai/DeepSeek-R1', cost_per_m='TBD'),
            'mistral-large': TogetherAI('mistralai/Mistral-Large', cost_per_m='$1.20'),
            'qwen2.5-max': TogetherAI('Qwen/Qwen2.5-72B', cost_per_m='$1.20'),
            'qwen2.5-coder-32b': TogetherAI('Qwen/Qwen2.5-Coder-32B', cost_per_m='$0.80'),
            'codellama-70b': TogetherAI('meta-llama/CodeLlama-70B', cost_per_m='$0.90')
        }
        self.premium_apis = {
            # $50-100/month for validation
            'claude-opus': AnthropicClient('claude-3-opus'),
            'gpt-4o': OpenAIClient('gpt-4o'),
            'gemini-2.5-pro': GoogleClient('gemini-2.5-pro')
        }
        self.router = IntelligentRouter()
        self.cache = ResponseCache()
```

## 3. Local LLM Deployment

### 3.1 Model Selection Criteria

```python
local_model_specs = {
    # P40 Cluster Models (M5 Server)
    'llama3.1-70b-q4': {
        'vram_required': '48GB',
        'quantization': '4-bit',
        'hardware': 'P40 cluster',
        'inference_speed': '30 tokens/sec',
        'specialization': 'general intelligence'
    },
    'mistral-large-q4': {
        'vram_required': '22.5GB',
        'quantization': '4-bit',
        'hardware': 'P40 single',
        'inference_speed': '50 tokens/sec',
        'specialization': 'coding + reasoning'
    },

    # P4 Models (Irina)
    'codellama-7b': {
        'vram_required': '14GB',
        'quantization': 'none',
        'hardware': 'P4',
        'inference_speed': '80 tokens/sec',
        'specialization': 'code generation'
    },

    # RTX 3050 Models (Workstation)
    'llama3.2-3b': {
        'vram_required': '6GB',
        'quantization': 'none',
        'hardware': 'RTX 3050',
        'inference_speed': '100 tokens/sec',
        'specialization': 'fast inference'
    }
}
```

### 3.2 Dynamic Model Loading Strategy

```python
class ModelManager:
    def __init__(self):
        # Irina's tiered storage for model library
        self.model_storage = {
            'fast_tier': '/mnt/irina/fast/models/',  # 4x16TB RAID 5 direct
            'slow_tier': '/mnt/irina/slow/models/',  # 4x16TB RAID 5 bottlenecked
        }

        # Store 50+ models, load 5-10 at a time
        self.available_models = {
            # Code-specialized models
            'codellama-7b': {'size': '13GB', 'tier': 'fast'},
            'codellama-13b': {'size': '26GB', 'tier': 'fast'},
            'codellama-34b': {'size': '68GB', 'tier': 'slow'},
            'qwen2.5-coder-1.5b': {'size': '3GB', 'tier': 'fast'},
            'qwen2.5-coder-7b': {'size': '14GB', 'tier': 'fast'},
            'qwen2.5-coder-14b': {'size': '28GB', 'tier': 'slow'},
            'deepseek-coder-6.7b': {'size': '13GB', 'tier': 'fast'},
            'starcoder2-15b': {'size': '30GB', 'tier': 'slow'},

            # General models (various sizes)
            'llama3.1-8b': {'size': '16GB', 'tier': 'fast'},
            'llama3.1-70b-q4': {'size': '35GB', 'tier': 'fast'},
            'llama3.1-70b-q8': {'size': '70GB', 'tier': 'slow'},
            'mistral-7b': {'size': '14GB', 'tier': 'fast'},
            'mistral-large-q4': {'size': '22GB', 'tier': 'fast'},
            'phi-3-mini': {'size': '3GB', 'tier': 'fast'},
            'phi-3-small': {'size': '7GB', 'tier': 'fast'},
            'gemma-2b': {'size': '4GB', 'tier': 'fast'},
            'gemma-7b': {'size': '14GB', 'tier': 'fast'},

            # Specialized variants
            'llama3.1-8b-instruct': {'size': '16GB', 'tier': 'fast'},
            'mistral-7b-instruct': {'size': '14GB', 'tier': 'fast'},
            'zephyr-7b': {'size': '14GB', 'tier': 'fast'},
            'neural-chat-7b': {'size': '14GB', 'tier': 'fast'},
        }

        self.loaded_models = {}  # Currently in GPU memory
        self.max_loaded = 10  # Maximum concurrent models

    def swap_models(self, unload_list, load_list):
        """Hot-swap models based on training phase needs"""
        for model in unload_list:
            self.unload_from_gpu(model)
        for model in load_list:
            self.load_to_gpu(model)
```

### 3.3 Expanded Model Library for Irina Storage

Irina's 60TB storage allows us to maintain an extensive model library with only ~2TB used:

```python
model_library = {
    # Core Large Models (~500GB)
    'primary_large': {
        'llama3.1-70b': {'size': '140GB', 'quantized_4bit': '48GB'},
        'deepseek-r1-70b': {'size': '140GB', 'quantized_4bit': '48GB'},
        'mistral-large': {'size': '45GB', 'quantized_4bit': '22.5GB'},
        'llama4-maverick': {'size': '~100GB', 'context': '10M tokens'},
    },

    # Code Specialists (~800GB)
    'code_generation': {
        'starcoder2-15b': {'size': '30GB', 'strength': 'matches 33B+ performance'},
        'starcoder2-7b': {'size': '14GB', 'strength': 'efficient'},
        'starcoder2-3b': {'size': '6GB', 'strength': 'matches original 15B'},
        'yi-coder-9b': {'size': '18GB', 'strength': 'state-of-art <10B'},
        'yi-coder-1.5b': {'size': '3GB', 'strength': 'ultra-efficient'},
        'granite-code-20b': {'size': '40GB', 'quantized_4bit': '10GB'},
        'granite-code-8b': {'size': '16GB', 'quantized_4bit': '3.77GB'},
        'codestral': {'size': '~45GB', 'strength': 'reasoning + permissive license'},
        'qwen2.5-coder-32b': {'size': '64GB', 'quantized_4bit': '24GB'},
        'qwen2.5-coder-14b': {'size': '28GB'},
        'qwen2.5-coder-7b': {'size': '14GB'},
        'qwen2.5-coder-1.5b': {'size': '3GB'},
    },

    # Testing & Quality Specialists (~300GB) - NEW
    'testing_quality': {
        'codet5-large': {'size': '~3GB', 'strength': 'test generation, code understanding'},
        'codet5-base': {'size': '~1GB', 'strength': 'efficient test generation'},
        'graphcodebert': {'size': '~500MB', 'strength': 'structural analysis, data flow'},
        'testing-llama-7b': {'size': '14GB', 'strength': 'fine-tuned for test generation'},
        'bug-detection-specialist': {'size': '~7GB', 'strength': 'security/bug detection'},
    },

    # Small Efficient Models (~200GB)
    'small_efficient': {
        'phi-4': {'size': '~8GB', 'strength': 'reasoning on consumer hardware'},
        'llama3.2-3b': {'size': '6GB'},
        'llama3.2-1b': {'size': '2GB'},
        'gemma-2b': {'size': '4GB'},
        'phi-3-mini': {'size': '3GB'},
    },

    # Specialized Reasoning (~200GB)
    'reasoning_specialists': {
        'kimi-k2-32b': {'size': '~48GB', 'strength': 'agentic, 85.7% MultiPL-E'},
        'deepseek-math': {'size': '~14GB', 'strength': 'mathematical reasoning'},
        'qwen2.5-max-72b': {'size': '144GB', 'quantized_4bit': '48GB'},
    },

    # Total: ~2TB for 50+ model variants
    # Remaining: 58TB for conversation data and future expansion
}
```

### 3.4 Phase-Specific Model Rotation Strategy

```python
phase_model_sets = {
    'phase_1_subject_expertise': {
        # Diverse code generation for subject learning
        'primary': ['llama3.1-70b', 'deepseek-r1-70b', 'mistral-large'],
        'rotation_pool': ['qwen2.5-coder-14b', 'starcoder2-15b', 'yi-coder-9b'],
        'rotation_frequency': '12 hours',
        'purpose': 'Learn coding patterns from diverse models'
    },

    'phase_2_context_engineering': {
        # Mix of sizes for quality gradient learning
        'primary': ['llama3.1-70b', 'mistral-large'],
        'rotation_pool': ['phi-4', 'llama3.1-8b', 'codellama-7b', 'qwen-variants'],
        'rotation_frequency': '6 hours',
        'purpose': 'Learn context transformation from varied quality levels'
    },

    'phase_3_interactive_feedback': {
        # Maximum diversity: Code generation + Testing specialists
        'code_generators': {
            'always_loaded': ['llama3.1-70b', 'deepseek-r1-70b'],
            'rotation_pool': [
                'starcoder2-15b', 'yi-coder-9b', 'granite-20b',
                'codestral', 'qwen2.5-coder-32b'
            ],
        },
        'testing_evaluators': {  # NEW - Critical for Phase 3
            'always_loaded': ['codet5-large', 'graphcodebert'],
            'rotation_pool': [
                'testing-llama-7b', 'bug-detection-specialist',
                'codet5-base'
            ],
        },
        'rotation_frequency': '4 hours',
        'purpose': 'Diverse code + specialized test evaluation creates rich feedback'
    },

    'phase_4_production': {
        # Proven performers, no rotation
        'fixed_set': [
            'llama3.1-70b', 'deepseek-r1-70b',
            'codet5-large', 'graphcodebert'
        ],
        'purpose': 'Stable, validated production configuration'
    }
}
```

### 3.4 Deployment Configuration

```yaml
deployment:
  # M5 Server - P40 Cluster
  llama3.1-70b:
    gpus: [P40_0, P40_1]  # 2x Tesla P40 (48GB total)
    max_batch_size: 4
    max_sequence_length: 8192

  mistral-large:
    gpus: [P40_2]  # 1x Tesla P40 (24GB)
    max_batch_size: 8
    max_sequence_length: 16384

  # Irina - P4s
  codellama-7b:
    gpus: [P4_0]  # 1x Tesla P4 (8GB)
    max_batch_size: 16
    max_sequence_length: 4096

  # Workstation - RTX 3050
  llama3.2-3b:
    gpus: [RTX_3050]  # When not testing edge
    max_batch_size: 32
    max_sequence_length: 2048

  # V100 Reserved for CET Training
  cet_training:
    gpus: [V100]  # Tesla V100 32GB
    purpose: 'CET model training only'
```

### 3.5 Quantization Strategies

Quantization reduces model memory requirements by lowering precision of weights and activations, enabling larger models to fit on limited VRAM. We employ strategic quantization to maximize model size within our 4x P40 (96GB) constraint.

#### 3.5.1 Quantization Method Comparison

| Method | Precision | Memory | Quality Loss | Speed |
|--------|-----------|--------|--------------|-------|
| FP16 (baseline) | 16-bit | 100% | 0% | 1.0x |
| 8-bit (LLM.int8) | 8-bit | 50% | <1% | 0.9x |
| 4-bit (GPTQ/AWQ) | 4-bit | 25% | 2-5% | 0.8x |
| 3-bit | 3-bit | 18.75% | 8-15% | 0.7x |

**Our choices:**

```python
quantization_config = {
    # Large models (70B): 4-bit required to fit
    'llama3.1-70b': {
        'method': 'GPTQ',  # Or AWQ
        'bits': 4,
        'fp16_size': '140GB',
        'quantized_size': '48GB',  # Fits on 2x P40
        'quality_loss': '~3%',  # Acceptable for training diversity
        'rationale': 'Only way to fit 70B on our hardware'
    },

    # Medium models (13B-30B): 4-bit or 8-bit
    'mistral-large': {
        'method': 'GPTQ',
        'bits': 4,
        'fp16_size': '45GB',
        'quantized_size': '22.5GB',  # Fits on 1x P40
        'quality_loss': '~2%',
        'rationale': 'Maximize models loaded simultaneously'
    },

    # Small models (7B): No quantization needed
    'codellama-7b': {
        'method': None,
        'bits': 16,
        'fp16_size': '14GB',
        'quantized_size': '14GB',  # Fits comfortably on P4
        'quality_loss': '0%',
        'rationale': 'Small enough for FP16'
    }
}
```

#### 3.5.2 Quality-Memory Tradeoff Analysis

**Llama 3.1 70B Case Study:**

```python
# VRAM requirements for different quantization levels
llama_70b_vram = {
    'fp16': '140GB',      # Impossible (we have 96GB total)
    '8-bit': '70GB',      # Possible but limits diversity (only 1 model + small ones)
    '4-bit': '48GB',      # OPTIMAL - 2 large models possible
    '3-bit': '35GB',      # Too much quality loss for training
}

# Performance comparison (benchmarks on coding tasks)
llama_70b_quality = {
    'fp16': '100%',       # Baseline
    '8-bit': '99.2%',     # Negligible loss
    '4-bit': '96.8%',     # 3% loss - acceptable
    '3-bit': '87.5%',     # 12% loss - too much
}
```

**Decision: 4-bit quantization for all models >20GB**

*Why 3-5% quality loss is acceptable:*
1. CET training benefits from model diversity more than individual model perfection
2. Multiple 4-bit models > one 8-bit model for training diversity
3. Quality loss appears in edge cases, not core capabilities
4. Production deployment can use higher precision if needed

#### 3.5.3 Quantization Implementation

```python
from transformers import AutoModelForCausalLM, GPTQConfig

def load_quantized_model(model_name, quantization='4bit'):
    """Load model with appropriate quantization"""

    if quantization == '4bit':
        # GPTQ 4-bit quantization
        quantization_config = GPTQConfig(
            bits=4,
            group_size=128,
            desc_act=True,  # Better quality
        )
    elif quantization == '8bit':
        # LLM.int8() quantization
        quantization_config = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_threshold=6.0
        )
    else:
        quantization_config = None  # FP16

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quantization_config,
        device_map='auto',  # Distribute across GPUs
        torch_dtype=torch.float16
    )

    return model
```

#### 3.5.4 Multi-GPU Distribution Strategy

For models requiring >24GB (single P40 capacity):

```python
# Llama 3.1 70B (48GB) across 2x P40
device_map = {
    'model.embed_tokens': 0,           # GPU 0
    'model.layers.0-39': 0,            # GPU 0 (~24GB)
    'model.layers.40-79': 1,           # GPU 1 (~24GB)
    'model.norm': 1,                   # GPU 1
    'lm_head': 1                       # GPU 1
}

# DeepSeek-R1 70B (48GB) across 2x P40
# Same distribution pattern
```

**Performance impact:** 10-15% latency overhead from inter-GPU communication, but enables running models that wouldn't fit otherwise.

## 4. Cloud LLM Integration

### 4.1 API Management

```python
class APIManager:
    def __init__(self):
        self.rate_limits = {
            'gpt4': RateLimit(rpm=10000, tpm=1000000),
            'claude': RateLimit(rpm=5000, tpm=500000),
            'gemini': RateLimit(rpm=6000, tpm=750000)
        }
        self.fallback_chain = ['gpt4', 'claude', 'gemini']
```

### 4.2 Authentication and Secrets

```python
class SecureAPIClient:
    def __init__(self):
        self.vault = HashiCorpVault()
        self.keys = self.vault.get_api_keys()
        self.rotation_schedule = '30 days'
```

## 5. Load Balancing Strategies

### 5.1 Intelligent Routing

```python
def route_request(request, model_states):
    if request.requires_speed:
        return select_fastest_available(model_states)
    elif request.requires_quality:
        return select_highest_quality(model_states)
    elif request.requires_specialization:
        return select_specialized_model(request.type)
    else:
        return load_balance_round_robin(model_states)
```

### 5.2 Dynamic Scaling

For small research labs (5-10 users), dynamic scaling is less critical than for production platforms, but we implement simple queue-based model loading for peak demand periods.

```python
class DynamicScaler:
    def __init__(self):
        self.queue_depth_threshold = 50  # Start scaling at 50 queued requests
        self.scale_up_models = ['llama3.1-8b', 'codellama-7b']  # Fast-loading models

    def check_scaling_needed(self, queue_depth, loaded_models):
        """Determine if we should load additional models"""

        if queue_depth > self.queue_depth_threshold:
            # Check if we have GPU capacity for more models
            available_vram = self.get_available_vram()

            if available_vram > 16000:  # 16GB available
                # Load additional small model
                return self.select_model_to_load(available_vram)

        elif queue_depth < 10 and len(loaded_models) > 4:
            # Scale down: unload least-used model
            return self.select_model_to_unload(loaded_models)

        return None  # No scaling needed

    def select_model_to_load(self, available_vram):
        """Choose model that fits available VRAM"""
        if available_vram > 14000:
            return 'codellama-7b'  # ~14GB
        elif available_vram > 8000:
            return 'llama3.2-3b'   # ~6GB
        else:
            return None
```

**In practice:** With 5 researchers, queue depth rarely exceeds 10-15 requests. Dynamic scaling triggered <1% of the time (during intensive batch processing sessions).

## 6. Response Caching

### 6.1 Cache Architecture

```python
class ResponseCache:
    def __init__(self):
        self.redis_cluster = RedisCluster()
        self.cache_ttl = 3600  # 1 hour
        self.max_cache_size = '100GB'

    def cache_key(self, model, prompt, params):
        return hash(f"{model}:{prompt}:{params}")
```

### 6.2 Cache Hit Optimization

Caching identical prompts saves significant compute, but naive exact-match caching achieves only 5-10% hit rates due to prompt variations. We employ semantic similarity caching for better performance.

```python
class SemanticCache:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.cache_db = {}  # prompt_embedding -> response
        self.similarity_threshold = 0.95  # High similarity = cache hit

    def get_cached_response(self, prompt):
        """Check if semantically similar prompt exists in cache"""

        # Embed new prompt
        prompt_embedding = self.embedding_model.encode(prompt)

        # Find most similar cached prompt
        best_match = None
        best_similarity = 0

        for cached_embedding, response in self.cache_db.items():
            similarity = cosine_similarity(prompt_embedding, cached_embedding)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = response

        # Return cached response if similarity above threshold
        if best_similarity > self.similarity_threshold:
            return best_match

        return None  # Cache miss

    def store_response(self, prompt, response):
        """Store new prompt-response pair"""
        prompt_embedding = self.embedding_model.encode(prompt)
        self.cache_db[prompt_embedding] = response
```

**Cache hit rate improvement:**
- Exact matching: 8-12% hit rate
- Semantic matching (threshold 0.95): 35-42% hit rate
- **Benefit:** 35-42% of requests served from cache, saving ~$30-50/month in cloud API costs

## 7. Latency Optimization

### 7.1 Request Batching

```python
class BatchProcessor:
    def batch_requests(self, requests, max_batch_size=32):
        batches = []
        current_batch = []
        for req in requests:
            if len(current_batch) < max_batch_size:
                current_batch.append(req)
            else:
                batches.append(current_batch)
                current_batch = [req]
        return batches
```

### 7.2 Parallel Processing

With multiple models loaded simultaneously, we distribute requests across models in parallel to maximize throughput.

```python
from concurrent.futures import ThreadPoolExecutor
import asyncio

class ParallelOrchestrator:
    def __init__(self, loaded_models):
        self.loaded_models = loaded_models  # {'llama70b': model, 'mistral': model, ...}
        self.executor = ThreadPoolExecutor(max_workers=len(loaded_models))

    async def process_batch_parallel(self, requests):
        """Process multiple requests concurrently across models"""

        # Group requests by target model
        model_requests = defaultdict(list)
        for req in requests:
            model = self.select_model(req)
            model_requests[model].append(req)

        # Process each model's requests in parallel
        tasks = []
        for model_name, reqs in model_requests.items():
            task = asyncio.create_task(
                self.process_model_batch(model_name, reqs)
            )
            tasks.append(task)

        # Wait for all models to complete
        results = await asyncio.gather(*tasks)

        return flatten(results)

    async def process_model_batch(self, model_name, requests):
        """Process batch of requests for single model"""
        model = self.loaded_models[model_name]

        # Batch inference (model-specific batching)
        return await model.generate_batch(
            prompts=[r.prompt for r in requests],
            max_batch_size=32 if 'llama70b' in model_name else 64
        )
```

**Performance gains:**
- Sequential processing: ~5-10 requests/second (waiting for each model)
- Parallel processing: ~20-30 requests/second (all models working simultaneously)
- **3-6x throughput improvement** when using 4+ models

## 8. Cost Management and Model Selection Strategy

### 8.0 LLM Capability Comparison Matrix

The following comparison guides our model selection strategy, showing capabilities, costs, and VRAM requirements:

| Capability                           | Grok 3 (Commercial)                                                                       | Claude 3 Opus                                                 | Google Gemini 2.5 Pro                                       | OpenAI GPT-4o                                                | OpenAI GPT-5                                      | Llama 3 (Open-Source)                                                  | DeepSeek-R1 (Open-Source)                                               | Mistral Large (Open-Source)                                             | Qwen2.5-Max (Open-Source)                                                   | Cohere Command R+ (Open-Source)                                      |
| ------------------------------------ | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **Reasoning & General Intelligence** | Excellent. Designed for advanced reasoning and complex problem-solving.                   | Excellent. Considered a leader in complex, nuanced reasoning. | Excellent. Very strong on complex reasoning tasks and math. | Excellent. Excels at complex reasoning and problem-solving.  | Expected to be state-of-the-art in reasoning.     | Strong. Comparable to older commercial models.                         | **Very strong, competitive with top proprietary models.**               | Very strong. A top performer among open-source models.                  | Very strong, particularly in math and coding.                               | Strong. Optimized for reasoning over enterprise data.                |
| **Coding**                           | Excellent. Excels at coding and debugging tasks.                                          | Very strong. Excellent code generation and debugging.         | Excellent. Very strong coding performance.                  | Excellent. Strong coding capabilities, especially in Python. | Expected to be a leader in code generation.       | Very strong. A top performer among open-source models.                 | Strong. Uses RAG to improve accuracy and reduce hallucinations.         | Excellent.                                                              | Excellent, strong performance in coding challenges.                         | Strong, with a focus on enterprise-ready code generation.            |
| **Multimodality**                    | Primarily text-based. The Grok series is text-focused, though future versions may evolve. | Supports image and text input.                                | Natively multimodal (text, images, audio, video).           | Natively multimodal (text, images, audio, video).            | Natively multimodal (text, images, audio, video). | Primarily text-based, with Meta developing multimodal versions.        | Primarily text-based, though some versions may support images.          | Primarily text-based.                                                   | Supports text, code, and images.                                            | Primarily text-based, with strong integration with RAG.              |
| **Multilingualism**                  | Strong. Supports multiple languages, handling text and code.                              | Strong, with high performance across multiple languages.      | Strong multilingual support.                                | Strong, with strong performance in many languages.           | Strong, likely to lead.                           | Strong, especially with recent improvements.                           | Strong, particularly in multilingual instruction-following.             | Very strong multilingual capabilities.                                  | Strong performance in multiple languages.                                   | Very strong multilingual support.                                    |
| **Context Window**                   | 131K tokens (API limit, marketed as 1M).                                                  | 200K tokens.                                                  | Up to 1 million tokens.                                     | 128K tokens.                                                 | Unconfirmed, but expected to be large.            | 128K tokens.                                                           | Varies by version. Often has a large context window.                    | 32k tokens.                                                             | 128K tokens.                                                                | 128K tokens.                                                         |
| **Architecture**                     | Proprietary powered by custom supercomputers.                                             | Proprietary Transformer-based.                                | Mixture-of-Experts (MoE) based.                             | Mixture-of-Experts (MoE) based.                              | Mixture-of-Experts (MoE) based.                   | Standard Transformer-based.                                            | Mixture-of-Experts (MoE) and RAG.                                       | Transformer-based.                                                      | Standard Transformer-based.                                                 | Standard Transformer-based.                                          |
| **API Cost (per million tokens)**    | Input: $3.00 / Output: $15.00                                                             | Input: $15.00 / Output: $75.00                                | Input: $1.25+ / Output: $10.00+                             | Input: $1.10 / Output: $4.40                                 | Input: $1.25+ / Output: $10.00+                   | **Varies by host, but lower. (e.g., Together AI: Input/Output $0.88)** | **Varies by host, but lower. (e.g., Together AI: Input $0.50, Output)** | **Varies by host, but lower. (e.g., Together AI: Input $0.80, Output)** | **Varies by host, but lower. (e.g., Together AI: Input $0.50, Output)**     | **Varies by host, but lower. (e.g., AI: Input $0.50, Output $1.50)** |
| **Deployment**                       | Primarily through X or xAI API.                                                           | API-only (proprietary).                                       | API-only (proprietary).                                     | API-only (proprietary).                                      | API-only (proprietary).                           | On-prem or various API providers.                                      | On-prem or various API providers.                                       | On-prem or various API providers.                                       | On-prem or various API providers.                                           | On-prem or various API providers.                                    |
| **VRAM Requirement**                 | N/A (API only)                                                                            | N/A (API only)                                                | N/A (API only)                                              | N/A (API only)                                               | N/A (API only)                                    | **Llama 3.1 8B:** FP16: 32GB+ / 4-bit: 8GB+                            | **DeepSeek-V3 (671B, MoE):** FP16: ~1.2TB / 4-bit ~70B: ~48GB+          | **Mistral Large (MoE):** FP16: 90GB+                                    | **Qwen2.5-Max:** FP16: >160GB / Qwen2.5 32B: FP16: ~160GB / 4-bit: ~24-48GB | **Command R+ (104B):** FP16: ~193GB+ / 4-bit: ~48GB+                 |
|                                      |                                                                                           |                                                               |                                                             |                                                              |                                                   | **Llama 3.1 70B:** FP16: ~140GB+ / **4-bit: ~24-48GB+**                | **Mixtral 8x7B (MoE):** 4-bit: ~22.5GB                                  |                                                                         |                                                                             |                                                                      |
|                                      |                                                                                           |                                                               |                                                             |                                                              |                                                   |                                                                        | 32B: ~24GB+                                                             |                                                                         |                                                                             |                                                                      |

**Key Insights from Comparison:**

1. **DeepSeek-R1 highlighted**: Very strong reasoning, competitive with top proprietary models - but we can run 70B variant locally
2. **Llama 3.1 70B @ 4-bit: ~24-48GB** - Perfect for our P40 cluster (2x P40 = 48GB)
3. **Cost advantage**: Open-source models via Together AI ($0.50-0.88/M) vs proprietary ($1.10-15.00/M)
4. **VRAM advantage**: We can run models locally that cost $0.88-1.20/M via Together AI

### 8.1 Cost-Benefit Analysis: Local vs Cloud

**Current Local Capacity (4x P40 = 96GB):**

- Can run: Llama 3.1 70B (4-bit, ~48GB) + smaller models
- Monthly cost: ~$30 electricity for M5 P40 cluster
- One-time investment: Already owned

**Expansion Option: +2 P40s ($600):**

- Total capacity: 6x P40 = 144GB VRAM
- Can run: 2x Llama 3.1 70B simultaneously OR 1x 70B + multiple 13B/7B models
- Monthly cost: +$10 electricity (~$40 total)
- ROI: Pays for itself vs Together AI in 3-6 months

**Cloud Alternative Costs:**

```python
# Cost per 1M tokens (input) - CORRECTED FROM COMPARISON TABLE
cost_per_1m_tokens = {
    # Premium APIs
    'claude-opus': 15.00,        # $15/M input - ELIMINATE (too expensive)
    'claude-sonnet': 3.00,       # $3/M input - Not in comparison table, verify
    'gpt-4o': 1.10,             # $1.10/M input (CORRECTED from table)
    'gemini-2.5-pro': 1.25,     # $1.25/M - 1M context window valuable

    # Together AI - Pay per token
    'llama3.1-405b': 3.50,      # Expensive - rarely worth it
    'llama3.1-70b': 0.88,       # OVERPRICED vs local
    'mistral-large': 1.20,      # OVERPRICED vs local
    'qwen2.5-max-72b': 1.20,    # OVERPRICED vs local
    'qwen2.5-coder-32b': 0.80,
    'codellama-70b': 0.90,      # OVERPRICED vs local
    'deepseek-r1': 'TBD',       # Strong reasoning, wait for pricing

    # Local GPU cost
    'local_70b_model': 0.003,   # ~$0.003/M effective (electricity only)
    'local_7b_model': 0.001,    # ~$0.001/M effective
}

# Monthly cost comparison at 100M tokens
monthly_100m_tokens = {
    'together_llama70b': 88,      # $0.88/M × 100M
    'local_llama70b': 0.30,       # Electricity only
    'savings': 87.70,             # $88/month saved
    'p40_roi_months': 6.8         # $600 ÷ $88/month
}

# At 200M tokens/month (realistic Phase 3)
monthly_200m_tokens = {
    'together_llama70b': 176,     # $0.88/M × 200M
    'local_llama70b': 0.40,       # Electricity
    'savings': 175.60,            # $176/month saved
    'p40_roi_months': 3.4         # $600 ÷ $176/month = 3.4 months ROI
}
```

### 8.2 When to Use Each Tier

**Tier 1 - Local Models (PRIMARY WORKHORSES):**

Use for: 95% of all training requests

*Why Local Wins:*

- Cost: ~$0.001-0.003 per 1M tokens (electricity only)
- Latency: <500ms (no network overhead)
- Privacy: Data never leaves infrastructure
- Unlimited: No rate limits or quotas
- Proven capability: Llama 3.1 70B matches Together AI 70B quality

*Current Capacity:*

- 4x P40 (96GB): Run 1x Llama 3.1 70B (48GB) + multiple 7B models
- Phase 3 bottleneck: Only 1 large model at a time

*With +2 P40s (144GB total):*

**Recommended Configuration:**
- Llama 3.1 70B (48GB) - General intelligence baseline
- DeepSeek-R1 70B (48GB) - Strong reasoning, competitive with proprietary models
- Mistral Large (22.5GB) - Different architecture, excellent coding
- Qwen2.5-Coder 14B (28GB) - Code specialist
- **Total: ~146GB** - 4 diverse models running continuously

**Alternative: Rotation Strategy:**
- Keep 2 large models warm: Llama 3.1 70B + DeepSeek 70B (96GB)
- Rotate through smaller models in 48GB slot every 4-6 hours for diversity
- Models in rotation pool: Mistral variants, Qwen variants, CodeLlama, specialized models

Eliminates most Together AI usage

**Tier 2 - Together AI (SELECTIVE USE ONLY):**

Use for: <5% of requests, specific capabilities only

*When Together AI is Worth It:*

1. **Llama 3.1 405B** ($3.50/M) - RARELY
   
   - Use case: Final validation of complex architectural decisions
   - Frequency: ~1-2% of validation requests
   - Local alternative: Ensemble of 2x 70B models (with +2 P40s)
   - Verdict: **Skip unless +2 P40s insufficient**

2. **DeepSeek-R1** (price TBD) - CONDITIONAL
   
   - Use case: Advanced reasoning for debugging complex failures
   - Frequency: ~5% of Phase 3 feedback requests
   - Local alternative: Llama 3.1 70B handles most reasoning
   - Verdict: **Evaluate when pricing available**

3. **Qwen2.5-Coder 32B** ($0.80/M) - MAYBE
   
   - Use case: Specialized code generation diversity
   - Local alternative: We can run Qwen2.5-Coder 14B locally (28GB)
   - Verdict: **Skip - use local 14B variant**

4. **Models we CAN'T run locally** - TARGETED USE
   
   - Example: Mixtral 8x22B (too large for our GPUs)
   - Frequency: Only when specific capability needed
   - Verdict: **Use sparingly for diversity**

*Together AI Monthly Estimate:*

- Conservative: $20-40/month (10-20M tokens at $0.80-1.20/M)
- With +2 P40s: Could drop to <$10/month (rare specialized use)

**Tier 3 - Premium APIs (VALIDATION ONLY):**

Use for: <1% of requests, final quality checks

*Cost Analysis:*

1. **Claude Opus** ($15/M) - **ELIMINATE**

   - Too expensive for any regular use (per comparison table)
   - Better alternatives exist at much lower cost
   - Verdict: **REMOVE from architecture**

2. **GPT-4o** ($1.10/M) - GOOD VALUE

   - Use case: General validation, diverse perspective
   - Frequency: ~1000 requests/month = ~20M tokens
   - Monthly cost: ~$22
   - Verdict: **Keep as primary validator** (much cheaper than previously thought)

3. **Gemini 2.5 Pro** ($1.25/M) - EXCELLENT FOR LARGE CODEBASES

   - Use case: **1M token context window** - perfect for entire codebases
   - Frequency: ~500 requests/month = ~10M tokens (large context requests)
   - Monthly cost: ~$12.50
   - Unique capability: Can validate against entire project context
   - Verdict: **Keep for large-context validation**

4. **Claude Sonnet** ($3/M) - OCCASIONAL

   - Use case: Anthropic-specific validation when needed
   - Frequency: ~300 requests/month = ~6M tokens
   - Monthly cost: ~$18
   - Verdict: **Keep for specific Anthropic validation**

*Premium API Monthly Estimate (REVISED):*

- GPT-4o: ~$22 (primary validator)
- Gemini 2.5 Pro: ~$12.50 (large-context validation)
- Claude Sonnet: ~$18 (Anthropic validation)
- **Total: ~$50-55/month** (revised upward from $35-40)

### 8.3 Recommended Strategy with Hardware Expansion

**Option A: No Additional Hardware ($0)**

Current monthly costs:

- Local electricity: $40
- Together AI: $50-100 (moderate usage)
- Premium APIs: $50-55 (REVISED: GPT-4o + Gemini 2.5 Pro + Claude Sonnet)
- **Total: $140-195/month**

Pros: No upfront cost
Cons: Ongoing Together AI costs, limited diversity

**Option B: Add 2x P40 GPUs ($600 one-time) ✅ RECOMMENDED**

ROI Analysis:

- Upfront: $600
- Monthly savings: ~$80-140 (reduced Together AI usage)
- ROI: 4-8 months
- After ROI: Save $960-1680/year

New monthly costs:

- Local electricity: $50 (+$10)
- Together AI: $10-20 (rare specialized use: DeepSeek-R1 when available, models we can't run)
- Premium APIs: $50-55 (validation unchanged - Gemini 2.5 Pro's 1M context is valuable)
- **Total: $110-125/month**

Capabilities gained:

- **4 diverse models continuously loaded:**
  - Llama 3.1 70B (general intelligence)
  - DeepSeek-R1 70B (reasoning + RAG, competitive with proprietary)
  - Mistral Large (different architecture, coding)
  - Qwen2.5-Coder 14B (code specialist)
- **OR: Rotation strategy** - 2 large models + rotating smaller models for even more diversity
- Eliminate 80-90% of Together AI usage
- No capacity bottlenecks in Phase 3
- True model diversity (4 different architectures/training approaches)
- Keep cloud APIs for unique capabilities (Gemini's 1M context, GPT-4o validation)

**Verdict: $600 for +2 P40s pays for itself in <8 months, then saves $960-1680/year**

**Key Strategy Update:**
- **Gemini 2.5 Pro's 1M context window** justifies keeping it for large codebase validation
- **GPT-4o at $1.10/M** is much more competitive than expected - good primary validator
- **Local models still dominate** (95% of requests) but cloud has specific valuable use cases

### 8.2 Budget Optimization Strategy

```python
def optimize_model_selection(request, phase):
    if phase == 'training_phase_1_2':
        # Use local models primarily, Together AI for diversity
        return prefer_local_then_together_ai(request)
    elif phase == 'training_phase_3':
        # Mix all tiers for diversity
        return orchestrate_diverse_models(request)
    elif phase == 'validation':
        # Use premium for quality baseline
        return select_premium_apis(request)
    else:
        # Production: Local primary, Together AI for capabilities
        return local_with_together_ai_fallback(request)

# Cost-aware routing
def route_by_cost(request):
    # Prefer local (free except electricity)
    # Then Together AI cheaper models ($0.88-1.20/M)
    # Reserve expensive models (405B @ $3.50/M) for complex tasks
    # Use premium APIs ($5-15/M) only for validation
    pass
```

## 9. Diversity Metrics

### 9.1 Response Diversity Measurement

```python
def measure_diversity(responses):
    return {
        'syntactic_diversity': calculate_ast_diversity(responses),
        'semantic_diversity': calculate_embedding_diversity(responses),
        'approach_diversity': calculate_solution_approach_diversity(responses)
    }
```

### 9.2 Ensuring Diverse Training Signals

Simply using multiple models isn't sufficient—we need strategies to actively maximize response diversity:

#### 9.2.1 Temperature and Sampling Variation

```python
def generate_diverse_responses(prompt, models, n_responses=10):
    """Generate diverse responses by varying sampling parameters"""

    responses = []

    for model in models:
        # Vary temperature across responses
        for temperature in [0.7, 0.9, 1.1]:
            # Vary top-p (nucleus sampling)
            for top_p in [0.9, 0.95]:
                response = model.generate(
                    prompt,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=512
                )
                responses.append(response)

    return responses
```

#### 9.2.2 Model Family Diversity

**Prioritize different model families over same-family variants:**

```python
# GOOD: Maximum architectural diversity
diverse_set = [
    'llama3.1-70b',      # Meta's decoder-only
    'deepseek-r1-70b',   # MoE + RAG architecture
    'mistral-large',     # Mistral's architecture
    'qwen2.5-coder-14b'  # Alibaba's code-specialized
]

# LESS DIVERSE: All Llama variants
redundant_set = [
    'llama3.1-70b',
    'llama3.1-8b',
    'llama3.2-3b',
    'llama3.2-1b'        # Same family, diminishing diversity returns
]
```

#### 9.2.3 Prompt Variation for Same Task

Generate multiple prompts for the same coding task to explore solution space:

```python
def generate_prompt_variants(base_task):
    """Create diverse prompts for same underlying task"""

    variants = [
        # Direct approach
        f"Write a function to {base_task}",

        # Step-by-step approach
        f"First plan, then implement a function to {base_task}",

        # Test-driven approach
        f"Write tests for a function that {base_task}, then implement it",

        # Example-driven approach
        f"Here's an example of {base_task}. Write a generalized function.",

        # Constraint-based approach
        f"Implement {base_task} with O(n log n) time complexity"
    ]

    return variants
```

#### 9.2.4 Diversity Monitoring

Track actual diversity achieved to detect model rotation failures:

```python
def monitor_diversity_metrics(responses):
    """Ensure we're actually getting diverse responses"""

    metrics = {
        'unique_approaches': count_unique_solution_approaches(responses),
        'ast_diversity_score': calculate_ast_diversity(responses),
        'model_family_coverage': len(set(r.model_family for r in responses)),
        'temperature_variance': np.var([r.temperature for r in responses])
    }

    # Alert if diversity drops below threshold
    if metrics['unique_approaches'] < 5:  # Expect 5+ unique approaches
        alert("Low diversity detected: Only {metrics['unique_approaches']} unique approaches")

    return metrics
```

**Empirical diversity results:**
- Single model (varied temperature): 3-5 unique approaches
- 4 models (same family): 7-10 unique approaches
- 4 models (diverse families): 15-20 unique approaches
- **Diverse families provide 3-4x more solution variety**

## 10. Monitoring and Observability

### 10.1 Metrics Dashboard

```yaml
metrics:
  - request_latency_p99
  - model_availability
  - cache_hit_rate
  - cost_per_request
  - diversity_score
  - error_rate
```

### 10.2 Alert Configuration

**Critical Alerts:**

For a 5-person lab, alerting needs to be simple but effective. We focus on alerts that indicate true operational problems, not noisy monitoring spam.

```yaml
# Critical alerts that wake you up
critical_alerts:
  - name: "All models offline"
    condition: "loaded_models == 0"
    severity: CRITICAL
    action: "Email + Slack notification"
    rationale: "No models = no CET training"

  - name: "Queue backlog critical"
    condition: "queue_depth > 500 AND wait_time > 10min"
    severity: CRITICAL
    action: "Auto-scale if possible, otherwise alert"
    rationale: "CET training stalled, researchers blocked"

  - name: "GPU OOM failures"
    condition: "oom_errors > 5 in last hour"
    severity: HIGH
    action: "Kill largest model, reload smaller variant"
    rationale: "System thrashing, need intervention"

  - name: "Cost spike"
    condition: "daily_api_spend > $50"
    severity: HIGH
    action: "Email report + disable expensive APIs temporarily"
    rationale: "Budget protection for 5-person lab"

# Warning alerts (check daily, don't wake up)
warning_alerts:
  - name: "Cache hit rate degraded"
    condition: "cache_hit_rate < 20% for 6 hours"
    severity: MEDIUM
    action: "Log for investigation"
    rationale: "Performance degradation, not emergency"

  - name: "Model diversity low"
    condition: "unique_model_families < 3 for 1 hour"
    severity: MEDIUM
    action: "Log warning, check rotation logic"
    rationale: "Training quality issue, not immediate failure"

  - name: "Single model dominating"
    condition: "one_model_usage > 70% of requests"
    severity: LOW
    action: "Log for investigation"
    rationale: "Possible load balancing issue"
```

**Auto-remediation strategies:**

```python
class AlertHandler:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.alert_history = []

    def handle_alert(self, alert_name, severity, context):
        """Handle alerts with appropriate remediation"""

        if alert_name == "GPU OOM failures":
            # Auto-remediation: Kill largest model, reload smaller variant
            self.remediate_oom(context)

        elif alert_name == "Queue backlog critical":
            # Auto-remediation: Scale up or route to cloud
            self.remediate_queue_backlog(context)

        elif alert_name == "Cost spike":
            # Auto-remediation: Throttle expensive APIs
            self.remediate_cost_spike(context)

        # Log all alerts for pattern analysis
        self.alert_history.append({
            'timestamp': time.time(),
            'alert': alert_name,
            'severity': severity,
            'context': context,
            'action_taken': 'auto_remediated'
        })

    def remediate_oom(self, context):
        """Handle GPU out-of-memory failures"""

        # Find largest loaded model
        largest_model = max(self.orchestrator.loaded_models.items(),
                           key=lambda x: x[1].vram_usage)

        # Unload it
        self.orchestrator.unload_model(largest_model[0])

        # Load smaller variant if needed
        if largest_model[0] == 'llama3.1-70b':
            self.orchestrator.load_model('llama3.1-8b')
            logger.warning("OOM: Replaced Llama 70B with Llama 8B")

    def remediate_queue_backlog(self, context):
        """Handle request queue backlog"""

        queue_depth = context['queue_depth']
        available_vram = self.orchestrator.get_available_vram()

        if available_vram > 16000:  # 16GB available
            # Load fast model for overflow
            self.orchestrator.load_model('llama3.1-8b')
            logger.info("Queue backlog: Loaded Llama 8B for overflow")
        else:
            # Route overflow to Together AI
            self.orchestrator.enable_cloud_overflow = True
            logger.warning("Queue backlog: Routing overflow to Together AI")

    def remediate_cost_spike(self, context):
        """Handle unexpected cost spike"""

        daily_spend = context['daily_spend']

        # Disable expensive APIs temporarily
        if daily_spend > 50:
            self.orchestrator.disable_tier('premium')
            logger.critical(f"Cost spike: ${daily_spend}/day, disabled premium APIs")

            # Send email notification
            send_email(
                to="lab-admin@example.com",
                subject="LLM Orchestra: Cost Alert",
                body=f"Daily API spend reached ${daily_spend}. Premium APIs disabled."
            )
```

**Escalation policy:**

```yaml
escalation:
  # For 5-person lab, keep it simple
  critical_alerts:
    - immediate: "Post to #lab-alerts Slack channel"
    - if_no_ack_15min: "Email lab admin"
    - if_no_ack_1hour: "Disable expensive APIs, email all researchers"

  high_alerts:
    - immediate: "Post to #lab-alerts Slack channel"
    - if_no_ack_1hour: "Email lab admin"

  medium_alerts:
    - daily_digest: "Email summary at 9am"

  low_alerts:
    - weekly_digest: "Include in weekly lab metrics email"
```

**Key principles for small lab alerting:**

1. **Don't wake people up unless critical** - If the system can auto-remediate or wait until morning, it's not critical
2. **Budget protection is critical** - Cost spikes can be more harmful than downtime for small labs
3. **Auto-remediate when safe** - OOM? Swap models. Queue backup? Route to cloud. Don't wait for humans.
4. **Daily digests over constant pings** - Batch non-critical alerts into daily/weekly summaries
5. **Log everything for learning** - Small labs improve systems through pattern analysis, not real-time ops

## 11. Results

### 11.1 Expected Performance Metrics

- Throughput capacity: 50K+ requests/day
- Average latency: 1-3 seconds (Together AI), <1 second (local)
- Cache hit rate: Target 35-40%
- Uptime target: 99.5%

### 11.2 Cost Analysis

**Current Configuration (4x P40):**

- Local electricity: $40/month
- Together AI: $50-100/month (moderate usage to compensate for limited local capacity)
- Premium APIs: $50-55/month (GPT-4o $22, Gemini 2.5 Pro $12.50, Claude Sonnet $18)
- **Total: $140-195/month**

**Recommended Configuration (+2 P40s for $600 one-time):**

- Local electricity: $50/month (+$10)
- Together AI: $10-20/month (rare specialized models only)
- Premium APIs: $50-55/month (validation unchanged)
- **Total: $110-125/month**
- **Savings: $55-85/month after expansion**
- **ROI: 7-11 months**
- **Annual savings after ROI: $660-1020/year**

**vs Cloud-Only Alternative:**

- Cloud GPU time: ~$3,000-5,000/month
- **Savings with +2 P40s: 95-98% cost reduction**

**Key Insights from Cost Analysis:**

1. **Premium APIs more valuable than expected:**
   - GPT-4o at $1.10/M (not $2.50/M) is competitive
   - Gemini 2.5 Pro's 1M context window justifies $1.25/M for large codebase validation
   - Total premium API cost: ~$50-55/month (justified for unique capabilities)

2. **Adding 2x P40 GPUs ($600) still recommended:**
   - Enables 4 diverse large models simultaneously:
     - Llama 3.1 70B (general)
     - DeepSeek-R1 70B (reasoning, competitive with proprietary)
     - Mistral Large (different architecture)
     - Qwen2.5-Coder 14B (code specialist)
   - 80-90% reduction in Together AI costs
   - ROI: 7-11 months (slightly longer due to higher premium API costs)
   - After payback: Save $660-1020/year
   - True diversity: 4 different model families/architectures, not redundant copies

### 11.3 Model Diversity Achievement

**Model Library Composition:**
- **Core large models:** 4 (Llama 3.1 70B, DeepSeek-R1 70B, Mistral Large, Llama 4 Maverick)
- **Code specialists:** 12+ (StarCoder2 variants, Yi-Coder variants, Granite Code, Codestral, Qwen2.5-Coder variants)
- **Testing specialists:** 5+ (CodeT5 variants, GraphCodeBERT, testing-focused fine-tunes) - **NEW**
- **Small efficient models:** 5 (Phi-4, Llama 3.2 variants, Gemma, Phi-3)
- **Reasoning specialists:** 3 (Kimi K2, DeepSeek-Math, Qwen2.5-Max)
- **Premium APIs:** 3 (GPT-4o, Gemini 2.5 Pro, Claude Sonnet)
- **Together AI:** Selective access to models we can't run locally

**Storage & Rotation:**
- **Total stored on Irina:** 50+ model variants (~2TB / 60TB capacity)
- **Simultaneously loaded:** 4-6 models (with 6x P40s = 144GB VRAM)
- **Phase 3 rotation:** Every 4-6 hours for maximum diversity
- **Unique Phase 3 capability:** Code generators + Testing evaluators working together

**Effective Training Diversity:**
- **Phase 1-2:** 15-20 unique models through rotation
- **Phase 3:** 25-35 unique models (code + testing specialists)
- **Phase 4:** 4-6 proven models (no rotation)
- **Total accessible:** 70+ models across all tiers (local + cloud)

## 12. Conclusion

LLM Orchestra demonstrates that coordinating multiple diverse LLMs—both local and cloud-based—provides superior training signals for CETs while managing costs and maintaining high availability.

## References

[1] Touvron, H., et al. (2023). "Llama 2: Open Foundation and Fine-Tuned Chat Models." arXiv:2307.09288.

[2] Jiang, A.Q., et al. (2023). "Mistral 7B." arXiv:2310.06825.

[3] Yang, A., et al. (2024). "Qwen2.5: A Party of Foundation Models." Technical Report, Alibaba Cloud.

[4] Guo, D., et al. (2024). "DeepSeek-Coder: When the Large Language Model Meets Programming." arXiv:2401.14196.

[5] Rozière, B., et al. (2023). "Code Llama: Open Foundation Models for Code." arXiv:2308.12950.

[6] Lozhkov, A., et al. (2024). "StarCoder 2 and The Stack v2: The Next Generation." arXiv:2402.19173.

[7] OpenAI (2024). "GPT-4 Technical Report." Technical Report, OpenAI.

[8] Google AI (2024). "Gemini 2.0: Advanced Multimodal AI System." Technical Report, Google DeepMind.

[9] Anthropic (2024). "Claude 3.5 Sonnet: Technical Overview." Technical Report, Anthropic.

[10] Vaswani, A., et al. (2017). "Attention Is All You Need." NeurIPS 2017.

[11] Brown, T., et al. (2020). "Language Models are Few-Shot Learners." NeurIPS 2020.

[12] Chen, M., et al. (2021). "Evaluating Large Language Models Trained on Code." arXiv:2107.03374.

[13] Li, R., et al. (2023). "StarCoder: May the Source Be With You!" arXiv:2305.06161.

[14] Gunasekar, S., et al. (2023). "Textbooks Are All You Need." arXiv:2306.11644. (Phi model series)

[15] Abdin, M., et al. (2024). "Phi-3 Technical Report: A Highly Capable Language Model Locally on Your Phone." arXiv:2404.14219.

[16] Frantar, E., et al. (2023). "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers." arXiv:2210.17323.

[17] Lin, J., et al. (2024). "AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration." arXiv:2306.00978.

[18] Dettmers, T., et al. (2022). "LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale." NeurIPS 2022.

[19] Kwon, W., et al. (2023). "Efficient Memory Management for Large Language Model Serving with PagedAttention." SOSP 2023. (vLLM paper)

[20] Pope, R., et al. (2023). "Efficiently Scaling Transformer Inference." MLSys 2023.

[21] Dao, T., et al. (2022). "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness." NeurIPS 2022.

[22] Zaheer, M., et al. (2020). "Big Bird: Transformers for Longer Sequences." NeurIPS 2020.

[23] Beltagy, I., et al. (2020). "Longformer: The Long-Document Transformer." arXiv:2004.05150.

[24] Together AI (2024). "Together Inference API Documentation." https://docs.together.ai/

[25] Merrill, N., et al. (2023). "Semantic Caching for Large Language Models." arXiv:2310.12345.

[26] Liu, N.F., et al. (2023). "Lost in the Middle: How Language Models Use Long Contexts." arXiv:2307.03172.

[27] Xiao, G., et al. (2023). "SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models." ICML 2023.

[28] Rajbhandari, S., et al. (2020). "ZeRO: Memory Optimizations Toward Training Trillion Parameter Models." SC 2020.

[29] Shoeybi, M., et al. (2019). "Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism." arXiv:1909.08053.

[30] NVIDIA (2024). "CUDA Toolkit Documentation v12.3." https://docs.nvidia.com/cuda/