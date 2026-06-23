import math
from dataclasses import dataclass


@dataclass
class WorldObject:
    tags: list[str]
    pos: tuple[int, int]


class World:
    """
    Simple 2-D grid. The agent has a position; objects have positions.
    Sensors read from the world; the behavior engine moves the agent through it.
    """

    def __init__(self, width: int = 20, height: int = 20):
        self.width = width
        self.height = height
        self.agent_pos: tuple[int, int] = (width // 2, height // 2)
        self._objects: dict[tuple[int, int], WorldObject] = {}

    # --- world authoring ---

    def place(self, tags: list[str], x: int, y: int) -> None:
        self._objects[(x, y)] = WorldObject(tags=tags, pos=(x, y))

    def remove(self, x: int, y: int) -> None:
        self._objects.pop((x, y), None)

    # --- spatial queries ---

    def distance_to(self, pos: tuple[int, int]) -> float:
        ax, ay = self.agent_pos
        px, py = pos
        return math.sqrt((px - ax) ** 2 + (py - ay) ** 2)

    def objects_near(self, radius: float = 6.0) -> list[tuple[WorldObject, float]]:
        results = []
        for obj in self._objects.values():
            d = self.distance_to(obj.pos)
            if d <= radius:
                results.append((obj, d))
        return sorted(results, key=lambda x: x[1])

    def at_agent(self) -> WorldObject | None:
        return self._objects.get(self.agent_pos)

    # --- movement ---

    def step_toward(self, target: tuple[int, int]) -> None:
        ax, ay = self.agent_pos
        tx, ty = target
        dx = 0 if tx == ax else (1 if tx > ax else -1)
        dy = 0 if ty == ay else (1 if ty > ay else -1)
        self.agent_pos = (
            max(0, min(self.width - 1, ax + dx)),
            max(0, min(self.height - 1, ay + dy)),
        )

    def step_away(self, target: tuple[int, int]) -> None:
        ax, ay = self.agent_pos
        tx, ty = target
        dx = 0 if tx == ax else (-1 if tx > ax else 1)
        dy = 0 if ty == ay else (-1 if ty > ay else 1)
        self.agent_pos = (
            max(0, min(self.width - 1, ax + dx)),
            max(0, min(self.height - 1, ay + dy)),
        )
