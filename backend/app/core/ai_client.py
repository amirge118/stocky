"""Shared Claude API client with JSON-from-markdown parsing."""
import json
import re
from typing import Optional

import anthropic

from app.core.config import settings


def _parse_json_response(raw: str) -> dict:
    """Parse JSON that may be wrapped in markdown code fences."""
    raw = raw.strip()
    # Strip markdown fences robustly (handles ```json, ``` json, ``` etc.)
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if match:
        raw = match.group(1).strip()
    return json.loads(raw)


def call_claude(
    prompt: str,
    max_tokens: int = 600,
    model: str = "claude-haiku-4-5-20251001",
) -> tuple[str, Optional[int]]:
    """Call Claude and return (raw_text, total_tokens)."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text if message.content else "{}"
    tokens = (
        message.usage.input_tokens + message.usage.output_tokens
        if message.usage
        else None
    )
    return raw, tokens


def call_claude_json(
    prompt: str,
    max_tokens: int = 600,
    model: str = "claude-haiku-4-5-20251001",
) -> tuple[dict, Optional[int]]:
    """Call Claude, parse the response as JSON, and return (data, total_tokens)."""
    raw, tokens = call_claude(prompt, max_tokens=max_tokens, model=model)
    return _parse_json_response(raw), tokens
