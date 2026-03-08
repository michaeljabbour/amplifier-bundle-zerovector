---
bundle:
  name: zerovector
  version: 0.2.0
  description: Zero-Vector Design — intent-to-artifact pipeline eliminating translation loss between vision and product

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: zerovector:behaviors/zerovector-methodology
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

## v0.2 Handoff Architecture

```
DECODE → (GATE 1: approve spec) → BUILD+REVIEW → convergence loop (max 3)
       → (GATE 2: approve artifact) → VERIFY → (GATE 3: choose finish action)
       → FINISH (merge / pr / keep / discard)
```

The critic runs two passes on every review (spec compliance + quality) and emits a
machine-readable `VERDICT: PASS|CONDITIONAL_PASS|FAIL` for recipe loop integration.
The convergence loop retries builder↔critic up to 3 rounds before surfacing unresolved issues.

## Available Recipes

Run the full pipeline or any sub-recipe independently:

| Recipe | Purpose | Gates |
|--------|---------|-------|
| `zerovector:recipes/intent-to-artifact.yaml` | **Master orchestrator** — full pipeline | 3 |
| `zerovector:recipes/decode-intent.yaml` | Intent capture + spec only | 1 |
| `zerovector:recipes/build-and-review.yaml` | Spec + build + critic convergence loop | 2 |
| `zerovector:recipes/verify-artifact.yaml` | Evidence-first verification pass | 1 |
| `zerovector:recipes/finish-artifact.yaml` | Finish action: merge / pr / keep / discard | 1 |

---

@foundation:context/shared/common-system-base.md
