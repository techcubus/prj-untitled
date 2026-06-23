from ..sensation import SensorBase, Sensation
from ..world import World


class WorldVisualSensor(SensorBase):
    """
    Reads the World grid and fires one Sensation per visible object.

    Intensity scales with proximity (1.0 at agent's feet, near 0 at visual_radius).
    Each sensation carries position and distance in `raw` so the perception module
    and behavior engine can reason about where things are, not just what they are.

    Use this instead of VisualSensor when the agent has a spatial world.
    """

    def __init__(self, bus, world: World, visual_radius: float = 6.0):
        super().__init__(bus)
        self.world = world
        self.visual_radius = visual_radius

    def sense(self) -> Sensation | None:
        return None  # tick() fires directly — one sensation per object

    def tick(self) -> None:
        for obj, dist in self.world.objects_near(self.visual_radius):
            intensity = max(0.1, 1.0 - dist / self.visual_radius)
            self.bus.publish("sensation", Sensation(
                modality="visual",
                intensity=intensity,
                valence=0.5,
                tags=frozenset(obj.tags),
                raw={"position": obj.pos, "distance": dist},
            ))
