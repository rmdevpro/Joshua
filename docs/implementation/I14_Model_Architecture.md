# I14: CET-D Model Architecture

**Version:** 1.0
**Date:** 2025-10-01
**Status:** Draft

---

## Changelog

### v1.0 (2025-10-01)
- **Created**: New document specifying CET-D transformer architecture
- **Rationale**: Address missing model architecture details from Opus review
- **Reference**: Opus review feedback (model architecture details missing)
- **Content**: Architecture specs, hyperparameters, memory requirements, baseline models

---

**Phase:** Phase 2 - CET Training (Weeks 5-12)
**Dependencies:** I02 (GPU infrastructure), I03 (LLM orchestr)
**Enables:** I06, I07, I08 (actual model training)

---

## Executive Summary

This document specifies the CET-D (Context Engineering Transformer for Domains) model architecture, including:
- Transformer architecture details (layers, attention heads, parameters)
- Training hyperparameters for Phase 1-4
- Memory and compute requirements
- Progressive model sizing strategy (1B → 3B → 5B)
- Baseline architecture selection (CodeT5 as starting point)

**Timeline:** Architecture finalized in Week 4, implemented in Week 5
**Critical Milestone:** 5B parameter CET-D architecture validated and trainable
**Success Criteria:** Model fits in 24GB P40 VRAM, <5s inference latency

---

## CET-D Architecture Philosophy

### Design Principles

**1. Specialized Context Optimizer (Not a Full LLM)**

CET-D is designed as a **context preprocessing layer**, not a standalone LLM:
- **90% of parameters** focused on context engineering
- **10% of parameters** for output generation
- **Pipeline role**: User → CET-D → Full LLM (70B+) → Response

**2. Code-Optimized Architecture**

- Encoder-decoder transformer (not decoder-only like GPT)
- Encoder: Deep understanding of source code structure
- Decoder: Generate structured requirements in natural language
- Code-aware tokenization (preserve identifiers, respect syntax)

**3. Progressive Sizing Strategy**

Start small, scale up based on results:
- **Phase 1-2**: 1B parameters (rapid iteration, debugging)
- **Phase 3**: 3B parameters (better quality, still fast)
- **Phase 4**: 5B parameters (production deployment)

---

## Baseline Architecture: CodeT5-Base

### Why CodeT5?

**Selected**: Salesforce CodeT5-base as starting architecture

**Rationale:**
1. **Encoder-Decoder**: Matches our use case (code → requirements)
2. **Code-Pretrained**: Already understands code structure
3. **Right Size**: 220M params → easy to scale to 1B, 3B, 5B
4. **Open Source**: MIT license, full control
5. **Proven**: Strong performance on code tasks (CodeXGLUE benchmarks)

**Alternatives Considered:**
- ❌ **CodeBERT**: Encoder-only (need decoder for generation)
- ❌ **GPT-2/3**: Not code-specialized, harder to fine-tune
- ❌ **StarCoder**: Decoder-only, too large (15B+)
- ✅ **CodeT5**: Perfect fit for code understanding + requirement generation

---

## CET-D Architecture Specifications

### 1B Parameter Model (Phase 1-2)

**Encoder:**
- **Layers**: 12
- **Hidden Size**: 768
- **Attention Heads**: 12
- **Intermediate Size**: 3072
- **Parameters**: ~400M

**Decoder:**
- **Layers**: 12
- **Hidden Size**: 768
- **Attention Heads**: 12
- **Intermediate Size**: 3072
- **Parameters**: ~400M

**Shared Embeddings**: ~100M parameters

**Total**: ~900M parameters (rounded to 1B)

**Memory Footprint:**
- **Model Weights (FP32)**: 3.6GB
- **Model Weights (FP16)**: 1.8GB
- **Optimizer States (AdamW)**: 7.2GB
- **Gradients**: 3.6GB
- **Activations (batch=2)**: ~4GB
- **Total Training**: ~18GB (fits in P40 24GB with headroom)

**Inference:**
- **FP16 Weights**: 1.8GB
- **KV Cache (max_len=2048)**: ~2GB
- **Total Inference**: ~4GB (can run 6× models on 24GB GPU)

---

### 3B Parameter Model (Phase 3)

**Encoder:**
- **Layers**: 18
- **Hidden Size**: 1024
- **Attention Heads**: 16
- **Intermediate Size**: 4096
- **Parameters**: ~1.2B

