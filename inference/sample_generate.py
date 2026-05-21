"""Sample generation using the final pilot checkpoint.

Loads `training/pilot_checkpoints/ckpt_final.pt`, the SentencePiece tokenizer
at `tokenizer/shona_bpe.model`, and runs greedy generation for a few prompts.
Saves outputs to `logs/sample_generations.txt` and prints them.
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
    # Match pilot_run architecture
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


def greedy_generate(model, tokenizer, prompt: str, cfg: ModelConfig, device, max_new_tokens: int = 32) -> str:
    if tokenizer is not None:
        input_ids = tokenizer.EncodeAsIds(prompt)
    else:
        input_ids = [abs(hash(w)) % cfg.vocab_size for w in prompt.split()]

    # keep only last positions that fit
    seq = input_ids[-cfg.max_position_embeddings:]
    generated = seq.copy()

    for _ in range(max_new_tokens):
        input_tensor = torch.tensor([generated[-cfg.max_position_embeddings:]], dtype=torch.long, device=device)
        with torch.no_grad():
            logits = model(input_tensor)  # (1, seq, vocab)
            next_logits = logits[0, -1, :]
            next_id = int(torch.argmax(next_logits).item())
        generated.append(next_id)

    if tokenizer is not None:
        try:
            text = tokenizer.DecodeIds(generated)
        except Exception:
            # Fallback to piece-wise join
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

    os.makedirs('logs', exist_ok=True)
    out_path = os.path.join('logs', 'sample_generations.txt')
    start = time.time()
    with open(out_path, 'w', encoding='utf-8') as f:
        for p in prompts:
            text = greedy_generate(model, tokenizer, p, cfg, device, max_new_tokens=40)
            line = f'PROMPT: {p}\nGENERATED: {text}\n---\n'
            print(line)
            f.write(line)
    elapsed = time.time() - start
    print(f"Saved generations to {out_path} (time={elapsed:.2f}s)")


if __name__ == '__main__':
    main()
