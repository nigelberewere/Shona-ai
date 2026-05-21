"""Generate using a model with expanded positional embeddings (larger context).

This script loads the final checkpoint, constructs a model with a larger
`max_position_embeddings` (e.g., 512), copies the checkpoint weights where
possible, expands positional embeddings by copying the trained positions into
the new embedding matrix, and then runs sampling generation.

Results are written to `logs/sample_generations_large_context.txt`.
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


def build_and_load_expanded_model(ckpt_path: str, tokenizer, new_max_pos: int = 512):
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
    cfg.max_position_embeddings = new_max_pos

    model = GPTModel(cfg).to(device)

    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")
    ckpt = torch.load(ckpt_path, map_location=device)
    old_state = ckpt['model_state_dict']

    model_state = model.state_dict()

    for k, v in old_state.items():
        if k not in model_state:
            continue
        if v.shape == model_state[k].shape:
            model_state[k] = v
            continue
        # handle positional embeddings expansion
        if 'pos_emb' in k or 'positional' in k:
            old_n = v.shape[0]
            new_n = model_state[k].shape[0]
            copy_n = min(old_n, new_n)
            model_state[k][:copy_n] = v[:copy_n]
            # leave remaining positions as initialized
            continue
        # handle token embedding vocab size differences
        if 'token_emb' in k or ('token' in k and v.ndim == model_state[k].ndim):
            # copy overlapping slice
            if v.ndim == 2:
                min0 = min(v.shape[0], model_state[k].shape[0])
                min1 = min(v.shape[1], model_state[k].shape[1])
                model_state[k][:min0, :min1] = v[:min0, :min1]
                continue
        # fallback: skip mismatched param

    model.load_state_dict(model_state)
    model.eval()
    return model, cfg, device


def top_k_filter(logits, k: int):
    if k <= 0:
        return logits
    values, _ = torch.topk(logits, k)
    min_value = values[-1]
    return torch.where(logits < min_value, torch.full_like(logits, -float('Inf')), logits)


def sample_generate(model, tokenizer, prompt: str, cfg: ModelConfig, device, max_new_tokens: int = 60, temperature: float = 1.0, top_k: int = 0, repetition_penalty: float = 1.0, frequency_penalty: float = 0.0):
    if tokenizer is not None:
        input_ids = tokenizer.EncodeAsIds(prompt)
    else:
        input_ids = [abs(hash(w)) % cfg.vocab_size for w in prompt.split()]

    # allow up to cfg.max_position_embeddings from the prompt
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
            # repetition penalty (HF-style)
            if repetition_penalty != 1.0:
                from collections import Counter
                counts = Counter(generated)
                for token_id, cnt in counts.items():
                    if token_id >= next_logits.size(0):
                        continue
                    if next_logits[token_id] < 0:
                        next_logits[token_id] = next_logits[token_id] * repetition_penalty
                    else:
                        next_logits[token_id] = next_logits[token_id] / repetition_penalty
            # frequency penalty: subtract scaled count
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
    # expand context to 512
    model, cfg, device = build_and_load_expanded_model(ckpt_path, tokenizer, new_max_pos=512)

    prompts: List[str] = [
        'mhoro',
        'maswera sei',
        'zita unonzi ani',
    ]

    temperature = 0.9
    top_k = 40
    samples_per_prompt = 3
    repetition_penalty = 1.2
    frequency_penalty = 0.6

    os.makedirs('logs', exist_ok=True)
    out_path = os.path.join('logs', 'sample_generations_large_context.txt')
    start = time.time()
    with open(out_path, 'w', encoding='utf-8') as f:
        for p in prompts:
            f.write(f'PROMPT: {p}\n')
            print(f'PROMPT: {p}')
            for i in range(samples_per_prompt):
                text = sample_generate(model, tokenizer, p, cfg, device, max_new_tokens=120, temperature=temperature, top_k=top_k, repetition_penalty=repetition_penalty, frequency_penalty=frequency_penalty)
                line = f'SAMPLE {i+1}: {text}\n'
                print(line[:1000])
                f.write(line)
            f.write('---\n')
    elapsed = time.time() - start
    print(f"Saved large-context sampling generations to {out_path} (time={elapsed:.2f}s)")


if __name__ == '__main__':
    main()
