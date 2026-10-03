"""Codex's model requests (OpenAI Responses API): who sent them, and running them on another model.

Codex (0.159) sends POST {openai_base_url}/responses with headers that say which
conversation and which turn a request belongs to:

    session-id: <thread id>
    x-codex-turn-metadata: {"session_id": ..., "turn_id": ..., "request_kind": "turn" | "prewarm" | ...}

With a ChatGPT sign-in the body is zstd-compressed (Content-Encoding: zstd).
"""

import gzip
import json
import zlib
from typing import Any, Dict, Optional, Tuple

from .catalog import ModelInfo

try:  # optional: needed to read ChatGPT sign-in requests (installed by scripts/install_codex.sh)
    import zstandard
except ImportError:  # pragma: no cover - depends on the environment
    zstandard = None

EFFORT_ORDER = ("none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra")
MAX_DECODED_BYTES = 64 * 1024 * 1024


def turn_metadata(headers) -> Dict[str, Any]:
    raw = headers.get("x-codex-turn-metadata")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def request_identity(headers, body: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """(session id, turn id, request kind) of a Codex request; None where unknown."""
    meta = turn_metadata(headers)
    client_meta = body.get("client_metadata") if isinstance(body.get("client_metadata"), dict) else {}
    session_id = (headers.get("session-id") or headers.get("session_id") or meta.get("session_id")
                  or client_meta.get("session_id") or body.get("prompt_cache_key"))
    turn_id = meta.get("turn_id") or client_meta.get("turn_id")
    kind = meta.get("request_kind")
    return ((str(session_id) if session_id else None), (str(turn_id) if turn_id else None),
            (str(kind) if kind else None))


def zstd_available() -> bool:
    return zstandard is not None


def decode_body(raw: bytes, encoding: str) -> Optional[bytes]:
    """The request body as plain bytes, or None if it can't be read here."""
    encoding = (encoding or "").strip().lower()
    try:
        if encoding in ("", "identity"):
            return raw
        if encoding == "gzip":
            return gzip.decompress(raw)
        if encoding == "deflate":
            return zlib.decompress(raw)
        if encoding == "zstd" and zstandard is not None:
            return zstandard.ZstdDecompressor().decompress(raw, max_output_size=MAX_DECODED_BYTES)
    except Exception:  # corrupt or unexpected data: forward it untouched instead
        return None
    return None


def closest_effort(effort: str, supported) -> str:
    """The strongest supported reasoning effort that isn't above `effort` (else the lowest supported)."""
    supported = [level for level in EFFORT_ORDER if level in supported]
    if not supported or effort not in EFFORT_ORDER:
        return effort
    wanted = EFFORT_ORDER.index(effort)
    lower = [level for level in supported if EFFORT_ORDER.index(level) <= wanted]
    return lower[-1] if lower else supported[0]


def adapt_request(body: Dict[str, Any], target: ModelInfo) -> Dict[str, Any]:
    """The same request for `target`, adjusted to what that model supports (per Codex's model list)."""
    routed = dict(body)
    routed["model"] = target.id

    reasoning = routed.get("reasoning")
    if isinstance(reasoning, dict) and target.reasoning_levels and reasoning.get("effort"):
        effort = str(reasoning["effort"])
        if effort not in target.reasoning_levels:
            routed["reasoning"] = dict(reasoning, effort=closest_effort(effort, target.reasoning_levels))

    text = routed.get("text")
    if target.supports_verbosity is False and isinstance(text, dict) and "verbosity" in text:
        text = {k: v for k, v in text.items() if k != "verbosity"}
        if text:
            routed["text"] = text
        else:
            routed.pop("text")

    tier = routed.get("service_tier")
    if (isinstance(tier, str) and tier not in ("auto", "default") and target.service_tiers is not None
            and tier not in target.service_tiers):
        routed.pop("service_tier")  # e.g. fast mode on a model that doesn't offer it
    return routed
