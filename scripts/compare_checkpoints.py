"""Compare checkpoint validation loss/perplexity.

Evaluates every .pt file in training/checkpoints against the same validation
split used by the training scripts.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.config import ModelConfig
from model.model import GPTModel
from training.dataset import load_dataset_from_file


def load_config(checkpoint: dict) -> ModelConfig:
    cfg = ModelConfig()
    for key, value in checkpoint.get("config", {}).items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)
    return cfg


def evaluate(model: GPTModel, val_tensor: torch.Tensor, cfg: ModelConfig, device: torch.device, batch_size: int) -> tuple[float, float, int]:
    model.eval()
    criterion = nn.CrossEntropyLoss(ignore_index=0, reduction="sum")
    total_loss = 0.0
    total_tokens = 0

    with torch.no_grad():
        for start in range(0, val_tensor.size(0), batch_size):
            batch = val_tensor[start : start + batch_size].to(device)
            x = batch[:, :-1].contiguous()
            y = batch[:, 1:].contiguous()
            logits = model(x)
            total_loss += criterion(logits.view(-1, cfg.vocab_size), y.view(-1)).item()
            total_tokens += int((y != 0).sum().item())

    avg_loss = total_loss / total_tokens if total_tokens else 0.0
    perplexity = math.exp(avg_loss) if avg_loss < 20 else float("inf")
    return avg_loss, perplexity, total_tokens


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank Shona AI checkpoints by validation perplexity.")
    parser.add_argument("--checkpoint-dir", type=Path, default=ROOT / "training" / "checkpoints")
    parser.add_argument("--valid-path", type=Path, default=ROOT / "data" / "processed" / "valid.txt")
    parser.add_argument("--tokenizer-model", type=Path, default=ROOT / "tokenizer" / "shona_bpe.model")
    parser.add_argument("--output", type=Path, default=ROOT / "logs" / "checkpoint_comparison.json")
    parser.add_argument("--seq-len", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    device = torch.device(args.device)
    checkpoint_paths = sorted(args.checkpoint_dir.glob("*.pt"))
    if not checkpoint_paths:
        raise FileNotFoundError(f"No checkpoints found in {args.checkpoint_dir}")

    val_tensor, tokenizer = load_dataset_from_file(
        str(args.valid_path),
        seq_len=args.seq_len + 1,
        max_samples=args.max_samples,
        tokenizer_model=str(args.tokenizer_model),
    )
    tokenizer_vocab = tokenizer.GetPieceSize() if tokenizer is not None else None

    results = []
    print(f"Validation samples: {val_tensor.size(0)} | seq_len: {args.seq_len} | device: {device}")
    for path in checkpoint_paths:
        started = time.time()
        result = {
            "checkpoint": str(path.relative_to(ROOT)),
            "status": "ok",
        }
        try:
            checkpoint = torch.load(path, map_location=device, weights_only=False)
            cfg = load_config(checkpoint)
            if tokenizer_vocab is not None:
                cfg.vocab_size = min(tokenizer_vocab, int(cfg.vocab_size))

            model = GPTModel(cfg).to(device)
            model.load_state_dict(checkpoint["model_state_dict"])
            avg_loss, perplexity, total_tokens = evaluate(model, val_tensor, cfg, device, args.batch_size)

            result.update(
                {
                    "step": checkpoint.get("step"),
                    "avg_loss": avg_loss,
                    "perplexity": perplexity,
                    "total_tokens": total_tokens,
                    "config": cfg.__dict__,
                    "elapsed_seconds": round(time.time() - started, 2),
                }
            )
            print(f"{path.name}: loss={avg_loss:.6f} ppl={perplexity:.2f} elapsed={result['elapsed_seconds']}s")
        except Exception as exc:
            result.update({"status": "error", "error": repr(exc), "elapsed_seconds": round(time.time() - started, 2)})
            print(f"{path.name}: ERROR {exc!r}")
        results.append(result)

    ranked = sorted((row for row in results if row["status"] == "ok"), key=lambda row: row["perplexity"])
    payload = {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "validation_path": str(args.valid_path.relative_to(ROOT)),
        "validation_samples": int(val_tensor.size(0)),
        "seq_len": args.seq_len,
        "batch_size": args.batch_size,
        "device": str(device),
        "best_checkpoint": ranked[0]["checkpoint"] if ranked else None,
        "results": ranked + [row for row in results if row["status"] != "ok"],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved comparison to {args.output}")


if __name__ == "__main__":
    main()
