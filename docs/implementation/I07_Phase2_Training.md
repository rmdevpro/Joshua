# I07: Phase 2 Training - Context Transformation

**Version:** 1.0
**Date:** 2025-10-01
**Status:** Draft
**Phase:** Phase 2 - CET Training (Weeks 7-8)
**Dependencies:** I06 (Phase 1 trained CET-D)
**Enables:** I08 (Phase 3 interactive training)

---

## Executive Summary

This document specifies Phase 2 training for CET-D, focusing on:
- Context transformation: code → requirements
- Learning to compress verbose source into compact context
- Optimizing requirements for downstream LLM comprehension
- Establishing degradation-reconstruction training loop

**Timeline:** 2 weeks
**Critical Milestone:** CET-D can extract requirements that enable basic reconstruction
**Success Criteria:** >50% reconstruction test pass rate, foundation ready for Phase 3 optimization

---

## Phase 2 Overview (from Paper 02)

### Purpose: Learn Context Engineering Skills

**What CET-D Learns in Phase 2:**
1. **Reverse Mapping:** Code → Requirements (reverse of Phase 1)
2. **Compression:** Distill 1,000 LOC into 10-20 requirements
3. **Clarity:** Write requirements LLMs can understand
4. **Completeness:** Capture all essential functionality

**Training Approach:**
- **Degradation:** Start with full source code, progressively remove details
- **Reconstruction:** Test if LLMs can rebuild from requirements
- **Feedback:** Reconstruction quality → training signal
- **Iteration:** Improve requirements based on reconstruction failures

**Why This Matters:**
- Core context engineering skill: compression without loss of meaning
- Foundation for Phase 3 interactive optimization
- First time CET-D produces output (requirements) instead of just retrieving

---

## Training Methodology: Degradation-Reconstruction Loop

### Conceptual Flow

```
Step 1: Full Source Code (1,000 LOC)
         ↓
Step 2: CET-D Extracts Requirements (10-20 items)
         ↓
Step 3: Hide Source, Give LLM Only Requirements
         ↓
Step 4: LLM Generates Implementation
         ↓
Step 5: Run Original Tests on LLM Implementation
         ↓
Step 6: Test Pass Rate → Reward Signal
         ↓
Step 7: Backprop to CET-D (improve requirements)
```

### Degradation Strategy

**Progressive Information Removal:**

**Level 1: Full Context (Baseline)**
- Source code
- Comments
- Docstrings
- README

**Level 2: Code Only**
- Source code
- ~~Comments~~
- ~~Docstrings~~
- ~~README~~

**Level 3: Signatures Only**
- Function/class signatures
- ~~Implementation details~~

**Level 4: CET-D Requirements Only**
- **Generated requirements**
- ~~All source code~~

**Goal:** Train CET-D to produce Level 4 that enables same reconstruction quality as Level 1

---

## Training Data Generation

### Requirement Extraction Training

**Input:** Application source code
**Output:** Requirements (functional, non-functional, constraints)

**Example Transformation:**

```python
# INPUT: Source Code (100 LOC)
def parse_json(json_str: str) -> dict:
    """
    Parse a JSON string into a Python dictionary.

    Args:
        json_str: Valid JSON string

    Returns:
        Parsed dictionary

    Raises:
        JSONSyntaxError: If invalid JSON
    """
    tokens = tokenize(json_str)
    return parse_tokens(tokens)

def tokenize(text: str) -> List[Token]:
    # ... 50 lines of tokenization logic ...
    pass

def parse_tokens(tokens: List[Token]) -> dict:
    # ... 40 lines of parsing logic ...
    pass

# OUTPUT: CET-D Requirements
1. Parse valid JSON strings into Python dictionaries
2. Support all JSON types: object, array, string, number, boolean, null
3. Detect and report syntax errors with line/column information
4. Raise JSONSyntaxError for invalid input
5. Handle nested structures up to 100 levels deep
```

### Synthetic Training Data

**Augmentation Strategy:**

