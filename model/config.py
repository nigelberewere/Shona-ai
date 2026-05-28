from dataclasses import dataclass


@dataclass
class ModelConfig:
    vocab_size: int = 32000
    hidden_size: int = 256
    num_layers: int = 6
    num_heads: int = 8
    intermediate_size: int = 1024
    max_position_embeddings: int = 256
    dropout: float = 0.1

