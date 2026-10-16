"""Goal Knowledge Base: loading, schema checks, goal-level chunking, and freezing (SHA-256).

A knowledge base is a directory of JSON files, one validated Solution GTM per file, following the
entry schema of the paper (Appendix B). Each IT goal with its sub-tree becomes one retrieval chunk.
"""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

REQUIRED = ["pattern_id", "organization_type", "business_domain", "organization_goal", "it_goals"]
GOAL_FIELDS = ["goal_id", "text", "kpis", "tasks", "resources", "actors", "beliefs", "constraints"]


@dataclass(frozen=True)
class Chunk:
    chunk_id: str      # <pattern_id>/<goal_id>
    pattern_id: str
    text: str          # serialized text that is embedded and shown to the model


def load_entries(kb_dir):
    files = sorted(Path(kb_dir).glob("*.json"))
    if not files:
        raise FileNotFoundError(f"no *.json entries in {kb_dir}")
    entries = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    for e, f in zip(entries, files):
        check_entry(e, f.name)
    ids = [e["pattern_id"] for e in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate pattern_id in knowledge base")
    return entries


def check_entry(e, name="entry"):
    missing = [k for k in REQUIRED if k not in e]
    if missing:
        raise ValueError(f"{name}: missing fields {missing}")
    for g in e["it_goals"]:
        gm = [k for k in GOAL_FIELDS if k not in g]
        if gm:
            raise ValueError(f"{name} goal {g.get('goal_id')}: missing fields {gm}")


def _line(label, items):
    return f"  {label}: " + ("; ".join(items) if items else "none")


def goal_text(e, g):
    kpis = [f"{k['id']} {k['text']}" + (f" (target {k['target']})" if k.get("target") else "") for k in g["kpis"]]
    parts = [
        f"PATTERN {e['pattern_id']} | {e['organization_type']} | {e['business_domain']}",
        f"Organization goal: {e['organization_goal']}",
        f"IT goal {g['goal_id']}: {g['text']}" + (f" (parent {g['parent_id']}, {g.get('decomposition', 'AND')})" if g.get("parent_id") else ""),
        _line("KPIs", kpis),
        _line("Tasks", g["tasks"]),
        _line("Resources", g["resources"]),
        _line("Actors", g["actors"]),
        _line("Beliefs", g["beliefs"]),
        _line("Constraints", g["constraints"]),
    ]
    rs = [r["text"] for r in e.get("rational_statements", []) if r.get("goal_id") == g["goal_id"]]
    if rs:
        parts.append(_line("Rational statement", rs))
    cr = [f"{c['conflict']} -> {c['resolution']}" for c in e.get("conflicts_and_resolutions", [])
          if g["goal_id"] in c.get("goals", [])]
    if cr:
        parts.append(_line("Conflict resolved", cr))
    return "\n".join(parts)


def chunk(entries):
    out = []
    for e in entries:
        for g in e["it_goals"]:
            if not (g["tasks"] or g["actors"] or g["resources"]):
                continue  # a root goal without own elements adds nothing to retrieve
            out.append(Chunk(f"{e['pattern_id']}/{g['goal_id']}", e["pattern_id"], goal_text(e, g)))
    return out


def kb_hash(entries):
    canon = json.dumps(sorted(entries, key=lambda e: e["pattern_id"]), sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()
