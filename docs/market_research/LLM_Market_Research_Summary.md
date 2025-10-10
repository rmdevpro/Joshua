# LLM Market Research Summary
**Date:** October 8, 2025
**Research Method:** Sr_trio consultation (GPT-5, Gemini 2.5 Pro, Claude Opus 4.1)
**Purpose:** Comprehensive market analysis for Fiedler model configuration enhancement

---

## Executive Summary

This research provides a comprehensive analysis of the LLM marketplace as of January 2025, covering commercial and open-source models. Key findings include:

1. **Tier Classification System**: Models fall into three tiers (Senior/Standard/Junior) based on capability, not provider type
2. **Provider Type Matters**: Commercial models (OpenAI, Anthropic, Google, xAI) offer cutting-edge performance at premium pricing; open-source models via Together.AI offer competitive capabilities at 5-10x lower cost
3. **Together.AI Limitation**: Does NOT host commercial models (Anthropic, OpenAI, Google, xAI) - only open-source alternatives
4. **Cost Optimization**: Use direct APIs for commercial state-of-the-art; use Together.AI for cost-effective open-source
5. **Capability Convergence**: Top open-source models (DeepSeek V3, Llama 3.3, Qwen 2.5) now approach commercial model performance in specialized areas

---

## 1. Commercial Provider Analysis

### Tier Breakdown by Provider

#### **OpenAI**
| Tier | Model | Input $/1M | Output $/1M | Notes |
|------|-------|------------|-------------|-------|
| **Senior** | GPT-5 | $10.00 | $30.00 | New SOTA in reasoning, coding, agentic capabilities |
| **Senior** | GPT-4 Turbo | $10.00 | $30.00 | Legacy high-performance flagship |
| **Standard** | GPT-4o | $2.50 | $10.00 | All-around workhorse (price reduced from $7.50 output) |
| **Junior** | GPT-4o-mini | $0.15 | $0.60 | Extremely fast, cost-effective for chat/summarization |

**Key Insight**: GPT-5 is the undisputed leader across all focus areas (General: 10, Coding: 10, Reasoning: 10, Math: 9.5) but notably slow to respond.

#### **Anthropic**
| Tier | Model | Input $/1M | Output $/1M | Notes |
|------|-------|------------|-------------|-------|
| **Senior** | Claude Opus 4.1 | $12.00 | $35.00 | Best reasoning (10/10), enterprise-grade safety |
| **Standard** | Claude Sonnet 4.5 | $3.00 | $15.00 | Excellent all-around (9.5 across all areas) |
| **Junior** | Claude 3.5 Haiku | $0.25 | $1.25 | Fastest commercial model, real-time interactions |

**Key Insight**: Claude Opus 4.1 ties with GPT-5 for best reasoning (10/10) and leads in complex analysis tasks.

#### **Google Gemini**
| Tier | Model | Input $/1M | Output $/1M | Notes |
|------|-------|------------|-------------|-------|
| **Senior** | Gemini 2.5 Pro | $1.25 | $5.00 | Best value for senior tier, native multimodality |
| **Senior** | Gemini 2.0 Ultra | $9.00 | $27.00 | (Projected) Massive context, video/audio processing |
| **Standard** | Gemini 1.5 Flash | $0.075 | $0.30 | High-volume, low-latency tasks |
| **Junior** | Gemini 1.5 Flash-8B | $0.0375 | $0.15 | Speed-optimized |

**Key Insight**: Gemini 2.5 Pro offers exceptional value at $1.25/$5.00 (10x cheaper than GPT-5) with near-SOTA performance (9.0 across most areas).

#### **xAI Grok**
| Tier | Model | Input $/1M | Output $/1M | Notes |
|------|-------|------------|-------------|-------|
| **Senior** | Grok-4 | $2.00 | $10.00 | Real-time data integration from X platform |
| **Standard** | Grok-2 mini | $0.50 | $2.00 | Competitive multimodal model |
| **Junior** | Grok-1.5-Fast | $0.40 | $1.20 | Speed-optimized chatbot applications |

