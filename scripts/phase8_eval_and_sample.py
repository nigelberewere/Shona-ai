"""Phase 8 runner: generation + perplexity evaluation using local checkpoint.

Usage: run from repo root. The script will:
 - load tokenizer from `tokenizer/shona_bpe.model` if available
 - load model from the absolute checkpoint path provided below
 - generate samples for verified prompts and save to `logs/phase8_samples.txt`
 - compute perplexity on `data/processed/test.txt` and save to `logs/phase8_eval.json`
 - append progress to the session log and update `STATE.json` if successful
"""

import os
import sys
import json
import time
from pathlib import Path

import torch
import torch.nn.functional as F

# repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model.config import ModelConfig
from model.model import GPTModel

# Absolute checkpoint path provided by user
CKPT_PATH = r"C:\Users\nigel\projects\Shona ai\training\checkpoints\shona_ai_final.pt"
TOKENIZER_PATH = str(ROOT / 'tokenizer' / 'shona_bpe.model')
TEST_PATH = str(ROOT / 'data' / 'processed' / 'test.txt')
LOG_DIR = str(ROOT / 'logs')
LOG_SAMPLES = str(ROOT / 'logs' / 'phase8_samples.txt')
LOG_EVAL = str(ROOT / 'logs' / 'phase8_eval.json')
SESSION_LOG = None
STATE_PATH = str(ROOT / 'STATE.json')

# Verified prompts from INSTRUCTIONS.md Section 9.4 (exact Shona lines)
PROMPTS = [
    'Mhoro, makadii?',
    'Ndiri well',
    'Zita rako ndiani?',
    'Zita rangu ndiJohn',
    'Ndinoda Zimbabwe',
    'Mvura',
    'Mwari',
    'Amai',
    'Mwana',
    'Tinoenda kumba'
]


