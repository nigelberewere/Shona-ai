import os
import sys
from pathlib import Path
import torch

ROOT = Path(__file__).resolve().parents[1]
CKPT_PATH = r"C:\Users\nigel\projects\Shona ai\training\checkpoints\shona_ai_final.pt"
TOKENIZER_PATH = str(ROOT / 'tokenizer' / 'shona_bpe.model')

print('--- Diagnostic: checkpoint and tokenizer ---')

# Load checkpoint
if not os.path.exists(CKPT_PATH):
    print('Checkpoint not found at', CKPT_PATH)
else:
    ckpt = torch.load(CKPT_PATH, map_location='cpu')
    print('\nCheckpoint keys:', list(ckpt.keys()))
    cfg = ckpt.get('config', {})
    print('\nckpt["config"]:')
    for k, v in cfg.items():
        print(f'  {k}: {v}')
    ckpt_vocab = cfg.get('vocab_size', None)
    print('\nCheckpoint config vocab_size:', ckpt_vocab)

# Load tokenizer
try:
    import sentencepiece as spm
    sp = spm.SentencePieceProcessor()
    if os.path.exists(TOKENIZER_PATH):
        sp.Load(TOKENIZER_PATH)
        tk_vocab = sp.GetPieceSize()
        print('\nTokenizer loaded from', TOKENIZER_PATH)
        print('Tokenizer vocab_size:', tk_vocab)
    else:
        print('\nTokenizer model not found at', TOKENIZER_PATH)
        sp = None
        tk_vocab = None
except Exception as e:
    print('\nFailed to load sentencepiece:', repr(e))
    sp = None
    tk_vocab = None

# Special token ids from checkpoint config (if present)
print('\nSpecial token ids from checkpoint config:')
for name in ['pad_token_id', 'eos_token_id', 'unk_token_id', 'bos_token_id']:
    print(f'  {name}: {cfg.get(name, None)}')

# Special token ids from tokenizer
if sp is not None:
    def piece_id_or_none(piece):
        try:
            pid = sp.PieceToId(piece)
            return pid
        except Exception:
            return None
    candidates = ['<pad>', '<unk>', '<s>', '</s>', '<eos>', '<bos>', '[PAD]', '[UNK]', '[CLS]', '[SEP]']
    print('\nTokenizer special token ids:')
    for p in candidates:
        pid = piece_id_or_none(p)
        print(f'  {p}: {pid}')

    # Roundtrip test
    test_text = 'Ndinoda Zimbabwe'
    ids = sp.EncodeAsIds(test_text)
    decoded = sp.DecodeIds(ids)
    print('\nRoundtrip test:')
    print('  text:', test_text)
    print('  ids:', ids)
    print('  decoded:', decoded)

    # Print first 20 pieces
    print('\nFirst 20 tokenizer pieces (id: piece):')
    for i in range(min(20, sp.GetPieceSize())):
        try:
            print(f'  {i}: {sp.IdToPiece(i)}')
        except Exception:
            print(f'  {i}: <error>')
else:
    print('\nTokenizer not available; skipping tokenizer diagnostics')

print('\n--- End diagnostic ---')
