from dataclasses import dataclass


@dataclass
class ModelConfig:
    vocab_size: int = 32000
    hidden_size: int = 512
    num_layers: int = 8
    num_heads: int = 8
    intermediate_size: int = 2048
    max_position_embeddings: int = 1024
    dropout: float = 0.1
"""Model configuration placeholders for Shona AI."""
