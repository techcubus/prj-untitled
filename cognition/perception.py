from __future__ import annotations
from dataclasses import replace
from .bus import EventBus
from .sensation import Sensation

# How limbic drives amplify (+) or dampen (-) perception of related sensation tags.
# format: drive -> (matching tags, scale factor per unit of drive value)
_DRIVE_MODULATION: dict[str, tuple[list[str], float]] = {
    "hunger":     (["food", "fruit", "meat", "drink"],  +0.60),
    "fear":       (["hazard", "threat"],                +0.70),
    "discomfort": (["pain", "nociceptive"],             +0.50),
    "curiosity":  (["novel", "opening"],                +0.50),
    "fatigue":    (["novel"],                           -0.40),  # tired → novelty less salient
}

# Concept graph. Extend this to teach the agent new things.
# is_a:       semantic categories used for drive-satisfier matching
# satisfies:  drives this concept can meet (food → hunger)
# triggers:   drives immediately spiked on perception
# valence:    intrinsic hedonic value; negative = aversive
# hazard:     True = causes ongoing nociceptive pain when in scene
CONCEPTS: dict[str, dict] = {
    # food & drink
    "apple":          {"is_a": ["food", "fruit"],  "satisfies": ["hunger"],  "valence":  0.8},
    "meat":           {"is_a": ["food"],           "satisfies": ["hunger"],  "valence":  0.9},
    "berry":          {"is_a": ["food", "fruit"],  "satisfies": ["hunger"],  "valence":  0.7},
    "rotten_food":    {"is_a": ["food"],           "satisfies": [],          "valence": -0.8},
    "water":          {"is_a": ["drink"],          "satisfies": ["thirst"],  "valence":  0.7},
    # static hazards — sight triggers fear; nociception sensor handles pain
    "fire":           {"is_a": ["hazard", "heat"], "triggers": ["fear"],     "valence": -0.9, "hazard": True},
    "thorns":         {"is_a": ["hazard"],         "triggers": ["fear"],     "valence": -0.6, "hazard": True},
    "cliff_edge":     {"is_a": ["hazard"],         "triggers": ["fear"],     "valence": -0.7, "hazard": True},
    "loud_noise":     {"is_a": ["hazard"],         "triggers": ["fear"],     "valence": -0.6, "hazard": True},
    # novel / exploratory
    "toy":            {"is_a": ["novel"],          "triggers": ["curiosity"],  "valence":  0.5},
    "new_smell":      {"is_a": ["novel"],          "triggers": ["curiosity"],  "valence":  0.4},
    "opening":        {"is_a": ["novel", "path"],  "triggers": ["curiosity"],  "valence":  0.3},
}


class PerceptionModule:
    def __init__(self, bus: EventBus, limbic=None):
        self.bus = bus
        self.limbic = limbic        # optional; enables emotional modulation when set
        self.current_scene: list[dict] = []
        bus.subscribe("sensation", self._on_sensation)

    def _on_sensation(self, sensation: Sensation) -> None:
        modulated = self._modulate(sensation)
        concepts = self._associate(modulated.tags)
        if not concepts:
            return
        # accumulate into scene; multiple sensors contribute within the same tick
        seen = {c["tag"] for c in self.current_scene}
        for c in concepts:
            if c["tag"] not in seen:
                self.current_scene.append(c)
                seen.add(c["tag"])
        self.bus.publish("perception", {"sensation": modulated, "concepts": concepts})

    def _modulate(self, sensation: Sensation) -> Sensation:
        if not self.limbic:
            return sensation
        snapshot = self.limbic.snapshot()
        multiplier = 1.0
        for drive, (tags, scale) in _DRIVE_MODULATION.items():
            drive_value = snapshot.get(drive, 0.0)
            if any(t in sensation.tags for t in tags):
                multiplier += scale * drive_value
        multiplier = max(0.1, multiplier)
        new_intensity = min(1.0, sensation.intensity * multiplier)
        if abs(new_intensity - sensation.intensity) < 0.001:
            return sensation
        return replace(sensation, intensity=new_intensity)

    def _associate(self, tags: frozenset[str]) -> list[dict]:
        matched: dict[str, dict] = {}
        for tag in tags:
            if tag in CONCEPTS:
                matched[tag] = {"tag": tag, **CONCEPTS[tag]}
            for concept, data in CONCEPTS.items():
                if tag in data.get("is_a", []) and concept not in matched:
                    matched[concept] = {"tag": concept, **data}
        return list(matched.values())

    def clear_scene(self) -> None:
        self.current_scene = []
