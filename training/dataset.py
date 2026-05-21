import os
from typing import List, Optional

import torch


def _load_lines(path: str, max_lines: Optional[int] = None) -> List[str]:
    lines = []
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if max_lines is not None and i >= max_lines:
                break
            line = line.strip()
            if line:
                lines.append(line)
    return lines


def get_sentencepiece_tokenizer(model_path: str):
    try:
        import sentencepiece as spm
    except Exception:
        return None
    if not os.path.exists(model_path):
        return None
    sp = spm.SentencePieceProcessor()
    sp.Load(model_path)
    return sp


def encode_lines_to_tensor(lines: List[str], seq_len: int, tokenizer, vocab_size: int):
    import torch

    ids_list = []
    for line in lines:
        if tokenizer is not None:
            ids = tokenizer.EncodeAsIds(line)
        else:
            # fallback: word-hash mapping
            ids = [abs(hash(w)) % vocab_size for w in line.split()]
        # trim or pad
        if len(ids) >= seq_len:
            ids = ids[:seq_len]
        else:
            ids = ids + [0] * (seq_len - len(ids))
        ids_list.append(ids)
    return torch.tensor(ids_list, dtype=torch.long)


def load_dataset_from_file(path: str, seq_len: int = 16, max_samples: int = 1000, tokenizer_model: str = 'tokenizer/shona_bpe.model', vocab_size: int = 32000):
    lines = _load_lines(path, max_lines=max_samples)
    tokenizer = get_sentencepiece_tokenizer(tokenizer_model)
    tensor = encode_lines_to_tensor(lines, seq_len, tokenizer, vocab_size)
    return tensor, tokenizer
"""Dataset loader placeholder for Shona AI."""


def load_dataset() -> None:
    raise NotImplementedError("Dataset loader will be implemented in Phase 6.")
