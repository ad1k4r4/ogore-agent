"""Fixed settings of the reference pipeline. Every run records these values in its log."""
from dataclasses import dataclass, asdict

# Claude Opus 5 is the model used in the OGORE case study (July 2026). The model ID is pinned.
# Claude Opus 5 does not accept sampling parameters (temperature, top_p, top_k); the controllable
# generation settings are the reasoning effort and the output schema, both fixed here.
MODEL = "claude-opus-5"
EFFORT = "high"
MAX_TOKENS = 32000

# Sentence-embedding model for retrieval, run locally on CPU so that retrieval is deterministic.
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
TOP_K = 4

ELEMENT_TYPES = ["Goal", "Task", "Resource", "Actor", "Belief", "Constraint"]


@dataclass(frozen=True)
class Settings:
    model: str = MODEL
    effort: str = EFFORT
    max_tokens: int = MAX_TOKENS
    embed_model: str = EMBED_MODEL
    embed_revision: str = EMBED_REVISION
    top_k: int = TOP_K

    def to_dict(self):
        return asdict(self)
