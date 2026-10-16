"""Command line interface.

  python -m ogore_agent kb-check  --kb data/synthetic_kb
  python -m ogore_agent retrieve  --kb data/synthetic_kb --query examples/company_s/queries/G05.json
  python -m ogore_agent run       --kb data/synthetic_kb --queries examples/company_s/queries --out runs/company_s --runs 3 [--live]
  python -m ogore_agent stability --out runs/company_s
"""
import argparse
import json
import os
import sys
from pathlib import Path


def load_env(path=".env"):
    """Read ANTHROPIC_API_KEY from a local .env file if it is not already set (the file is git-ignored)."""
    p = Path(path)
    if p.exists() and not os.environ.get("ANTHROPIC_API_KEY"):
        for line in p.read_text(encoding="utf-8-sig").splitlines():
            if line.strip().startswith("ANTHROPIC_API_KEY="):
                os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip().strip('"')


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="ogore_agent")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("kb-check"); a.add_argument("--kb", required=True)
    a = sub.add_parser("retrieve"); a.add_argument("--kb", required=True); a.add_argument("--query", required=True)
    a = sub.add_parser("run")
    a.add_argument("--kb", required=True); a.add_argument("--queries", required=True)
    a.add_argument("--out", required=True); a.add_argument("--runs", type=int, default=3)
    a.add_argument("--live", action="store_true", help="call the API and record; default is replay")
    a = sub.add_parser("stability"); a.add_argument("--out", required=True)
    a.add_argument("--threshold", type=float, default=0.8)
    args = ap.parse_args(argv)

    from .config import Settings
    from .kb import chunk, kb_hash, load_entries
    if args.cmd == "kb-check":
        e = load_entries(args.kb)
        print(f"{len(e)} entries, {len(chunk(e))} chunks, SHA-256 {kb_hash(e)}")
    elif args.cmd == "retrieve":
        from .retrieve import top_k
        q = json.loads(Path(args.query).read_text(encoding="utf-8"))
        for c, s in top_k(q, chunk(load_entries(args.kb)), Settings().top_k):
            print(f"{s:.4f}  {c.chunk_id}")
    elif args.cmd == "run":
        from .pipeline import run_query
        if args.live:
            load_env()
        qpath = Path(args.queries)
        files = sorted(qpath.glob("*.json")) if qpath.is_dir() else [qpath]
        for f in files:
            q = json.loads(f.read_text(encoding="utf-8"))
            logs = run_query(q, args.kb, args.out, args.runs, "live" if args.live else "replay")
            s = [l["summary"] for l in logs]
            print(f"{q['query_id']}: " + " | ".join(f"run {i+1}: {x['passed']} passed, {x['flagged']} flagged, "
                                                    f"{x['rejected']} rejected" for i, x in enumerate(s)))
    elif args.cmd == "stability":
        from .stability import summarize
        report = {}
        for d in sorted(p for p in Path(args.out).iterdir() if p.is_dir() and p.name != "recordings"):
            logs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(d.glob("run_*.json"))]
            if logs:
                report[d.name] = summarize(logs, args.threshold)
        Path(args.out, "stability.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
        for k, v in report.items():
            print(k, v)


if __name__ == "__main__":
    main()
