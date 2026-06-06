"""
Experiment: hunger vs. fear/discomfort — food and a static hazard (fire) appear simultaneously.

All four new senses are active: nociception builds pain from contact, taste fires after eating,
emotional modulation sharpens relevant perceptions, fatigue accumulates from actions.
If the agent dies, it respawns with mutated parameters.
"""

from cognition import Agent
from cognition.sensors.visual import VisualSensor
from cognition.sensors.internal import InternalSensor
from cognition.sensors.nociception import NociceptionSensor
from cognition.sensors.taste import TasteSensor


def _make_agent(base: Agent | None = None) -> tuple[Agent, VisualSensor]:
    agent = base.respawn() if base else Agent("mouse")
    visual   = VisualSensor(agent.bus)
    internal = InternalSensor(agent.bus, agent.limbic)
    noci     = NociceptionSensor(agent.bus, agent.perception)
    taste    = TasteSensor(agent.bus)
    # external sensors first so nociception has fresh hazard context when it fires
    agent.attach_sensor(visual).attach_sensor(internal).attach_sensor(noci).attach_sensor(taste)
    return agent, visual


def _header():
    print(f"{'Tick':>4}  {'Hunger':>6}  {'Discomf':>7}  {'Fear':>5}  {'Fatigue':>7}  {'Mood':>6}  {'Scene':<24}  Action")
    print("─" * 84)


def run(
    ticks: int = 60,
    conflict_starts_at: int = 18,
    conflict_lasts: int = 15,
    max_generations: int = 3,
):
    agent, visual = _make_agent()
    print(f"\nGen {agent.generation} | hunger={agent.limbic.drives['hunger'].value:.2f}  "
          f"hunger_decay={agent.limbic.drives['hunger'].decay_rate:.4f}\n")
    _header()

    t = 0
    while t < ticks:
        t += 1

        if t == conflict_starts_at:
            visual.set_scene(["apple", "fire"])
        elif t == conflict_starts_at + conflict_lasts:
            visual.set_scene(["apple"])

        action = agent.tick()
        s = agent.status()

        hunger  = s["drives"]["hunger"]
        discomf = s["drives"]["discomfort"]
        fear    = s["drives"]["fear"]
        fatigue = s["drives"]["fatigue"]
        mood    = s["mood"]
        scene   = ", ".join(s["scene"]) if s["scene"] else "—"
        act     = str(action) if action else "—"
        marker  = " <" if conflict_starts_at <= t < conflict_starts_at + conflict_lasts else "  "

        print(f"{t:>4}  {hunger:>6.3f}  {discomf:>7.3f}  {fear:>5.3f}  {fatigue:>7.3f}  {mood:>6.3f}  {scene:<24}  {act}{marker}")

        if not agent.alive:
            cause = agent.limbic._cause_of_death()
            print(f"\n  *** died at tick {t} ({cause}) | gen {agent.generation} | "
                  f"age {s['age']} | memories {s['memories']} ***\n")
            if agent.generation >= max_generations - 1:
                print("  Max generations reached.")
                break
            agent, visual = _make_agent(agent)
            t = 0
            print(f"\nGen {agent.generation} | "
                  f"hunger_decay={agent.limbic.drives['hunger'].decay_rate:.4f}  "
                  f"discomfort_threshold={agent.limbic.drives['discomfort'].threshold:.3f}\n")
            _header()

    s = agent.status()
    print(f"\nFinal: gen={s['generation']}  age={s['age']}  memories={s['memories']}  mood={s['mood']:.3f}")


if __name__ == "__main__":
    run()
