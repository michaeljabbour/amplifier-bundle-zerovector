# Zero-Vector Design — Core Principles

Zero-Vector Design is a philosophy founded by Erika Flowers that eliminates the translation
chain between vision and product. The person with the vision directs a crew of AI agents
and moves directly from intent to working artifact.

---

## The Translation Problem

Traditional product creation is a chain of lossy compressions:

```
Intent → Sketch → Wireframe → Mockup → Handoff → Dev Interpretation → Build → Review → Ship
```

Every handoff loses information. The final artifact is a degraded version of the original intent.

Zero-Vector eliminates the chain:

```
Intent → Crew → Artifact
```

The artifact is not a picture of the thing. It is the thing.

---

## The Seven Principles

### 1. Work in the Medium
Build real artifacts, not representations of artifacts. A working module, not a mockup of one.
A deployed configuration, not a diagram of one. The medium is the message.

### 2. Boundaryless by Nature
Disciplinary walls (design / engineering / research / content) are constraints of the old model.
The person with the vision can operate across all of them. Crew members don't have job titles.

### 3. The Medium Shapes Thought
The tool you use changes how you think. Working directly in the real artifact changes what you
see, what you ask, and what you build. Representations lie. Working code tells the truth.

### 4. Intentional Impermanence
Artifacts are regeneratable from specification. Don't patch — regenerate. The spec is the truth;
the artifact is an instance of it. This frees you to iterate without fear.

### 5. POSIWID (The Purpose of a System Is What It Does)
Judge systems by their outputs, not their intentions. If the process produces translation loss,
it doesn't matter how well-intentioned the handoff was. Change the system, not the intention.

### 6. Compound Your Leverage
Each pipeline stage amplifies the last. A precise intent produces a sharper spec. A sharp spec
produces a more faithful build. Invest in early precision; it compounds downstream.

### 7. Venture Beyond "Possible"
The old ceiling was set by the translation chain. When translation is eliminated, the ceiling
rises. Work that was previously impractical for one person is now tractable.

---

## What This Is / Is Not

| This IS | This IS NOT |
|---------|-------------|
| Rigorous, intentional work | Vibe coding (no intent → no crew → no quality) |
| High-fidelity artifact production | Anti-craft (the crew has craft; you direct it) |
| Systems thinking about your workflow | Anti-process (the pipeline IS the process) |
| Amplified individual leverage | AI replacing designers/engineers |
| Direct intent-to-medium work | Skipping design thinking |

---

## The Crew Model

In Zero-Vector, agents are **crew members**, not assistants.

An assistant waits for instructions and executes them literally.
A crew member has a role, a standard, and a contract — and executes with judgment.

| Crew Role | Responsibility | Failure Mode |
|-----------|----------------|--------------|
| Intent Analyst | Surface the real intent | Under-specified → builds wrong thing |
| Architect | Translate intent into structure | Over-specified → builds too much |
| Builder | Implement the artifact | Scope creep → loses fidelity |
| Critic | Validate against original intent | Too lenient → ships translation loss |
| Shipper | Deliver cleanly | Messy delivery → artifact is unusable |

Each role is a quality gate for the next. Together they eliminate translation loss at every stage.

---

## Integration with Amplifier

The Zero-Vector pipeline maps cleanly onto Amplifier's primitives:

| ZVD Concept | Amplifier Mechanism |
|-------------|---------------------|
| Intent capture | Intent Analyst agent |
| Crew orchestration | Mode + delegate pattern |
| Pipeline with gates | Staged recipe with approvals |
| Regeneratable artifacts | Bricks & Studs module philosophy |
| Compound leverage | Bundle composition |

The bundle's five agents, six modes, and one master recipe implement the full Zero-Vector pipeline
in Amplifier's native patterns.
