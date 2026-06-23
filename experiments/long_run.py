"""
Long-run spatial experiment: up to 3200 slow ticks, food respawns, unlimited generations.

A 30×30 grid with two static fire hazards. The apple respawns at a random location
after each eat, forcing the agent to navigate afresh each time. The agent dies and
respawns with mutated drive parameters as many times as the tick budget allows.

Summary lines print every `summary_every` slow ticks. Generation transitions and
notable events print immediately. The final block shows per-generation stats so you
can see whether drive parameter drift correlates with survival.

At hunger timescale (~1.5 hrs/slow tick) this represents roughly 200 simulated days.
"""

import random
import math
from cognition import Agent
from cognition.world import World
from cognition.sensors.world_visual import WorldVisualSensor
from cognition.sensors.internal import InternalSensor
from cognition.sensors.nociception import NociceptionSensor
from cognition.sensors.taste import TasteSensor

GRID          = 30
SPAWN_POS     = (3, 15)
HAZARDS       = [(15, 15), (24, 8)]
VIS_RADIUS    = 8.0
MIN_FOOD_DIST = 3    # not right at the agent's feet
MAX_FOOD_DIST = 12   # reachable by foraging before starvation


def _place_food(world: World, avoid: tuple[int, int]) -> tuple[int, int]:
    occupied = set(world._objects.keys())
    for _ in range(1000):
        pos = (random.randint(1, GRID - 2), random.randint(1, GRID - 2))
        if pos in occupied:
            continue
        d = math.dist(pos, avoid)
        if d < MIN_FOOD_DIST or d > MAX_FOOD_DIST:
            continue
        return pos
    # fallback: relax max distance if grid is too constrained
    while True:
        pos = (random.randint(1, GRID - 2), random.randint(1, GRID - 2))
        if pos not in occupied and math.dist(pos, avoid) >= MIN_FOOD_DIST:
            return pos


def _make_agent(world: World, base: Agent | None = None) -> Agent:
    agent = base.respawn() if base else Agent("mouse")
    world.agent_pos = SPAWN_POS
    agent.attach_world(world)
    agent.attach_sensor(WorldVisualSensor(agent.bus, world, visual_radius=VIS_RADIUS))
    agent.attach_sensor(InternalSensor(agent.bus, agent.limbic))
    agent.attach_sensor(NociceptionSensor(agent.bus, agent.perception))
    agent.attach_sensor(TasteSensor(agent.bus))
    return agent


def run(slow_ticks: int = 3200, summary_every: int = 50):
    random.seed(42)

    world = World(GRID, GRID)
    for hx, hy in HAZARDS:
        world.place(["fire"], hx, hy)

    food_pos = _place_food(world, SPAWN_POS)
    world.place(["apple"], *food_pos)

    agent = _make_agent(world)
    div   = agent.limbic.slow_divisor

    # stats
    gen_eats      = 0
    gen_start     = 1
    total_eats    = 0
    gen_log: list[dict] = []

    print(f"\nLong-run spatial experiment  |  {GRID}×{GRID} grid  |  {slow_ticks} slow ticks")
    print(f"Spawn: {SPAWN_POS}  |  Hazards: {HAZARDS}  |  Visual radius: {VIS_RADIUS}")
    print(f"Timescale: 1 slow tick = {div} fast ticks  |  Summary every {summary_every} ticks\n")

    print(f"{'Tick':>6}  {'Gen':>3}  {'Pos':>8}  {'Hunger':>6}  {'Fear':>5}  "
          f"{'Discomf':>7}  {'Mood':>6}  {'Food':>8}  {'Eats/gen':>8}")
    print("─" * 80)

    for t in range(1, slow_ticks + 1):
        action = None
        consumed = False

        for _ in range(div):
            a = agent.tick()
            if a is not None:
                action = a
            # respawn food immediately on first consume so later fast ticks don't double-eat
            if action and action.name == "consume" and not consumed:
                consumed = True
                world.remove(*food_pos)
                food_pos = _place_food(world, world.agent_pos)
                world.place(["apple"], *food_pos)
                gen_eats   += 1
                total_eats += 1

        if t % summary_every == 0:
            s = agent.status()
            print(f"{t:>6}  {agent.generation:>3}  {str(s['pos']):>8}  "
                  f"{s['drives']['hunger']:>6.3f}  {s['drives']['fear']:>5.3f}  "
                  f"{s['drives']['discomfort']:>7.3f}  {s['mood']:>6.3f}  "
                  f"{str(food_pos):>8}  {gen_eats:>8}")

        if not agent.alive:
            cause      = agent.limbic._cause_of_death()
            ticks_lived = t - gen_start + 1
            gen_log.append({
                "gen":          agent.generation,
                "ticks":        ticks_lived,
                "eats":         gen_eats,
                "cause":        cause,
                "h_decay":      agent.limbic.drives["hunger"].decay_rate,
                "d_threshold":  agent.limbic.drives["discomfort"].threshold,
                "fear_decay":   abs(agent.limbic.drives["fear"].decay_rate),
            })
            print(f"\n  ✗ Gen {agent.generation:>2} died  t={t}  ({cause})  "
                  f"lived={ticks_lived}  eats={gen_eats}  "
                  f"h_decay={agent.limbic.drives['hunger'].decay_rate:.4f}\n")

            agent     = _make_agent(world, base=agent)
            world.remove(*food_pos)
            food_pos  = _place_food(world, SPAWN_POS)
            world.place(["apple"], *food_pos)
            gen_eats  = 0
            gen_start = t + 1

    # ── final report ──────────────────────────────────────────────────────────
    s = agent.status()
    print(f"\n{'═' * 80}")
    print(f"Run complete  |  total ticks: {slow_ticks}  |  total eats: {total_eats}  "
          f"|  generations: {agent.generation + 1}")
    print(f"Final agent: gen={agent.generation}  pos={s['pos']}  "
          f"hunger={s['drives']['hunger']:.3f}  mood={s['mood']:.3f}  "
          f"memories={s['memories']}")

    if gen_log:
        print(f"\nGeneration history:")
        print(f"  {'Gen':>3}  {'Ticks':>6}  {'Eats':>5}  {'Cause':<12}  "
              f"{'H_decay':>8}  {'D_thresh':>8}  {'F_decay':>8}")
        print("  " + "─" * 62)
        for g in gen_log:
            print(f"  {g['gen']:>3}  {g['ticks']:>6}  {g['eats']:>5}  "
                  f"{g['cause']:<12}  {g['h_decay']:>8.4f}  "
                  f"{g['d_threshold']:>8.3f}  {g['fear_decay']:>8.4f}")
        avg_eats = sum(g["eats"] for g in gen_log) / len(gen_log)
        print(f"\n  Avg eats/generation (completed): {avg_eats:.1f}")


if __name__ == "__main__":
    run()
