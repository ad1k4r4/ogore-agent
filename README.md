# ogore-agent: reference implementation of the OGORE Activity 2.1 agent

This repository accompanies the paper *An AI-Augmented Goal-Oriented Requirements Engineering Framework for
Enterprise Information Systems* (IEEE Access, manuscript Access-2026-49609). It contains:

- a reference implementation of the retrieval-augmented agent that OGORE uses in Activity 2.1 (goal refinement);
- a **synthetic** Goal Knowledge Base of nine fictional Solution GTMs (`data/synthetic_kb/`);
- a complete **synthetic** worked example, Company S, a pharmaceutical distributor with an access (zero-trust)
  goal, a privacy goal, and an AI governance goal for an LLM-based ordering assistant (`examples/company_s/`);
- the recorded runs used in the paper (`runs/`), which can be replayed without an API key.

All organizations, goals, KPIs, and decisions in `data/` and `examples/` are fictional. The confidential
knowledge base and documents of the paper's real case (Company T) are **not** included.

## What the pipeline does

```
structured query (JSON)                                   Step 1
  -> goal-level chunks of the Goal Knowledge Base
  -> sentence embeddings on CPU, cosine top-k              Step 2  (deterministic)
  -> Claude Opus 5 with a fixed prompt and JSON schema     Step 3  (recorded)
  -> validation rules R1-R4                                 automated (R3 screened)
  -> review sheet for the analyst                           Step 4  (human)
```

| Setting | Value |
|---|---|
| Language model | `claude-opus-5` (pinned model ID), adaptive thinking, effort `high` |
| Sampling parameters | not accepted by this model; reproducibility comes from recording and replay |
| Output | JSON schema with the six OGORE element types only |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, CPU |
| Chunking | one chunk per IT goal with its sub-tree |
| Retrieval | cosine similarity, top-4, tie-break by chunk ID |
| Knowledge base integrity | SHA-256 over the canonical JSON of all entries, stored in every run log |

Validation rules (paper, Section IV.D): R1 element type is one of the six; R2 the element links to the queried
goal or one of its KPIs; R3 the element does not contradict recorded beliefs and constraints (screened for excluded
terms, checked by the analyst on the review sheet); R4 the element cites a retrieved pattern, otherwise it is
flagged `UNGROUNDED`; a citation of a pattern that was not retrieved is rejected.

## Quick start (no API key needed)

```bash
python -m pip install -r requirements.txt
python -m ogore_agent kb-check  --kb data/synthetic_kb
python -m ogore_agent retrieve  --kb data/synthetic_kb --query examples/company_s/queries/G05.json
python -m ogore_agent run       --kb data/synthetic_kb --queries examples/company_s/queries --out runs/company_s_replay --runs 3
python -m ogore_agent stability --out runs/company_s
python -m pytest -q
```

`run` without `--live` replays the recordings in `runs/company_s/recordings/`. A replay is accepted only if
the request (model, effort, schema, prompt, and retrieved chunks) is byte-identical to the recorded one, so it
also verifies that retrieval reproduces on your machine.

## Live runs

1. Create an API key at https://platform.claude.com and put it in a file `.env` in the repository root:
   `ANTHROPIC_API_KEY=sk-ant-...` (the file is git-ignored).
2. `python -m ogore_agent run --kb data/synthetic_kb --queries examples/company_s/queries --out runs/my_run --runs 3 --live`

Live outputs will differ in wording from the recordings, because the model is not deterministic;
`python -m ogore_agent stability --out runs/my_run` reports how much.

## Repository layout

```
ogore_agent/            pipeline code (kb, retrieve, prompt, generate, validate, pipeline, stability, CLI)
data/synthetic_kb/      nine synthetic Solution GTMs (JSON, schema of Appendix B of the paper)
data/build_synthetic_kb.py
examples/company_s/     profile, Initial GTM, six structured queries, analyst review, AGORA analysis, Solution GTM
runs/                   recorded runs and stability reports
tests/                  offline tests (schema, rules, deterministic retrieval, replay)
```

## Citation

See `CITATION.cff`. Code: MIT License. Synthetic data and example: CC BY 4.0.
