from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class Sensation:
    modality: str           # "visual", "olfactory", "tactile", "internal", ...
    intensity: float        # 0.0–1.0
    valence: float          # -1.0 (aversive) → 1.0 (appetitive)
    tags: frozenset[str]    # semantic labels: {"apple", "food", "red"}
    raw: Any = None
    timestamp: float = field(default_factory=time.time)


class SensorBase(ABC):
    def __init__(self, bus):
        self.bus = bus

    @abstractmethod
    def sense(self) -> Sensation | None: ...

    def tick(self) -> None:
        sensation = self.sense()
        if sensation is not None:
            self.bus.publish("sensation", sensation)
