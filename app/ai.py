"""Thin, failure-proof wrapper around the Gemini SDK.

Every function returns None on any problem so callers can fall back to the
built-in generators without special error handling.
"""
import json
import logging
import re
from typing import Any

from . import config

log = logging.getLogger("movemap.ai")
_client = None


def _get_client():
    global _client
    if _client is None:
        from google import genai
        from google.genai import types

        _client = genai.Client(
            api_key=config.GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=30000),
        )
    return _client


def _call(prompt: str, model: str, as_json: bool) -> str:
    from google.genai import types

    cfg = types.GenerateContentConfig(
        temperature=0.7,
        response_mime_type="application/json" if as_json else "text/plain",
    )
    resp = _get_client().models.generate_content(model=model, contents=prompt, config=cfg)
    return (resp.text or "").strip()


def ask_json(prompt: str, model: str) -> Any | None:
    if not config.gemini_enabled():
        return None
    try:
        text = _call(prompt, model, as_json=True)
        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
        return json.loads(text)
    except Exception as exc:  # noqa: BLE001 - deliberate catch-all
        log.warning("Gemini JSON call failed: %s", exc)
        return None


def ask_text(prompt: str, model: str) -> str | None:
    if not config.gemini_enabled():
        return None
    try:
        return _call(prompt, model, as_json=False) or None
    except Exception as exc:  # noqa: BLE001
        log.warning("Gemini text call failed: %s", exc)
        return None