```python
def generate_synthetic_requirements(source_code: str, cet_model):
    """
    Generate multiple requirement variants for same code.
    """
    # Base requirements (from gold standard)
    gold_reqs = extract_gold_requirements(source_code)

    # Variant 1: CET-D generated
    cet_reqs = cet_model.extract_requirements(source_code)

    # Variant 2: Paraphrased (using Llama-3.1)
    paraphrased_reqs = llm_paraphrase(gold_reqs)

    # Variant 3: Degraded (remove details)
    degraded_reqs = remove_random_details(gold_reqs, degradation_rate=0.3)

    return {
        'gold': gold_reqs,
        'cet_generated': cet_reqs,
        'paraphrased': paraphrased_reqs,
        'degraded': degraded_reqs
    }
```

---

## Model Architecture Updates

### Phase 2 CET-D: Generation Head

**Extension of Phase 1 Model:**

```python
from transformers import AutoModelForCausalLM
import torch.nn as nn

class CET_D_Phase2(nn.Module):
    def __init__(self, phase1_checkpoint: str):
        super().__init__()

        # Load Phase 1 trained encoder
        self.encoder = AutoModelForCausalLM.from_pretrained(phase1_checkpoint)

        # Freeze encoder initially (optional)
        for param in self.encoder.parameters():
            param.requires_grad = False

        # Add generation head for requirements
        self.requirement_generator = nn.TransformerDecoder(
            nn.TransformerDecoderLayer(
                d_model=self.encoder.config.hidden_size,
                nhead=8,
                dim_feedforward=2048,
                dropout=0.1
            ),
            num_layers=4
        )

        # Output projection
        self.output_projection = nn.Linear(
            self.encoder.config.hidden_size,
            self.encoder.config.vocab_size
        )

    def forward(self, source_code_ids, requirement_ids=None):
        # Encode source code
        encoder_output = self.encoder(
            input_ids=source_code_ids,
            output_hidden_states=True
        )
        code_embedding = encoder_output.hidden_states[-1]

        if requirement_ids is not None:
            # Training: Teacher forcing
            req_embeddings = self.encoder.get_input_embeddings()(requirement_ids)
            decoder_output = self.requirement_generator(
                req_embeddings.transpose(0, 1),
                code_embedding.transpose(0, 1)
            )
            logits = self.output_projection(decoder_output.transpose(0, 1))
            return logits
        else:
            # Inference: Autoregressive generation
            return self.generate_requirements(code_embedding)

    def generate_requirements(self, code_embedding, max_length=512):
        """
        Generate requirements autoregressively.
        """
        batch_size = code_embedding.size(0)
        device = code_embedding.device

        # Start token
        generated = torch.full(
            (batch_size, 1),
            self.encoder.config.bos_token_id,
            dtype=torch.long,
            device=device
        )

        for _ in range(max_length):
            # Embed current sequence
            req_embeds = self.encoder.get_input_embeddings()(generated)

            # Decode
            decoder_output = self.requirement_generator(
                req_embeds.transpose(0, 1),
                code_embedding.transpose(0, 1)
            )

            # Get logits for next token
            logits = self.output_projection(decoder_output.transpose(0, 1))
            next_token_logits = logits[:, -1, :]

            # Sample (or greedy)
            next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)

            # Append
            generated = torch.cat([generated, next_token], dim=1)

            # Stop if EOS
            if (next_token == self.encoder.config.eos_token_id).all():
                break

        return generated
```

### Training Objective

**Loss Function:**

