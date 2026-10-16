"""Generation with Claude, with record and replay.

live    call the API and store the full request and response under runs/recordings/
replay  load the stored response for the same request; no API key or network needed

The recording key is the SHA-256 of the canonical request plus the run number, so a replay is only
accepted for exactly the request (model, effort, schema, prompt, retrieved chunks) that produced it.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .prompt import OUTPUT_SCHEMA, SYSTEM, canonical


def build_request(settings, user_text):
    return {
        "model": settings.model,
        "max_tokens": settings.max_tokens,
        "system": SYSTEM,
        "messages": [{"role": "user", "content": user_text}],
        "output_config": {"effort": settings.effort,
                          "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
    }


def request_key(request, run):
    return hashlib.sha256((canonical(request) + f"#run{run}").encode("utf-8")).hexdigest()[:20]


class GenerationError(RuntimeError):
    pass


def generate(request, run, mode, rec_dir):
    rec_dir = Path(rec_dir)
    key = request_key(request, run)
    path = rec_dir / f"{key}.json"
    if mode == "replay":
        if not path.exists():
            raise GenerationError(f"no recording {path.name}; run in live mode first")
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec["request"] != request:
            raise GenerationError(f"recording {path.name} was made for a different request")
        return rec
    if path.exists():  # live mode resumes: a request that is already recorded is not sent again
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec["request"] == request:
            return rec
    import anthropic
    client = anthropic.Anthropic()
    with client.messages.stream(**request) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise GenerationError(f"model declined the request: {msg.stop_details}")
    if msg.stop_reason == "max_tokens":
        raise GenerationError("output truncated at max_tokens")
    text = next(b.text for b in msg.content if b.type == "text")
    rec = {
        "key": key,
        "run": run,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "request": request,
        "response_id": msg.id,
        "request_id": getattr(msg, "_request_id", None),
        "model_served": msg.model,
        "stop_reason": msg.stop_reason,
        "usage": msg.usage.to_dict(),
        "output": json.loads(text),
    }
    rec_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    return rec
