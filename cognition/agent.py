import random
from .bus import EventBus
from .limbic import LimbicSystem
from .memory import MemoryStore
from .perception import PerceptionModule
from .behavior import BehaviorEngine, Action
from .sensation import SensorBase


class Agent:
    def __init__(self, name: str = "agent", generation: int = 0):
        self.name = name
        self.generation = generation
        self.bus = EventBus()
        self.limbic = LimbicSystem(self.bus)
        self.perception = PerceptionModule(self.bus, self.limbic)  # limbic enables emotional modulation
        self.memory = MemoryStore()
        self.behavior = BehaviorEngine(self.bus, self.limbic, self.memory)
        self._sensors: list[SensorBase] = []

    def attach_sensor(self, sensor: SensorBase) -> "Agent":
        self._sensors.append(sensor)
        return self

    def tick(self) -> Action | None:
        if not self.limbic.alive:
            return None
        self.perception.clear_scene()
        self.behavior.current_concepts = []    # reset per-tick accumulation
        for sensor in self._sensors:
            sensor.tick()
        self.limbic.tick()
        if not self.limbic.alive:
            return None
        return self.behavior.tick()

    def respawn(self, mutation_rate: float = 0.1) -> "Agent":
        """New agent with mutated drive parameters. No memory transfer."""
        child = Agent(self.name, generation=self.generation + 1)
        for name, drive in self.limbic.drives.items():
            child_drive = child.limbic.drives[name]
            child_drive.decay_rate = max(0.001, drive.decay_rate * random.gauss(1.0, mutation_rate))
            child_drive.threshold  = max(0.10, min(0.95, drive.threshold * random.gauss(1.0, mutation_rate)))
        return child

    @property
    def alive(self) -> bool:
        return self.limbic.alive

    def status(self) -> dict:
        return {
            "drives":     self.limbic.snapshot(),
            "mood":       self.limbic.mood(),
            "memories":   len(self.memory),
            "scene":      [c["tag"] for c in self.perception.current_scene],
            "alive":      self.limbic.alive,
            "age":        self.limbic.age,
            "generation": self.generation,
        }
