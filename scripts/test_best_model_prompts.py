"""Generate prompt responses from the best local checkpoint."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Test checkpoint generations for several prompts.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "training" / "checkpoints" / "shona_ai_v2.pt")
    parser.add_argument("--tokenizer", type=Path, default=ROOT / "tokenizer" / "shona_bpe.model")
    parser.add_argument("--output", type=Path, default=ROOT / "logs" / "best_model_prompt_test.txt")
    parser.add_argument("--max-tokens", type=int, default=80)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("prompts", nargs="*", help="Optional prompts. Defaults are used when omitted.")
    args = parser.parse_args()

    tokenizer = load_tokenizer(str(args.tokenizer))
    model, device = build_model_from_checkpoint(str(args.checkpoint), tokenizer, device=args.device)
    prompts = args.prompts or DEFAULT_PROMPTS

    args.output.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    lines = [
        f"checkpoint: {args.checkpoint}",
        f"max_tokens: {args.max_tokens}",
        f"temperature: {args.temperature}",
        f"top_p: {args.top_p}",
        "",
    ]

    for prompt in prompts:
        response = generate(
            model,
            tokenizer,
            prompt,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            device=device,
        )
        block = f"PROMPT: {prompt}\nRESPONSE: {response}\n---"
        print(block)
        lines.append(block)

    lines.append(f"elapsed_seconds: {time.time() - started:.2f}")
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved prompt test to {args.output}")


if __name__ == "__main__":
    main()
