from ..sensation import SensorBase, Sensation
from ..limbic import LimbicSystem


class InternalSensor(SensorBase):
    """Interoception — the agent sensing its own body state (hunger pangs, heart rate, etc.)."""

    def __init__(self, bus, limbic: LimbicSystem, threshold: float = 0.3):
        super().__init__(bus)
        self.limbic = limbic
        self.threshold = threshold

    def sense(self) -> Sensation | None:
        snapshot = self.limbic.snapshot()
        dominant = max(snapshot, key=snapshot.get)
        value = snapshot[dominant]

        if value < self.threshold:
            return None

        aversive = dominant in ("hunger", "fear", "discomfort")
        return Sensation(
            modality="internal",
            intensity=value,
            valence=-value if aversive else value,
            tags=frozenset([dominant, f"{dominant}_sensation"]),
        )