```python
def phase2_loss(cet_model, source_code, target_requirements, reconstruction_quality):
    """
    Combined loss: generation quality + reconstruction signal.

    Args:
        cet_model: Phase 2 CET-D model
        source_code: Input source code
        target_requirements: Gold standard requirements
        reconstruction_quality: Test pass rate from LLM reconstruction

    Returns:
        Total loss
    """
    # Loss 1: Generation quality (cross-entropy)
    generated_logits = cet_model(source_code, target_requirements)
    generation_loss = F.cross_entropy(
        generated_logits.view(-1, generated_logits.size(-1)),
        target_requirements.view(-1)
    )

    # Loss 2: Reconstruction quality (REINFORCE)
    # Generate requirements
    generated_reqs = cet_model(source_code)

    # LLM reconstruction (cached or computed)
    # reconstruction_quality is test_pass_rate from I08

    # Reward: test pass rate
    reward = reconstruction_quality - 0.5  # Baseline: 50% pass rate

    # REINFORCE gradient
    reconstruction_loss = -reward * generation_loss.detach()

    # Combined loss
    total_loss = generation_loss + 0.1 * reconstruction_loss

    return total_loss, {
        'generation_loss': generation_loss.item(),
        'reconstruction_loss': reconstruction_loss.item(),
        'reward': reward
    }
```

---

## Training Procedure

### Two-Stage Training

**Stage 1: Supervised Learning (Week 7)**

Train on gold standard requirements (human-extracted from I04).

**Config:**
```yaml
stage1:
  objective: "generation_quality"
  num_epochs: 5
  batch_size: 4
  learning_rate: 1e-5
  warmup_steps: 200

  # Use gold requirements as targets
  train_on: "gold_requirements"

  # Evaluation
  eval_metric: "BLEU"  # Similarity to gold requirements
  early_stopping_patience: 2
```

**Stage 2: Reconstruction-Guided Learning (Week 8)**

Fine-tune based on reconstruction quality.

**Config:**
```yaml
stage2:
  objective: "reconstruction_quality"
  num_epochs: 3
  batch_size: 2  # Smaller (reconstruction is expensive)
  learning_rate: 5e-6
  warmup_steps: 100

  # Use LLM orchestra for reconstruction
  llm_models: ["deepseek-coder-33b", "codellama-34b", "mistral-7b"]
  reconstruction_batch_size: 6  # 2 apps × 3 models

  # Evaluation
  eval_metric: "test_pass_rate"
  target_pass_rate: 0.5  # 50% by end of Phase 2
```

### Training Script

**File:** `/mnt/projects/ICCM/training/phase2/train.py`

