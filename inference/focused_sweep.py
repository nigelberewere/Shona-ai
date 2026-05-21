"""Focused sampling sweep around best-known params.

Runs a narrower grid around the current winner: temp in [1.4, 1.6, 1.8],
top_k in [40, 50, 60], rep_pen in [1.4, 1.5, 1.6], top_p in [None, 0.9].
Saves full outputs to `logs/focused_sweep_results.txt` and top-ranked samples to
`logs/focused_sweep_best.txt`.
"""
import os
import time
from itertools import product
from typing import List, Tuple

import sys
sys.path.insert(0, os.getcwd())

from inference import sampling_sweep as ss


def main():
    ckpt_path = os.environ.get('FOCUSED_SWEEP_CKPT', 'training/checkpoint_real_smoke.pt')
    tokenizer = ss.load_tokenizer()
    model, cfg, device = ss.build_model(ckpt_path, tokenizer, new_max_pos=512)

    prompts = ['mhoro', 'maswera sei', 'zita unonzi ani']
    temperatures = [1.4, 1.6, 1.8]
    top_ks = [40, 50, 60]
    rep_pens = [1.4, 1.5, 1.6]
    top_ps = [None, 0.9]
    frequency_penalty = 0.6

    samples_per_prompt = 3
    max_new_tokens = 80

    os.makedirs('logs', exist_ok=True)
    out_path = 'logs/focused_sweep_results.txt'
    start = time.time()
    entries = []  # (score, combo, prompt, text)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f'FOCUSED SWEEP START {time.ctime()}\n')
        for temperature, k, rp, top_p in product(temperatures, top_ks, rep_pens, top_ps):
            combo = (temperature, k, rp, top_p)
            f.write(f'=== PARAMS temp={temperature} top_k={k} top_p={top_p} rep_pen={rp} freq_pen={frequency_penalty} ===\n')
            print(f'Running temp={temperature} top_k={k} top_p={top_p} rep_pen={rp}')
            for p in prompts:
                for s in range(samples_per_prompt):
                    toks, text = ss.sample_once(model, tokenizer, p, cfg, device, max_new_tokens, temperature, k, top_p, rp, frequency_penalty)
                    score = ss.repetition_score(toks)
                    f.write(f'PROMPT: {p} SAMPLE {s+1} SCORE {score:.4f}\n')
                    f.write(text + '\n')
                    f.write('---\n')
                    entries.append((score, combo, p, text))
    elapsed = time.time() - start
    entries.sort(key=lambda x: x[0])
    summary_path = 'logs/focused_sweep_best.txt'
    with open(summary_path, 'w', encoding='utf-8') as sf:
        sf.write('BEST SAMPLES (lowest repetition score first)\n')
        for entry in entries[:20]:
            score, combo, prompt, text = entry
            sf.write(f'SCORE={score:.4f} PARAMS={combo} PROMPT={prompt}\n')
            sf.write(text + '\n')
            sf.write('---\n')
    print(f'Focused sweep complete in {elapsed:.1f}s. Results: {out_path}, best: {summary_path}')


if __name__ == '__main__':
    main()
