"""
Experiment: spatial navigation — agent must move through a 2D grid to reach food,
with a static fire hazard appearing mid-run to test retreat behaviour.

Layout (20×20 grid):
  Agent  @ (3, 10)
  Apple    (8, 10)  — 5 tiles east, within visual radius from the start
  Fire     (6, 10)  — appears at tick 40, directly between agent and apple

Phase 1 (ticks 1–39): Pure approach. Agent navigates east toward apple, eats,
hunger resets, approaches again. Shows that spatial navigation and consume work.

Phase 2 (ticks 40–80): Fire appears between agent and apple. Approach-avoidance
conflict: fear drives retreat (west), hunger drives approach (east). Watch which
drive dominates tick by tick as hunger rebuilds after each eat.

Navigation: one tile per slow tick (metabolic cadence). Visual radius: 6 tiles.
"""

from cognition import Agent
from cognition.world import World
from cognition.sensors.world_visual import WorldVisualSensor
from cognition.sensors.internal import InternalSensor
from cognition.sensors.nociception import NociceptionSensor
from cognition.sensors.taste import TasteSensor


def run(slow_ticks: int = 80):
    world = World(width=20, height=20)
    world.agent_pos = (3, 10)
    world.place(["apple"], 8, 10)

    agent = Agent("mouse")
    agent.attach_world(world)

    world_vis = WorldVisualSensor(agent.bus, world, visual_radius=6.0)
    internal  = InternalSensor(agent.bus, agent.limbic)
    noci      = NociceptionSensor(agent.bus, agent.perception)
    taste     = TasteSensor(agent.bus)
    agent.attach_sensor(world_vis).attach_sensor(internal).attach_sensor(noci).attach_sensor(taste)

    div = agent.limbic.slow_divisor
    fire_tick = 40

    print(f"\nWorld: 20×20  |  Agent @ (3,10)  Apple @ (8,10)  Fire @ (6,10) appears at tick {fire_tick}")
    print(f"Visual radius: 6 tiles  |  Timescale: 1 slow tick = {div} fast ticks\n")

    header = f"{'Tick':>4}  {'Pos':>7}  {'Hunger':>6}  {'Fear':>5}  {'Discomf':>7}  {'Mood':>6}  {'Visible':<22}  Action"
    print(header)
    print("─" * len(header))

    for t in range(1, slow_ticks + 1):
        if t == fire_tick:
            world.place(["fire"], 6, 10)
            print(f"\n  --- fire appears at (6,10) ---\n")

        action = None
        for _ in range(div):
            a = agent.tick()
            if a is not None:
                action = a

        s = agent.status()
        pos     = s["pos"]
        hunger  = s["drives"]["hunger"]
        fear    = s["drives"]["fear"]
        discomf = s["drives"]["discomfort"]
        mood    = s["mood"]
        visible = ", ".join(s["scene"]) if s["scene"] else "—"
        act     = str(action) if action else "—"

        print(f"{t:>4}  {str(pos):>7}  {hunger:>6.3f}  {fear:>5.3f}  {discomf:>7.3f}  {mood:>6.3f}  {visible:<22}  {act}")

        if not agent.limbic.alive:
            print("\n  [agent died]")
            break

    s = agent.status()
    print(f"\nFinal: pos={s['pos']}  hunger={s['drives']['hunger']:.3f}  "
          f"memories={s['memories']}  mood={s['mood']:.3f}")


if __name__ == "__main__":
    run()
