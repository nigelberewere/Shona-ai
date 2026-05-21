import argparse
import os
import time
import torch
import torch.nn as nn
import torch.optim as optim

from model.config import ModelConfig
from model.model import GPTModel
from .dataset import load_dataset_from_file


def evaluate(model, val_tensor, cfg, device):
    model.eval()
    criterion = nn.CrossEntropyLoss()
    with torch.no_grad():
        x = val_tensor.to(device)
        y = x.clone()
        logits = model(x)
        loss = criterion(logits.view(-1, cfg.vocab_size), y.view(-1))
    model.train()
    return loss.item()


def run_pilot(total_steps=10000, ckpt_interval=1000, eval_interval=500, seq_len=16, batch_size=8, max_train_samples=1024, max_val_samples=256):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    train_path = 'data/processed/train.txt'
    val_path = 'data/processed/valid.txt'

    train_tensor, tokenizer = load_dataset_from_file(train_path, seq_len=seq_len, max_samples=max_train_samples)
    val_tensor, _ = load_dataset_from_file(val_path, seq_len=seq_len, max_samples=max_val_samples)

    if tokenizer is not None:
        vocab_size = tokenizer.GetPieceSize()
    else:
        vocab_size = 32000

    cfg = ModelConfig()
    cfg.vocab_size = min(vocab_size, 32000)
    cfg.hidden_size = 256
    cfg.num_layers = 4
    cfg.num_heads = 8
    cfg.intermediate_size = 1024
    cfg.max_position_embeddings = 128

    model = GPTModel(cfg).to(device)
    model.train()

    optimizer = optim.AdamW(model.parameters(), lr=5e-4)
    criterion = nn.CrossEntropyLoss()

    losses = []
    start = time.time()
    for step in range(1, total_steps + 1):
        idx = torch.randint(0, train_tensor.size(0), (batch_size,))
        x = train_tensor[idx].to(device)
        y = x.clone()

        optimizer.zero_grad()
        logits = model(x)
        loss = criterion(logits.view(-1, cfg.vocab_size), y.view(-1))
        loss.backward()
        optimizer.step()

        losses.append(loss.item())

        if step % 10 == 0:
            avg = sum(losses[-100:]) / min(len(losses), 100)
            print(f"[PILOT] step={step}/{total_steps} loss={loss.item():.4f} avg100={avg:.4f}")

        if step % eval_interval == 0:
            val_loss = evaluate(model, val_tensor[:batch_size], cfg, device)
            print(f"[PILOT][EVAL] step={step} val_loss={val_loss:.4f}")

        if step % ckpt_interval == 0:
            ckpt_dir = 'training/pilot_checkpoints'
            os.makedirs(ckpt_dir, exist_ok=True)
            ckpt_path = os.path.join(ckpt_dir, f'ckpt_step_{step}.pt')
            torch.save({'step': step, 'model_state_dict': model.state_dict(), 'optimizer_state_dict': optimizer.state_dict(), 'loss': loss.item()}, ckpt_path)
            print(f"[PILOT][CKPT] Saved checkpoint {ckpt_path}")

    total_time = time.time() - start
    print(f"PILOT RUN COMPLETE: steps={total_steps} final_loss={losses[-1]:.4f} time={total_time:.1f}s")
    # final checkpoint
    final_ckpt = 'training/pilot_checkpoints/ckpt_final.pt'
    torch.save({'step': total_steps, 'model_state_dict': model.state_dict(), 'optimizer_state_dict': optimizer.state_dict(), 'losses': losses}, final_ckpt)
    return losses


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('total_steps', type=int, help='Total training steps')
    parser.add_argument('--ckpt-interval', type=int, default=1000)
    parser.add_argument('--eval-interval', type=int, default=500)
    parser.add_argument('--seq-len', type=int, default=16)
    parser.add_argument('--batch-size', type=int, default=8)
    args = parser.parse_args()
    run_pilot(total_steps=args.total_steps, ckpt_interval=args.ckpt_interval, eval_interval=args.eval_interval, seq_len=args.seq_len, batch_size=args.batch_size)
