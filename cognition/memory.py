import time
from dataclasses import dataclass, field


@dataclass
class Episode:
    tags: frozenset[str]
    limbic_snapshot: dict[str, float]   # drive values when memory was formed
    action: str
    outcome_valence: float              # did it go well? -1.0 to 1.0
    concepts: list[dict] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class MemoryStore:
    def __init__(self):
        self._episodes: list[Episode] = []

    def store(self, episode: Episode) -> None:
        self._episodes.append(episode)

    def retrieve(
        self,
        tags: frozenset[str],
        limbic_state: dict[str, float],
        top_k: int = 3,
    ) -> list[Episode]:
        if not self._episodes:
            return []

        scored = [
            (self._score(ep, tags, limbic_state), ep)
            for ep in self._episodes
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:top_k]]

    def _score(self, ep: Episode, tags: frozenset[str], limbic: dict[str, float]) -> float:
        semantic = _jaccard(tags, ep.tags)
        emotional = _cosine(limbic, ep.limbic_snapshot)
        # emotional context gates retrieval: hungry → food memories surface faster
        return semantic * 0.5 + emotional * 0.5

    def __len__(self) -> int:
        return len(self._episodes)


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) & set(b)
    if not keys:
        return 0.0
    dot = sum(a[k] * b[k] for k in keys)
    mag_a = sum(v ** 2 for v in a.values()) ** 0.5
    mag_b = sum(v ** 2 for v in b.values()) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
