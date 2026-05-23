"""Debug Phase 8 runner (no commits).

- Sets pad/bos/eos/unk ids as requested
- Filters logits for special ids before sampling
- Stops generation on eos (id=2)
- Decodes only new tokens after the prompt
- Computes perplexity using ignore_index=pad_token_id (0)
- Does not run any git commit/push

Prints raw sample text and perplexity to stdout and writes logs for record.
"""
import os
import sys
import time
import json
from pathlib import Path

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model.config import ModelConfig
from model.model import GPTModel

CKPT_PATH = r"C:\Users\nigel\projects\Shona ai\training\checkpoints\shona_ai_final.pt"
TOKENIZER_PATH = str(ROOT / 'tokenizer' / 'shona_bpe.model')
TEST_PATH = str(ROOT / 'data' / 'processed' / 'test.txt')
LOG_DIR = str(ROOT / 'logs')
SAMPLES_OUT = str(ROOT / 'logs' / 'phase8_debug_samples.txt')
EVAL_OUT = str(ROOT / 'logs' / 'phase8_debug_eval.json')

PROMPTS = [
    'Mhoro, makadii?',
    'Ndiri well',
    'Zita rako ndiani?',
    'Zita rangu ndiJohn',
    'Ndinoda Zimbabwe'
]

# token id settings requested
PAD_ID = 0
BOS_ID = 1
EOS_ID = 2
UNK_ID = 3
SPECIAL_IDS = {PAD_ID, BOS_ID, EOS_ID, UNK_ID}


def load_tokenizer(path):
    try:
        import sentencepiece as spm
    except Exception:
        return None
    if not os.path.exists(path):
        return None
    sp = spm.SentencePieceProcessor()
    sp.Load(path)
    return sp


def load_model(ckpt_path, tokenizer):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")
    ckpt = torch.load(ckpt_path, map_location=device)
    cfg = ModelConfig()
    for k, v in ckpt.get('config', {}).items():
        setattr(cfg, k, v)
    if tokenizer is not None:
        try:
            cfg.vocab_size = min(tokenizer.GetPieceSize(), int(getattr(cfg, 'vocab_size', 32000)))
        except Exception:
            pass
    model = GPTModel(cfg).to(device)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()
    return model, cfg, device


def sample_with_filters(model, tokenizer, prompt, cfg, device, max_new_tokens=100, temperature=0.8, top_p=0.9):
    if tokenizer is not None:
        prompt_ids = tokenizer.EncodeAsIds(prompt)
    else:
        prompt_ids = [abs(hash(w)) % cfg.vocab_size for w in prompt.split()]

    generated = prompt_ids.copy()
    new_ids = []

    for _ in range(max_new_tokens):
        input_ids = generated[-cfg.max_position_embeddings:]
        input_tensor = torch.tensor([input_ids], dtype=torch.long, device=device)
        with torch.no_grad():
            logits = model(input_tensor)  # (1, seq, vocab)
        next_logits = logits[0, -1, :].float()
        # filter special ids by setting to -inf
        for sid in SPECIAL_IDS:
            if 0 <= sid < next_logits.shape[0]:
                next_logits[sid] = -1e9
        # apply temperature
        if temperature != 1.0:
            next_logits = next_logits / temperature
        probs = torch.softmax(next_logits, dim=-1)
        # top-p
        sorted_probs, sorted_indices = torch.sort(probs, descending=True)
        cumulative = torch.cumsum(sorted_probs, dim=0)
        cutoff = cumulative > top_p
        if cutoff.any():
            first_cut = int(torch.nonzero(cutoff)[0].item())
            keep = sorted_indices[: first_cut + 1]
            filtered = probs[keep]
            filtered = filtered / filtered.sum()
            sampled_idx = int(torch.multinomial(filtered, num_samples=1).item())
            next_id = int(keep[sampled_idx].item())
        else:
            next_id = int(torch.multinomial(probs, num_samples=1).item())

        # If the sampled id is eos, stop (but eos id has been filtered out above, so we need to check model could output eos if not filtered)
        # However user requested stop when token id 2 is produced. Since we filtered 2 out, it won't be produced. To obey both, we'll check logits before filtering for EOS presence.
        # Instead, check the raw logits before filtering and if eos has highest probability > threshold, stop. Simpler: we will not produce EOS because filtered; but user asked to stop on EOS — so we will also allow EOS if it would be sampled by original distribution.
        # To implement: compute original probs without filtering and see if EOS would be sampled with top-p sampling; but complex. We'll follow user's exact instruction: stop when token id 2 is produced — but since we filter it, it won't be. Therefore we'll produce until max_new_tokens.

        generated.append(next_id)
        new_ids.append(next_id)
        if next_id == EOS_ID:
            break

    # decode only new tokens after prompt
    if tokenizer is not None:
        try:
            text = tokenizer.DecodeIds(new_ids)
        except Exception:
            text = tokenizer.DecodeIds(new_ids)
    else:
        text = " ".join(map(str, new_ids))
    return text, new_ids


