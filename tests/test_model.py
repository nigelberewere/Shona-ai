import pytest
import torch

from model.config import ModelConfig
from model.model import GPTModel


def test_forward_pass_shapes():
    cfg = ModelConfig()
    # use a very small model for unit test speed
    cfg.num_layers = 2
    cfg.hidden_size = 128
    cfg.num_heads = 8
    cfg.intermediate_size = 512
    model = GPTModel(cfg)
    batch = 2
    seq = 16
    input_ids = torch.randint(0, cfg.vocab_size, (batch, seq))
    logits = model(input_ids)
    assert logits.shape == (batch, seq, cfg.vocab_size)
def test_model_placeholder() -> None:
    assert True
