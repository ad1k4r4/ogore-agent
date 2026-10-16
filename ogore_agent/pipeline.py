"""Steps 1 to 3 of Activity 2.1 (structured query, retrieval, generation) followed by the validation rules.
Step 4, the analyst review, is human work: the pipeline writes a review sheet for it."""
import csv
import json
from pathlib import Path

from . import __version__
from .config import Settings
from .generate import build_request, generate
from .kb import chunk, kb_hash, load_entries
from .prompt import build_user
from .retrieve import top_k
from .validate import check


def run_query(query, kb_dir, out_dir, runs=1, mode="replay", settings=Settings(), rec_dir=None):
    entries = load_entries(kb_dir)
    chunks = chunk(entries)
    retrieved = top_k(query, chunks, settings.top_k)
    retrieved_ids = sorted({c.pattern_id for c, _ in retrieved})
    request = build_request(settings, build_user(query, retrieved))
    out = Path(out_dir) / query["query_id"]
    out.mkdir(parents=True, exist_ok=True)
    rec_dir = Path(rec_dir) if rec_dir else Path(out_dir) / "recordings"
    results = []
    for r in range(1, runs + 1):
        rec = generate(request, r, mode, rec_dir)
        rows = check(rec["output"], query, retrieved_ids)
        log = {
            "pipeline_version": __version__,
            "settings": settings.to_dict(),
            "kb_sha256": kb_hash(entries),
            "query": query,
            "retrieved": [{"chunk_id": c.chunk_id, "score": s} for c, s in retrieved],
            "recording": rec["key"],
            "response_id": rec.get("response_id"),
            "model_served": rec.get("model_served"),
            "usage": rec.get("usage"),
            "output": rec["output"],
            "validation": rows,
            "summary": {s: sum(1 for x in rows if x["status"] == s) for s in ("passed", "flagged", "rejected")},
        }
        (out / f"run_{r}.json").write_text(json.dumps(log, indent=1, ensure_ascii=False), encoding="utf-8")
        write_review_sheet(out / f"run_{r}_review.csv", rows, query)
        results.append(log)
    return results


def write_review_sheet(path, rows, query):
    cons = " | ".join(query.get("constraints", []))
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["n", "element_type", "text", "linked_to", "source_pattern_id", "status", "issues", "flags",
                    "constraints to check (R3)", "analyst decision (accept/modify/reject)", "reason"])
        for x in rows:
            w.writerow([x["n"], x["element_type"], x["text"], x["linked_to"], x["source_pattern_id"],
                        x["status"], x["issues"], x["flags"], cons, "", ""])
