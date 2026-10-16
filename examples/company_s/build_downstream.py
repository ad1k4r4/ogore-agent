"""Company S, Activities 2.1 (Step 4) to 2.3 and Process 3: analyst review of run 1 of every query, AGORA analysis,
Solution GTM, and use cases. The decisions were made by the authors acting as the development team; like the rest
of Company S they are illustrative, not empirical evidence.
Run after the agent runs:  python examples/company_s/build_downstream.py
"""
import csv
import json
from pathlib import Path
from statistics import mean, pvariance

HERE = Path(__file__).parent
RUNS = HERE.parents[1] / "runs" / "company_s"

# Analyst review of run 1. A = accept, R = reject (reason), M = modify (new text). Elements not listed are accepted.
MOVED7 = "belongs to G07 (AI governance), where the same control was proposed"
REVIEW = {
    "S-G02": {3: ("R", MOVED7), 4: ("R", MOVED7), 6: ("R", "release of regulated medicines is handled in G03 and G04"),
              11: ("R", MOVED7), 15: ("R", MOVED7), 16: ("R", "the pharmacist takes no part in order entry"),
              17: ("R", "quality assurance takes no part in order entry"), 18: ("R", "belongs to G06 (privacy)"),
              21: ("R", "duplicates a belief of G03"),
              23: ("M", "An order line that is not on the hospital contract catalogue is held for the Sales Administrator instead of being confirmed"),
              24: ("R", MOVED7), 25: ("R", "duplicates constraints of G06 and G07")},
    "S-G03": {1: ("R", "the decomposition adds no element; the tasks attach to G03 directly"), 2: ("R", "as for element 1"),
              9: ("R", MOVED7), 14: ("R", MOVED7),
              25: ("M", "Recall lists that contain hospital contact data are shared only through channels approved by the Data Protection Officer")},
    "S-G04": {3: ("R", "duplicates the batch capture task of G03"), 9: ("R", MOVED7), 14: ("R", "duplicates the order module resource of G02"),
              19: ("R", MOVED7), 22: ("R", "duplicates a belief of G03"), 26: ("R", MOVED7)},
    "S-G05": {6: ("R", "duplicates element 3"), 14: ("R", "duplicates the order module resource of G02"),
              19: ("R", "belongs to G06 (privacy)"), 20: ("R", "not an access-control role"), 21: ("R", "not an access-control role"),
              27: ("R", "duplicates element 3"), 28: ("R", "belongs to G03 and G04"), 29: ("R", "duplicates a constraint of G02")},
    "S-G06": {6: ("R", MOVED7), 9: ("R", "merged into the joint risk review of G07"), 13: ("R", MOVED7), 14: ("R", MOVED7),
              18: ("R", MOVED7), 20: ("R", "not a privacy role")},
    "S-G07": {13: ("R", "duplicates the identifier filter kept in G06"), 19: ("R", "duplicates the price list resource of G02"),
              30: ("R", "duplicates a belief of G02"), 32: ("R", "duplicates a constraint of G06")},
}

# Modified AGORA analysis (Activity 2.3). Weights: preference for the first goal of each pair (the second gets 1 - w).
STAKEHOLDERS = ["Sales Administrator", "Quality Assurance Officer", "Responsible Pharmacist", "IT Security Officer",
                "Data Protection Officer", "AI Product Owner"]
NEGOTIATION_THRESHOLD = 0.03   # variance above which a negotiation round is held (Activity 2.3, step 8)
CONFLICTS = [
    {"id": "C1", "type": "soft", "goals": ["G05", "G02"],
     "issue": "per-request verification and step-up authentication add latency to order entry, against the 15-minute confirmation KPI",
     "contribution": "Evaluate access policy per request: Make (++) to G05-K1, Hurt (-) to G02-K2",
     "rounds": [[0.4, 0.6, 0.6, 0.9, 0.7, 0.6]],
     "resolution": "verify every request; cache policy decisions for 5 minutes for non-privileged reads; order submission is non-privileged, price changes and bulk exports are privileged and need step-up authentication",
     "rational_statement": "Order submission stays fast because only privileged actions are re-verified with a second factor; no request is trusted without verification."},
    {"id": "C2", "type": "soft", "goals": ["G07", "G02"],
     "issue": "sales asked the assistant to answer availability and price questions without a citation to save time, against the 100% citation and zero-disclosure KPIs",
     "contribution": "Attach a source citation to every answer: Make (++) to G07-K1, Hurt (-) to G02-K2",
     "rounds": [[0.3, 0.8, 0.8, 0.8, 0.9, 0.5], [0.6, 0.8, 0.8, 0.8, 0.9, 0.7]],
     "resolution": "every answer cites its source; availability is answered from the live stock record, which is itself the cited source, so no answer waits for a manual check",
     "rational_statement": "An uncited answer cannot be audited for disclosure or correctness, so citation is kept; using the stock record as the source removes the delay that motivated the request."},
    {"id": "C3", "type": "soft", "goals": ["G03", "G06"],
     "issue": "a recall of a named-patient medicine needs to reach the patient within 2 hours, but patient identifiers may exist only in named-patient order records",
     "contribution": "List patients in the recall trace: Help (+) to G03-K2, Break (--) to G06-K2",
     "rounds": [[0.7, 0.9, 0.8, 0.5, 0.3, 0.5], [0.7, 0.9, 0.8, 0.6, 0.6, 0.5]],
     "resolution": "the recall trace lists hospitals and named-patient order numbers, not patient names; the hospital pharmacist resolves the patient; recall lists leave the system only through channels approved by the Data Protection Officer",
     "rational_statement": "The hospital already holds the patient relationship, so routing the recall through the order number meets the 2-hour KPI without copying identifiers out of the order record."},
    {"id": "C4", "type": "hard", "goals": ["G04", "G02"],
     "issue": "sales proposed automatic release of goods after short temperature excursions, as in a retrieved pattern, to keep delivery promises; the constraint allows release only by the Quality Assurance Officer",
     "contribution": "Automatic release of minor excursions: Help (+) to G02, Break (--) to G04-K3",
     "rounds": [[0.2, 1.0, 0.9, 0.6, 0.5, 0.5], [0.7, 1.0, 0.9, 0.7, 0.6, 0.7]],
     "resolution": "no automatic release; the Quality Assurance Officer is on call, acknowledges excursion alerts within 30 minutes, and records a decision within 2 hours; affected hospitals are informed of the delay",
     "rational_statement": "A release decision by quality assurance is a regulatory control; the on-call arrangement addresses the delivery concern that motivated automatic release."},
]

