from ..sensation import SensorBase, Sensation


class VisualSensor(SensorBase):
    """Presents a scene as a visual sensation. Call set_scene() to change what the agent sees."""

    def __init__(self, bus, scene: list[str] | None = None):
        super().__init__(bus)
        self._scene: list[str] = scene or []

    def set_scene(self, tags: list[str]) -> None:
        self._scene = tags

    def sense(self) -> Sensation | None:
        if not self._scene:
            return None
        return Sensation(
            modality="visual",
            intensity=0.8,
            valence=0.5,
            tags=frozenset(self._scene),
        )
