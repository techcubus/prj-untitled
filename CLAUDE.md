# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Python simulation of lower-order biological cognition (mouse/dog/infant level). The goal is to model how drives, sensory input, memory, and behavior interact — and to run controlled experiments against that model.

## Running experiments

```bash
python main.py hunger          # hunger → food perception → consume → satiation
python main.py fear            # threat perception → fear drive → flee
python main.py hunger --ticks 60
```

Or run an experiment file directly:
```bash
python experiments/basic_hunger.py
```

## Architecture

All modules communicate through a central `EventBus` (pub/sub). No module holds a direct reference to another — they only know the bus.

**Data flow per tick:**
1. Sensors → publish `"sensation"` events (tags + intensity + valence)
2. `PerceptionModule` receives sensations → maps tags to concepts via `CONCEPTS` graph → publishes `"perception"`
3. `LimbicSystem` ticks drives forward (needs build over time) → publishes `"need"` when drives cross threshold
4. `BehaviorEngine` receives perceptions → selects highest-urgency drive → matches against current scene or past memory → executes action → stores `Episode` in `MemoryStore`

**Memory retrieval** is weighted by both semantic similarity (Jaccard over tags) and emotional similarity (cosine over limbic snapshots). A hungry agent surfaces food-related memories faster than a calm one.

## Adding a sensor

Subclass `SensorBase`, implement `sense() -> Sensation | None`, attach to agent:

```python
from cognition.sensation import SensorBase, Sensation

class MySensor(SensorBase):
    def sense(self) -> Sensation | None:
        return Sensation(modality="tactile", intensity=0.6, valence=-0.5, tags=frozenset(["sharp", "pain"]))

agent.attach_sensor(MySensor(agent.bus))
```

## Adding a concept

Edit `cognition/perception.py` → `CONCEPTS` dict:

```python
"mushroom": {"is_a": ["food"], "satisfies": ["hunger"], "valence": 0.6},
```

## Key files

| File | Role |
|------|------|
| `cognition/bus.py` | EventBus — the nervous system |
| `cognition/limbic.py` | Drives (hunger, fear, curiosity, discomfort) + mood |
| `cognition/sensation.py` | `Sensation` dataclass + `SensorBase` ABC |
| `cognition/perception.py` | Concept graph + association engine |
| `cognition/memory.py` | Episodic memory with limbic-weighted retrieval |
| `cognition/behavior.py` | Drive-reduction action selection |
| `cognition/agent.py` | Orchestrator — holds all modules, exposes `tick()` |
| `cognition/sensors/` | Pluggable sensors: `visual`, `olfactory`, `internal` |
| `experiments/` | Self-contained runnable scenarios |