```python
#!/usr/bin/env python3
"""
Phase 2 Training: Context transformation (code → requirements).
"""
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, get_scheduler
import json
from pathlib import Path
from tqdm import tqdm
import asyncio

class Phase2Dataset:
    def __init__(self, apps_dir: Path, tokenizer, stage="supervised"):
        self.apps = []
        self.tokenizer = tokenizer
        self.stage = stage

        # Load applications
        for app_dir in apps_dir.glob("*/"):
            if "holdout" in str(app_dir):
                continue  # Skip holdout set

            # Load source code
            source_files = list((app_dir / "src").glob("*.py"))
            source_code = "\n\n".join([f.read_text() for f in source_files])

            # Load gold requirements
            gold_reqs_file = app_dir / "gold_requirements.md"
            gold_reqs = parse_requirements(gold_reqs_file.read_text())

            self.apps.append({
                'app_id': app_dir.name,
                'source_code': source_code,
                'gold_requirements': gold_reqs,
                'test_suite': app_dir / "tests"
            })

    def __len__(self):
        return len(self.apps)

    def __getitem__(self, idx):
        app = self.apps[idx]

        # Tokenize source code
        source_tokens = self.tokenizer(
            app['source_code'],
            max_length=4096,
            truncation=True,
            padding='max_length',
            return_tensors='pt'
        )

        # Tokenize requirements
        req_text = "\n".join([f"{i+1}. {req}" for i, req in enumerate(app['gold_requirements'])])
        req_tokens = self.tokenizer(
            req_text,
            max_length=512,
            truncation=True,
            padding='max_length',
            return_tensors='pt'
        )

        return {
            'app_id': app['app_id'],
            'source_code': source_tokens,
            'requirements': req_tokens,
            'test_suite': str(app['test_suite'])
        }

async def get_reconstruction_quality(cet_model, app, llm_models, test_harness):
    """
    Measure reconstruction quality:
    1. CET-D generates requirements
    2. LLMs reconstruct from requirements
    3. Run tests, get pass rate
    """
    # Generate requirements with CET-D
    generated_reqs = cet_model.generate_requirements(
        app['source_code']['input_ids']
    )
    req_text = cet_model.tokenizer.decode(generated_reqs[0])

    # Reconstruct with LLM orchestra
    reconstructions = []
    for llm_model in llm_models:
        impl = await llm_model.generate_implementation(req_text)
        reconstructions.append(impl)

    # Run tests
    test_results = []
    for impl in reconstructions:
        result = test_harness.run_tests(
            app_id=app['app_id'],
            implementation=impl,
            test_suite_path=app['test_suite']
        )
        test_results.append(result['test_pass_rate'])

    # Average pass rate across LLMs
    avg_pass_rate = sum(test_results) / len(test_results)
    return avg_pass_rate

def train_phase2_stage1(model, train_loader, config):
    """
    Stage 1: Supervised learning on gold requirements.
    """
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config['learning_rate']
    )

    scheduler = get_scheduler(
        "linear",
        optimizer=optimizer,
        num_warmup_steps=config['warmup_steps'],
        num_training_steps=len(train_loader) * config['num_epochs']
    )

    model.train()

    for epoch in range(config['num_epochs']):
        epoch_loss = 0
        progress_bar = tqdm(train_loader, desc=f"Stage 1 - Epoch {epoch+1}")

        for batch in progress_bar:
            # Forward pass
            logits = model(
                source_code_ids=batch['source_code']['input_ids'].cuda(),
                requirement_ids=batch['requirements']['input_ids'].cuda()
            )

            # Loss
            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                batch['requirements']['input_ids'].view(-1).cuda(),
                ignore_index=model.tokenizer.pad_token_id
            )

            # Backward
            loss.backward()
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()

            epoch_loss += loss.item()
            progress_bar.set_postfix({'loss': loss.item()})

        print(f"Stage 1 - Epoch {epoch+1} Loss: {epoch_loss / len(train_loader):.4f}")

    print("✓ Stage 1 complete")

async def train_phase2_stage2(model, train_loader, llm_orchestra, test_harness, config):
    """
    Stage 2: Reconstruction-guided learning.
    """
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config['learning_rate']
    )

    model.train()

    for epoch in range(config['num_epochs']):
        epoch_loss = 0
        epoch_reward = 0

        progress_bar = tqdm(train_loader, desc=f"Stage 2 - Epoch {epoch+1}")

        for batch in progress_bar:
            # Get reconstruction quality
            reconstruction_quality = await get_reconstruction_quality(
                model,
                batch,
                llm_orchestra,
                test_harness
            )

            # Forward pass
            logits = model(
                source_code_ids=batch['source_code']['input_ids'].cuda(),
                requirement_ids=batch['requirements']['input_ids'].cuda()
            )

            # Generation loss
            gen_loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                batch['requirements']['input_ids'].view(-1).cuda(),
                ignore_index=model.tokenizer.pad_token_id
            )

            # Reward signal
            reward = reconstruction_quality - 0.5  # Baseline: 50%

            # Total loss
            loss = gen_loss - 0.1 * reward * gen_loss.detach()

            # Backward
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

            epoch_loss += loss.item()
            epoch_reward += reward

            progress_bar.set_postfix({
                'loss': loss.item(),
                'reward': reward,
                'pass_rate': reconstruction_quality
            })

        avg_reward = epoch_reward / len(train_loader)
        print(f"Stage 2 - Epoch {epoch+1} Loss: {epoch_loss / len(train_loader):.4f}, Avg Reward: {avg_reward:.3f}")

    print("✓ Stage 2 complete")

if __name__ == "__main__":
    import yaml

    # Load config
    with open('/mnt/projects/ICCM/training/phase2/train_config.yaml') as f:
        config = yaml.safe_load(f)

    # Load Phase 1 model
    from I06_Phase1_Training import CET_D_Phase1
    phase1_model = CET_D_Phase1.from_pretrained(
        "/mnt/nvme/models/cet-d-phase1/final"
    )

    # Initialize Phase 2 model
    model = CET_D_Phase2(phase1_checkpoint="/mnt/nvme/models/cet-d-phase1/final")
    model.cuda()

    # Load data
    tokenizer = AutoTokenizer.from_pretrained("/mnt/nvme/models/cet-d-phase1/final")
    train_dataset = Phase2Dataset(
        Path("/mnt/projects/ICCM/datasets/applications/train"),
        tokenizer,
        stage="supervised"
    )
    train_loader = DataLoader(train_dataset, batch_size=config['stage1']['batch_size'])

    # Stage 1: Supervised
    print("Starting Stage 1: Supervised Learning")
    train_phase2_stage1(model, train_loader, config['stage1'])

    # Stage 2: Reconstruction-guided
    print("Starting Stage 2: Reconstruction-Guided Learning")
    from I03_LLM_Infrastructure import LLM_Orchestra
    from I02_Foundation_Layer import TestHarness

    llm_orchestra = LLM_Orchestra()
    test_harness = TestHarness()

    asyncio.run(
        train_phase2_stage2(
            model,
            train_loader,
            llm_orchestra,
            test_harness,
            config['stage2']
        )
    )

    # Save final model
    model.save_pretrained("/mnt/nvme/models/cet-d-phase2/final")
    print("✓ Phase 2 training complete")
```