**Decoder:**
- **Layers**: 18
- **Hidden Size**: 1024
- **Attention Heads**: 16
- **Intermediate Size**: 4096
- **Parameters**: ~1.2B

**Shared Embeddings**: ~200M parameters

**Total**: ~2.6B parameters (rounded to 3B)

**Memory Footprint:**
- **Model Weights (FP16)**: 5.2GB
- **Optimizer States (AdamW)**: 20.8GB
- **Gradients**: 10.4GB
- **Activations (batch=2)**: ~6GB
- **Total Training**: ~42GB (requires tensor parallelism across 2× P40)

**Inference:**
- **FP16 Weights**: 5.2GB
- **KV Cache**: ~3GB
- **Total Inference**: ~8.5GB (can run 2-3× models on 24GB GPU)

---

### 5B Parameter Model (Phase 4 - Production)

**Encoder:**
- **Layers**: 24
- **Hidden Size**: 1280
- **Attention Heads**: 20
- **Intermediate Size**: 5120
- **Parameters**: ~2B

**Decoder:**
- **Layers**: 24
- **Hidden Size**: 1280
- **Attention Heads**: 20
- **Intermediate Size**: 5120
- **Parameters**: ~2B

**Shared Embeddings**: ~300M parameters

**Total**: ~4.3B parameters (rounded to 5B)

**Memory Footprint:**
- **Model Weights (FP16)**: 8.6GB
- **Optimizer States (AdamW)**: 34.4GB
- **Gradients**: 17.2GB
- **Activations (batch=2)**: ~10GB
- **Total Training**: ~70GB (requires tensor parallelism across 3× P40)

**Inference:**
- **FP16 Weights**: 8.6GB
- **KV Cache**: ~5GB
- **Total Inference**: ~14GB (single P40 sufficient for inference)

---

## Training Hyperparameters

### Phase 1: Subject Expertise (RAG-Grounded)

**Objective**: Learn to retrieve relevant code sections given requirements

```python
phase1_config = {
    # Model
    'model_size': '1B',  # Start small for rapid iteration
    'max_input_length': 2048,  # Code context
    'max_output_length': 512,   # Relevant code sections

    # Training
    'num_epochs': 10,
    'batch_size': 4,
    'gradient_accumulation_steps': 2,  # Effective batch = 8
    'learning_rate': 5e-5,
    'warmup_steps': 1000,
    'weight_decay': 0.01,
    'max_grad_norm': 1.0,

    # Optimizer
    'optimizer': 'AdamW',
    'betas': (0.9, 0.999),
    'eps': 1e-8,

    # Scheduler
    'scheduler': 'linear_warmup_decay',

    # Regularization
    'dropout': 0.1,
    'attention_dropout': 0.1,

    # Early stopping
    'patience': 3,
    'min_delta': 0.001
}
```

**Expected Training Time (40 apps, ~400k examples):**
- 1B model on 1× P40: ~60 hours (2.5 days)

---

### Phase 2: Context Transformation

**Objective**: Learn to transform poor context into excellent context

```python
phase2_config = {
    # Model
    'model_size': '1B',
    'max_input_length': 2048,  # Poor quality context
    'max_output_length': 1024,  # Transformed context

    # Training
    'num_epochs': 5,
    'batch_size': 4,
    'gradient_accumulation_steps': 2,
    'learning_rate': 3e-5,  # Lower than Phase 1
    'warmup_steps': 500,
    'weight_decay': 0.01,
    'max_grad_norm': 1.0,

    # Optimizer
    'optimizer': 'AdamW',

    # Scheduler
    'scheduler': 'linear_warmup_decay',

    # Regularization
    'dropout': 0.1
}
```

**Expected Training Time (40 apps, ~200k pairs):**
- 1B model on 1× P40: ~30 hours (1.25 days)

---

### Phase 3: Interactive Feedback

**Objective**: Optimize requirements for maximal reconstruction quality across 6 LLMs