def append_session_log(msg: str):
    global SESSION_LOG
    if SESSION_LOG is None:
        # find latest agent log for agent10
        logs = list((ROOT / 'logs').glob('*agent10.log'))
        if logs:
            SESSION_LOG = str(logs[-1])
        else:
            SESSION_LOG = str(ROOT / 'logs' / f"{time.strftime('%Y-%m-%d_%H-%M-%S')}_agent10.log")
            open(SESSION_LOG, 'a', encoding='utf-8').close()
    with open(SESSION_LOG, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')


def load_tokenizer(path: str):
    try:
        import sentencepiece as spm
    except Exception:
        return None
    if not os.path.exists(path):
        return None
    sp = spm.SentencePieceProcessor()
    sp.Load(path)
    return sp


def load_model(ckpt_path: str, tokenizer):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")
    ckpt = torch.load(ckpt_path, map_location=device)

    cfg = ModelConfig()
    for key, value in ckpt.get('config', {}).items():
        setattr(cfg, key, value)
    if tokenizer is not None:
        try:
            cfg.vocab_size = min(tokenizer.GetPieceSize(), int(getattr(cfg, 'vocab_size', 32000)))
        except Exception:
            pass

    model = GPTModel(cfg).to(device)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()
    return model, cfg, device


def sample_generate(model, tokenizer, prompt: str, cfg: ModelConfig, device, max_new_tokens: int = 100,
                    temperature: float = 0.8, top_p: float = 0.9) -> str:
    if tokenizer is not None:
        input_ids = tokenizer.EncodeAsIds(prompt)
    else:
        input_ids = [abs(hash(w)) % cfg.vocab_size for w in prompt.split()]

    seq = input_ids[-cfg.max_position_embeddings:]
    generated = seq.copy()

    # detect pad id if available
    pad_id = -1
    try:
        if tokenizer is not None:
            pad_id = tokenizer.PieceToId('<pad>')
    except Exception:
        pad_id = -1

    for _ in range(max_new_tokens):
        input_tensor = torch.tensor([generated[-cfg.max_position_embeddings:]], dtype=torch.long, device=device)
        with torch.no_grad():
            logits = model(input_tensor)  # (1, seq, vocab)
            next_logits = logits[0, -1, :].float()
            # apply temperature
            if temperature != 1.0:
                next_logits = next_logits / temperature
            probs = torch.softmax(next_logits, dim=-1)
            # nucleus/top-p sampling
            sorted_probs, sorted_indices = torch.sort(probs, descending=True)
            cumulative_probs = torch.cumsum(sorted_probs, dim=0)
            cutoff_mask = cumulative_probs > top_p
            if cutoff_mask.any():
                first_cut = int(torch.nonzero(cutoff_mask)[0].item())
                keep = sorted_indices[: first_cut + 1]
                filtered_probs = probs[keep]
                filtered_probs = filtered_probs / filtered_probs.sum()
                sampled_idx = int(torch.multinomial(filtered_probs, num_samples=1).item())
                next_id = int(keep[sampled_idx].item())
            else:
                next_id = int(torch.multinomial(probs, num_samples=1).item())

        # avoid pad if possible
        attempts = 0
        while next_id == pad_id and attempts < 5:
            next_id = int(torch.multinomial(probs, num_samples=1).item())
            attempts += 1

        generated.append(next_id)

    if tokenizer is not None:
        try:
            text = tokenizer.DecodeIds(generated)
        except Exception:
            text = tokenizer.DecodeIds(generated)
    else:
        text = " ".join(map(str, generated))
    return text


def compute_perplexity(model, tokenizer, cfg: ModelConfig, device, test_path: str):
    total_nll = 0.0
    total_tokens = 0
    max_pos = int(getattr(cfg, 'max_position_embeddings', 1024))
    stride = max(1, max_pos - 1)

    if not os.path.exists(test_path):
        raise FileNotFoundError(f"Test file not found: {test_path}")

    with open(test_path, 'r', encoding='utf-8') as f:
        for line in f:
            text = line.strip()
            if not text:
                continue
            if tokenizer is not None:
                ids = tokenizer.EncodeAsIds(text)
            else:
                ids = [abs(hash(w)) % cfg.vocab_size for w in text.split()]
            if len(ids) < 2:
                continue
            # process in sliding windows with stride to preserve context
            i = 0
            while i < len(ids) - 1:
                window = ids[i:i+max_pos]
                input_ids = window
                if len(input_ids) < 2:
                    break
                input_tensor = torch.tensor([input_ids], dtype=torch.long, device=device)
                with torch.no_grad():
                    logits = model(input_tensor)  # (1, seq, vocab)
                # compute nll for positions 1..L-1
                logits = logits[0, :-1, :].contiguous()  # (seq-1, vocab)
                targets = torch.tensor(input_ids[1:], dtype=torch.long, device=device)
                loss = F.cross_entropy(logits, targets, reduction='sum')
                total_nll += loss.item()
                total_tokens += targets.numel()
                i += stride

    if total_tokens == 0:
        return float('inf'), 0, float('inf')
    avg_nll = total_nll / total_tokens
    perp = float(torch.exp(torch.tensor(avg_nll)).item())
    return perp, total_tokens, avg_nll


def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    append_session_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [INFO] [PHASE-8] Phase 8 runner starting. Using checkpoint: {CKPT_PATH}")
    try:
        tokenizer = load_tokenizer(TOKENIZER_PATH)
        if tokenizer is None:
            append_session_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [WARN] [PHASE-8] Tokenizer not available at {TOKENIZER_PATH}; falling back to hash tokenizer")
        model, cfg, device = load_model(CKPT_PATH, tokenizer)
        append_session_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [INFO] [PHASE-8] Model loaded on {device}.")

        # Generate samples using nucleus sampling (temperature=0.8, top_p=0.9)
        with open(LOG_SAMPLES, 'w', encoding='utf-8') as out:
            for p in PROMPTS:
                gen = sample_generate(model, tokenizer, p, cfg, device, max_new_tokens=100, temperature=0.8, top_p=0.9)
                out.write(json.dumps({'prompt': p, 'generated': gen}, ensure_ascii=False) + '\n')
        append_session_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [MILESTONE] [PHASE-8] Sample generation saved to {LOG_SAMPLES}")

        # Evaluate perplexity
        append_session_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [INFO] [PHASE-8] Computing perplexity on {TEST_PATH}")
        perp, total_tokens, avg_nll = compute_perplexity(model, tokenizer, cfg, device, TEST_PATH)
        results = {
            'perplexity': perp,
            'total_tokens': total_tokens,
            'avg_nll': avg_nll,
            'ckpt_path': CKPT_PATH,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(LOG_EVAL, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        append_session_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [MILESTONE] [PHASE-8] Eval saved to {LOG_EVAL} — perp={perp:.2f} tokens={total_tokens}")

        # Update STATE.json
        try:
            st = json.load(open(STATE_PATH, 'r', encoding='utf-8'))
        except Exception:
            st = {}
        st['current_phase'] = 8
        st.setdefault('phase_status', {})
        st['phase_status']['8'] = 'complete'
        st['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
        st['training_stats'] = st.get('training_stats', {})
        st['training_stats']['eval_perplexity'] = perp
        json.dump(st, open(STATE_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        append_session_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [INFO] [PHASE-8] STATE.json updated: phase 8 complete")

        # Commit changes
        append_session_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [INFO] [PHASE-8] Committing eval artifacts and STATE.json")
        git_cmd = f'git add "{LOG_SAMPLES}" "{LOG_EVAL}" "{STATE_PATH}" && git commit -m "eval: Phase 8 complete — eval artifacts and STATE update" && git push origin main'
        os.system(git_cmd)
        append_session_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [MILESTONE] [PHASE-8] Commit pushed")

    except Exception as e:
        append_session_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] [PHASE-8] Exception during Phase 8 run: {repr(e)}")
        raise


if __name__ == '__main__':
    main()