---

## Evaluation Metrics

### Primary Metrics

**1. Generation Quality (BLEU Score)**
```python
from nltk.translate.bleu_score import sentence_bleu

def evaluate_generation_quality(generated_reqs, gold_reqs):
    """
    BLEU: Similarity between generated and gold requirements.
    """
    bleu_scores = []

    for gen, gold in zip(generated_reqs, gold_reqs):
        score = sentence_bleu([gold.split()], gen.split())
        bleu_scores.append(score)

    return sum(bleu_scores) / len(bleu_scores)
```

**2. Reconstruction Test Pass Rate**
```python
async def evaluate_reconstruction(cet_model, test_apps, llm_orchestra, test_harness):
    """
    End-to-end: CET-D requirements → LLM reconstruction → test pass rate.
    """
    total_pass_rate = 0

    for app in test_apps:
        # Generate requirements
        reqs = cet_model.extract_requirements(app['source_code'])

        # Reconstruct with LLMs
        implementations = await llm_orchestra.generate_all(reqs)

        # Test
        pass_rates = []
        for impl in implementations:
            result = test_harness.run_tests(app['id'], impl, app['test_suite'])
            pass_rates.append(result['test_pass_rate'])

        total_pass_rate += sum(pass_rates) / len(pass_rates)

    return total_pass_rate / len(test_apps)
```

### Success Criteria

**Week 8 Exit Criteria:**
- [ ] BLEU score >0.6 vs gold requirements
- [ ] Average reconstruction test pass rate >50%
- [ ] At least 30% of apps achieve >75% test pass rate
- [ ] Requirements are human-readable and clear

---

## Validation & Testing

### Week 7: Stage 1 Validation

**Test 1: Generation Quality**
```bash
# Generate requirements for test app
python /mnt/projects/ICCM/training/phase2/generate_requirements.py \
    --app-id 001 \
    --checkpoint /mnt/nvme/models/cet-d-phase2/stage1

# Compare to gold standard
# Expected: BLEU >0.6
```

**Test 2: Human Evaluation**
```python
# Sample 10 apps, show generated vs gold requirements
for app_id in random.sample(train_apps, 10):
    gen_reqs = cet_model.extract_requirements(app_id)
    gold_reqs = load_gold_requirements(app_id)

    print(f"App: {app_id}")
    print(f"Generated:\n{gen_reqs}\n")
    print(f"Gold:\n{gold_reqs}\n")
    print("---")
```

### Week 8: Stage 2 Validation

**Test 1: Reconstruction Quality**
```bash
# Full reconstruction test
python /mnt/projects/ICCM/training/phase2/test_reconstruction.py \
    --checkpoint /mnt/nvme/models/cet-d-phase2/stage2 \
    --num-apps 10

# Expected output:
# Average test pass rate: 52.3%
# Apps with >75% pass rate: 3/10 (30%)
```

