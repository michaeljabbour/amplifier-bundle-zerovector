---
bundle:
  name: zerovector
  version: 0.1.0
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

## Available Recipe

| Recipe | Purpose |
|--------|---------|
| `zerovector:recipes/intent-to-artifact.yaml` | Full pipeline: intent → spec → build → validate → ship |

---

@foundation:context/shared/common-system-base.md
