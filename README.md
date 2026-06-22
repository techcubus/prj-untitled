# Cognitive Drive Simulation

This is a personal educational project. I'm not a neuroscientist or AI researcher — I'm trying to understand how primitive cognition might work by building a simulation of it from scratch, then running controlled experiments against it and seeing what falls out.

---

## The premise

Most AI discussion focuses on large language models: systems that predict text. This project asks a different question — what came *before* language? What does cognition look like at the level of a mouse, a dog, or an infant?

The answer, as far as neuroscience can tell us, is something like this: the organism has a set of internal drives (hunger, fear, discomfort, fatigue, curiosity) that build over time and create pressure toward action. Sensory input from the environment gets filtered through the emotional state — a hungry animal perceives food more intensely; a fearful one is hypervigilant to threats. The animal acts to reduce the most urgent drive, and stores the outcome as a memory weighted by how it felt emotionally at the time. The next time it encounters a similar situation, that memory shapes what it does.

No language. No planning. No reasoning. Just drives, sensation, memory, and behavior in a loop.

---

## Architecture and methodology

The simulation is built in pure Python (no external dependencies, Python 3.11+) around five core ideas:

### 1. The event bus
All modules communicate through a central publish/subscribe bus — no module holds a direct reference to another. This mirrors how the nervous system works: components react to signals without needing to know where they came from.

### 2. Drives (the limbic system)
Five drives are modeled, each with a current value, a natural build or decay rate, and an urgency threshold:

| Drive | Timescale | Behavior |
|---|---|---|
| Hunger | Slow | Builds steadily; death at 1.0 (starvation) |
| Fear | **Fast** | Spikes on hazard perception; decays quickly when threat is gone |
| Discomfort | Slow | Fed by nociception (tissue damage) and bad taste; heals slowly |
| Fatigue | Slow | Builds with each action taken; drives rest behavior |
| Curiosity | Slow | Builds over time; satisfied by exploring novel stimuli |

Drives run on two timescales. The simulation ticks at a fast rate (roughly seconds); every `slow_divisor` fast ticks (default: 10), slow drives also advance. This separates reflexive responses from metabolic ones — fear reacts within a single fast tick the way the amygdala does, while hunger and healing operate on a much longer cycle. A displayed "tick" in experiments represents one slow tick (one metabolic cycle), with 10 fast ticks of neural processing happening inside it.

### 3. Sensors
Sensors are split into two categories, which is a distinction that matters architecturally:

**Exteroceptive** (world-facing) — visual, olfactory. These fire sensations that pass through a concept graph before reaching the limbic system. A visual sensor that sees "fire" produces a concept tagged `hazard`, which spikes fear.

**Interoceptive** (body-facing) — nociception, taste. These bypass the concept graph entirely and publish directly to the limbic system. Pain is not something perceived in the world; it is felt. This separation turned out to be important: early versions incorrectly ran pain through the concept graph, which created architectural confusion between what the agent *sees* and what it *feels*.

### 4. Emotional modulation of perception
The limbic state scales sensation intensity before concept matching. A hungry agent perceives food more intensely. A tired agent finds novelty less salient. This means the same physical environment produces a different perceptual experience depending on internal state.

### 5. Episodic memory
The agent stores episodes (what happened, what the scene looked like, what the emotional state was). Retrieval is weighted by both semantic similarity (tag overlap with current context) and emotional similarity (cosine distance between current limbic state and the state at encoding time). A hungry agent surfaces food memories faster than a calm one.

### 6. Behavioral loop
Each fast tick:
1. Sensors fire
2. Perception processes sensations into concepts (with emotional modulation)
3. Fast drives (fear) tick forward
4. Every `slow_divisor` fast ticks, slow drives (hunger, discomfort, fatigue, curiosity) also tick
5. The highest-urgency active drive becomes the primary need
6. The behavior engine scans the current scene and memory for something that satisfies it
7. An action is executed; the outcome is stored in memory
8. If drives breach death thresholds (hunger or discomfort ≥ 1.0), the agent dies and can respawn with mutated drive parameters (an evolutionary loop)

---

## Current results

Three experiments have been built and run:

### Experiment 1: basic hunger (`python main.py hunger`)
Apple appears in the environment partway through. The agent ignores it until hunger crosses threshold, then consumes it and resets. Straightforward drive-reduction loop working as expected.

### Experiment 2: fear response (`python main.py fear`)
A fire hazard appears briefly. The agent flees each tick it's present. After the fire leaves, **nociception continues building for several ticks** (accumulated tissue damage), peaking several ticks after the hazard is gone before slowly healing. The recovery arc takes roughly 35 ticks after peak pain. Fatigue from repeated fleeing eventually triggers a rest event. The agent returns to baseline around tick 55.

This produced an interesting emergent behavior: pain gets worse *after* the threat is gone, then heals. That's not a bug — it's how real nociception works.

### Experiment 3: conflicting drives (`python main.py conflict`)
Apple and fire appear simultaneously. All five drives are active. This produced several notable behaviors:

**Approach-avoidance oscillation.** The agent alternates between fleeing (fear dominant) and occasionally eating (hunger dominant when starvation pressure exceeds threat response). When fear was fully satisfied by fleeing and curiosity happened to be building above it, the agent froze for one tick — unable to act on its curiosity (no novel stimuli) and not urgent enough on fear to flee immediately. This is the approach-avoidance conflict playing out in the architecture without being explicitly programmed.

**Hunger overrides fear under sufficient pressure.** At tick 21, hunger value (0.625) exceeded fear value (0.500) for the first time, and the agent ate the apple with fire still present. It then resumed fleeing. The starvation drive overcame the threat response — which is realistic.

**Fatigue as a secondary failure mode.** Six consecutive flee actions drove fatigue to near-threshold. After the fire left, the agent collapsed into an extended rest period (ticks 33–53) before hunger built back up enough to act again.

**Unresolvable pain.** After the conflict period, discomfort remained above 0.70 through the end of the experiment (tick 60) with no available action to address it. The agent could detect the problem but not fix it — there was no hazard to avoid and no treatment mechanic. This is an honest limitation of the current model: the agent can't self-treat injury.

---

## Running it

```bash
python main.py hunger           # basic hunger → satiation loop
python main.py fear             # fear spike → flee → pain → recovery
python main.py conflict         # hunger + fire simultaneously, all drives active

python main.py hunger --ticks 120   # override tick count
python experiments/fear_response.py # run experiment directly
```

Python 3.11+, no dependencies.

---

## What this is not

- This is not a language model or anything related to one.
- This is not a claim about how the brain actually works — it's a simplified model for learning purposes.
- The agent has no representation of the world, no planning, no self-concept. It has drives and it acts to reduce them. That's it.
- Predators are deliberately excluded. Modeling a predator with realistic behavior would require giving it the same architecture, which is a separate problem.
