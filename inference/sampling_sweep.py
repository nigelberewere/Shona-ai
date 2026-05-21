"""Parameter sweep for sampling hyperparameters.

Runs combinations of temperature, top_k, and repetition_penalty (frequency_penalty fixed)
using the expanded-context model, saves all outputs to `logs/sweep_results.txt`, and
reports a simple repetition score per sample so we can pick the least-repetitive outputs.
"""

import os
import time
from itertools import product
from collections import Counter
from typing import List, Tuple

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


def build_model(ckpt_path: str, tokenizer, new_max_pos: int = 512):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    cfg = ModelConfig()
    if tokenizer is not None:
        cfg.vocab_size = min(tokenizer.GetPieceSize(), 32000)
    else:
        cfg.vocab_size = 32000
    # match the smoke-training model size so checkpoints can be loaded
    cfg.hidden_size = 128
    cfg.num_layers = 2
    cfg.num_heads = 8
    cfg.intermediate_size = 512
    cfg.max_position_embeddings = new_max_pos

    model = GPTModel(cfg).to(device)

    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(ckpt_path)
    ckpt = torch.load(ckpt_path, map_location=device)
    old_state = ckpt.get('model_state_dict', ckpt)
    model_state = model.state_dict()
    for k, v in old_state.items():
        if k in model_state and v.shape == model_state[k].shape:
            model_state[k] = v
        elif 'pos_emb' in k and k in model_state:
                old_n = v.shape[0]
                new_n = model_state[k].shape[0]
                copy_n = min(old_n, new_n)
                # handle possible hidden-size mismatch (pos_emb may be [pos, hidden])
                if v.ndim == 2 and model_state[k].ndim == 2:
                    min_hidden = min(v.shape[1], model_state[k].shape[1])
                    model_state[k][:copy_n, :min_hidden] = v[:copy_n, :min_hidden]
                else:
                    model_state[k][:copy_n] = v[:copy_n]
        elif 'token_emb' in k and k in model_state and v.ndim == 2:
            min0 = min(v.shape[0], model_state[k].shape[0])
            min1 = min(v.shape[1], model_state[k].shape[1])
            model_state[k][:min0, :min1] = v[:min0, :min1]
    model.load_state_dict(model_state)
    model.eval()
    return model, cfg, device


def top_k_filter(logits, k: int):
    if k <= 0:
        return logits
    values, _ = torch.topk(logits, k)
    min_value = values[-1]
    return torch.where(logits < min_value, torch.full_like(logits, -float('Inf')), logits)


def top_p_filter(logits, p: float):
    if p is None or p <= 0.0 or p >= 1.0:
        return logits
    sorted_logits, sorted_idx = torch.sort(logits, descending=True)
    probs = F.softmax(sorted_logits, dim=-1)
    cumprobs = torch.cumsum(probs, dim=-1)
    # tokens to remove (those with cumulative prob > p)
    remove_mask = cumprobs > p
    # ensure at least the top token remains
    remove_mask[0] = False
    tokens_to_remove = sorted_idx[remove_mask]
    filtered = logits.clone()
    if tokens_to_remove.numel() > 0:
        filtered[tokens_to_remove] = -float('Inf')
    return filtered


def sample_once(model, tokenizer, prompt: str, cfg: ModelConfig, device, max_new_tokens: int, temperature: float, top_k: int, top_p: float, repetition_penalty: float, frequency_penalty: float) -> Tuple[List[int], str]:
    if tokenizer is not None:
        input_ids = tokenizer.EncodeAsIds(prompt)
    else:
        input_ids = [abs(hash(w)) % cfg.vocab_size for w in prompt.split()]
    generated = input_ids[-cfg.max_position_embeddings:]
    for _ in range(max_new_tokens):
        input_tensor = torch.tensor([generated[-cfg.max_position_embeddings:]], dtype=torch.long, device=device)
        with torch.no_grad():
            logits = model(input_tensor)
            next_logits = logits[0, -1, :]
            if temperature != 1.0:
                next_logits = next_logits / temperature
            if top_k > 0:
                next_logits = top_k_filter(next_logits, top_k)
            if top_p is not None and top_p > 0.0 and top_p < 1.0:
                next_logits = top_p_filter(next_logits, top_p)
            if repetition_penalty != 1.0:
                counts = Counter(generated)
                for tid, cnt in counts.items():
                    if tid >= next_logits.size(0):
                        continue
                    if next_logits[tid] < 0:
                        next_logits[tid] = next_logits[tid] * repetition_penalty
                    else:
                        next_logits[tid] = next_logits[tid] / repetition_penalty
            if frequency_penalty != 0.0:
                counts = Counter(generated)
                for tid, cnt in counts.items():
                    if tid >= next_logits.size(0):
                        continue
                    next_logits[tid] = next_logits[tid] - float(frequency_penalty) * float(cnt)
            probs = F.softmax(next_logits, dim=-1)
            next_id = int(torch.multinomial(probs, num_samples=1).item())
        generated.append(next_id)
    if tokenizer is not None:
        text = tokenizer.DecodeIds(generated)
    else:
        text = " ".join(map(str, generated))
    return generated, text


def repetition_score(token_ids: List[int]) -> float:
    if not token_ids:
        return 1.0
    cnt = Counter(token_ids)
    total = len(token_ids)
    unique = len(cnt)
    # lower is better (less repetition)
    return 1.0 - (unique / total)


def main():
    ckpt_path = 'training/pilot_checkpoints/ckpt_final.pt'
    tokenizer = load_tokenizer()
    model, cfg, device = build_model(ckpt_path, tokenizer, new_max_pos=512)

    prompts = ['mhoro', 'maswera sei', 'zita unonzi ani']

    temperatures = [1.2, 1.4, 1.6]
    top_ks = [20, 50, 80]
    rep_pens = [1.1, 1.3, 1.5]
    frequency_penalty = 0.6

    samples_per_prompt = 2
    max_new_tokens = 80

    out_path = 'logs/sweep_results.txt'
    os.makedirs('logs', exist_ok=True)
    start = time.time()
    best_samples = []  # (score, combo, prompt, text)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f'SWEEP START {time.ctime()}\n')
        for temp, k, rp in product(temperatures, top_ks, rep_pens):
            f.write(f'=== PARAMS temp={temp} top_k={k} rep_pen={rp} freq_pen={frequency_penalty} ===\n')
            print(f'Running temp={temp} top_k={k} rep_pen={rp}')
            for p in prompts:
                for s in range(samples_per_prompt):
                    toks, text = sample_once(model, tokenizer, p, cfg, device, max_new_tokens, temp, k, rp, frequency_penalty)
                    score = repetition_score(toks)
                    f.write(f'PROMPT: {p} SAMPLE {s+1} SCORE {score:.4f}\n')
                    f.write(text + '\n')
                    f.write('---\n')
                    best_samples.append((score, (temp, k, rp), p, text))
    elapsed = time.time() - start
    # sort best by lowest repetition score
    best_samples.sort(key=lambda x: x[0])
    summary_path = 'logs/sweep_best_samples.txt'
    with open(summary_path, 'w', encoding='utf-8') as sf:
        sf.write('BEST SAMPLES (lowest repetition score first)\n')
        for entry in best_samples[:10]:
            score, combo, prompt, text = entry
            sf.write(f'SCORE={score:.4f} PARAMS={combo} PROMPT={prompt}\n')
            sf.write(text + '\n')
            sf.write('---\n')
    print(f'Sweep complete in {elapsed:.1f}s. Results: {out_path}, best: {summary_path}')


if __name__ == '__main__':
    main()
