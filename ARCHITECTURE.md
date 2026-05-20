# SHONA AI — MODEL ARCHITECTURE
## Reference for agents working on Phase 5

---

## Decision: Decoder-Only Transformer (GPT-style)

**Rationale:** Decoder-only models excel at text generation, continuation, and instruction following — the primary use cases for Shona AI. They also require simpler training (next-token prediction only) which is ideal for low-resource languages.

---

## Model Variants

### Shona AI v0.1 Small (Development & Validation)
Use this first. Trains fast. Used to validate the data pipeline and training loop before committing GPU time.

```python
ModelConfig(
    vocab_size=32000,
    hidden_size=512,
    num_hidden_layers=8,
    num_attention_heads=8,
    intermediate_size=2048,
    max_position_embeddings=1024,
    hidden_dropout_prob=0.1,
    attention_probs_dropout_prob=0.1,
    initializer_range=0.02,
    layer_norm_eps=1e-12,
    use_rotary_embeddings=True,
    use_flash_attention=True,  # if available
    tie_word_embeddings=True,
)
# Parameters: ~25M
# Training time estimate: ~6 hours on single A100 with 10M tokens
```

### Shona AI v1.0 Base (Production)
Build this after v0.1 validates. This is the actual release model.

```python
ModelConfig(
    vocab_size=32000,
    hidden_size=768,
    num_hidden_layers=12,
    num_attention_heads=12,
    intermediate_size=3072,
    max_position_embeddings=2048,
    hidden_dropout_prob=0.1,
    attention_probs_dropout_prob=0.1,
    initializer_range=0.02,
    layer_norm_eps=1e-12,
    use_rotary_embeddings=True,
    use_flash_attention=True,
    tie_word_embeddings=True,
)
# Parameters: ~117M
# Training time estimate: ~48 hours on single A100 with 50M tokens
```

---

## Architecture Choices Explained

### Rotary Positional Embeddings (RoPE)
- Better than learned absolute positions for generalization to longer sequences
- Used by LLaMA, Mistral — proven at scale
- Implementation: apply rotation to Q and K in attention, leave V alone

### Pre-Layer Norm
- Apply layer norm BEFORE attention/FFN (not after)
- More stable training for low-resource settings
- Matches GPT-NeoX, LLaMA convention

### SwiGLU Activation
- Use SwiGLU in FFN: `SwiGLU(x) = Swish(W1·x) ⊗ (W3·x)`
- Better than GELU for language modeling
- Adjust intermediate_size to 8/3 * hidden_size if using SwiGLU

### Grouped Query Attention (GQA) — Optional for v1.0
- If GPU memory is tight, use GQA with 4 KV heads instead of 12
- Reduces memory by 3x at inference time

### Weight Tying
- Tie input embedding weights to output projection
- Reduces parameters, often improves perplexity for small models

---

## Training Hyperparameters

```yaml
# training/config.yaml

model:
  variant: v0.1-small  # change to v1.0-base for production

training:
  batch_size: 32
  gradient_accumulation_steps: 4  # effective batch = 128
  learning_rate: 3.0e-4
  lr_schedule: cosine
  warmup_steps: 2000
  max_steps: 100000
  weight_decay: 0.1
  beta1: 0.9
  beta2: 0.95
  epsilon: 1.0e-8
  gradient_clip: 1.0
  label_smoothing: 0.1

  # Mixed precision
  fp16: false
  bf16: true  # if A100/H100 available; else use fp16

  # Checkpointing
  save_every_steps: 1000
  eval_every_steps: 500
  keep_last_n_checkpoints: 5

  # Logging
  log_every_steps: 50
  wandb_project: "shona-ai"
  wandb_run_name: "v0.1-small-run1"

data:
  max_seq_length: 1024
  pack_sequences: true  # pack short docs into one sequence
  seed: 42

output:
  checkpoint_dir: "checkpoints/"
  log_dir: "logs/"
```

---

## Model Implementation Skeleton

```python
# model/config.py
from dataclasses import dataclass

@dataclass
class ShonaAIConfig:
    vocab_size: int = 32000
    hidden_size: int = 512
    num_hidden_layers: int = 8
    num_attention_heads: int = 8
    intermediate_size: int = 2048
    max_position_embeddings: int = 1024
    hidden_dropout_prob: float = 0.1
    attention_dropout_prob: float = 0.1
    initializer_range: float = 0.02
    layer_norm_eps: float = 1e-12
    use_rope: bool = True
    tie_word_embeddings: bool = True
    pad_token_id: int = 0
    bos_token_id: int = 1
    eos_token_id: int = 2
```

---

## Why NOT fine-tune an existing model?

Agents should be aware of this decision:

**Fine-tuning option** (XGLM, BLOOM): Faster start but:
- Pre-trained vocabulary is inefficient for Shona (high fertility, wasted tokens)
- Embedding space biased toward high-resource languages
- Hard to claim "native Shona model"

**Training from scratch** (our approach):
- Custom tokenizer optimized for Shona morphology
- Every parameter learns from Shona-first data
- True low-resource best practice
- Yields a genuinely Shona-native model

If data proves insufficient (<5M tokens), fallback plan: fine-tune XGLM-564M with our Shona tokenizer as a vocabulary-extended adapter.

---

*Architecture Guide v1.0 | Shona AI Project*