**Test 2: Ablation Study**
```python
# Compare different requirement sources
baselines = {
    'gold': lambda app: load_gold_requirements(app),
    'phase1': lambda app: phase1_model.retrieve(app),  # Just retrieval
    'phase2_stage1': lambda app: phase2_stage1.extract(app),  # No reconstruction training
    'phase2_stage2': lambda app: phase2_stage2.extract(app)   # Full Phase 2
}

for name, req_fn in baselines.items():
    pass_rate = evaluate_reconstruction(req_fn, test_apps, llm_orchestra)
    print(f"{name}: {pass_rate:.1%}")

# Expected ranking: gold > phase2_stage2 > phase2_stage1 > phase1
```

---

## Integration with Phase 3

### Output: CET-D Phase 2 Checkpoint

**Capabilities:**
- Extract requirements from source code
- Generate clear, LLM-comprehensible requirements
- Achieve >50% reconstruction test pass rate
- Foundation for interactive optimization (Phase 3)

**Handoff to I08 (Phase 3 Training):**
- CET-D checkpoint: `/mnt/nvme/models/cet-d-phase2/final`
- Baseline reconstruction metrics
- Training logs showing reward signal effectiveness

**Phase 3 Preview:**
CET-D will learn to:
1. **Optimize** requirements based on multi-LLM reconstruction feedback
2. **Minimize variance** across LLM implementations
3. **Maximize test pass rate** through iterative refinement
4. **Achieve >75% target** through interactive learning

---

## Risks & Mitigation

### High-Impact Risks

1. **Reconstruction Too Hard**
   - **Risk:** Even good requirements can't enable >50% pass rate
   - **Mitigation:** Validate with gold requirements first, simplify apps if needed
   - **Monitoring:** Track gold standard reconstruction as upper bound

2. **Training Instability (REINFORCE)**
   - **Risk:** High variance in reward signal destabilizes training
   - **Mitigation:** Baseline subtraction, gradient clipping, small learning rate
   - **Monitoring:** Track reward variance, loss trends

3. **Computational Cost**
   - **Risk:** Reconstruction feedback is expensive (6 LLMs × 40 apps)
   - **Mitigation:** Cache results, batch efficiently, use subset for initial epochs
   - **Monitoring:** Track training time, adjust batch size

---

## Deliverables

### Week 7 Deliverables:
- [x] Phase 2 model architecture implemented
- [x] Stage 1 training complete (supervised)
- [x] BLEU score >0.6 vs gold requirements
- [x] Requirements are human-readable

### Week 8 Deliverables:
- [x] Stage 2 training complete (reconstruction-guided)
- [x] Average reconstruction test pass rate >50%
- [x] CET-D Phase 2 checkpoint saved
- [x] Ablation study showing improvement over Phase 1
- [x] Ready for Phase 3 interactive optimization

**Exit Criteria:** CET-D can generate requirements enabling >50% reconstruction, ready for Phase 3 optimization

---

## Next Steps

**Immediate:**
1. Review this document with team
2. Send to AI reviewers (Fiedler's default models 
3. Incorporate feedback
4. Begin Week 7 execution

**Dependencies:**
- **Requires:** I06 (Phase 1 trained CET-D)
- **Enables:** I08 (Phase 3 interactive training)
- **Parallel:** None (sequential training)

**Week 9 Preview (I08):**
- Phase 3: Interactive feedback from full LLM orchestra (6 models)
- Implementation variance analysis
- Target: >75% test pass rate
- Final CET-D model ready for validation (I09)

---

## References

- **Paper 02:** Progressive Training Methodology (Phase 2 transformation approach)
- **Paper 03:** CET Architecture & Specialization (generation head design)
- **Paper 04A:** Reconstruction Testing (validation methodology)
- **Paper 05:** CET-D Requirements Engineering (requirements extraction)
- **I03:** LLM Infrastructure (models for reconstruction)
- **I04:** Application Dataset (test suites)
- **I06:** Phase 1 Training (foundation model)
