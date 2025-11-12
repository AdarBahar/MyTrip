"""
SSE proxy router: exposes /api/location/live/sse to browsers.
It forwards to the canonical SSE endpoint at {BASE}/location/live/sse and injects X-API-Token.

Env vars:
- LOC_API_TOKEN: required (secret header for upstream)
- MYTRIPS_API_BASEURL: optional (defaults to APP_BASE_URL or http://localhost:8000)
- APP_BASE_URL: optional fallback if MYTRIPS_API_BASEURL is missing
"""
from __future__ import annotations

import os
import logging
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.get("/location/live/sse")
async def location_live_sse_proxy(request: Request):
    """
    SSE proxy endpoint for browser clients that cannot send custom headers.
    Streams upstream SSE from the MyTrips API and injects X-API-Token.
    """

    async def stream() -> AsyncGenerator[str, None]:
        token = (os.environ.get("LOC_API_TOKEN") or "").strip()
        if not token:
            logging.error("LOC_API_TOKEN not configured")
            yield "event: error\n"
            yield "data: {\"error\": \"API token not configured\"}\n\n"
            return

        base = (
            os.environ.get("MYTRIPS_API_BASEURL")
            or os.environ.get("APP_BASE_URL")
            or "http://localhost:8000"
        )
        base = base.rstrip("/")
        target = f"{base}/location/live/sse"

        headers = {
            "X-API-Token": token,
            "Accept": "text/event-stream",
            # Help upstream treat this as a streaming request
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        last_event_id = request.headers.get("Last-Event-ID")
        if last_event_id:
            headers["Last-Event-ID"] = last_event_id

        params = dict(request.query_params)

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "GET", target, params=params, headers=headers
                ) as resp:
                    if resp.status_code != 200:
                        logging.error("Upstream SSE error: %s %s", resp.status_code, target)
                        yield "event: error\n"
                        yield (
                            f"data: {{\"error\": \"upstream status {resp.status_code}\"}}\n\n"
                        )
                        return

                    async for line in resp.aiter_lines():
                        # Stop streaming if client disconnected
                        if await request.is_disconnected():
                            break
                        # Forward lines verbatim, preserving empty lines as SSE frame delimiters
                        yield (line + "\n") if line is not None else "\n"
        except httpx.TimeoutException:
            logging.exception("Upstream SSE timeout")
            yield "event: error\n"
            yield "data: {\"error\": \"API timeout\"}\n\n"
        except Exception as e:  # noqa: BLE001
            logging.exception("SSE proxy error: %s", e)
            yield "event: error\n"
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Disable proxy buffering (nginx) to ensure immediate flush of SSE frames
            "X-Accel-Buffering": "no",
        },
    )

