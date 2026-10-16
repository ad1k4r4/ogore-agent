"""The four validation rules of Activity 2.1 (paper, Section IV.D).

R1  the element is one of the six OGORE element types                      automated, reject on failure
R2  it attaches to the queried KPI-annotated goal or to one of its KPIs     automated, reject on failure
R3  it does not contradict the recorded beliefs and constraints             analyst check; the pipeline flags
    Tasks, Resources, and Actors that mention a term the query marks as excluded, and lists the constraints
    beside every element on the review sheet (Beliefs and Constraints may restate a prohibition, so they are
    not screened)
R4  it cites the retrieved pattern it was adapted from                      automated; the citation may be the
    pattern ID or the chunk ID (pattern/goal); an element without a source is flagged UNGROUNDED, and one that
    cites a pattern that was not retrieved is rejected
"""
from .config import ELEMENT_TYPES


def check(output, query, retrieved_pattern_ids):
    allowed_links = {query["goal"]["id"]} | {k["id"] for k in query["kpis"]}
    excluded = [t.lower() for t in query.get("excluded_terms", [])]
    rows = []
    for i, el in enumerate(output["elements"], 1):
        issues, flags = [], []
        if el["element_type"] not in ELEMENT_TYPES:
            issues.append("R1 unknown element type")
        if el["linked_to"].strip() not in allowed_links:
            issues.append(f"R2 linked to '{el['linked_to']}', not to the goal or its KPIs")
        hit = [t for t in excluded if t in el["text"].lower()]
        if hit and el["element_type"] in ("Task", "Resource", "Actor"):
            flags.append(f"R3 check: mentions excluded term(s) {', '.join(hit)}")
        src = el["source_pattern_id"].strip()
        if src.upper() == "UNGROUNDED":
            flags.append("UNGROUNDED")
        elif src.split("/")[0] not in retrieved_pattern_ids:
            issues.append(f"R4 cites '{src}', which was not retrieved")
        rows.append({
            "n": i, **el,
            "status": "rejected" if issues else ("flagged" if flags else "passed"),
            "issues": "; ".join(issues), "flags": "; ".join(flags),
        })
    return rows
