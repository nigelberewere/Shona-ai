"""Quick parameter sweep (small grid) for faster feedback.

Runs a small set of sampling params and writes outputs to
`logs/quick_sweep_results.txt` and a short `logs/quick_sweep_best.txt`.
"""

import os
import time
from itertools import product
from collections import Counter
from typing import List

import sys
# Ensure repo root is on PYTHONPATH so local package imports work
sys.path.insert(0, os.getcwd())

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
    cfg.hidden_size = 256
    cfg.num_layers = 4
    cfg.num_heads = 8
    cfg.intermediate_size = 1024
    cfg.max_position_embeddings = new_max_pos

    model = GPTModel(cfg).to(device)
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


def sample_once(model, tokenizer, prompt: str, cfg: ModelConfig, device, max_new_tokens: int, temperature: float, top_k: int, repetition_penalty: float, frequency_penalty: float):
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
    return 1.0 - (unique / total)


def main():
    ckpt_path = 'training/pilot_checkpoints/ckpt_final.pt'
    tokenizer = load_tokenizer()
    model, cfg, device = build_model(ckpt_path, tokenizer, new_max_pos=512)

    prompts = ['mhoro', 'maswera sei', 'zita unonzi ani']
    temperatures = [1.2, 1.4, 1.6]
    top_ks = [50]
    rep_pens = [1.3]
    frequency_penalty = 0.6

    samples_per_prompt = 2
    max_new_tokens = 60

    out_path = 'logs/quick_sweep_results.txt'
    best_path = 'logs/quick_sweep_best.txt'
    os.makedirs('logs', exist_ok=True)
    results = []
    start = time.time()
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f'QUICK SWEEP START {time.ctime()}\n')
        for temp, k, rp in product(temperatures, top_ks, rep_pens):
            f.write(f'=== PARAMS temp={temp} top_k={k} rep_pen={rp} freq_pen={frequency_penalty} ===\n')
            for p in prompts:
                for s in range(samples_per_prompt):
                    toks, text = sample_once(model, tokenizer, p, cfg, device, max_new_tokens, temp, k, rp, frequency_penalty)
                    score = repetition_score(toks)
                    f.write(f'PROMPT: {p} SAMPLE {s+1} SCORE {score:.4f}\n')
                    f.write(text + '\n')
                    f.write('---\n')
                    results.append((score, (temp, k, rp), p, text))
    results.sort(key=lambda x: x[0])
    with open(best_path, 'w', encoding='utf-8') as bf:
        bf.write('BEST QUICK SAMPLES\n')
        for r in results[:6]:
            score, combo, prompt, text = r
            bf.write(f'SCORE={score:.4f} PARAMS={combo} PROMPT={prompt}\n')
            bf.write(text + '\n')
            bf.write('---\n')
    elapsed = time.time() - start
    print(f'Quick sweep done in {elapsed:.1f}s. Results: {out_path}, best: {best_path}')


if __name__ == '__main__':
    main()
