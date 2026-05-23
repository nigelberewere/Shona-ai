# Shona AI — Inference API

Run the FastAPI inference server:

```bash
pip install -r api/requirements.txt
uvicorn api.main:APP --reload
```

Endpoints:
- `GET /health` — health check
- `POST /generate` — body: {"prompt": "Shona text", "max_tokens": 100}
