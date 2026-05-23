from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch

from inference.generate import load_tokenizer, build_model_from_checkpoint, generate

APP = FastAPI()


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 100


@APP.on_event("startup")
def load_resources():
    global MODEL, TOKENIZER, DEVICE
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
    try:
        TOKENIZER = load_tokenizer('tokenizer/shona_bpe.model')
    except Exception as e:
        raise RuntimeError(f"Failed to load tokenizer: {e}")

    try:
        MODEL, _ = build_model_from_checkpoint('training/checkpoints/shona_ai_final.pt', TOKENIZER, device=DEVICE)
    except Exception as e:
        raise RuntimeError(f"Failed to load model checkpoint: {e}")


@APP.get('/health')
def health():
    return {"status": "ok", "model_loaded": True}


@APP.post('/generate')
def api_generate(req: GenerateRequest):
    if not req.prompt or not isinstance(req.prompt, str):
        raise HTTPException(status_code=400, detail="`prompt` must be a non-empty string")

    try:
        text = generate(
            MODEL,
            TOKENIZER,
            req.prompt,
            max_tokens=req.max_tokens,
            temperature=0.8,
            top_p=0.9,
            device=DEVICE,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"generated": text}
