"""
hmas.agents.tinyfish_client
───────────────────────────
SSE streaming client for the TinyFish Web Agent API.

The agent autonomously navigates live ticketing websites (Ticketmaster,
Songkick, Bandcamp) to find real-time tour dates and ticket prices.
This is the "Hands" layer — it does genuine multi-step web automation:
  1. Navigate to ticketing site
  2. Dismiss cookie consent popups
  3. Search for the artist
  4. Parse event listings, dates, venues, prices
  5. Return structured JSON with ticket URLs

The SSE stream lets the frontend show each step in real-time,
demonstrating the agent "thinking" and acting on the live web.

API Reference: https://docs.tinyfish.ai/api-reference/automation/run-sse
  - Auth: X-API-Key header
  - Body: { url, goal, browser_profile }
  - SSE events: STARTED → PROGRESS* → COMPLETE
"""

from __future__ import annotations

import json
from typing import AsyncGenerator, Generator

import httpx

from hmas.core.config import settings

# ── Master Agent Goal ─────────────────────────────────────────────────────────
# The `goal` tells TinyFish what multi-step web workflow to perform.

AGENT_GOAL = """
You are a music event discovery agent.

Search for '{artist_name}' on this website.

Steps:
1. Dismiss any cookie consent popup or overlay immediately
2. Use the search bar to search for '{artist_name}'
3. Wait for results to load, select the best artist match
4. Navigate to their upcoming events / tour dates
5. For each event, extract: event name, date, venue, city, and ticket price
6. Identify the cheapest available ticket

Return your findings as JSON:
{{
  "status": "found" | "no_upcoming_events",
  "events": [
    {{
      "event_name": "...",
      "date": "YYYY-MM-DD",
      "venue": "...",
      "city": "...",
      "price": "$XX.XX",
      "ticket_url": "https://..."
    }}
  ],
  "cheapest_ticket": {{
    "event_name": "...",
    "price": "$XX.XX",
    "ticket_url": "https://..."
  }}
}}

If no events are found, return {{ "status": "no_upcoming_events" }}
Do NOT hallucinate data — only return what you actually find on the page.
"""


def _get_headers() -> dict:
    """Build authentication headers for TinyFish API (X-API-Key)."""
    api_key = settings.tinyfish_api_key
    if not api_key:
        raise ValueError(
            "HMAS_TINYFISH_API_KEY not set. "
            "Add it to your .env file or set the environment variable."
        )
    return {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }


def _build_payload(artist: str) -> dict:
    """Build the TinyFish API request payload."""
    return {
        "url": "https://www.ticketmaster.com",
        "goal": AGENT_GOAL.format(artist_name=artist),
        "browser_profile": "stealth",
    }


def _parse_sse_event(event: dict) -> dict:
    """
    Normalize TinyFish SSE events into a consistent format for the frontend.

    TinyFish event types:
      STARTED     → Agent has begun
      STREAMING_URL → Live browser stream URL
      PROGRESS    → Intermediate step with 'purpose' field
      COMPLETE    → Final result with 'resultJson' and 'status'
      HEARTBEAT   → Keep-alive (skip)
    """
    event_type = event.get("type", "unknown").upper()

    if event_type == "STARTED":
        return {"type": "action", "content": f"🚀 Agent started (run: {event.get('runId', 'N/A')})"}
    elif event_type == "STREAMING_URL":
        url = event.get("streamingUrl", "")
        return {"type": "action", "content": f"🖥️ Live browser stream: {url}", "streamingUrl": url}
    elif event_type == "PROGRESS":
        purpose = event.get("purpose", "Working...")
        return {"type": "action", "content": purpose}
    elif event_type == "COMPLETE":
        status = event.get("status", "UNKNOWN")
        result = event.get("resultJson", event.get("result", {}))
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except (json.JSONDecodeError, TypeError):
                result = {"raw": result}
        return {
            "type": "complete",
            "content": f"✅ Agent completed with status: {status}",
            "status": result.get("status", "found") if isinstance(result, dict) else "found",
            "events": result.get("events", []) if isinstance(result, dict) else [],
            "source": "ticketmaster",
            "cheapest_ticket": result.get("cheapest_ticket") if isinstance(result, dict) else None,
            "resultJson": result,
        }
    elif event_type == "HEARTBEAT":
        return None  # Skip heartbeats
    else:
        # Pass through unknown event types
        content = event.get("purpose", event.get("message", event.get("content", json.dumps(event))))
        return {"type": "raw", "content": str(content)}


def run_agent_sync(artist: str, timeout: int = 180) -> Generator[dict, None, None]:
    """
    Synchronous SSE streaming client for TinyFish.
    Yields parsed JSON events from the agent's execution stream.
    """
    payload = _build_payload(artist)
    headers = _get_headers()

    with httpx.stream(
        "POST",
        settings.tinyfish_api_url,
        json=payload,
        headers=headers,
        timeout=timeout,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line.startswith("data:"):
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    raw_event = json.loads(data_str)
                    parsed = _parse_sse_event(raw_event)
                    if parsed is not None:
                        yield parsed
                except json.JSONDecodeError:
                    yield {"type": "raw", "content": data_str}


async def run_agent_async(
    artist: str, timeout: int = 180
) -> AsyncGenerator[dict, None]:
    """
    Async SSE streaming client for TinyFish (for FastAPI StreamingResponse).
    Yields parsed events — forwarded to the frontend via SSE in real-time.
    """
    payload = _build_payload(artist)
    headers = _get_headers()

    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream(
            "POST",
            settings.tinyfish_api_url,
            json=payload,
            headers=headers,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        raw_event = json.loads(data_str)
                        parsed = _parse_sse_event(raw_event)
                        if parsed is not None:
                            yield parsed
                    except json.JSONDecodeError:
                        yield {"type": "raw", "content": data_str}
