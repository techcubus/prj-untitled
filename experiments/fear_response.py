"""
Experiment: static hazard (fire) triggers fear → flee → fear subsides.

Demonstrates the fear spike-and-decay cycle and the nociceptive pain
that builds from sustained contact if the agent doesn't flee fast enough.
"""

from cognition import Agent
from cognition.sensors.visual import VisualSensor
from cognition.sensors.internal import InternalSensor
from cognition.sensors.nociception import NociceptionSensor


def run(ticks: int = 70, hazard_appears_at: int = 8, hazard_lasts: int = 6):
    agent = Agent("mouse")

    # This experiment isolates fear/pain — neutralise hunger so starvation
    # doesn't kill the agent before the full recovery arc plays out.
    agent.limbic.drives["hunger"].value = 0.0
    agent.limbic.drives["hunger"].decay_rate = 0.0

    visual   = VisualSensor(agent.bus)
    internal = InternalSensor(agent.bus, agent.limbic)
    noci     = NociceptionSensor(agent.bus, agent.perception)
    agent.attach_sensor(visual).attach_sensor(internal).attach_sensor(noci)

    print(f"\n{'Tick':>4}  {'Fear':>6}  {'Discomf':>7}  {'Fatigue':>7}  {'Mood':>6}  {'Scene':<22}  Action")
    print("─" * 76)

    for t in range(1, ticks + 1):
        if t == hazard_appears_at:
            visual.set_scene(["fire"])
        elif t == hazard_appears_at + hazard_lasts:
            visual.set_scene([])

        action = agent.tick()
        s = agent.status()

        fear    = s["drives"]["fear"]
        discomf = s["drives"]["discomfort"]
        fatigue = s["drives"]["fatigue"]
        mood    = s["mood"]
        scene   = ", ".join(s["scene"]) if s["scene"] else "—"
        act     = str(action) if action else "—"

        print(f"{t:>4}  {fear:>6.3f}  {discomf:>7.3f}  {fatigue:>7.3f}  {mood:>6.3f}  {scene:<22}  {act}")

        if not agent.limbic.alive:
            print("\n  [agent died]")
            break


if __name__ == "__main__":
    run()
