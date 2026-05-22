"""GPU training entrypoint for Kaggle or other CUDA hosts.

This script is intentionally strict about preflight checks so we do not
waste GPU time on missing data or accidental CPU runs.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import time
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim

# Allow direct execution from the repository root: `python training/train_full.py`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.config import ModelConfig
from model.model import GPTModel
from training.dataset import load_dataset_from_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Shona AI on a GPU host.")
    parser.add_argument("--data-root", type=Path, default=Path("data/processed"), help="Directory containing train/valid splits or all_clean.txt.")
    parser.add_argument("--train-path", type=Path, default=None, help="Optional explicit train split path.")
    parser.add_argument("--valid-path", type=Path, default=None, help="Optional explicit valid split path.")
    parser.add_argument("--all-clean-path", type=Path, default=None, help="Optional explicit clean corpus path used to derive splits.")
    parser.add_argument("--tokenizer-model", type=Path, default=Path("tokenizer/shona_bpe.model"), help="SentencePiece model path.")
    parser.add_argument("--steps", type=int, default=100000, help="Total training steps.")
    parser.add_argument("--batch-size", type=int, default=8, help="Training batch size.")
    parser.add_argument("--eval-batch-size", type=int, default=8, help="Validation batch size.")
    parser.add_argument("--seq-len", type=int, default=256, help="Token length per sample before the causal shift.")
    parser.add_argument("--lr", type=float, default=3e-4, help="AdamW learning rate.")
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("training/checkpoints"), help="Directory for checkpoints.")
    parser.add_argument("--checkpoint-every", type=int, default=1000, help="Save a checkpoint every N steps.")
    parser.add_argument("--eval-every", type=int, default=500, help="Run validation every N steps.")
    parser.add_argument("--max-train-samples", type=int, default=10000, help="Max samples to load for training when using text files.")
    parser.add_argument("--max-val-samples", type=int, default=702, help="Max samples to load for validation when using text files.")
    parser.add_argument("--hidden-size", type=int, default=512, help="Model hidden size.")
    parser.add_argument("--num-layers", type=int, default=8, help="Number of decoder layers.")
    parser.add_argument("--num-heads", type=int, default=8, help="Number of attention heads.")
    parser.add_argument("--intermediate-size", type=int, default=2048, help="Feed-forward width.")
    parser.add_argument("--max-position-embeddings", type=int, default=1024, help="Maximum sequence length supported by the model.")
    parser.add_argument("--dropout", type=float, default=0.1, help="Dropout rate.")
    parser.add_argument("--allow-cpu", action="store_true", help="Allow CPU execution instead of requiring CUDA.")
    parser.add_argument("--resume-from", type=Path, default=None, help="Optional checkpoint to resume from.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def resolve_data_paths(args: argparse.Namespace) -> tuple[Path, Path, Path | None]:
    data_root = args.data_root
    train_path = args.train_path or (data_root / "train.txt")
    valid_path = args.valid_path or (data_root / "valid.txt")
    all_clean_path = args.all_clean_path or (data_root / "all_clean.txt")
    return train_path, valid_path, all_clean_path if all_clean_path.exists() else None


def load_split_from_corpus(all_clean_path: Path, seq_len: int, max_train_samples: int, max_val_samples: int) -> tuple[torch.Tensor, torch.Tensor, int]:
    lines = [line.strip() for line in all_clean_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise FileNotFoundError(f"No usable lines found in {all_clean_path}")

    rng = random.Random(42)
    rng.shuffle(lines)
    total = len(lines)
    train_end = int(total * 0.98)
    valid_end = int(total * 0.99)
    train_lines = lines[:train_end][:max_train_samples]
    valid_lines = lines[train_end:valid_end][:max_val_samples]
    if not train_lines:
        raise RuntimeError("Training split is empty after sampling.")
    if not valid_lines:
        raise RuntimeError("Validation split is empty after sampling.")

    tokenizer = None
    tokenizer_model = Path("tokenizer/shona_bpe.model")
    if tokenizer_model.exists():
        from training.dataset import get_sentencepiece_tokenizer

        tokenizer = get_sentencepiece_tokenizer(str(tokenizer_model))
    vocab_size = tokenizer.GetPieceSize() if tokenizer is not None else 32000
    train_tensor = load_dataset_from_lines(train_lines, seq_len + 1, tokenizer, vocab_size)
    valid_tensor = load_dataset_from_lines(valid_lines, seq_len + 1, tokenizer, vocab_size)
    return train_tensor, valid_tensor, vocab_size


def load_dataset_from_lines(lines: list[str], seq_len: int, tokenizer, vocab_size: int) -> torch.Tensor:
    ids_list = []
    for line in lines:
        if tokenizer is not None:
            ids = tokenizer.EncodeAsIds(line)
        else:
            ids = [abs(hash(word)) % vocab_size for word in line.split()]
        if len(ids) >= seq_len:
            ids = ids[:seq_len]
        else:
            ids = ids + [0] * (seq_len - len(ids))
        ids_list.append(ids)
    return torch.tensor(ids_list, dtype=torch.long)


def evaluate(model: GPTModel, val_tensor: torch.Tensor, cfg: ModelConfig, device: torch.device, batch_size: int) -> tuple[float, float]:
    model.eval()
    total_loss = 0.0
    total_non_pad_tokens = 0
    with torch.no_grad():
        for i in range(0, val_tensor.size(0), batch_size):
            batch = val_tensor[i:i + batch_size].to(device)
            if batch.size(0) == 0:
                continue
            x = batch[:, :-1].contiguous()
            y = batch[:, 1:].contiguous()
            logits = model(x)
            sum_criterion = nn.CrossEntropyLoss(ignore_index=0, reduction="sum")
            loss_sum = sum_criterion(logits.view(-1, cfg.vocab_size), y.view(-1))
            non_pad_tokens = (y != 0).sum().item()
            total_loss += loss_sum.item()
            total_non_pad_tokens += non_pad_tokens
    model.train()
    avg_loss = total_loss / total_non_pad_tokens if total_non_pad_tokens > 0 else 0.0
    perplexity = math.exp(avg_loss) if avg_loss < 20 else float("inf")
    return avg_loss, perplexity


def preflight(args: argparse.Namespace) -> None:
    if not torch.cuda.is_available() and not args.allow_cpu:
        raise SystemExit("CUDA is required for `train_full.py`. Run on Kaggle/GPU or pass --allow-cpu only for a tiny local test.")

    train_path, valid_path, all_clean_path = resolve_data_paths(args)
    if train_path.exists() and valid_path.exists():
        return
    if all_clean_path is not None and all_clean_path.exists():
        return

    raise SystemExit(
        "Missing training data. Provide data/processed/train.txt and valid.txt, or mount data/processed/all_clean.txt so the script can split it on the fly."
    )


def load_data(args: argparse.Namespace) -> tuple[torch.Tensor, torch.Tensor, int, Path | None]:
    train_path, valid_path, all_clean_path = resolve_data_paths(args)

    if train_path.exists() and valid_path.exists():
        train_tensor, tokenizer = load_dataset_from_file(
            str(train_path),
            seq_len=args.seq_len + 1,
            max_samples=args.max_train_samples,
            tokenizer_model=str(args.tokenizer_model),
        )
        if tokenizer is not None:
            vocab_size = tokenizer.GetPieceSize()
        else:
            vocab_size = 32000
        valid_tensor, _ = load_dataset_from_file(
            str(valid_path),
            seq_len=args.seq_len + 1,
            max_samples=args.max_val_samples,
            tokenizer_model=str(args.tokenizer_model),
            vocab_size=vocab_size,
        )
        return train_tensor, valid_tensor, vocab_size, None

    if all_clean_path is None:
        raise FileNotFoundError("No usable dataset files were found.")

    train_tensor, valid_tensor, vocab_size = load_split_from_corpus(
        all_clean_path,
        seq_len=args.seq_len,
        max_train_samples=args.max_train_samples,
        max_val_samples=args.max_val_samples,
    )
    return train_tensor, valid_tensor, vocab_size, all_clean_path


def maybe_resume(model: GPTModel, optimizer: optim.Optimizer, checkpoint_path: Path | None) -> int:
    if checkpoint_path is None:
        return 0
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Resume checkpoint not found: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return int(checkpoint.get("step", 0))


def save_checkpoint(path: Path, step: int, model: GPTModel, optimizer: optim.Optimizer, losses: list[float], cfg: ModelConfig, source_note: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "step": step,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "losses": losses,
            "config": cfg.__dict__,
            "source_note": source_note,
        },
        path,
    )


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    preflight(args)

    device = torch.device("cuda" if torch.cuda.is_available() and not args.allow_cpu or torch.cuda.is_available() else "cpu")
    if device.type == "cpu" and not args.allow_cpu:
        raise SystemExit("GPU not available. Kaggle or another CUDA host is required for the full training run.")

    print("Loading data...")
    train_tensor, valid_tensor, vocab_size, source_note = load_data(args)
    print(f"Loaded {train_tensor.size(0)} training samples and {valid_tensor.size(0)} validation samples on {device}.")
    print(f"Vocabulary size: {vocab_size}")

    cfg = ModelConfig(
        vocab_size=min(vocab_size, 32000),
        hidden_size=args.hidden_size,
        num_layers=args.num_layers,
        num_heads=args.num_heads,
        intermediate_size=args.intermediate_size,
        max_position_embeddings=args.max_position_embeddings,
        dropout=args.dropout,
    )

    model = GPTModel(cfg).to(device)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss(ignore_index=0)

    start_step = maybe_resume(model, optimizer, args.resume_from)
    losses: list[float] = []
    if start_step:
        print(f"Resumed from step {start_step}.")

    scaler = torch.cuda.amp.GradScaler(enabled=device.type == "cuda")
    print(f"Starting training for {args.steps} steps.")
    started_at = time.time()

    model.train()
    for step in range(start_step + 1, args.steps + 1):
        idx = torch.randint(0, train_tensor.size(0), (args.batch_size,))
        batch = train_tensor[idx].to(device)
        x = batch[:, :-1].contiguous()
        y = batch[:, 1:].contiguous()

        optimizer.zero_grad(set_to_none=True)
        with torch.cuda.amp.autocast(enabled=device.type == "cuda"):
            logits = model(x)
            loss = criterion(logits.view(-1, cfg.vocab_size), y.view(-1))

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        losses.append(float(loss.item()))

        if step % args.eval_every == 0 or step == args.steps:
            val_loss, val_ppl = evaluate(model, valid_tensor, cfg, device, args.eval_batch_size)
            train_window = losses[-args.eval_every:] if len(losses) >= args.eval_every else losses
            train_loss = sum(train_window) / max(len(train_window), 1)
            elapsed = time.time() - started_at
            print(f"step {step} | train_loss={train_loss:.2f} | val_loss={val_loss:.2f} | val_ppl={val_ppl:.1f} | elapsed={elapsed/60:.1f}m")

        if step % args.checkpoint_every == 0 or step == args.steps:
            ckpt_name = f"full_step_{step}.pt" if step != args.steps else "full_last.pt"
            ckpt_path = args.checkpoint_dir / ckpt_name
            save_checkpoint(ckpt_path, step, model, optimizer, losses, cfg, source_note or "train/valid split")
            print(f"Checkpoint saved to {ckpt_path}")


if __name__ == "__main__":
    main()