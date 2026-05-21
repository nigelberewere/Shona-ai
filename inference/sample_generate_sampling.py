"""Stochastic sampling generation using final pilot checkpoint.

Supports `temperature` and `top_k` sampling; writes multiple samples per prompt
to `logs/sample_generations_sampling.txt`.
"""

import os
import time
from typing import List

import torch
import torch.nn.functional as F

from model.config import ModelConfig
from model.model import GPTModel


def load_tokenizer(path: str = 'tokenizer/shona_bpe.model'):
    try:
        import sentencepiece as spm
    except Exception:
        return None
    if not os.path.exists(path):
        return None
    sp = spm.SentencePieceProcessor()
    sp.Load(path)
    return sp


def load_model(ckpt_path: str, tokenizer):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    cfg = ModelConfig()
    if tokenizer is not None:
        cfg.vocab_size = min(tokenizer.GetPieceSize(), 32000)
    else:
        cfg.vocab_size = 32000
    cfg.hidden_size = 256
    cfg.num_layers = 4
    cfg.num_heads = 8
    cfg.intermediate_size = 1024
    cfg.max_position_embeddings = 128

    model = GPTModel(cfg).to(device)
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")
    ckpt = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()
    return model, cfg, device


def top_k_filter(logits, k: int):
    if k <= 0:
        return logits
    values, _ = torch.topk(logits, k)
    min_value = values[-1]
    return torch.where(logits < min_value, torch.full_like(logits, -float('Inf')), logits)


def top_p_filter(logits, p: float):
    """Nucleus (top-p) filtering: keep smallest set of tokens with cumulative prob >= p."""
    if p is None or p <= 0.0 or p >= 1.0:
        return logits
    sorted_logits, sorted_idx = torch.sort(logits, descending=True)
    probs = F.softmax(sorted_logits, dim=-1)
    cumprobs = torch.cumsum(probs, dim=-1)
    # mask tokens with cumulative prob above p
    cutoff = cumprobs > p
    # ensure at least one token kept
    cutoff[0] = False
    mask = cutoff.scatter(0, sorted_idx, cutoff).to(logits.dtype)
    return torch.where(mask > 0, torch.full_like(logits, -float('Inf')), logits)


def sample_generate(model, tokenizer, prompt: str, cfg: ModelConfig, device, max_new_tokens: int = 40, temperature: float = 1.0, top_k: int = 0, top_p: float = None, repetition_penalty: float = 1.0, frequency_penalty: float = 0.0):
    if tokenizer is not None:
        input_ids = tokenizer.EncodeAsIds(prompt)
    else:
        input_ids = [abs(hash(w)) % cfg.vocab_size for w in prompt.split()]

    seq = input_ids[-cfg.max_position_embeddings:]
    generated = seq.copy()

    for _ in range(max_new_tokens):
        input_tensor = torch.tensor([generated[-cfg.max_position_embeddings:]], dtype=torch.long, device=device)
        with torch.no_grad():
            logits = model(input_tensor)
            next_logits = logits[0, -1, :]
            if temperature != 1.0:
                next_logits = next_logits / temperature
            if top_k > 0:
                next_logits = top_k_filter(next_logits, top_k)
            # apply nucleus (top-p) filtering if requested
            if top_p is not None and top_p > 0.0 and top_p < 1.0:
                next_logits = top_p_filter(next_logits, top_p)
            # apply repetition penalty (HuggingFace-style)
            if repetition_penalty != 1.0:
                # count occurrences in generated so far
                from collections import Counter

                counts = Counter(generated)
                for token_id, cnt in counts.items():
                    if token_id >= next_logits.size(0):
                        continue
                    # HF's repetition penalty uses division or multiplication depending on logit sign
                    if next_logits[token_id] < 0:
                        next_logits[token_id] = next_logits[token_id] * repetition_penalty
                    else:
                        next_logits[token_id] = next_logits[token_id] / repetition_penalty
            # apply simple frequency penalty (subtract proportional to previous frequency)
            if frequency_penalty != 0.0:
                from collections import Counter

                counts = Counter(generated)
                for token_id, cnt in counts.items():
                    if token_id >= next_logits.size(0):
                        continue
                    next_logits[token_id] = next_logits[token_id] - float(frequency_penalty) * float(cnt)
            probs = F.softmax(next_logits, dim=-1)
            next_id = int(torch.multinomial(probs, num_samples=1).item())
        generated.append(next_id)

    if tokenizer is not None:
        text = tokenizer.DecodeIds(generated)
    else:
        text = " ".join(map(str, generated))
    return text


def main():
    ckpt_path = 'training/pilot_checkpoints/ckpt_final.pt'
    tokenizer = load_tokenizer()
    model, cfg, device = load_model(ckpt_path, tokenizer)

    prompts: List[str] = [
        'Ndiri kuenda kumusika',
        'Rudo rwaMwari',
        'Nhasi zuva rakanaka',
    ]

    temperature = 0.8
    top_k = 50
    samples_per_prompt = 3
    # diversity penalties
    repetition_penalty = 1.2  # >1.0 penalizes repeating tokens
    frequency_penalty = 0.6   # subtract proportional to token frequency

    os.makedirs('logs', exist_ok=True)
    out_path = os.path.join('logs', 'sample_generations_sampling.txt')
    start = time.time()
    with open(out_path, 'w', encoding='utf-8') as f:
        for p in prompts:
            f.write(f'PROMPT: {p}\n')
            print(f'PROMPT: {p}')
            for i in range(samples_per_prompt):
                text = sample_generate(model, tokenizer, p, cfg, device, max_new_tokens=60, temperature=temperature, top_k=top_k, repetition_penalty=repetition_penalty, frequency_penalty=frequency_penalty)
                line = f'SAMPLE {i+1}: {text}\n'
                print(line)
                f.write(line)
            f.write('---\n')
    elapsed = time.time() - start
    print(f"Saved sampling generations to {out_path} (time={elapsed:.2f}s)")


if __name__ == '__main__':
    main()
