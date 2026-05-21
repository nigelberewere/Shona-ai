"""Generate with enlarged context by resizing positional embeddings.

This script loads the final pilot checkpoint, creates a model with a larger
`max_position_embeddings` (default 512), copies existing positional weights
into the new embedding matrix, and runs stochastic sampling.
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


def build_model_with_resized_pos(ckpt_path: str, new_max_pos: int = 512):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Load checkpoint to inspect vocab size
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")
    ckpt = torch.load(ckpt_path, map_location='cpu')
    state = ckpt.get('model_state_dict', ckpt)

    # infer vocab from token embedding in checkpoint
    token_key = 'embeddings.token_emb.weight'
    if token_key in state:
        vocab_size = state[token_key].shape[0]
    else:
        vocab_size = 32000

    cfg = ModelConfig()
    cfg.vocab_size = min(int(vocab_size), 32000)
    cfg.hidden_size = 256
    cfg.num_layers = 4
    cfg.num_heads = 8
    cfg.intermediate_size = 1024
    cfg.max_position_embeddings = new_max_pos

    model = GPTModel(cfg).to(device)

    # load model state, copying positional embeddings where possible
    model_state = model.state_dict()
    loaded = {}
    for k, v in state.items():
        if k in model_state and v.shape == model_state[k].shape:
            loaded[k] = v
        elif k == 'embeddings.pos_emb.weight':
            # resize: copy prefix rows
            old = v
            new = model_state[k]
            n_copy = min(old.shape[0], new.shape[0])
            new[:n_copy] = old[:n_copy]
            loaded[k] = new
        elif k == 'embeddings.token_emb.weight' and v.shape[0] != model_state[k].shape[0]:
            # token vocab mismatch: copy common rows
            old = v
            new = model_state[k]
            n_copy = min(old.shape[0], new.shape[0])
            new[:n_copy] = old[:n_copy]
            loaded[k] = new
        # else: skip mismatched keys

    model_state.update(loaded)
    model.load_state_dict(model_state)
    model.eval()
    return model, cfg, device


def top_k_filter(logits, k: int):
    if k <= 0:
        return logits
    values, _ = torch.topk(logits, k)
    min_value = values[-1]
    return torch.where(logits < min_value, torch.full_like(logits, -float('Inf')), logits)


def sample_generate(model, tokenizer, prompt: str, cfg: ModelConfig, device, max_new_tokens: int = 100, temperature: float = 1.0, top_k: int = 50):
    if tokenizer is not None:
        input_ids = tokenizer.EncodeAsIds(prompt)
    else:
        input_ids = [abs(hash(w)) % cfg.vocab_size for w in prompt.split()]

    # provide longer context by repeating prompt if needed
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
    model, cfg, device = build_model_with_resized_pos(ckpt_path, new_max_pos=512)

    prompts: List[str] = [
        'Ndiri kuenda kumusika',
        'Rudo rwaMwari',
        'Nhasi zuva rakanaka',
    ]

    temperature = 0.9
    top_k = 80
    samples_per_prompt = 3

    os.makedirs('logs', exist_ok=True)
    out_path = os.path.join('logs', 'sample_generations_longcontext.txt')
    start = time.time()
    with open(out_path, 'w', encoding='utf-8') as f:
        for p in prompts:
            f.write(f'PROMPT: {p}\n')
            print(f'PROMPT: {p}')
            for i in range(samples_per_prompt):
                text = sample_generate(model, tokenizer, p, cfg, device, max_new_tokens=120, temperature=temperature, top_k=top_k)
                line = f'SAMPLE {i+1}: {text}\n'
                print(line)
                f.write(line)
            f.write('---\n')
    elapsed = time.time() - start
    print(f"Saved long-context sampling generations to {out_path} (time={elapsed:.2f}s)")


if __name__ == '__main__':
    main()
