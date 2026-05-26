"""Generate side-by-side prompt responses for all local checkpoints."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inference.generate import build_model_from_checkpoint, generate, load_tokenizer


DEFAULT_PROMPTS = [
    "Mhoro, makadii?",
    "Unonzi ani?",
    "Ndinoda kudzidza chiShona nokuti",
    "Nhasi ndiri kuenda kumusika kunotenga",
    "Tsanangura kuti mhuri inokosha sei",
]


def checkpoint_sort_key(path: Path) -> tuple[int, str]:
    priority = {
        "shona_ai_final.pt": 10,
        "shona_ai_v2.pt": 20,
        "shona_ai_v4.pt": 30,
        "step_300.pt": 40,
        "step_500.pt": 50,
    }
    return priority.get(path.name, 100), path.name


def main() -> None:
    parser = argparse.ArgumentParser(description="Prompt every checkpoint and save comparable responses.")
    parser.add_argument("--checkpoint-dir", type=Path, default=ROOT / "training" / "checkpoints")
    parser.add_argument("--tokenizer", type=Path, default=ROOT / "tokenizer" / "shona_bpe.model")
    parser.add_argument("--output", type=Path, default=ROOT / "logs" / "model_prompt_comparison.md")
    parser.add_argument("--max-tokens", type=int, default=60)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("prompts", nargs="*", help="Optional prompts. Defaults are used when omitted.")
    args = parser.parse_args()

    checkpoints = sorted(args.checkpoint_dir.glob("*.pt"), key=checkpoint_sort_key)
    if not checkpoints:
        raise FileNotFoundError(f"No .pt checkpoints found in {args.checkpoint_dir}")

    tokenizer = load_tokenizer(str(args.tokenizer))
    prompts = args.prompts or DEFAULT_PROMPTS

    lines = [
        "# Model Prompt Comparison",
        "",
        f"- Created: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Checkpoint directory: `{args.checkpoint_dir.relative_to(ROOT)}`",
        f"- Decoding: max_tokens={args.max_tokens}, temperature={args.temperature}, top_p={args.top_p}, seed={args.seed}",
        f"- Device: `{args.device}`",
        "",
    ]

    for checkpoint in checkpoints:
        print(f"Loading {checkpoint.name}...")
        started = time.time()
        lines.extend([f"## {checkpoint.name}", ""])
        try:
            raw = torch.load(checkpoint, map_location=args.device, weights_only=False)
            step = raw.get("step") if isinstance(raw, dict) else None
            if step is not None:
                lines.extend([f"- Step: `{step}`", ""])

            model, device = build_model_from_checkpoint(str(checkpoint), tokenizer, device=args.device)
            for prompt_index, prompt in enumerate(prompts):
                torch.manual_seed(args.seed + prompt_index)
                response = generate(
                    model,
                    tokenizer,
                    prompt,
                    max_tokens=args.max_tokens,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    device=device,
                )
                lines.extend(
                    [
                        f"### Prompt: {prompt}",
                        "",
                        "```text",
                        response,
                        "```",
                        "",
                    ]
                )
                print(f"  {checkpoint.name} | {prompt}")
            lines.append(f"_Elapsed: {time.time() - started:.2f}s_")
            lines.append("")
        except Exception as exc:
            lines.extend(["```text", f"ERROR: {exc!r}", "```", ""])
            print(f"  ERROR {checkpoint.name}: {exc!r}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved comparison to {args.output}")


if __name__ == "__main__":
    main()
