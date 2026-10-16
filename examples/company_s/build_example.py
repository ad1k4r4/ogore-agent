"""Builds the Company S worked example: organization profile, Initial GTM (Process 1 output), and the six
structured queries for Activity 2.1. Company S is synthetic; every name, figure, and decision is fictional.
Run:  python examples/company_s/build_example.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent

PROFILE = {
    "organization": "Company S (synthetic)",
    "description": ("Pharmaceutical distributor supplying about 300 hospitals and clinics from three regional "
                    "warehouses, 400 employees. It replaces e-mail and telephone ordering with an order portal and "
                    "adds an ordering assistant (a language model with retrieval over product and contract data) "
                    "for hospital buyers. Distribution must follow good distribution practice for medicines, "
                    "including batch records and cold-chain control."),
    "vision": "To be the most trusted distributor of medicines to hospitals in the region.",
    "mission": "Deliver the right medicine, in the right condition, on time, with records that regulators and customers can rely on.",
    "organization_goals": [
        {"id": "OG1", "text": "Supply hospitals reliably and in compliance with distribution regulation", "priority": 1},
        {"id": "OG2", "text": "Grow the hospital customer base", "priority": 2},
        {"id": "OG3", "text": "Reduce distribution cost per order line", "priority": 3},
    ],
    "actors": ["Hospital Buyer", "Sales Administrator", "Responsible Pharmacist", "Quality Assurance Officer",
               "IT Security Officer", "Data Protection Officer", "AI Product Owner"],
}

ROOT = {"id": "G01", "text": "Regulated order-to-delivery controlled and secure", "maps_to": "OG1"}

# Initial GTM after Activity 1.3: every IT goal carries KPIs. Goals G05 to G07 are the security, privacy,
# and AI governance goals that the revised Activities 1.2 and 1.3 make mandatory.
GOALS = [
    {"id": "G02", "text": "Hospital orders recorded accurately and confirmed promptly",
     "kpis": [("Order lines matching the hospital purchase order", ">= 99.5% per month"),
              ("Order confirmation sent after submission", "within 15 minutes")],
     "beliefs": ["Each hospital has a contract price list", "Hospital buyers order through the portal or the assistant"],
     "constraints": ["A confirmed order cannot be changed without a change request"]},
    {"id": "G03", "text": "Batch and expiry traceable to each hospital",
     "kpis": [("Shipped lines with batch number and expiry date recorded", "100%"),
              ("Time to list every hospital that received a recalled batch", "under 2 hours")],
     "beliefs": ["Good distribution practice requires batch records for every medicine"],
     "constraints": ["A line without batch and expiry cannot be shipped"]},
    {"id": "G04", "text": "Cold-chain products kept within their temperature range",
     "kpis": [("Cold-chain shipments with a continuous temperature log", "100%"),
              ("Temperature excursion alerts acknowledged", "within 30 minutes"),
              ("Goods with an excursion released without a quality decision", "0")],
     "beliefs": ["Vaccines and insulin need 2 to 8 degrees Celsius"],
     "constraints": ["Only the Quality Assurance Officer may release goods after an excursion"]},
    {"id": "G05", "text": "Access to order, stock, and contract data verified for every request (zero trust)",
     "kpis": [("Requests authenticated and authorized per request", "100%"),
              ("Privileged actions protected by multi-factor authentication", "100%"),
              ("Quarterly access reviews completed", "100%")],
     "beliefs": ["No network location, including the office network, is trusted by default"],
     "constraints": ["Shared accounts are not permitted"], "excluded_terms": ["shared account"]},
    {"id": "G06", "text": "Personal data of hospital staff and named patients protected",
     "kpis": [("Personal data fields classified with a documented purpose", "100%"),
              ("Patient identifiers stored outside named-patient order records", "0"),
              ("Data subject requests closed", "within the legal deadline")],
     "beliefs": ["Named-patient orders contain a patient name and medical record number"],
     "constraints": ["Patient identifiers are not sent to the language model provider"]},
    {"id": "G07", "text": "Ordering assistant governed as an AI system",
     "kpis": [("Assistant answers that cite an approved source", "100%"),
              ("Hospital-specific prices disclosed to another hospital in the monthly audit", "0"),
              ("Answers rated correct in the monthly evaluation", ">= 95%"),
              ("Model and prompt changes approved before release", "100%")],
     "beliefs": ["The assistant runs on an external model provider"],
     "constraints": ["The assistant cannot place or change an order without the buyer's confirmation",
                     "Patient identifiers are not sent to the language model provider"]},
]


def query(goal):
    q = {
        "query_id": f"S-{goal['id']}",
        "goal": {"id": goal["id"], "text": goal["text"]},
        "parent": {"id": ROOT["id"], "text": ROOT["text"]},
        "domain": "pharmaceutical distribution to hospitals",
        "organization_type": "medium-sized distributor with an order portal and an LLM-based ordering assistant",
        "kpis": [{"id": f"{goal['id']}-K{i+1}", "text": f"{t} ({tg})"} for i, (t, tg) in enumerate(goal["kpis"])],
        "actors_in_scope": PROFILE["actors"],
        "beliefs": goal["beliefs"],
        "constraints": goal["constraints"],
    }
    if goal.get("excluded_terms"):
        q["excluded_terms"] = goal["excluded_terms"]
    return q


if __name__ == "__main__":
    (HERE / "queries").mkdir(exist_ok=True)
    (HERE / "profile.json").write_text(json.dumps(PROFILE, indent=1, ensure_ascii=False), encoding="utf-8")
    initial = {"root": ROOT, "decomposition": "AND", "sub_goals": GOALS}
    (HERE / "initial_gtm.json").write_text(json.dumps(initial, indent=1, ensure_ascii=False), encoding="utf-8")
    for goal in GOALS:
        (HERE / "queries" / f"{goal['id']}.json").write_text(json.dumps(query(goal), indent=1, ensure_ascii=False),
                                                             encoding="utf-8")
    print(f"wrote profile, Initial GTM, and {len(GOALS)} queries")