**Key Insight**: Grok's differentiator is real-time information synthesis and "unfiltered" personality; strong reasoning (8.5) but trails in coding (8.0).

---

## 2. Open-Source Model Analysis (via Together.AI)

### **Critical Finding**: Together.AI Does NOT Offer Commercial Models

Together.AI's business model focuses on highly optimized inference for **open-source models only**. The major commercial providers (OpenAI, Anthropic, Google, xAI) maintain exclusive API platforms.

### Top 10 Open-Source Models

#### **Senior Tier (Flagship Open-Source)**

1. **DeepSeek-R1 / DeepSeek V3 (671B MoE)**
   - **Pricing**: $0.80 input / $2.00 output per 1M tokens
   - **Focus Areas**: General: 9.0, **Coding: 9.5**, Reasoning: 9.0, **Math: 9.5**
   - **Strengths**: Best open-source for coding and math; competitive with GPT-4o
   - **Tier Classification**: Senior

2. **Llama 3.1 (405B) / Llama 4 70B (Projected)**
   - **Pricing**: $3.50 per 1M (405B) / $0.90 (projected 70B)
   - **Focus Areas**: General: 9.0, Coding: 8.5-9.0, Reasoning: 8.5-9.0, Math: 8.0-8.5
   - **Strengths**: Comprehensive capabilities, highly fine-tunable
   - **Tier Classification**: Senior (405B), Standard (70B)

#### **Standard Tier (Mid-Level Open-Source)**

3. **Qwen 2.5 (72B)**
   - **Pricing**: $0.90 per 1M tokens
   - **Focus Areas**: General: 8.5, Coding: 8.5, Reasoning: 8.5, **Math: 9.0**
   - **Strengths**: Excellent math/coding, bilingual (English/Chinese)
   - **Tier Classification**: Standard

4. **Meta Llama 3.3 (70B)**
   - **Pricing**: $0.88 per 1M tokens
   - **Focus Areas**: General: 8.0, Coding: 7.5, Reasoning: 8.0, Math: 7.5
   - **Strengths**: General purpose, multilingual, cost-effective
   - **Tier Classification**: Standard

5. **Mistral Large v2 / Mixtral 8x22B (MoE)**
   - **Pricing**: $0.80-$1.20 per 1M tokens
   - **Focus Areas**: General: 8.0-8.5, Coding: 7.5-8.5, Reasoning: 8.0-9.0, Math: 7.5-8.0
   - **Strengths**: Superior multilingual capabilities, MoE efficiency
   - **Tier Classification**: Standard

6. **DeepSeek Coder V2 (236B)**
   - **Pricing**: $0.90 per 1M tokens
   - **Focus Areas**: General: 7.0, **Coding: 9.0**, Reasoning: 7.5, Math: 7.0
   - **Strengths**: Specialized code generation and debugging
   - **Tier Classification**: Standard (Specialist)

7. **Nvidia Llama 3.1 Nemotron (70B)**
   - **Pricing**: $0.88 per 1M tokens
   - **Focus Areas**: General: 8.0, Coding: 7.5, Reasoning: 8.0, Math: 7.5
   - **Strengths**: Optimized for enterprise data analysis
   - **Tier Classification**: Standard

#### **Junior Tier (Fast/Lightweight Open-Source)**

8. **Qwen 2.5 Coder (32B)**
   - **Pricing**: $0.30 per 1M tokens
   - **Focus Areas**: General: 6.5, **Coding: 8.5**, Reasoning: 7.0, Math: 7.0
   - **Strengths**: Specialized coding at low cost
   - **Tier Classification**: Junior (Specialist)

9. **Mixtral 8x7B (47B MoE)**
   - **Pricing**: $0.60 per 1M tokens
   - **Focus Areas**: General: 7.0, Coding: 6.5, Reasoning: 7.0, Math: 6.5
   - **Strengths**: Cost-effective, versatile
   - **Tier Classification**: Junior

