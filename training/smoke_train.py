import math
import os
import time
import torch
import torch.nn as nn
import torch.optim as optim

from model.config import ModelConfig
from model.model import GPTModel


def synthetic_batch(batch_size, seq_len, vocab_size, device):
    # create random input tokens and targets as input shifted by 1 modulo vocab
    x = torch.randint(0, vocab_size, (batch_size, seq_len), dtype=torch.long, device=device)
    y = (x + 1) % vocab_size
    return x, y


def train_smoke(steps=100, log_interval=10, ckpt_path="training/checkpoint_smoke.pt"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = ModelConfig()
    # small config for speed
    cfg.vocab_size = 4096
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
    seq_len = 16

    losses = []
    start = time.time()
    for step in range(1, steps + 1):
        x, y = synthetic_batch(batch_size, seq_len, cfg.vocab_size, device)
        optimizer.zero_grad()
        logits = model(x)  # (B, T, V)
        loss = criterion(logits.view(-1, cfg.vocab_size), y.view(-1))
        loss.backward()
        optimizer.step()

        losses.append(loss.item())
        if step % log_interval == 0 or step == 1:
            elapsed = time.time() - start
            print(f"[SMOKE] step={step}/{steps} loss={loss.item():.4f} avg_loss={sum(losses)/len(losses):.4f} time={elapsed:.1f}s")

    # save checkpoint
    os.makedirs(os.path.dirname(ckpt_path), exist_ok=True)
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'losses': losses,
        'config': cfg.__dict__,
    }, ckpt_path)

    return losses


if __name__ == '__main__':
    import sys
    steps = 100
    if len(sys.argv) > 1:
        steps = int(sys.argv[1])
    losses = train_smoke(steps=steps)
    first, last = losses[0], losses[-1]
    print(f"SMOKE TRAIN COMPLETE: first_loss={first:.4f} last_loss={last:.4f}")
    if last < first:
        print("LOSS_DECREASED")
        exit(0)
    else:
        print("LOSS_NOT_DECREASED")
        exit(2)
