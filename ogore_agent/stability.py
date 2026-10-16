"""Run-to-run stability of the agent output for one query.

Two elements of different runs are matched when they have the same type and a cosine similarity of at least
`threshold` between their text embeddings (greedy one-to-one matching, highest similarity first). For each
pair of runs the matched F1 is 2m / (n1 + n2). The cited patterns are compared with the Jaccard index.
"""
from itertools import combinations

from .retrieve import embed


def matched_f1(a, b, threshold=0.8):
    if not a and not b:
        return 1.0
    ta, tb = [e["text"] for e in a], [e["text"] for e in b]
    va, vb = embed(ta), embed(tb)
    sim = va @ vb.T
    pairs = sorted(((sim[i, j], i, j) for i in range(len(a)) for j in range(len(b))
                    if a[i]["element_type"] == b[j]["element_type"] and sim[i, j] >= threshold), reverse=True)
    used_a, used_b, m = set(), set(), 0
    for _, i, j in pairs:
        if i not in used_a and j not in used_b:
            used_a.add(i); used_b.add(j); m += 1
    return 2 * m / (len(a) + len(b))


def jaccard(x, y):
    x, y = set(x), set(y)
    return 1.0 if not x and not y else len(x & y) / len(x | y)


def summarize(logs, threshold=0.8):
    outs = [l["output"] for l in logs]
    f1 = [matched_f1(a["elements"], b["elements"], threshold) for a, b in combinations(outs, 2)]
    cited = [{e["source_pattern_id"] for e in o["elements"] if e["source_pattern_id"] != "UNGROUNDED"} for o in outs]
    jac = [jaccard(a, b) for a, b in combinations(cited, 2)]
    counts = [len(o["elements"]) for o in outs]
    return {
        "runs": len(logs),
        "elements_per_run": counts,
        "mean_pairwise_matched_f1": round(sum(f1) / len(f1), 3) if f1 else None,
        "mean_pairwise_cited_pattern_jaccard": round(sum(jac) / len(jac), 3) if jac else None,
        "ungrounded_share": round(sum(e["source_pattern_id"] == "UNGROUNDED" for o in outs for e in o["elements"])
                                  / max(1, sum(counts)), 3),
        "rejected_by_rules": sum(l["summary"]["rejected"] for l in logs),
    }