```python
phase3_config = {
    # Model
    'model_size': '3B',  # Scale up for better quality
    'max_input_length': 4096,  # Full application code
    'max_output_length': 2048,  # Complete requirements

    # Training
    'num_epochs': 20,  # More epochs for RL-style optimization
    'batch_size': 2,  # Larger model → smaller batch
    'gradient_accumulation_steps': 4,  # Effective batch = 8
    'learning_rate': 1e-4,
    'warmup_steps': 2000,
    'weight_decay': 0.01,
    'max_grad_norm': 0.5,  # Tighter gradient clipping for stability

    # Optimizer
    'optimizer': 'AdamW',

    # Reward-weighted loss
    'use_reward_weighting': True,
    'reward_scale': 1.0,

    # Variance minimization
    'variance_penalty': 0.1,  # Penalize high variance across LLMs

    # Scheduler
    'scheduler': 'cosine_annealing',
    'min_lr': 1e-6,

    # Regularization
    'dropout': 0.15,  # More dropout to prevent overfitting to reconstruction
}
```

**Expected Training Time (40 apps, 10 iterations each):**
- 3B model on 2× P40 (tensor parallel): ~120 hours (5 days)

**Note**: Phase 3 is slowest because each training iteration requires:
1. CET-D generates requirements
2. 6 LLMs generate implementations (parallel)
3. Test all 6 implementations
4. Compute rewards
5. Backpropagate through CET-D

---

### Phase 4: Continuous Learning (Online)

**Objective**: Incremental fine-tuning on production data

```python
phase4_config = {
    # Model
    'model_size': '5B',  # Production quality
    'max_input_length': 4096,
    'max_output_length': 2048,

    # Training (conservative for stability)
    'num_epochs': 5,
    'batch_size': 2,
    'gradient_accumulation_steps': 4,
    'learning_rate': 1e-6,  # 100× lower than Phase 3!
    'warmup_steps': 10,
    'weight_decay': 0.01,
    'max_grad_norm': 0.5,

    # Optimizer
    'optimizer': 'AdamW',

    # Scheduler
    'scheduler': 'constant',  # No decay for online learning

    # Regularization
    'dropout': 0.1,

    # Early stopping (aggressive to prevent overfitting)
    'patience': 2,
    'min_delta': 0.005
}
```

**Expected Retraining Time (20-40 new examples):**
- 5B model on 3× P40: ~2 hours (weekly retraining)

---

## Model Implementation

### Base Architecture (CodeT5 Extended)

```python
from transformers import T5Config, T5ForConditionalGeneration

def create_cet_d(model_size='1B'):
    """
    Create CET-D model based on T5/CodeT5 architecture.
    """
    if model_size == '1B':
        config = T5Config(
            vocab_size=32128,  # CodeT5 vocabulary
            d_model=768,
            d_ff=3072,
            num_layers=12,
            num_decoder_layers=12,
            num_heads=12,
            relative_attention_num_buckets=32,
            dropout_rate=0.1,
            layer_norm_eps=1e-6,
            initializer_factor=1.0,
            feed_forward_proj="relu"
        )
    elif model_size == '3B':
        config = T5Config(
            vocab_size=32128,
            d_model=1024,
            d_ff=4096,
            num_layers=18,
            num_decoder_layers=18,
            num_heads=16,
            relative_attention_num_buckets=32,
            dropout_rate=0.15,
            layer_norm_eps=1e-6,
            initializer_factor=1.0,
            feed_forward_proj="relu"
        )
    elif model_size == '5B':
        config = T5Config(
            vocab_size=32128,
            d_model=1280,
            d_ff=5120,
            num_layers=24,
            num_decoder_layers=24,
            num_heads=20,
            relative_attention_num_buckets=32,
            dropout_rate=0.1,
            layer_norm_eps=1e-6,
            initializer_factor=1.0,
            feed_forward_proj="relu"
        )

    model = T5ForConditionalGeneration(config)

    return model
```

### Tokenization Strategy

```python
from transformers import RobertaTokenizer

# Use CodeT5 tokenizer (RoBERTa-based, code-aware)
tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')

# Custom tokens for requirements engineering
special_tokens = {
    'additional_special_tokens': [
        '<FUNCTIONAL_REQ>',
        '<NON_FUNCTIONAL_REQ>',
        '<CONSTRAINT>',
        '<API_CALL>',
        '<CLASS_DEF>',
        '<FUNCTION_DEF>'
    ]
}

tokenizer.add_special_tokens(special_tokens)
```

---

## Hardware Requirements

### Training Infrastructure

**Phase 1-2 (1B model):**
- **GPUs**: 1× NVIDIA P40 (24GB VRAM)
- **RAM**: 64GB
- **Storage**: 500GB NVMe (model checkpoints, training data)
- **Training Time**: ~4 days total

