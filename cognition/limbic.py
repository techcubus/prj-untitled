from dataclasses import dataclass


@dataclass
class Drive:
    name: str
    value: float = 0.0
    decay_rate: float = 0.02    # positive = need builds; negative = naturally heals
    threshold: float = 0.6      # urgency level that triggers a need signal
    timescale: str = "fast"     # "fast": ticks every agent tick; "slow": every slow_divisor fast ticks

    def tick(self) -> None:
        self.value = max(0.0, min(1.0, self.value + self.decay_rate))

    def satisfy(self, amount: float = 1.0) -> None:
        self.value = max(0.0, self.value - amount)


# Spikes from exteroceptive perception events (things seen/heard in the world)
_PERCEPTION_SPIKE: dict[str, float] = {
    "fear":      0.45,
    "curiosity": 0.25,
    # discomfort is NOT here — nociception handles it directly, bypassing concept graph
}


class LimbicSystem:
    def __init__(self, bus, slow_divisor: int = 10):
        self.bus = bus
        self.slow_divisor = slow_divisor
        self._fast_ticks = 0
        self.drives: dict[str, Drive] = {
            "hunger":     Drive("hunger",     value=0.10, decay_rate= 0.025, timescale="slow"),
            "fear":       Drive("fear",       value=0.00, decay_rate=-0.050, threshold=0.40, timescale="fast"),
            "discomfort": Drive("discomfort", value=0.00, decay_rate=-0.015, timescale="slow"),
            "fatigue":    Drive("fatigue",    value=0.05, decay_rate= 0.004, threshold=0.70, timescale="slow"),
            "curiosity":  Drive("curiosity",  value=0.35, decay_rate= 0.008, threshold=0.50, timescale="slow"),
        }
        self.alive: bool = True
        self.age: int = 0
        bus.subscribe("perception",   self._on_perception)
        bus.subscribe("nociception",  self._on_nociception)
        bus.subscribe("taste",        self._on_taste)

    def _on_perception(self, payload: dict) -> None:
        """Exteroceptive signals — things in the world that spike drives on sight."""
        for concept in payload["concepts"]:
            for trigger in concept.get("triggers", []):
                if trigger in self.drives:
                    spike = _PERCEPTION_SPIKE.get(trigger, 0.2)
                    self.drives[trigger].value = min(1.0, self.drives[trigger].value + spike)

    def _on_nociception(self, payload: dict) -> None:
        """Direct tissue-damage signal — bypasses concept graph, drives discomfort.

        Scaled by slow_divisor so total discomfort impact per slow tick stays constant
        regardless of how many fast ticks fire nociception within it.
        """
        pain = payload["pain_level"]
        self.drives["discomfort"].value = min(
            1.0, self.drives["discomfort"].value + pain * 0.22 / self.slow_divisor
        )

    def _on_taste(self, payload: dict) -> None:
        """Post-ingestive signal — bad food spikes discomfort; good food needs no action."""
        valence = payload["valence"]
        if valence < 0:
            self.drives["discomfort"].value = min(
                1.0, self.drives["discomfort"].value + abs(valence) * 0.35
            )

    def tick(self) -> None:
        self._fast_ticks += 1
        self.age += 1
        slow_tick = (self._fast_ticks % self.slow_divisor) == 0

        for drive in self.drives.values():
            if drive.timescale == "fast" or slow_tick:
                drive.tick()

        if self.drives["hunger"].value >= 1.0 or self.drives["discomfort"].value >= 1.0:
            self.alive = False
            self.bus.publish("death", {"age": self.age, "cause": self._cause_of_death()})
            return
        active = self.active_needs()
        if active:
            self.bus.publish("need", active)

    def _cause_of_death(self) -> str:
        return "starvation" if self.drives["hunger"].value >= 1.0 else "injury"

    def active_needs(self) -> list[str]:
        return [name for name, d in self.drives.items() if d.value >= d.threshold]

    def satisfy(self, drive_name: str, amount: float = 1.0) -> None:
        if drive_name in self.drives:
            self.drives[drive_name].satisfy(amount)

    def mood(self) -> float:
        d = self.drives
        distress = (d["hunger"].value + d["fear"].value
                    + d["discomfort"].value + d["fatigue"].value * 0.5)
        engagement = d["curiosity"].value
        return round(engagement * 0.3 - distress * 0.5, 3)

    def snapshot(self) -> dict[str, float]:
        return {name: d.value for name, d in self.drives.items()}