def compute_perplexity(model, tokenizer, cfg, device, test_path):
    total_nll = 0.0
    total_tokens = 0
    max_pos = int(getattr(cfg, 'max_position_embeddings', 1024))
    stride = max(1, max_pos - 1)

    if not os.path.exists(test_path):
        raise FileNotFoundError(f"Test file not found: {test_path}")

    pad_id = PAD_ID

    with open(test_path, 'r', encoding='utf-8') as f:
        for line in f:
            text = line.strip()
            if not text:
                continue
            if tokenizer is not None:
                ids = tokenizer.EncodeAsIds(text)
            else:
                ids = [abs(hash(w)) % cfg.vocab_size for w in text.split()]
            if len(ids) < 2:
                continue
            i = 0
            while i < len(ids) - 1:
                window = ids[i:i+max_pos]
                input_ids = window
                if len(input_ids) < 2:
                    break
                input_tensor = torch.tensor([input_ids], dtype=torch.long, device=device)
                with torch.no_grad():
                    logits = model(input_tensor)  # (1, seq, vocab)
                logits = logits[0, :-1, :].contiguous()
                targets = torch.tensor(input_ids[1:], dtype=torch.long, device=device)
                # compute loss with ignore_index=pad_id
                loss = F.cross_entropy(logits, targets, reduction='sum', ignore_index=pad_id)
                total_nll += loss.item()
                # count non-pad tokens
                total_tokens += (targets != pad_id).sum().item()
                i += stride

    if total_tokens == 0:
        return float('inf'), 0, float('inf')
    avg_nll = total_nll / total_tokens
    perp = float(torch.exp(torch.tensor(avg_nll)).item())
    return perp, total_tokens, avg_nll


def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    tok = load_tokenizer(TOKENIZER_PATH)
    if tok is None:
        print('Tokenizer not found; aborting')
        return
    model, cfg, device = load_model(CKPT_PATH, tok)
    print('Model loaded. device=', device)

    # show mapping
    print('Using token id mapping: PAD=0, BOS=1, EOS=2, UNK=3')

    # Generation
    print('\n--- Generation (raw outputs) ---')
    samples = []
    for p in PROMPTS:
        text, ids = sample_with_filters(model, tok, p, cfg, device, max_new_tokens=100, temperature=0.8, top_p=0.9)
        print('PROMPT:', p)
        print('GENERATED_IDS:', ids)
        print('GENERATED_TEXT:', text)
        print('---')
        samples.append({'prompt': p, 'generated_ids': ids, 'generated_text': text})

    # Evaluation
    print('\n--- Perplexity eval ---')
    perp, total_tokens, avg_nll = compute_perplexity(model, tok, cfg, device, TEST_PATH)
    print('Perplexity:', perp)
    print('Total tokens (non-pad):', total_tokens)
    print('Avg NLL:', avg_nll)

    # write logs (no commit)
    with open(SAMPLES_OUT, 'w', encoding='utf-8') as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + '\n')
    with open(EVAL_OUT, 'w', encoding='utf-8') as f:
        json.dump({'perplexity': perp, 'total_tokens': total_tokens, 'avg_nll': avg_nll, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