**Phase 3 (3B model):**
- **GPUs**: 2× NVIDIA P40 (48GB VRAM total)
- **Tensor Parallelism**: Required
- **RAM**: 128GB
- **Storage**: 1TB NVMe
- **Training Time**: ~5 days

**Phase 4 (5B model):**
- **GPUs**: 3× NVIDIA P40 (72GB VRAM total)
- **Tensor Parallelism**: Required
- **RAM**: 128GB
- **Storage**: 1.5TB NVMe
- **Retraining**: ~2 hours/week

### Inference Infrastructure

**5B Production Model:**
- **GPU**: 1× NVIDIA P40 (24GB VRAM) sufficient
- **RAM**: 32GB
- **Inference Latency**: <5s for requirements extraction
- **Throughput**: ~200 requests/hour (single GPU)

---

## Validation Metrics

### Architecture Validation

**Week 5 (Implementation):**
- ✅ Model instantiates without errors
- ✅ Forward pass completes (<10s)
- ✅ Backward pass computes gradients
- ✅ Memory footprint matches estimates (±10%)

**Week 6 (Overfitting Test):**
- ✅ Can overfit to 10 training examples (proves model capacity)
- ✅ Loss drops to near-zero on tiny dataset
- ✅ Generated output matches target exactly

**Week 7 (Scaling Test):**
- ✅ Scales from 1B → 3B without errors
- ✅ Tensor parallelism works across 2× GPUs
- ✅ Training speed scales linearly with model size

---

## Progressive Sizing Strategy

### Rationale

**Why Start Small (1B)?**
1. **Rapid Iteration**: Debug training pipeline, data loading, metrics
2. **Fast Experiments**: Test hyperparameters in hours, not days
3. **Lower Risk**: Smaller investment if approach fails

**Why Scale Up (3B, 5B)?**
1. **Capacity**: Larger models can capture more nuanced patterns
2. **Quality**: Better requirements → higher reconstruction pass rate
3. **Production**: 5B matches quality expectations for real deployment

### Decision Points

**After Phase 1-2 (1B model):**
- **If test pass rate >60%**: Scale to 3B for Phase 3
- **If test pass rate <50%**: Fix data/training before scaling
- **If test pass rate 50-60%**: Gather more training data, retry 1B

**After Phase 3 (3B model):**
- **If test pass rate >70%**: Scale to 5B for Phase 4
- **If test pass rate <65%**: Improve Phase 3 training, stay at 3B
- **If test pass rate 65-70%**: Optional 5B (marginal gains)

---

## Risks & Mitigation

### High-Impact Risks

1. **Model Too Large for P40**
   - **Risk**: 5B model doesn't fit in 24GB VRAM
   - **Mitigation**: Tensor parallelism across 3× P40, FP16 training, gradient checkpointing

2. **Training Instability**
   - **Risk**: Loss diverges, NaN gradients
   - **Mitigation**: Gradient clipping (max_norm=0.5), lower learning rate, multiple random seeds

3. **Insufficient Capacity**
   - **Risk**: 5B model can't learn task
   - **Mitigation**: Progressive sizing (1B → 3B → 5B), overfitting test, architecture ablations

---

## Next Steps

### Week 4 (Architecture Finalization)
1. Implement CET-D 1B model in PyTorch
2. Test forward/backward passes
3. Validate memory footprint
4. Run overfitting test on 10 examples

### Week 5 (Phase 1 Training Start)
1. Begin Phase 1 training with 1B model
2. Monitor training curves (loss, perplexity)
3. Validate retrieval accuracy on dev set
4. Checkpoint every 1000 steps

### Week 7 (Scaling Decision)
1. Evaluate Phase 1 results on validation set
2. Decide: stay at 1B or scale to 3B?
3. If scaling: implement tensor parallelism
4. Test 3B model training on subset

---

## References

- **CodeT5**: https://github.com/salesforce/CodeT5
- **Transformer Architecture**: Vaswani et al., 2017 ("Attention Is All You Need")
- **T5 Architecture**: Raffel et al., 2020 ("Exploring the Limits of Transfer Learning")
- **Paper 02**: CET Architecture Specialization (theoretical framework)
- **Paper 03**: Progressive Training Methodology (four-phase approach)

---

*This document provides complete CET-D architecture specifications for implementation in Phase 2 of the ICCM project.*
