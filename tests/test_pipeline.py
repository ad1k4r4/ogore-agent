"""Offline tests: knowledge-base schema, validation rules, deterministic retrieval, and replay of the recorded runs.
Run:  python -m pytest -q
"""
import json
from pathlib import Path

import pytest

from ogore_agent.config import Settings
from ogore_agent.generate import GenerationError, build_request, generate
from ogore_agent.kb import chunk, kb_hash, load_entries
from ogore_agent.validate import check

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "data" / "synthetic_kb"
QUERIES = ROOT / "examples" / "company_s" / "queries"
RUNS = ROOT / "runs" / "company_s"


def q(name="G05"):
    return json.loads((QUERIES / f"{name}.json").read_text(encoding="utf-8"))


def test_kb_loads_and_hash_is_stable():
    e = load_entries(KB)
    assert len(e) == 9 and len(chunk(e)) == 13
    assert kb_hash(e) == kb_hash(list(reversed(e)))


def test_validation_rules():
    out = {"elements": [
        {"element_type": "Task", "text": "Verify each request", "linked_to": "G05-K1", "source_pattern_id": "SKB-04", "justification": ""},
        {"element_type": "Task", "text": "Use a shared account for night shifts", "linked_to": "G05", "source_pattern_id": "SKB-04/G2", "justification": ""},
        {"element_type": "Actor", "text": "Auditor", "linked_to": "G99", "source_pattern_id": "UNGROUNDED", "justification": ""},
        {"element_type": "Resource", "text": "Token", "linked_to": "G05", "source_pattern_id": "SKB-99", "justification": ""},
    ], "ranked_patterns": [], "rational_statement": ""}
    rows = check(out, q(), ["SKB-04"])
    assert [r["status"] for r in rows] == ["passed", "flagged", "rejected", "rejected"]
    assert "R3" in rows[1]["flags"] and "R2" in rows[2]["issues"] and "UNGROUNDED" in rows[2]["flags"]
    assert "R4" in rows[3]["issues"]


def test_retrieval_is_deterministic():
    pytest.importorskip("sentence_transformers")
    from ogore_agent.retrieve import top_k
    c = chunk(load_entries(KB))
    a, b = top_k(q(), c, 4), top_k(q(), c, 4)
    assert [(x.chunk_id, s) for x, s in a] == [(x.chunk_id, s) for x, s in b]
    assert a[0][0].pattern_id == "SKB-04"


def test_replay_rejects_changed_request(tmp_path):
    req = build_request(Settings(), "hello")
    with pytest.raises(GenerationError):
        generate(req, 1, "replay", tmp_path)


@pytest.mark.skipif(not (RUNS / "recordings").exists(), reason="no recorded runs")
def test_replay_reproduces_recorded_logs(tmp_path):
    pytest.importorskip("sentence_transformers")
    from ogore_agent.pipeline import run_query
    for f in sorted(QUERIES.glob("*.json")):
        query = json.loads(f.read_text(encoding="utf-8"))
        logs = run_query(query, KB, tmp_path, runs=3, mode="replay", rec_dir=RUNS / "recordings")
        for i, log in enumerate(logs, 1):
            ref = json.loads((RUNS / query["query_id"] / f"run_{i}.json").read_text(encoding="utf-8"))
            assert log["output"] == ref["output"] and log["validation"] == ref["validation"]
            assert log["retrieved"] == ref["retrieved"]