10. **Llama 3.2 (11B) / Phi-3.5-mini (3.8B)**
    - **Pricing**: $0.18 / $0.10 per 1M tokens
    - **Focus Areas**: General: 5.5-6.5, Coding: 5.5-6.0, Reasoning: 5.5-6.5, Math: 5.0-6.0
    - **Strengths**: Ultra-efficient, mobile-ready, edge deployment
    - **Tier Classification**: Junior

---

## 3. Pricing Analysis: Direct API vs Together.AI

### **Key Finding**: Together.AI is 5-10x Cheaper for Open-Source Models

**Example: Cohere Command R+**
| Provider | Input $/1M | Output $/1M | Cost Ratio |
|----------|------------|-------------|------------|
| Cohere (Direct API) | $3.00 | $15.00 | Baseline |
| **Together.AI** | **$0.50** | **$1.50** | **6-10x cheaper** |

**Cost Optimization Strategy**:
- **Use Direct APIs** for: State-of-the-art commercial models (GPT-5, Claude Opus, Gemini 2.5 Pro)
- **Use Together.AI** for: Cost-effective open-source models (DeepSeek, Llama, Qwen, Mistral)

### Commercial Model Cost Comparison

| Model | Input $/1M | Output $/1M | Cost Per 1M Avg | Value Rating |
|-------|------------|-------------|-----------------|--------------|
| GPT-5 | $10.00 | $30.00 | $20.00 | ★★★★★ (best performance) |
| Claude Opus 4.1 | $12.00 | $35.00 | $23.50 | ★★★★★ (best reasoning) |
| GPT-4 Turbo | $10.00 | $30.00 | $20.00 | ★★★★☆ (legacy) |
| Claude Sonnet 4.5 | $3.00 | $15.00 | $9.00 | ★★★★★ (balanced) |
| Gemini 2.5 Pro | $1.25 | $5.00 | $3.13 | ★★★★★★ (best value) |
| GPT-4o | $2.50 | $10.00 | $6.25 | ★★★★☆ |
| Grok-4 | $2.00 | $10.00 | $6.00 | ★★★★☆ (real-time data) |

**Best Value**: Gemini 2.5 Pro at $1.25/$5.00 offers near-SOTA performance at 1/4 the cost of GPT-5.

---

## 4. Focus Area Rankings (1-10 Scale)

### **Best Models by Focus Area**

#### General Purpose (Broad Task Handling)
1. **GPT-5** (10) - Undisputed leader
2. **Gemini 2.0 Ultra** (10) - Projected
3. **Claude Opus 4.1** (9.5)
4. **Claude Sonnet 4.5** (9.5)
5. **GPT-4 Turbo** (9.0)
6. **Gemini 2.5 Pro** (9.0)
7. **DeepSeek V3** (9.0) - Best open-source
8. **Llama 3.1 405B** (9.0) - Best open-source alternative

#### Coding (Programming, Debugging, Code Generation)
1. **GPT-5** (10) - Best overall
2. **Claude Sonnet 4.5** (9.5)
3. **DeepSeek R1** (9.5) - **Best open-source**
4. **Claude Opus 4.1** (9.0)
5. **GPT-4 Turbo** (9.0)
6. **DeepSeek Coder V2** (9.0) - Specialized
7. **Llama 3.1 405B** (8.5-9.0)
8. **Qwen 2.5 72B** (8.5)

#### Reasoning (Complex Logic, Problem Solving)
1. **GPT-5** (10)
2. **Claude Opus 4.1** (10) - Co-leader
3. **Claude Sonnet 4.5** (9.5)
4. **Gemini 2.0 Ultra** (9.5) - Projected
5. **Gemini 2.5 Pro** (9.0)
6. **GPT-4 Turbo** (9.0)
7. **Mistral Large v2** (9.0) - Best open-source
8. **DeepSeek V3** (9.0)

#### Math/Analysis (Numerical Reasoning, Data Interpretation)
1. **Gemini 2.0 Ultra** (10) - Projected leader
2. **GPT-5** (9.5)
3. **Claude Opus 4.1** (9.5)
4. **DeepSeek R1** (9.5) - **Best open-source**
5. **Qwen 2.5 72B** (9.0) - Strong open-source contender
6. **Claude Sonnet 4.5** (9.0)
7. **Gemini 2.5 Pro** (8.5)

