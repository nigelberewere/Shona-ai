import torch
import torch.nn as nn
import torch.nn.functional as F


class CausalSelfAttention(nn.Module):
    def __init__(self, hidden_size, num_heads, dropout=0.1):
        super().__init__()
        assert hidden_size % num_heads == 0
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads

        self.qkv_proj = nn.Linear(hidden_size, 3 * hidden_size)
        self.out_proj = nn.Linear(hidden_size, hidden_size)
        self.attn_dropout = nn.Dropout(dropout)
        self.resid_dropout = nn.Dropout(dropout)

    def forward(self, x):
        # x: (batch, seq, hidden)
        B, T, C = x.size()
        qkv = self.qkv_proj(x)  # (B, T, 3C)
        qkv = qkv.reshape(B, T, 3, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]  # each: (B, num_heads, T, head_dim)

        attn_weights = (q @ k.transpose(-2, -1)) / (self.head_dim ** 0.5)  # (B, heads, T, T)
        mask = torch.tril(torch.ones(T, T, device=x.device)).unsqueeze(0).unsqueeze(0)
        attn_weights = attn_weights.masked_fill(mask == 0, float('-inf'))
        attn_probs = F.softmax(attn_weights, dim=-1)
        attn_probs = self.attn_dropout(attn_probs)

        attn_output = attn_probs @ v  # (B, heads, T, head_dim)
        attn_output = attn_output.transpose(1, 2).contiguous().reshape(B, T, C)
        out = self.out_proj(attn_output)
        return self.resid_dropout(out)
"""Attention mechanisms for Shona AI."""


def build_attention() -> None:
    raise NotImplementedError("Attention implementation will be added in Phase 5.")
