"""Reconcile perplexity: run trainer.evaluate identically and re-run generation allowing EOS.

- Uses training.trainer.evaluate on validation tensor loaded with seq_len=256+1
- Then runs generation where only pad/bos/unk are filtered; EOS (2) allowed to be sampled and stops generation
- Prints trainer code snippet used and the numeric results
"""
import os
import sys
from pathlib import Path
import json
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import torch
from training.dataset import load_dataset_from_file
from training.trainer import evaluate as trainer_evaluate
from model.config import ModelConfig
from model.model import GPTModel

CKPT_PATH = r"C:\Users\nigel\projects\Shona ai\training\checkpoints\shona_ai_final.pt"
TOKENIZER_PATH = str(ROOT / 'tokenizer' / 'shona_bpe.model')
VALID_PATH = str(ROOT / 'data' / 'processed' / 'valid.txt')
LOG_DIR = str(ROOT / 'logs')

PAD_ID = 0
BOS_ID = 1
EOS_ID = 2
UNK_ID = 3

print('--- Running trainer.evaluate on validation set ---')
# Load tokenizer
try:
    import sentencepiece as spm
    sp = spm.SentencePieceProcessor()
    sp.Load(TOKENIZER_PATH)
except Exception as e:
    sp = None

# Load validation tensor with seq_len=256+1 per trainer
seq_len = 256
seq_len_dataset = seq_len + 1
if not os.path.exists(VALID_PATH):
    raise FileNotFoundError(f'Validation file not found: {VALID_PATH}')
val_tensor, tokenizer = load_dataset_from_file(VALID_PATH, seq_len=seq_len_dataset, max_samples=None)
print('val_tensor shape:', val_tensor.size())

# Load model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
ckpt = torch.load(CKPT_PATH, map_location=device)
cfg = ModelConfig()
for k, v in ckpt.get('config', {}).items():
    setattr(cfg, k, v)
if sp is not None:
    cfg.vocab_size = min(sp.GetPieceSize(), int(getattr(cfg, 'vocab_size', 32000)))
model = GPTModel(cfg).to(device)
model.load_state_dict(ckpt['model_state_dict'])

# Run trainer's evaluate (batch_size=8 default)
avg_loss, perplexity = trainer_evaluate(model, val_tensor, cfg, device, batch_size=8)
print(f'Trainer evaluate -> avg_loss={avg_loss:.6f}, perplexity={perplexity:.6f}')

print('\n--- Re-run generation allowing EOS (filter only pad,bos,unk) ---')
# Generation function: allow EOS to be sampled; filter pad,bos,unk
PROMPTS = ['Mhoro, makadii?','Ndiri well','Zita rako ndiani?','Zita rangu ndiJohn','Ndinoda Zimbabwe']

model.eval()
for p in PROMPTS:
    if sp is not None:
        prompt_ids = sp.EncodeAsIds(p)
    else:
        prompt_ids = [abs(hash(w)) % cfg.vocab_size for w in p.split()]
    generated = prompt_ids.copy()
    new_ids = []
    for _ in range(200):
        input_ids = generated[-cfg.max_position_embeddings:]
        input_tensor = torch.tensor([input_ids], dtype=torch.long, device=device)
        with torch.no_grad():
            logits = model(input_tensor)
        next_logits = logits[0, -1, :].float()
        # filter pad,bos,unk only
        for sid in [PAD_ID, BOS_ID, UNK_ID]:
            if 0 <= sid < next_logits.shape[0]:
                next_logits[sid] = -1e9
        # temperature and top-p
        temperature = 0.8
        top_p = 0.9
        next_logits = next_logits / temperature
        probs = torch.softmax(next_logits, dim=-1)
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

        generated.append(next_id)
        new_ids.append(next_id)
        if next_id == EOS_ID:
            break
    # decode new_ids
    if sp is not None:
        text = sp.DecodeIds(new_ids)
    else:
        text = ' '.join(map(str, new_ids))
    print('PROMPT:', p)
    print('GENERATED_IDS:', new_ids)
    print('GENERATED_TEXT:', text)
    print('---')

print('\nDone. No commits made.')
