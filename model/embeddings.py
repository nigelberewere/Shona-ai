import torch
import torch.nn as nn
from .config import ModelConfig


class Embeddings(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.token_emb = nn.Embedding(config.vocab_size, config.hidden_size)
        self.pos_emb = nn.Embedding(config.max_position_embeddings, config.hidden_size)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, input_ids):
        # input_ids: (batch, seq)
        positions = torch.arange(input_ids.size(1), device=input_ids.device).unsqueeze(0)
        x = self.token_emb(input_ids) + self.pos_emb(positions)
        return self.dropout(x)
"""Embedding layers for Shona AI."""


def build_embeddings() -> None:
    raise NotImplementedError("Embedding implementation will be added in Phase 5.")
