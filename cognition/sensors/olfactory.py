from ..sensation import SensorBase, Sensation


class OlfactorySensor(SensorBase):
    """Smell sensor — lower intensity than visual, often precedes a visual confirmation."""

    def __init__(self, bus, scents: list[str] | None = None, intensity: float = 0.5):
        super().__init__(bus)
        self._scents: list[str] = scents or []
        self.intensity = intensity

    def set_scents(self, tags: list[str], intensity: float | None = None) -> None:
        self._scents = tags
        if intensity is not None:
            self.intensity = intensity

    def sense(self) -> Sensation | None:
        if not self._scents:
            return None
        return Sensation(
            modality="olfactory",
            intensity=self.intensity,
            valence=0.4,
            tags=frozenset(self._scents),
        )
