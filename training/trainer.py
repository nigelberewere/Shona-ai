"""Training utilities for Phase 6 training loop diagnosis and fix.

Trains a causal language model with correct next-token prediction targets.
"""

import os
import math
import time
import torch
import torch.nn as nn
import torch.optim as optim
from .dataset import load_dataset_from_file
from model.config import ModelConfig
from model.model import GPTModel


def evaluate(model, val_tensor, cfg, device, batch_size=8):
    model.eval()
    criterion = nn.CrossEntropyLoss()
    total_loss = 0.0
    num_samples = 0
    with torch.no_grad():
        for i in range(0, val_tensor.size(0), batch_size):
            batch = val_tensor[i:i+batch_size].to(device)
            if batch.size(0) == 0:
                continue
            x = batch[:, :-1]
            y = batch[:, 1:]
            logits = model(x)
            loss = criterion(logits.view(-1, cfg.vocab_size), y.view(-1))
            total_loss += loss.item() * batch.size(0)
            num_samples += batch.size(0)
    model.train()
    avg_loss = total_loss / num_samples if num_samples > 0 else 0.0
    perplexity = math.exp(avg_loss) if avg_loss < 20 else float('inf')
    return avg_loss, perplexity


def train_real_smoke(steps: int = 500, log_interval: int = 100):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    train_path = 'data/processed/train.txt'
    val_path = 'data/processed/valid.txt'
    seq_len = 256
    
    # We load seq_len + 1 tokens so that after shifting we have seq_len tokens.
    max_train_samples = 10000
    max_val_samples = 702

    print("Loading datasets...")
    if os.path.exists(train_path):
        train_tensor, tokenizer = load_dataset_from_file(train_path, seq_len=seq_len + 1, max_samples=max_train_samples)
        if tokenizer is not None:
            vocab_size = tokenizer.GetPieceSize()
        else:
            vocab_size = 32000
        print(f"Loaded {train_tensor.size(0)} training samples from {train_path}; vocab_size={vocab_size}")
    else:
        raise FileNotFoundError(f"Training data not found at {train_path}")

    if os.path.exists(val_path):
        val_tensor, _ = load_dataset_from_file(val_path, seq_len=seq_len + 1, max_samples=max_val_samples)
        print(f"Loaded {val_tensor.size(0)} validation samples from {val_path}")
    else:
        raise FileNotFoundError(f"Validation data not found at {val_path}")

    # Use a lightweight and fast config suitable for CPU training
    cfg = ModelConfig()
    cfg.vocab_size = min(vocab_size, 32000)
    cfg.hidden_size = 128
    cfg.num_layers = 2
    cfg.num_heads = 8
    cfg.intermediate_size = 512
    cfg.max_position_embeddings = 256

    model = GPTModel(cfg).to(device)
    model.train()

    # Hyperparameters requested by step 2
    batch_size = 4
    lr = 3e-4
    optimizer = optim.AdamW(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    losses = []
    start = time.time()
    
    print(f"Starting {steps}-step training loop on {device}...")
    for step in range(1, steps + 1):
        idx = torch.randint(0, train_tensor.size(0), (batch_size,))
        batch = train_tensor[idx].to(device)
        
        # Causal shift
        x = batch[:, :-1]
        y = batch[:, 1:]

        optimizer.zero_grad()
        logits = model(x)
        loss = criterion(logits.view(-1, cfg.vocab_size), y.view(-1))
        loss.backward()
        optimizer.step()

        losses.append(loss.item())

        if step % log_interval == 0:
            val_loss, val_ppl = evaluate(model, val_tensor, cfg, device, batch_size=8)
            train_loss_avg = sum(losses[-log_interval:]) / log_interval
            print(f"  step {step} | train_loss={train_loss_avg:.2f} | val_loss={val_loss:.2f} | val_ppl={val_ppl:.1f}")

    # Save checkpoint to training/checkpoints/step_500.pt
    ckpt_dir = 'training/checkpoints'
    os.makedirs(ckpt_dir, exist_ok=True)
    ckpt_path = os.path.join(ckpt_dir, 'step_500.pt')
    torch.save({
        'step': steps,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'losses': losses,
        'config': cfg.__dict__
    }, ckpt_path)
    print(f"Checkpoint saved to {ckpt_path}")
    return losses


if __name__ == '__main__':
    train_real_smoke()
