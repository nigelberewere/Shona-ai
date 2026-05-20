# Shona AI

Shona AI is a focused effort to build the most fluent large language model for the Shona (ChiShona) language. The project targets high-quality Shona text collection, careful cleaning, Shona-aware tokenization, and a decoder-only transformer trained to handle Shona morphology, dialect variation, and code-switching.

## Why it matters

Shona is spoken by more than 14 million people, but high-quality language technology support is limited. Shona AI aims to close this gap by producing a robust model for generation, translation, and reasoning in Shona.

## Project goals

- Build a clean, deduplicated Shona corpus from public sources
- Train a Shona-optimized SentencePiece BPE tokenizer
- Train a decoder-only transformer model for high-quality Shona generation
- Provide a FastAPI inference server and CLI demo

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Repository layout

- `data/` - raw and processed datasets
- `scripts/` - data collection and processing scripts
- `tokenizer/` - SentencePiece tokenizer training and artifacts
- `model/` - model architecture
- `training/` - training pipeline
- `evaluation/` - benchmarks and metrics
- `inference/` - generation and API server

## License

TBD
