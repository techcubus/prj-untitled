class NociceptionSensor:
    """
    Tissue-damage sense — an interoceptive module, not an exteroceptive sensor.

    Reads the current perceptual scene for hazard contact each tick and publishes
    directly to the 'nociception' bus topic. LimbicSystem subscribes to that topic
    and updates the discomfort drive — no concept graph involved.

    Pain level builds under sustained hazard contact and heals when hazards leave.
    Attach after external sensors (visual, olfactory) so perception.current_scene
    is populated for this tick before sense() runs.
    """

    def __init__(self, bus, perception, build_rate: float = 0.10, heal_rate: float = 0.09):
        self.bus = bus
        self.perception = perception
        self._pain_level: float = 0.0
        self.build_rate = build_rate
        self.heal_rate = heal_rate

    def tick(self) -> None:
        hazards = [c for c in self.perception.current_scene if c.get("hazard")]

        if hazards:
            worst = max(abs(h.get("valence", -0.5)) for h in hazards)
            self._pain_level = min(1.0, self._pain_level + worst * self.build_rate)
        else:
            self._pain_level = max(0.0, self._pain_level - self.heal_rate)

        if self._pain_level >= 0.05:
            self.bus.publish("nociception", {"pain_level": self._pain_level})
