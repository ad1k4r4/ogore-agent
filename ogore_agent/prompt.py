"""Prompt template and output schema. The template follows Appendix B of the paper; the only change is that
retrieval is done by the pipeline, so the model receives the top-k chunks instead of the whole knowledge base."""
import json

from .config import ELEMENT_TYPES

SYSTEM = (
    "You assist requirements analysts who apply the OGORE framework. You refine one IT goal of an "
    "organization's Initial Goal Tree Model by adapting validated goal patterns retrieved from a Goal "
    "Knowledge Base. Use only the six OGORE element types: Goal, Task, Resource, Actor, Belief, Constraint. "
    "Do not invent KPI values."
)

TASK = (
    "TASK: (1) Rank the retrieved patterns by relevance to the query and state why each is relevant, citing its "
    "pattern ID. (2) Adapt them to the query and propose Tasks, Actors, Resources, Beliefs, and Constraints for "
    "the goal (and sub-goals only if the goal needs further decomposition). (3) Link every proposed element to "
    "the goal ID or to one of its KPI IDs, exactly as given in the query. (4) Draft one rational statement that "
    "explains how the goal and its elements serve the parent goal and its KPIs. (5) Give, for each element, the "
    "pattern ID it was adapted from; if it was not taken from a retrieved pattern, write UNGROUNDED. Every "
    "proposed element must respect the beliefs and constraints listed in the query."
)

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "ranked_patterns": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"pattern_id": {"type": "string"}, "relevance": {"type": "string"}},
                "required": ["pattern_id", "relevance"],
                "additionalProperties": False,
            },
        },
        "elements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "element_type": {"type": "string", "enum": ELEMENT_TYPES},
                    "text": {"type": "string"},
                    "linked_to": {"type": "string"},
                    "source_pattern_id": {"type": "string"},
                    "justification": {"type": "string"},
                },
                "required": ["element_type", "text", "linked_to", "source_pattern_id", "justification"],
                "additionalProperties": False,
            },
        },
        "rational_statement": {"type": "string"},
    },
    "required": ["ranked_patterns", "elements", "rational_statement"],
    "additionalProperties": False,
}


def render_query(q):
    kpis = "; ".join(f"{k['id']} = {k['text']}" for k in q["kpis"])
    lines = [
        f"GOAL: {q['goal']['id']} \"{q['goal']['text']}\"; parent {q['parent']['id']} \"{q['parent']['text']}\"",
        f"DOMAIN: {q['domain']}; organization type: {q['organization_type']}",
        f"KPIS: {kpis}",
        "ACTORS IN SCOPE: " + ("; ".join(q.get("actors_in_scope", [])) or "not given (propose them)"),
        "BELIEFS: " + ("; ".join(q.get("beliefs", [])) or "none recorded"),
        "CONSTRAINTS: " + ("; ".join(q.get("constraints", [])) or "none recorded"),
    ]
    return "\n".join(lines)


def build_user(query, retrieved):
    kb = "\n\n".join(f"[{c.chunk_id}] (similarity {s})\n{c.text}" for c, s in retrieved)
    return f"RETRIEVED PATTERNS:\n{kb}\n\nQUERY:\n{render_query(query)}\n\n{TASK}"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