USE_CASES = [
    ("UC01", "Submit hospital order in the portal", ["G02"]), ("UC02", "Draft order with the ordering assistant and confirm it", ["G02", "G07"]),
    ("UC03", "Confirm order and notify the hospital buyer", ["G02"]), ("UC04", "Raise a change request for a confirmed order", ["G02"]),
    ("UC05", "Receive goods with batch and expiry capture", ["G03"]), ("UC06", "Pick order lines by earliest expiry with batch capture", ["G03"]),
    ("UC07", "Run a recall trace", ["G03", "G06"]), ("UC08", "Quarantine and release a batch", ["G03", "G04"]),
    ("UC09", "Monitor cold-chain temperature and acknowledge an excursion", ["G04"]), ("UC10", "Record a quality decision after an excursion", ["G04"]),
    ("UC11", "Authenticate and authorize a request", ["G05"]), ("UC12", "Step up authentication for a privileged action", ["G05"]),
    ("UC13", "Run the quarterly access review", ["G05"]), ("UC14", "Maintain the personal data inventory", ["G06"]),
    ("UC15", "Handle a data subject request", ["G06"]), ("UC16", "Answer a buyer question with cited sources", ["G07"]),
    ("UC17", "Approve a model or prompt change", ["G07"]), ("UC18", "Run the monthly assistant evaluation and disclosure audit", ["G07"]),
]


def main():
    initial = json.loads((HERE / "initial_gtm.json").read_text(encoding="utf-8"))
    review_rows, per_goal, proposed = [], {}, {}
    for qid, decisions in REVIEW.items():
        log = json.loads((RUNS / qid / "run_1.json").read_text(encoding="utf-8"))
        c = {"proposed": 0, "accepted": 0, "modified": 0, "rejected": 0, "ungrounded_accepted": 0}
        kept = []
        for v in log["validation"]:
            dec, info = decisions.get(v["n"], ("A", ""))
            c["proposed"] += 1
            c[{"A": "accepted", "M": "modified", "R": "rejected"}[dec]] += 1
            text = info if dec == "M" else v["text"]
            if dec != "R":
                kept.append({"type": v["element_type"], "text": text, "linked_to": v["linked_to"], "source": v["source_pattern_id"]})
                c["ungrounded_accepted"] += v["source_pattern_id"] == "UNGROUNDED"
            review_rows.append([qid, v["n"], v["element_type"], v["text"], v["source_pattern_id"], v["status"],
                                {"A": "accept", "M": "modify", "R": "reject"}[dec], info])
        per_goal[qid[2:]] = c
        proposed[qid[2:]] = kept
    with open(HERE / "review_run1.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["query", "n", "element_type", "text", "source_pattern_id", "rule_status", "decision", "reason or new text"])
        w.writerows(review_rows)

    agora = []
    for cf in CONFLICTS:
        rounds = [{"weights": dict(zip(STAKEHOLDERS, r)), "mean": round(mean(r), 3), "variance": round(pvariance(r), 4)} for r in cf["rounds"]]
        agora.append({**{k: v for k, v in cf.items() if k != "rounds"}, "rounds": rounds,
                      "negotiation_rounds": len(rounds) - 1, "threshold": NEGOTIATION_THRESHOLD})
    (HERE / "agora_analysis.json").write_text(json.dumps(agora, indent=1, ensure_ascii=False), encoding="utf-8")

    solution = {"root": initial["root"], "sub_goals": []}
    for g in initial["sub_goals"]:
        solution["sub_goals"].append({**g, "elements": proposed[g["id"]],
                                      "resolved_conflicts": [c["id"] for c in CONFLICTS if g["id"] in c["goals"]]})
    (HERE / "solution_gtm.json").write_text(json.dumps(solution, indent=1, ensure_ascii=False), encoding="utf-8")
    ucs = [{"id": u, "name": n, "goals": g, "kpis": [k for gg in g for k in
            [f"{gg}-K{i+1}" for i in range(len(next(x for x in initial["sub_goals"] if x["id"] == gg)["kpis"]))]]}
           for u, n, g in USE_CASES]
    (HERE / "use_cases.json").write_text(json.dumps(ucs, indent=1, ensure_ascii=False), encoding="utf-8")

    summary = {"per_goal": per_goal,
               "totals": {k: sum(c[k] for c in per_goal.values()) for k in next(iter(per_goal.values()))},
               "kpis": sum(len(g["kpis"]) for g in initial["sub_goals"]),
               "conflicts": [{"id": a["id"], "type": a["type"], "goals": a["goals"],
                              "variance_by_round": [r["variance"] for r in a["rounds"]], "negotiation_rounds": a["negotiation_rounds"]}
                             for a in agora],
               "use_cases": len(ucs),
               "goals_without_use_case": [g["id"] for g in initial["sub_goals"] if not any(g["id"] in u["goals"] for u in ucs)]}
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
