"""
Experiment: hunger → food perception → consume → satiation + taste sensation → memory.

Watch how emotional modulation sharpens food perception as hunger rises.
The taste sensor fires on the tick after eating, reinforcing (or correcting) the memory.

Tick resolution: 1 slow tick = slow_divisor fast ticks (default 10).
Fast drives (fear, curiosity) update every fast tick.
Slow drives (hunger, fatigue, discomfort) update every slow tick.
Display rows show state at the end of each slow tick.
"""

from cognition import Agent
from cognition.sensors.visual import VisualSensor
from cognition.sensors.internal import InternalSensor
from cognition.sensors.taste import TasteSensor


def run(slow_ticks: int = 60, apple_appears_at: int = 15, apple_lasts: int = 200):
    agent = Agent("mouse")
    div = agent.limbic.slow_divisor

    visual   = VisualSensor(agent.bus)
    internal = InternalSensor(agent.bus, agent.limbic)
    taste    = TasteSensor(agent.bus)
    agent.attach_sensor(visual).attach_sensor(internal).attach_sensor(taste)

    print(f"\nTimescale: 1 slow tick = {div} fast ticks")
    print(f"\n{'Tick':>4}  {'Hunger':>6}  {'Fatigue':>7}  {'Mood':>6}  {'Scene':<22}  Action")
    print("─" * 70)

    for t in range(1, slow_ticks + 1):
        if t == apple_appears_at:
            visual.set_scene(["apple"])
        elif t == apple_appears_at + apple_lasts:
            visual.set_scene([])

        action = None
        for _ in range(div):
            a = agent.tick()
            if a is not None:
                action = a   # last action in the fast-tick burst

        s = agent.status()
        hunger  = s["drives"]["hunger"]
        fatigue = s["drives"]["fatigue"]
        mood    = s["mood"]
        scene   = ", ".join(s["scene"]) if s["scene"] else "—"
        act     = str(action) if action else "—"

        print(f"{t:>4}  {hunger:>6.3f}  {fatigue:>7.3f}  {mood:>6.3f}  {scene:<22}  {act}")

    print(f"\nMemories stored: {agent.status()['memories']}")


if __name__ == "__main__":
    run()
