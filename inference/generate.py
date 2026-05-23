import math
import torch
import torch.nn.functional as F
from typing import List, Tuple

import sentencepiece as spm

from model.config import ModelConfig
from model.model import GPTModel


def load_tokenizer(path: str):
    sp = spm.SentencePieceProcessor()
    sp.Load(path)
    return sp


def build_model_from_checkpoint(checkpoint_path: str, tokenizer, device: str = 'cpu') -> Tuple[GPTModel, str]:
    # Load checkpoint without instantiating the model so we can infer shapes
    raw = torch.load(checkpoint_path, map_location=device)
    if isinstance(raw, dict) and 'model_state_dict' in raw:
        state_dict = raw['model_state_dict']
    elif isinstance(raw, dict) and any(isinstance(k, str) for k in raw.keys()):
        state_dict = raw
    else:
        raise RuntimeError('Unsupported checkpoint format for inference')

    # Infer vocab_size and hidden_size from embeddings
    vocab_size = None
    hidden_size = None
    max_pos = None
    num_layers = None
    intermediate_size = None

    # token embeddings: embeddings.token_emb.weight -> (vocab_size, hidden_size)
    for k, v in state_dict.items():
        if k.endswith('embeddings.token_emb.weight') or k.endswith('embeddings.token_emb.weight'):
            vocab_size, hidden_size = v.shape[0], v.shape[1]
        if k.endswith('embeddings.pos_emb.weight'):
            max_pos = v.shape[0]
        # feedforward intermediate size
        if k.endswith('ff.net.0.weight'):
            # shape: (intermediate_size, hidden_size)
            intermediate_size = v.shape[0]
        # count layers
        if k.startswith('layers.'):
            try:
                idx = int(k.split('.')[1])
                if num_layers is None or idx + 1 > num_layers:
                    num_layers = idx + 1
            except Exception:
                pass

    # Fallbacks
    if vocab_size is None:
        try:
            vocab_size = tokenizer.GetPieceSize()
        except Exception:
            vocab_size = ModelConfig.vocab_size
    if hidden_size is None:
        hidden_size = ModelConfig.hidden_size
    if max_pos is None:
        max_pos = ModelConfig.max_position_embeddings
    if intermediate_size is None:
        intermediate_size = ModelConfig.intermediate_size
    if num_layers is None:
        num_layers = ModelConfig.num_layers

    # Build config matching checkpoint
    config = ModelConfig(
        vocab_size=vocab_size,
        hidden_size=hidden_size,
        num_layers=num_layers,
        intermediate_size=intermediate_size,
        max_position_embeddings=max_pos,
    )

    model = GPTModel(config)
    model.to(device)
    model.eval()

    # Load weights (allow partial mismatches but shapes should match)
    try:
        model.load_state_dict(state_dict, strict=False)
    except RuntimeError as e:
        # re-raise with helpful message
        raise RuntimeError(f"Error(s) in loading state_dict for GPTModel: {e}")

    return model, device


def top_p_filtering(logits: torch.Tensor, top_p: float = 0.9) -> torch.Tensor:
    # logits: (vocab,)
    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
    probs = F.softmax(sorted_logits, dim=-1)
    cumulative_probs = torch.cumsum(probs, dim=-1)

    # mask tokens with cumulative prob above top_p
    cutoff = cumulative_probs > top_p
    if cutoff.any():
        # keep at least one token
        first_idx = torch.nonzero(cutoff).min()
        sorted_logits[first_idx + 1 :] = -float('Inf')

    # reconstruct logits in original order
    filtered_logits = torch.full_like(logits, -float('Inf'))
    filtered_logits[sorted_indices] = sorted_logits
    return filtered_logits


def generate(
    model: GPTModel,
    tokenizer,
    prompt: str,
    max_tokens: int = 100,
    temperature: float = 0.8,
    top_p: float = 0.9,
    device: str = 'cpu',
    pad_id: int = 0,
    bos_id: int = 1,
    eos_id: int = 2,
    unk_id: int = 3,
):
    # Encode
    input_ids = tokenizer.EncodeAsIds(prompt)
    if not isinstance(input_ids, list):
        input_ids = list(input_ids)

    input_ids = torch.tensor([input_ids], dtype=torch.long, device=device)

    generated = []
    with torch.no_grad():
        for _ in range(max_tokens):
            logits = model(input_ids)  # (1, seq, vocab)
            next_token_logits = logits[:, -1, :].squeeze(0)  # (vocab,)

            # filter special tokens
            for tid in (pad_id, bos_id, unk_id):
                if 0 <= tid < next_token_logits.size(0):
                    next_token_logits[tid] = -float('Inf')

            # apply temperature
            if temperature != 1.0:
                next_token_logits = next_token_logits / (temperature + 1e-8)

            # apply top-p (nucleus) filtering
            filtered_logits = top_p_filtering(next_token_logits, top_p=top_p)

            # sample
            probs = F.softmax(filtered_logits, dim=-1)
            if torch.isnan(probs).all() or probs.sum() == 0:
                # fallback to argmax
                next_token = torch.argmax(next_token_logits)
            else:
                next_token = torch.multinomial(probs, num_samples=1).squeeze(1) if probs.dim() == 2 else torch.multinomial(probs, num_samples=1)

            # ensure tensor is on correct device and shape (1,)
            next_token = next_token.to(device)
            next_token = next_token.long().reshape(-1)
            next_id = int(next_token.item())
            if next_id == eos_id:
                break

            generated.append(next_id)
            # append to input_ids
            # ensure nt has shape (1,1)
            nt = next_token.view(1, 1)
            input_ids = torch.cat([input_ids, nt], dim=1)

    # Decode
    try:
        text = tokenizer.DecodeIds(generated)
    except Exception:
        # some sentencepiece versions use DecodeIds vs Decode
        text = tokenizer.Decode(generated)
    return text
