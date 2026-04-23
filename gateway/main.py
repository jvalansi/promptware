import json
import time
import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from .config import get_customer
from .logger import log_request

ROUTELLM_URL = os.getenv("ROUTELLM_URL", "http://localhost:18080")

app = FastAPI(title="Promptware Gateway")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing API key")

    customer_key = auth.removeprefix("Bearer ").strip()
    customer = get_customer(customer_key)
    if customer is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    body_bytes = await request.body()
    body = json.loads(body_bytes)

    forward_headers = {
        "Authorization": f"Bearer {customer['openai_key']}",
        "Content-Type": "application/json",
    }

    t0 = time.time()

    if body.get("stream"):
        return StreamingResponse(
            _stream(body_bytes, forward_headers),
            media_type="text/event-stream",
        )

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{ROUTELLM_URL}/v1/chat/completions",
            content=body_bytes,
            headers=forward_headers,
        )

    if resp.status_code != 200:
        return JSONResponse(status_code=resp.status_code, content=resp.json())

    resp_data = resp.json()
    latency_ms = int((time.time() - t0) * 1000)
    log_request(customer["id"], body, resp_data, latency_ms)

    return JSONResponse(content=resp_data)


async def _stream(body_bytes: bytes, headers: dict):
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream(
            "POST",
            f"{ROUTELLM_URL}/v1/chat/completions",
            content=body_bytes,
            headers=headers,
        ) as resp:
            async for chunk in resp.aiter_bytes():
                yield chunk