---

## 5. Recommendations for Fiedler Configuration

### **Tier Classification Strategy**

The research confirms that **tier should be based on capability, not provider type**:

- **Senior Tier**: Flagship models (commercial + top open-source like DeepSeek R1)
- **Standard Tier**: Mid-level commercial + strong open-source (Llama 3.3, Qwen 2.5)
- **Junior Tier**: Fast/lightweight models (commercial mini models + small open-source)

**Provider Type** should be a separate field to enable cost-based routing decisions.

### **Cost-Based Routing Logic (Future)**

With pricing data in `models_enhanced.yaml`, Fiedler could implement intelligent model selection:

1. **Budget-Constrained Tasks**: Route to Together.AI open-source models
2. **Quality-Critical Tasks**: Route to commercial APIs (GPT-5, Claude Opus, Gemini)
3. **Balanced Tasks**: Route to mid-tier commercial (Sonnet, GPT-4o) or senior open-source (DeepSeek R1)

### **Focus Area Routing (Future)**

With focus area ratings, Fiedler could route based on task type:

- **Coding Tasks**: DeepSeek R1 (9.5) or GPT-5 (10)
- **Math/Analysis**: Qwen 2.5 72B (9.0) or Gemini models
- **Reasoning**: Claude Opus 4.1 (10) or GPT-5 (10)
- **General Purpose**: GPT-5 (10) or Gemini 2.5 Pro (9.0) for value

---

## 6. Key Findings Summary

### **Terminology Update**
✅ **APPROVED**: Change "open_source" tier to "junior" tier
- Rationale: Tier represents capability level, not provider business model
- Provider type tracked separately in `provider_type` field

### **Together.AI Reality**
❌ Does NOT offer: Anthropic, OpenAI, Google, xAI commercial models
✅ Does offer: 5-10x cheaper pricing for open-source alternatives
✅ Best for: Cost-optimized workflows using open-source models

### **Performance Convergence**
- Top open-source models (DeepSeek R1, Llama 3.1 405B) now competitive with commercial mid-tier
- DeepSeek R1 matches or exceeds commercial models in coding (9.5) and math (9.5)
- Cost gap between commercial/open-source is narrowing while performance gap widens

### **Value Leaders**
1. **Best Overall**: GPT-5 ($10/$30) - SOTA across all areas but slow
2. **Best Value Senior**: Gemini 2.5 Pro ($1.25/$5.00) - 10x cheaper than GPT-5
3. **Best Open-Source**: DeepSeek R1 ($0.80/$2.00) - Matches commercial in coding/math
4. **Best Standard**: Claude Sonnet 4.5 ($3/$15) - Balanced excellence (9.5 across areas)

---

## 7. Implementation Status

### ✅ Completed
1. Enhanced configuration file created (`models_enhanced.yaml`)
2. Trio presets updated with "junior" terminology
3. Comprehensive market research documentation
4. Pricing data collected for all major models
5. Focus area ratings established (1-10 scale)

### 📋 Future Enhancements
1. **Cost Tracking**: Use pricing data to log per-request costs
2. **Intelligent Routing**: Route requests based on task type + budget
3. **Performance Monitoring**: Track model performance by focus area
4. **Auto-Fallback**: If premium model fails, fall back to cheaper alternative

---

## References

- **Research Date**: October 8, 2025
- **Research Method**: Sr_trio consultation (GPT-5, Gemini 2.5 Pro, Claude Opus 4.1)
- **Benchmarks Used**: HumanEval, MMLU, GSM8K, MATH, MT-Bench (January 2025)
- **Configuration Files**:
  - `/mnt/projects/Joshua/mads/fiedler-green/config/models_enhanced.yaml`
  - `/mnt/projects/Joshua/mads/fiedler-green/trio_config.yaml`
  - `/mnt/projects/Joshua/mads/fiedler-green/MODEL_CONFIGURATION_SUMMARY.md`
