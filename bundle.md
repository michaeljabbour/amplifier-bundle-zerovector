---
bundle:
  name: zerovector
  version: 0.3.0
  description: Zero-Vector Design — fidelity convergence architecture eliminating translation loss between vision and product

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: zerovector:behaviors/zerovector-crew
---

# Zero-Vector Design

You have access to the Zero-Vector methodology — a philosophy and pipeline for moving directly
from intent to working artifact, using AI agents as a directed crew rather than assistants.

@zerovector:context/zerovector-principles.md
@zerovector:context/crew-instructions.md
@zerovector:context/domain-tuning.md

---

## Core Philosophy

Zero-Vector eliminates the translation chain between vision and product:

```
OLD: Intent → Sketch → Wireframe → Mockup → Handoff → Dev Interpretation → Build → Review → Ship
NEW: Intent → Crew → Artifact
```

The person with the vision directs a specialized crew. Each crew member has a precise role.
No information is lost in translation. The output is the thing, not a picture of the thing.

## Crews

Invoke any crew with a slash command. Each crew is tuned for a specific work domain.

| Command | Crew | Best For |
|---------|------|----------|
| `/crew` | General | Any intent-to-artifact work |
| `/crew-build` | Build | New features, apps, tools, scripts |
| `/crew-product` | Product | UX, flows, specs, validation, strategy |
| `/crew-platform` | Platform | Infrastructure, modules, APIs, architecture |
| `/crew-research` | Research | Papers, analysis, investigation, synthesis |
| `/crew-content` | Content | Writing, documentation, curriculum, posts |

## The Five Crew Roles

| Role | Agent | Responsibility |
|------|-------|----------------|
| Intent Analyst | `zerovector:intent-analyst` | Decode intent, surface constraints, define success |
| Architect | `zerovector:architect` | Translate intent into structure and spec |
| Builder | `zerovector:builder` | Implement the artifact from spec |
| Critic | `zerovector:critic` | Validate artifact against original intent |
| Shipper | `zerovector:shipper` | Package, commit, document, deliver |

## v0.3 Fidelity Convergence Architecture

Instead of a linear pipeline of sequential stages, ZeroVector v0.3 uses a **fidelity convergence
model**: five concurrent lenses are assessed simultaneously, and the crew routes to whichever lens
is weakest until the overall fidelity score reaches the target threshold.

### The Five Fidelity Lenses

| Lens | What It Measures |
|------|-----------------|
| **Intent Clarity** | Is the original intent fully understood and unambiguous? |
| **Specification** | Does the spec completely and correctly capture the intent? |
| **Implementation** | Does the artifact faithfully implement the spec? |
| **Quality** | Does the artifact meet quality standards (tests, style, correctness)? |
| **Ship-Readiness** | Is the artifact packaged and deliverable? |

### The Convergence Loop

```
DECODE-INTENT → (GATE 1: approve spec)
  → ASSESS all five lenses simultaneously (fidelity score 0.0–1.0)
  → while fidelity_score < target_fidelity (default 0.85):
      route to weakest lens → act → re-assess
  → (GATE 2: approve converged artifact)
  → FINISH (merge / pr / keep / discard)
```

Each assessment produces a machine-readable fidelity score. The loop terminates when the score
meets the target or after a maximum of 8 iterations.

### Universal Fidelity Diagnostic Layer

The fidelity behavior (`zerovector:behaviors/fidelity`) is an **extractable, standalone layer**
that can be included by any Amplifier bundle — not just ZeroVector. It wires the
`zerovector:critic` agent, the `tool-fidelity-state` tool, and the `hooks-fidelity-reporter`
hook into any session that needs structured fidelity scoring.

## Available Recipes

| Recipe | Purpose | Gates |
|--------|---------|-------|
| `zerovector:recipes/intent-to-artifact.yaml` | **Master orchestrator** — fidelity convergence pipeline | 2 |
| `zerovector:recipes/fidelity-convergence.yaml` | **Core convergence engine** — assess → route → act loop | 0 |
| `zerovector:recipes/decode-intent.yaml` | Intent capture + spec only | 1 |
| `zerovector:recipes/finish-artifact.yaml` | Finish action: merge / pr / keep / discard | 1 |

---

@foundation:context/shared/common-system-base.md
