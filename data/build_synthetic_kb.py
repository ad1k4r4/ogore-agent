"""Generates the synthetic Goal Knowledge Base (data/synthetic_kb/*.json).

All organizations, goals, KPIs, and decisions below are fictional. They were written by the authors to
exercise the pipeline and are not derived from any real organization or from the Company T case.
Run:  python data/build_synthetic_kb.py
"""
import json
from pathlib import Path

V = {"validated_by": "synthetic (authors)", "date": "2026-10-16"}


def g(goal_id, text, kpis, tasks=(), resources=(), actors=(), beliefs=(), constraints=(), parent_id=None):
    return {"goal_id": goal_id, "text": text, "parent_id": parent_id, "decomposition": "AND",
            "kpis": [{"id": f"{goal_id}-K{i+1}", "text": t, "target": tg} for i, (t, tg) in enumerate(kpis)],
            "tasks": list(tasks), "resources": list(resources), "actors": list(actors),
            "beliefs": list(beliefs), "constraints": list(constraints)}


KB = [
 {"pattern_id": "SKB-01", "organization_type": "medium-sized food and beverage distributor (synthetic)",
  "business_domain": "wholesale distribution; order-to-cash and lot traceability",
  "organization_goal": "deliver complete and traceable orders to retail customers",
  "it_goals": [
   g("G1", "Controlled order-to-delivery", [("Order lines delivered as ordered", "99.5%")]),
   g("G2", "Customer orders recorded accurately", [("Order lines matching the customer purchase order", "99.5%"),
       ("Order confirmation sent after entry", "within 30 minutes")],
     ["Capture customer purchase order with price list validation", "Confirm order to customer"],
     ["Customer price list", "Order management module"], ["Sales Administrator", "Customer"],
     ["Price lists are customer specific"], ["A confirmed order cannot be edited without a change request"], "G1"),
   g("G3", "Lot numbers traceable from receipt to customer", [("Shipped lines with lot number recorded", "100%"),
       ("Time to list all customers of a recalled lot", "under 4 hours")],
     ["Scan lot number at goods receipt", "Record lot number on each picked line", "Run recall trace report"],
     ["Barcode scanners", "Lot master data"], ["Warehouse Clerk", "Quality Officer"],
     ["Suppliers print lot numbers on every carton"], ["A line without a lot number cannot be shipped"], "G1")],
  "contribution_values": [{"element": "Run recall trace report", "goal": "G3", "value": "Make (++)"}],
  "rational_statements": [{"goal_id": "G3", "text": "Lot capture at receipt and picking makes a recall trace a query instead of a manual search, which is what the 4-hour KPI requires."}],
  "conflicts_and_resolutions": [{"goals": ["G2", "G3"], "conflict": "lot scanning slows picking and delays confirmation",
     "resolution": "confirm the order at entry and scan lots at picking, so confirmation time is unaffected"}],
  "validation": V},

 {"pattern_id": "SKB-02", "organization_type": "cold-chain logistics provider for frozen food (synthetic)",
  "business_domain": "temperature-controlled warehousing and transport",
  "organization_goal": "keep every temperature-controlled shipment within its specified range",
  "it_goals": [
   g("G1", "Temperature compliance assured", [("Shipments within range for the whole journey", "99%")]),
   g("G2", "Temperature excursions detected and handled", [("Cold shipments with a continuous temperature log", "100%"),
       ("Excursion alerts acknowledged", "within 30 minutes")],
     ["Stream logger readings to the monitoring service", "Alert the duty supervisor on an excursion",
      "Quarantine affected goods pending a release decision"],
     ["Temperature data loggers", "Monitoring dashboard"], ["Duty Supervisor", "Quality Manager"],
     ["Loggers record every five minutes"], ["Goods with an unresolved excursion cannot be released"], "G1")],
  "contribution_values": [{"element": "Quarantine affected goods pending a release decision", "goal": "G2", "value": "Make (++)"}],
  "rational_statements": [{"goal_id": "G2", "text": "A release decision by the Quality Manager is the control that turns a detected excursion into a safe outcome."}],
  "conflicts_and_resolutions": [{"goals": ["G2"], "conflict": "automatic release would speed dispatch but bypass quality review",
     "resolution": "automatic release only for excursions under 15 minutes and 2 degrees; all others need the Quality Manager"}],
  "validation": V},

 {"pattern_id": "SKB-03", "organization_type": "online retailer (synthetic)",
  "business_domain": "e-commerce; customer personal data protection",
  "organization_goal": "earn customer trust by protecting personal data",
  "it_goals": [
   g("G1", "Personal data processed lawfully", [("Personal data fields with a recorded legal basis", "100%")]),
   g("G2", "Personal data minimized and classified", [("Personal data fields classified", "100%"),
       ("Fields without a documented purpose", "0")],
     ["Maintain a data inventory with purpose and retention per field", "Mask personal data in non-production systems"],
     ["Data inventory", "Masking tool"], ["Data Protection Officer", "System Owner"],
     ["Customers expect data to be used only for their orders"], ["Personal data is retained no longer than its purpose requires"], "G1"),
   g("G3", "Data subject requests fulfilled", [("Requests closed", "within 30 days")],
     ["Register and verify each data subject request", "Export or erase the customer's data"],
     ["Request register"], ["Data Protection Officer", "Customer Service Agent"],
     [], ["Identity is verified before any data is released"], "G1")],
  "contribution_values": [],
  "rational_statements": [{"goal_id": "G2", "text": "Classification is the precondition for every other privacy control, so it is measured at 100%."}],
  "conflicts_and_resolutions": [{"goals": ["G2"], "conflict": "marketing wanted to keep full purchase histories indefinitely",
     "resolution": "keep aggregated histories; delete personal identifiers after 24 months"}],
  "validation": V},

 {"pattern_id": "SKB-04", "organization_type": "regional bank back office (synthetic)",
  "business_domain": "financial services; zero-trust access to transaction systems",
  "organization_goal": "protect customer transactions against unauthorized access and change",
  "it_goals": [
   g("G1", "Transaction systems protected", [("Security incidents with customer impact", "0 per year")]),
   g("G2", "Every access request verified", [("Requests authenticated and authorized per request", "100%"),
       ("Privileged sessions with multi-factor authentication", "100%")],
     ["Authenticate each request against the identity provider", "Evaluate access policy per request (role, device, context)",
      "Require step-up authentication for privileged actions"],
     ["Identity provider", "Policy decision point"], ["IT Security Officer", "Branch Staff"],
     ["No network location is trusted by default"], ["Shared accounts are not permitted"], "G1"),
   g("G3", "Changes to posted transactions controlled", [("Changes to posted records approved by a second person", "100%"),
       ("Changes logged with user, time, and reason", "100%")],
     ["Route changes to posted records for approval", "Write an immutable audit log entry for each change"],
     ["Audit log store"], ["Supervisor", "Internal Auditor"], [], ["Audit logs cannot be edited or deleted"], "G1")],
  "contribution_values": [{"element": "Require step-up authentication for privileged actions", "goal": "G2", "value": "Make (++)"}],
  "rational_statements": [{"goal_id": "G2", "text": "Per-request verification removes the implicit trust that let compromised sessions move laterally."}],
  "conflicts_and_resolutions": [{"goals": ["G2"], "conflict": "per-request policy checks added latency to teller screens",
     "resolution": "cache policy decisions for 5 minutes for non-privileged reads; privileged actions always re-verified"}],
  "validation": V},

 {"pattern_id": "SKB-05", "organization_type": "insurance company (synthetic)",
  "business_domain": "customer service; governance of an LLM-based assistant with retrieval",
  "organization_goal": "offer fast, correct, and accountable answers to customers",
  "it_goals": [
   g("G1", "AI assistant answers are correct and accountable", [("Answers rated correct in the monthly evaluation", "95%")]),
   g("G2", "Assistant answers grounded and traceable", [("Answers citing an approved source document", "100%"),
       ("Answers on topics outside the approved corpus that are escalated to a human agent", "100%")],
     ["Retrieve answers only from the approved policy corpus", "Escalate out-of-scope questions to a human agent",
      "Run a monthly evaluation on a fixed test set"],
     ["Approved policy corpus", "Evaluation test set"], ["AI Product Owner", "Customer Service Agent"],
     ["Customers act on the assistant's answers"], ["The assistant does not give answers that commit the company financially"], "G1"),
   g("G3", "AI risks governed", [("Model or prompt changes recorded and approved before release", "100%"),
       ("Risk assessment of the assistant reviewed", "every 6 months")],
     ["Keep a model and prompt change register", "Review the AI risk assessment with the risk committee"],
     ["Change register", "AI risk register"], ["AI Product Owner", "Risk Officer"],
     [], ["Customer personal data is not sent to the model provider beyond the session"], "G1")],
  "contribution_values": [{"element": "Escalate out-of-scope questions to a human agent", "goal": "G2", "value": "Help (+)"}],
  "rational_statements": [{"goal_id": "G3", "text": "A change register makes every model or prompt change attributable, which the evaluation KPI depends on."}],
  "conflicts_and_resolutions": [{"goals": ["G2"], "conflict": "broader corpus would answer more questions but include unapproved drafts",
     "resolution": "only approved documents enter the corpus; coverage gaps are filled by escalation"}],
  "validation": V},

 {"pattern_id": "SKB-06", "organization_type": "automotive spare-parts wholesaler (synthetic)",
  "business_domain": "inventory control",
  "organization_goal": "keep stock records equal to physical stock",
  "it_goals": [
   g("G1", "Stock records accurate", [("Items whose system stock equals the physical count", "99%")],
     ["Post every goods movement on scan", "Run cyclic stock counts"], ["Warehouse management system"],
     ["Warehouse Clerk", "Inventory Controller"], [], ["Stock adjustments need the Inventory Controller's approval"])],
  "contribution_values": [], "rational_statements": [], "conflicts_and_resolutions": [], "validation": V},

 {"pattern_id": "SKB-07", "organization_type": "hospital pharmacy (synthetic)",
  "business_domain": "medicine handling; expiry and dispensing control",
  "organization_goal": "dispense safe medicines without waste from expiry",
  "it_goals": [
   g("G1", "Medicines dispensed safely", [("Dispensing errors", "0 per month")]),
   g("G2", "Expiry dates controlled", [("Items picked first-expiry-first-out", "100%"),
       ("Expired items removed from stock", "within 1 day of expiry")],
     ["Record batch and expiry at receipt", "Suggest picking by earliest expiry", "Report items expiring within 90 days"],
     ["Pharmacy stock module"], ["Pharmacist in Charge", "Pharmacy Technician"],
     ["Regulation requires batch records for every medicine"], ["Only a pharmacist may release quarantined medicines"], "G1")],
  "contribution_values": [], "rational_statements": [{"goal_id": "G2", "text": "Batch and expiry captured at receipt make both FEFO picking and recalls possible."}],
  "conflicts_and_resolutions": [], "validation": V},

 {"pattern_id": "SKB-08", "organization_type": "manufacturing company (synthetic)",
  "business_domain": "procurement; supplier invoice matching",
  "organization_goal": "pay suppliers correctly and on time",
  "it_goals": [
   g("G1", "Supplier invoices matched before payment", [("Invoices three-way matched", "100%"), ("Invoices paid on due date", "98%")],
     ["Match invoice, purchase order, and goods receipt", "Hold mismatched invoices for review"], ["Accounts payable module"],
     ["Accounts Payable Clerk", "Purchasing Officer"], [], ["Payment runs need a second approver"])],
  "contribution_values": [], "rational_statements": [], "conflicts_and_resolutions": [], "validation": V},

 {"pattern_id": "SKB-09", "organization_type": "cloud software provider (synthetic)",
  "business_domain": "cloud service security; threat assessment and incident response",
  "organization_goal": "operate a trustworthy cloud service",
  "it_goals": [
   g("G1", "Cloud threats assessed and mitigated", [("Services with a threat model reviewed in the last 12 months", "100%"),
       ("Critical vulnerabilities remediated", "within 7 days")],
     ["Maintain a threat model per service", "Scan dependencies and infrastructure for vulnerabilities",
      "Run incident response exercises"],
     ["Threat model repository", "Vulnerability scanner"], ["Security Architect", "Service Owner"],
     ["Shared responsibility: the provider secures the platform, the customer its configuration"],
     ["Customer data stays in the contracted region"])],
  "contribution_values": [], "rational_statements": [{"goal_id": "G1", "text": "A reviewed threat model per service is the input that makes remediation priorities defensible."}],
  "conflicts_and_resolutions": [], "validation": V},
]

if __name__ == "__main__":
    out = Path(__file__).parent / "synthetic_kb"
    out.mkdir(exist_ok=True)
    for e in KB:
        (out / f"{e['pattern_id']}.json").write_text(json.dumps(e, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(KB)} entries to {out}")
