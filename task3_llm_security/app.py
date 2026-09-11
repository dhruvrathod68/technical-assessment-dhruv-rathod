"""
Meridian Grid Security - Local LLM Reverse Proxy (Task 3)
FastAPI security proxy sitting in front of the local Ollama API.

Enforces:
1. Authentication: Enforced via X-API-Key or Authorization Bearer header (HTTP 401).
2. Rate Limiting: 10 requests/minute per client IP via SlowAPI (HTTP 429).
3. Resource Constraints: Prompt limit 2,000 chars (HTTP 413), 30s timeout, num_predict 256.
4. Prompt Injection Defense: Detection & rejection (HTTP 400), strict <user_input> isolation.
5. Context Leakage Protection: Hardened system prompt & outbound canary response scrubber.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from .security import (
    limiter,
    RATE_LIMIT_RULE,
    verify_authentication,
    validate_payload_length,
    sanitize_and_isolate_prompt,
    scrub_completion,
    HARDENED_SYSTEM_PROMPT,
    UPSTREAM_TIMEOUT_SECONDS,
    MAX_PREDICT_TOKENS,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("llm_security_proxy")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


# ==============================================================================
# REQUEST & RESPONSE MODELS
# ==============================================================================
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role (user, system, assistant)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    model: str = Field("llama3.2:3b", description="Target model name (e.g., llama3.2:3b, llama3:latest)")
    messages: List[ChatMessage] = Field(..., description="Chat conversation history")
    stream: bool = Field(False, description="Streaming mode (default: false)")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Model generation options")


class GenerateRequest(BaseModel):
    model: str = Field("llama3.2:3b", description="Target model name (e.g., llama3.2:3b, llama3:latest)")
    prompt: str = Field(..., description="Generation prompt")
    system: Optional[str] = Field(None, description="Optional custom system prompt")
    stream: bool = Field(False, description="Streaming mode (default: false)")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Model generation options")


# ==============================================================================
# FASTAPI APPLICATION SETUP
# ==============================================================================
app = FastAPI(
    title="Meridian Grid LLM Security Proxy",
    version="1.0.0",
    description="Hardened reverse proxy defending local Ollama endpoints against authentication bypass, prompt injection, context leakage, and resource exhaustion.",
)

# Register SlowAPI limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/health", tags=["Health"])
async def health_check():
    """Healthcheck endpoint reporting proxy status."""
    return {
        "status": "healthy",
        "service": "Meridian Grid LLM Security Proxy",
        "upstream_target": OLLAMA_BASE_URL,
    }


# ==============================================================================
# PROTECTED GENERATIVE ENDPOINTS
# ==============================================================================
@app.post("/api/chat", tags=["Ollama Proxy"])
@limiter.limit(RATE_LIMIT_RULE)
async def proxy_chat(
    request: Request,
    payload: ChatRequest,
    authenticated_key: str = Depends(verify_authentication),
):
    """
    Secure chat proxy endpoint forwarding client requests to upstream Ollama `/api/chat`.
    Applies auth, rate limits, prompt length checks, injection defenses, and response scrubbing.
    """
    if not payload.messages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Messages array cannot be empty")

    # Locate the latest user message
    user_msgs = [m for m in payload.messages if m.role.lower() == "user"]
    if not user_msgs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user message found in conversation")

    latest_user_msg = user_msgs[-1]
    raw_prompt = latest_user_msg.content

    # 1. Enforce payload constraints (Resource Exhaustion Defense)
    validate_payload_length(raw_prompt)

    # 2. Enforce prompt injection defense & isolation delimiters
    isolated_prompt = sanitize_and_isolate_prompt(raw_prompt)

    # 3. Assemble hardened upstream messages payload with system prompt & canary
    hardened_messages = [{"role": "system", "content": HARDENED_SYSTEM_PROMPT}]
    for msg in payload.messages[:-1]:
        # Preserve prior context while ensuring no system injection
        if msg.role.lower() != "system":
            hardened_messages.append({"role": msg.role, "content": msg.content})
    hardened_messages.append({"role": "user", "content": isolated_prompt})

    # 4. Enforce safe generation limits to protect GPU VRAM
    safe_options = payload.options or {}
    safe_options["num_predict"] = safe_options.get("num_predict", MAX_PREDICT_TOKENS)
    # Ensure num_predict cannot exceed safe maximum
    safe_options["num_predict"] = min(safe_options["num_predict"], MAX_PREDICT_TOKENS)

    upstream_payload = {
        "model": payload.model,
        "messages": hardened_messages,
        "stream": False,
        "options": safe_options,
    }

    # 5. Forward request to upstream Ollama with timeout protection
    try:
        async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT_SECONDS) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=upstream_payload)
            if resp.status_code != 200:
                logger.error(f"Upstream Ollama error {resp.status_code}: {resp.text}")
                return Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    media_type="application/json",
                )
            upstream_data = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Upstream LLM generation timed out after 60 seconds",
        )
    except httpx.RequestError as exc:
        logger.error(f"Failed to connect to upstream Ollama: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to reach upstream Ollama service at {OLLAMA_BASE_URL}",
        )

    # 6. Outbound Context / System Prompt Leakage Scrubbing
    raw_response_content = upstream_data.get("message", {}).get("content", "")
    scrubbed_content, was_scrubbed = scrub_completion(raw_response_content)

    upstream_data["message"]["content"] = scrubbed_content
    headers = {"X-Content-Scrubbed": "true"} if was_scrubbed else {}

    return JSONResponse(content=upstream_data, headers=headers)


@app.post("/api/generate", tags=["Ollama Proxy"])
@limiter.limit(RATE_LIMIT_RULE)
async def proxy_generate(
    request: Request,
    payload: GenerateRequest,
    authenticated_key: str = Depends(verify_authentication),
):
    """
    Secure generate proxy endpoint forwarding client requests to upstream Ollama `/api/generate`.
    Applies auth, rate limits, prompt length checks, injection defenses, and response scrubbing.
    """
    raw_prompt = payload.prompt

    # 1. Enforce payload constraints (Resource Exhaustion Defense)
    validate_payload_length(raw_prompt)

    # 2. Enforce prompt injection defense & isolation delimiters
    isolated_prompt = sanitize_and_isolate_prompt(raw_prompt)

    # 3. Enforce safe generation limits to protect GPU VRAM
    safe_options = payload.options or {}
    safe_options["num_predict"] = safe_options.get("num_predict", MAX_PREDICT_TOKENS)
    safe_options["num_predict"] = min(safe_options["num_predict"], MAX_PREDICT_TOKENS)

    upstream_payload = {
        "model": payload.model,
        "prompt": isolated_prompt,
        "system": HARDENED_SYSTEM_PROMPT,
        "stream": False,
        "options": safe_options,
    }

    # 4. Forward request to upstream Ollama with timeout protection
    try:
        async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT_SECONDS) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=upstream_payload)
            if resp.status_code != 200:
                logger.error(f"Upstream Ollama error {resp.status_code}: {resp.text}")
                return Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    media_type="application/json",
                )
            upstream_data = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Upstream LLM generation timed out after 60 seconds",
        )
    except httpx.RequestError as exc:
        logger.error(f"Failed to connect to upstream Ollama: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to reach upstream Ollama service at {OLLAMA_BASE_URL}",
        )

    # 5. Outbound Context / System Prompt Leakage Scrubbing
    raw_response_content = upstream_data.get("response", "")
    scrubbed_content, was_scrubbed = scrub_completion(raw_response_content)

    upstream_data["response"] = scrubbed_content
    headers = {"X-Content-Scrubbed": "true"} if was_scrubbed else {}

    return JSONResponse(content=upstream_data, headers=headers)
