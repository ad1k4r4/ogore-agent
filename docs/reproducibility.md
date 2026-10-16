# Reproducibility notes

## What is deterministic

| Stage | Deterministic? | How |
|---|---|---|
| Knowledge base | yes | JSON entries; SHA-256 over the canonical JSON of all entries is stored in every run log |
| Chunking | yes | one chunk per IT goal with its sub-tree, in file order |
| Embedding and retrieval | yes | pinned model revision, CPU, deterministic torch algorithms, scores rounded to 6 decimals, ties broken by chunk ID |
| Prompt | yes | fixed template; the request is serialized canonically and hashed |
| Generation | no | Claude Opus 5 accepts no sampling parameters; the model ID and the effort level are fixed |
| Validation rules | yes | pure functions of the output and the query |

## Record and replay

Each live call stores the full request, the response ID, the served model, the token usage, and the parsed output
under `runs/<example>/recordings/<key>.json`, where `key` is the first 20 hex digits of
SHA-256(canonical request + run number). A replay looks up the same key and refuses a recording whose stored
request differs from the request rebuilt on the reader's machine. A successful replay therefore shows that the
reader's retrieval and prompt construction are identical to ours, and it reproduces the outputs, validation results,
and stability figures reported in the paper exactly.

## Run-to-run stability

`python -m ogore_agent stability --out runs/company_s` compares the three live runs of each query:

- matched F1: elements of two runs are matched one-to-one when they have the same type and a cosine similarity of
  at least 0.8 between their text embeddings; F1 = 2m / (n1 + n2), averaged over the three run pairs;
- cited-pattern Jaccard: overlap of the patterns cited by two runs;
- ungrounded share and the number of elements rejected by the rules.

## Private re-run of the paper's real case

The paper also reports a re-run of the four Company T queries with the frozen case-study knowledge base. That
knowledge base is confidential and is not in this repository; the same code was run with
`--kb <private directory>`, and only aggregate figures are reported in the paper.
