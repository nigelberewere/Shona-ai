"""Training utilities for Phase 6 smoke runs.

This script runs a small real-data smoke training using `data/processed/train.txt`.
Falls back to synthetic data if tokenizer or data is missing.
"""

import os
import time
import torch
import torch.nn as nn
import torch.optim as optim
from .dataset import load_dataset_from_file
from model.config import ModelConfig
from model.model import GPTModel


def train_real_smoke(steps: int = 100, log_interval: int = 10):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    data_path = 'data/processed/train.txt'
    seq_len = 16
    max_samples = 256

    if os.path.exists(data_path):
        data_tensor, tokenizer = load_dataset_from_file(data_path, seq_len=seq_len, max_samples=max_samples)
        if tokenizer is not None:
            vocab_size = tokenizer.GetPieceSize()
        else:
            vocab_size = 32000
        print(f"Loaded {data_tensor.size(0)} samples from {data_path}; vocab_size={vocab_size}; tokenizer_present={tokenizer is not None}")
    else:
        print(f"Data file {data_path} not found — falling back to synthetic batches.")
        data_tensor = None
        vocab_size = 4096

    cfg = ModelConfig()
    cfg.vocab_size = min(vocab_size, 32000)
    cfg.hidden_size = 128
    cfg.num_layers = 2
    cfg.num_heads = 8
    cfg.intermediate_size = 512
    cfg.max_position_embeddings = 64

    model = GPTModel(cfg).to(device)
    model.train()

    optimizer = optim.AdamW(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    batch_size = 8

    losses = []
    start = time.time()
    for step in range(1, steps + 1):
        if data_tensor is not None:
            idx = torch.randint(0, data_tensor.size(0), (batch_size,))
            x = data_tensor[idx].to(device)
            y = x.clone()
        else:
            x = torch.randint(0, cfg.vocab_size, (batch_size, seq_len), device=device)
            y = (x + 1) % cfg.vocab_size

        optimizer.zero_grad()
        logits = model(x)
        loss = criterion(logits.view(-1, cfg.vocab_size), y.view(-1))
        loss.backward()
        optimizer.step()

        losses.append(loss.item())
        if step % log_interval == 0 or step == 1:
            elapsed = time.time() - start
            avg = sum(losses) / len(losses)
            print(f"[TRAIN] step={step}/{steps} loss={loss.item():.4f} avg_loss={avg:.4f} time={elapsed:.1f}s")

    ckpt_dir = 'training'
    os.makedirs(ckpt_dir, exist_ok=True)
    ckpt_path = os.path.join(ckpt_dir, 'checkpoint_real_smoke.pt')
    torch.save({'model_state_dict': model.state_dict(), 'optimizer_state_dict': optimizer.state_dict(), 'losses': losses}, ckpt_path)
    print(f"Saved checkpoint to {ckpt_path}")
    return losses


if __name__ == '__main__':
    import sys
    steps = 100
    if len(sys.argv) > 1:
        steps = int(sys.argv[1])
    train_real_smoke(steps=steps)
