import json
import time
import os
import httpx
import litellm
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from routellm.controller import Controller
from .config import get_customer
from .logger import log_request

ROUTELLM_URL = os.getenv("ROUTELLM_URL", "http://localhost:18080")

DEFAULT_WEAK = {"openai": "gpt-4o-mini", "anthropic": "anthropic/claude-haiku-4-5-20251001"}
DEFAULT_STRONG = {"openai": "gpt-4o", "anthropic": "anthropic/claude-sonnet-4-5"}

app = FastAPI(title="Promptware Gateway")
_controller = None


def get_controller() -> Controller:
    global _controller
    if _controller is None:
        _controller = Controller(routers=["mf"], strong_model="strong", weak_model="weak")
    return _controller


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

    provider = customer.get("provider", "openai")
    threshold = customer.get("threshold", 0.11593)
    api_key = customer.get("api_key") or customer.get("openai_key")

    if provider == "openai":
        return await _handle_openai(body, body_bytes, api_key, threshold, customer)

    return await _handle_litellm(body, api_key, threshold, provider, customer)


async def _handle_openai(body, body_bytes, api_key, threshold, customer):
    body["model"] = f"router-mf-{threshold}"
    body_bytes = json.dumps(body).encode()

    forward_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    t0 = time.time()

    if body.get("stream"):
        return StreamingResponse(
            _stream_openai(body_bytes, forward_headers),
            media_type="text/event-stream",
        )

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{ROUTELLM_URL}/v1/chat/completions",
            content=body_bytes,
            headers=forward_headers,
        )

    try:
        resp_data = resp.json()
    except Exception:
        return JSONResponse(status_code=502, content={"error": resp.text})

    if resp.status_code != 200:
        return JSONResponse(status_code=resp.status_code, content=resp_data)

    latency_ms = int((time.time() - t0) * 1000)
    log_request(customer["id"], body, resp_data, latency_ms)
    return JSONResponse(content=resp_data)


async def _handle_litellm(body, api_key, threshold, provider, customer):
    messages = body.get("messages", [])

    routed = get_controller().route(prompt=messages, router="mf", threshold=threshold)
    if routed == "strong":
        model = customer.get("strong_model", DEFAULT_STRONG.get(provider, DEFAULT_STRONG["openai"]))
    else:
        model = customer.get("weak_model", DEFAULT_WEAK.get(provider, DEFAULT_WEAK["openai"]))

    kwargs = {"model": model, "messages": messages, "api_key": api_key}
    for param in ["temperature", "max_tokens", "top_p", "stop"]:
        if param in body:
            kwargs[param] = body[param]

    t0 = time.time()

    if body.get("stream"):
        kwargs["stream"] = True
        return StreamingResponse(_stream_litellm(kwargs), media_type="text/event-stream")

    resp = await litellm.acompletion(**kwargs)
    resp_data = resp.model_dump()
    latency_ms = int((time.time() - t0) * 1000)
    log_request(customer["id"], body, resp_data, latency_ms)
    return JSONResponse(content=resp_data)


async def _stream_openai(body_bytes: bytes, headers: dict):
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream(
            "POST",
            f"{ROUTELLM_URL}/v1/chat/completions",
            content=body_bytes,
            headers=headers,
        ) as resp:
            async for chunk in resp.aiter_bytes():
                yield chunk


async def _stream_litellm(kwargs: dict):
    resp = await litellm.acompletion(**kwargs)
    async for chunk in resp:
        yield f"data: {json.dumps(chunk.model_dump())}\n\n"
    yield "data: [DONE]\n\n"
