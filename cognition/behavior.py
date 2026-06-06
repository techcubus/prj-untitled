from dataclasses import dataclass
from .bus import EventBus
from .limbic import LimbicSystem
from .memory import MemoryStore, Episode
from .perception import CONCEPTS


SATISFIERS: dict[str, list[str]] = {
    "hunger":     ["food", "fruit", "meat", "drink"],
    "thirst":     ["drink"],
    "curiosity":  ["novel"],
    "fear":       [],
    "discomfort": [],
    "fatigue":    [],
}

ACTION_EFFECTS: dict[str, tuple[str, float]] = {
    "consume":  ("hunger",     0.85),
    "drink":    ("thirst",     0.85),
    "flee":     ("fear",       0.70),
    "freeze":   ("fear",       0.30),
    "avoid":    ("discomfort", 0.20),
    "explore":  ("curiosity",  0.60),
    "rest":     ("fatigue",    0.60),
}

# Energy cost per action — increases fatigue drive
ACTION_FATIGUE_COST: dict[str, float] = {
    "consume": 0.02,
    "drink":   0.02,
    "flee":    0.08,
    "freeze":  0.01,
    "avoid":   0.04,
    "explore": 0.05,
    "rest":    0.00,
}


@dataclass
class Action:
    name: str
    target: str | None = None
    drive: str | None = None

    def __str__(self) -> str:
        return f"{self.name}({self.target})" if self.target else self.name


class BehaviorEngine:
    def __init__(self, bus: EventBus, limbic: LimbicSystem, memory: MemoryStore):
        self.bus = bus
        self.limbic = limbic
        self.memory = memory
        self.current_concepts: list[dict] = []
        bus.subscribe("perception", self._on_perception)

    def _on_perception(self, payload: dict) -> None:
        # accumulate from multiple sensors firing within the same tick
        seen = {c["tag"] for c in self.current_concepts}
        for c in payload["concepts"]:
            if c["tag"] not in seen:
                self.current_concepts.append(c)
                seen.add(c["tag"])

    def tick(self) -> "Action | None":
        needs = self.limbic.active_needs()
        if not needs:
            return None
        primary = max(needs, key=lambda n: self.limbic.drives[n].value)
        action = self._select_action(primary)
        if action:
            self._execute(action)
            self.bus.publish("action", action)
        return action

    def _select_action(self, need: str) -> "Action | None":
        satisfiers = SATISFIERS.get(need, [])
        hazards = [c for c in self.current_concepts if c.get("hazard")]
        bad_tags = frozenset(c["tag"] for c in hazards)

        if need == "fatigue":
            return Action(name="rest", drive="fatigue")

        if need == "discomfort":
            if hazards:
                return Action(name="avoid", target=hazards[0]["tag"], drive="discomfort")
            return Action(name="rest", drive="discomfort")

        if need == "fear":
            fearful = [c for c in self.current_concepts if "hazard" in c.get("is_a", [])]
            return Action(name="flee" if fearful else "freeze", drive="fear",
                          target=fearful[0]["tag"] if fearful else None)

        # direct perception match — skip known hazards and memory-flagged bad items
        for concept in self.current_concepts:
            if concept["tag"] in bad_tags:
                continue
            in_is_a = any(s in concept.get("is_a", []) for s in satisfiers)
            in_satisfies = need in concept.get("satisfies", [])
            if in_is_a or in_satisfies:
                past = self.memory.retrieve(
                    tags=frozenset([concept["tag"]]),
                    limbic_state=self.limbic.snapshot(),
                    top_k=1,
                )
                if past and past[0].outcome_valence < 0:
                    continue    # learned aversion
                verb = "drink" if "drink" in concept.get("is_a", []) else "consume"
                return Action(name=verb, target=concept["tag"], drive=need)

        # memory-guided fallback
        past = self.memory.retrieve(
            tags=frozenset(satisfiers),
            limbic_state=self.limbic.snapshot(),
        )
        for ep in past:
            if ep.outcome_valence > 0 and ep.action in ACTION_EFFECTS:
                drive, _ = ACTION_EFFECTS[ep.action]
                if drive == need:
                    return Action(name=ep.action, drive=need)

        return None

    def _execute(self, action: Action) -> None:
        if action.name not in ACTION_EFFECTS:
            return

        # real outcome valence comes from the concept being consumed, not a fixed 0.8
        concept_valence = 1.0
        if action.target and action.name in ("consume", "drink"):
            concept_valence = CONCEPTS.get(action.target, {}).get("valence", 1.0)

        if action.name in ("consume", "drink") and concept_valence < 0:
            # bad food: don't satisfy hunger; taste sensor owns the discomfort spike
            outcome_valence = concept_valence
        else:
            drive_name, amount = ACTION_EFFECTS[action.name]
            self.limbic.satisfy(drive_name, amount)
            outcome_valence = max(0.1, concept_valence)

        # every action costs fatigue
        cost = ACTION_FATIGUE_COST.get(action.name, 0.02)
        if cost > 0 and "fatigue" in self.limbic.drives:
            self.limbic.drives["fatigue"].value = min(
                1.0, self.limbic.drives["fatigue"].value + cost
            )

        self.memory.store(Episode(
            tags=frozenset(filter(None, [action.target, action.name])),
            limbic_snapshot=self.limbic.snapshot(),
            action=action.name,
            outcome_valence=outcome_valence,
            concepts=list(self.current_concepts),
        ))
