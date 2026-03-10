# Zero-Vector Design Bundle

An Amplifier bundle that eliminates translation loss between vision and product. State your intent once — receive a tested artifact.

```
OLD: Intent → Sketch → Wireframe → Mockup → Handoff → Dev Interpretation → Build → Review → Ship
NEW: Intent → Crew → Artifact
```

Built on [Zero-Vector Design](https://zerovector.design/) by Erika Flowers. Implemented as a thin Amplifier bundle: five specialized agents, six crew modes, six recipes, and a fidelity convergence engine. **v0.3.0**

## Installation

Add zerovector as an app bundle so it's automatically composed into every session:

```bash
amplifier bundle add git+https://github.com/michaeljabbour/amplifier-bundle-zerovector@main --app
```

Or to use a local development copy:

```bash
amplifier bundle add /path/to/amplifier-bundle-zerovector --app
```

## Quick Start

### Interactive (crew modes)

Activate a crew with a slash command. The crew assesses all fidelity lenses and converges to a high-quality artifact.

```
/crew              # General — any domain
/crew-build        # Code — features, apps, tools, scripts
/crew-product      # UX — flows, specs, validation, strategy
/crew-platform     # Infra — modules, APIs, architecture
/crew-research     # Analysis — investigation, synthesis, papers
/crew-content      # Writing — docs, curriculum, posts
```

Then state your intent:

```
/crew-build
> Build a CLI tool that validates bundle.md frontmatter against the bundle schema
```

The crew will: decode intent → spec → assess fidelity lenses → route to weakest → converge → deliver.

### Automated (recipe execution)

Run the full fidelity convergence pipeline as a staged recipe with approval gates:

```
recipes(operation="execute",
  recipe_path="zerovector:recipes/intent-to-artifact.yaml",
  context={"intent": "Build a CLI tool that validates bundle.md frontmatter", "domain": "build"})
```

The recipe pauses at two gates:
1. **After spec** — review the specification before convergence starts
2. **After convergence** — approve to finish or deny to stop

Valid `domain` values: `build`, `product`, `platform`, `research`, `content`, `general` (default).

## Crew Selection Matrix

| Command | Domain | Best For | Agent Tuning |
|---------|--------|----------|--------------|
| `/crew` | General | Any intent; auto-adapts | Default convergence pipeline |
| `/crew-build` | Code | Features, apps, tools, scripts, modules | TDD tasks, test-first build, spec compliance |
| `/crew-product` | Product | UX flows, specs, strategy, validation | Jobs-to-be-done, user-centricity, decision points |
| `/crew-platform` | Infrastructure | Modules, APIs, architecture, config | Contracts, migration paths, breaking change analysis |
| `/crew-research` | Research | Investigation, analysis, synthesis, papers | Evidence standards, source strategy, actionability |
| `/crew-content` | Content | Documentation, writing, curriculum, posts | Audience-fit, narrative arc, clarity |

**When in doubt, use `/crew`** — the Intent Analyst will surface the correct domain from your intent.

## The Five Agents

Each agent is a crew specialist with a precise role and quality bar:

| # | Role | Agent | Produces | Quality Bar |
|---|------|-------|----------|-------------|
| 1 | Intent Analyst | `zerovector:intent-analyst` | Intent Document (job, outcome, scope, constraints, anti-goals) | Could the Architect spec from this without questions? |
| 2 | Architect | `zerovector:architect` | Specification (structure, interfaces, ordered tasks + acceptance criteria) | Could the Builder start immediately from this? |
| 3 | Builder | `zerovector:builder` | Built artifact + self-verification report | Every task's acceptance criteria met |
| 4 | Critic | `zerovector:critic` | Fidelity Score Report (0.0–1.0 per lens, PASS/FAIL verdict) | Every claim backed by specific evidence |
| 5 | Shipper | `zerovector:shipper` | Delivered artifact + Delivery Report | Artifact is immediately usable |

## v0.3 Fidelity Convergence Architecture

Instead of a linear pipeline, ZeroVector v0.3 uses a **fidelity convergence model**. The core question is: **"How much translation loss exists between intent and artifact?"**

Five concurrent fidelity lenses are assessed simultaneously. The crew routes to whichever lens is weakest and acts until the overall fidelity score reaches the target threshold.

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

Each assessment produces a machine-readable fidelity score. The loop terminates when the score meets the target or after a maximum of 8 iterations.

**Failure handling:**
- **Weak lens** → Crew routes to that lens, acts, re-assesses all lenses
- **Persistent failure** → Builder receives Critic's exact findings, fixes, Critic re-validates
- **Converged** → Proceeds to Shipper

## Universal Fidelity

The fidelity behavior (`zerovector:behaviors/fidelity`) is an **extractable, standalone layer** that can be included by any Amplifier bundle — not just ZeroVector. It delivers:

- **`zerovector:critic` agent** — structured fidelity scoring against the five lenses
- **`tool-fidelity-state`** — Python module for reading and writing fidelity scores
- **`hooks-fidelity-reporter`** — Python module that prints a live fidelity dashboard after each agent turn

Any bundle can add fidelity diagnostics without the full ZVD crew:

```yaml
includes:
  - bundle: zerovector:behaviors/fidelity
```

This gives you the Critic agent, the fidelity framework context (`context/fidelity-framework.md`), the live dashboard hook, and the fidelity state tool — all without the crew modes or convergence recipes.

## Alignment Monitoring (AMOS)

[AMOS](https://github.com/michaeljabbour/amplifier-bundle-amos) is a recommended companion bundle for real-time per-turn alignment monitoring. While fidelity tracks project-level translation loss across the convergence loop, AMOS measures turn-level quality on every LLM response.

AMOS fires at priority 40 (before the fidelity reporter at 50) and evaluates three dimensions:

- **Prompt-response alignment** — does the response address what was asked?
- **Context consistency** — does it stay coherent with prior conversation?
- **Goal alignment** — does it advance the stated objective?

It also tracks cognitive state signals (confusion, frustration, engagement) to detect when the conversation is going off track.

**Measurement layers:** AMOS = per-turn quality, Fidelity = per-project convergence. They complement each other. Both bundles operate independently and can be used separately or together.

To add AMOS alongside ZeroVector:

```bash
amplifier bundle add git+https://github.com/michaeljabbour/amplifier-bundle-amos@main --app
```

## Recipes

All six recipes are available under `zerovector:recipes/`:

| Recipe | Purpose | Gates |
|--------|---------|-------|
| `intent-to-artifact.yaml` | **Master orchestrator** — wraps decode-intent + fidelity-convergence + finish-artifact | 2 |
| `fidelity-convergence.yaml` | **Core convergence engine** — assess → route → act loop (up to 8 iterations) | 0 |
| `decode-intent.yaml` | Intent capture + spec only | 1 |
| `build-and-review.yaml` | Single build + critic validation pass | 0 |
| `verify-artifact.yaml` | Standalone Critic validation | 0 |
| `finish-artifact.yaml` | Finish action: merge / pr / keep / discard | 1 |

## Bundle Structure

```
amplifier-bundle-zerovector/
├── bundle.md                                  # Thin entry point (v0.3.0)
├── behaviors/
│   ├── fidelity.yaml                          # Extractable fidelity layer
│   └── zerovector-crew.yaml                   # Wires agents, modes, hooks, context
├── agents/
│   ├── intent-analyst.md                      # Stage 1: decode intent
│   ├── architect.md                           # Stage 2: produce specification
│   ├── builder.md                             # Stage 3: build artifact
│   ├── critic.md                              # Stage 4: fidelity assessment
│   └── shipper.md                             # Stage 5: deliver
├── modes/
│   ├── crew.md                                # /crew — general
│   ├── crew-build.md                          # /crew-build — code
│   ├── crew-product.md                        # /crew-product — UX/product
│   ├── crew-platform.md                       # /crew-platform — infra
│   ├── crew-research.md                       # /crew-research — analysis
│   └── crew-content.md                        # /crew-content — writing
├── recipes/
│   ├── intent-to-artifact.yaml               # Master pipeline (2 gates)
│   ├── fidelity-convergence.yaml             # Core convergence engine
│   ├── decode-intent.yaml                    # Intent + spec only
│   ├── build-and-review.yaml                 # Build + validate pass
│   ├── verify-artifact.yaml                  # Standalone validation
│   └── finish-artifact.yaml                  # Finish action
├── context/
│   ├── zerovector-principles.md               # 7 ZVD principles + philosophy
│   ├── crew-instructions.md                   # Orchestration rules + delegation contract
│   ├── domain-tuning.md                       # Per-crew domain context
│   └── fidelity-framework.md                  # Five-lens framework + scoring rubric
├── modules/
│   ├── tool-fidelity-state/                   # Python package: fidelity score I/O
│   └── hooks-fidelity-reporter/               # Python package: live dashboard hook
└── research/
    ├── 00-source-material.md                  # Original zerovector.design content extraction
    ├── 01-philosophy-deep-dive.md             # Analysis of ZVD's 7 principles + thesis
    ├── 02-amplifier-alignment.md              # ZVD ↔ Amplifier mapping + gap analysis
    ├── 03-crew-design-rationale.md            # Why 6 crews, 5 agents, ~/dev survey
    ├── 04-implementation-decisions.md         # Every structural choice with rationale
    └── 05-roadmap.md                          # Phased roadmap through v1.0.0
```

> Optional companion: [amplifier-bundle-amos](https://github.com/michaeljabbour/amplifier-bundle-amos) — per-turn alignment monitoring

## Smoke Tests

Verify the bundle is correctly assembled.

### 1. File tree check

Run from the bundle root (`cd` into the repo first):

```bash
# Runtime files only (agents, modes, behaviors, recipes, context, modules, bundle.md)
find . -type f ! -name '.gitignore' ! -name 'README.md' \
  ! -path '*/.git/*' ! -path './research/*' \
  ! -path './.pytest_cache/*' ! -path './.ruff_cache/*' \
  ! -path './__pycache__/*' ! -path '*/tests/*' \
  ! -name '*.pyc' | wc -l
# Expected: ~23  (5 agents + 6 modes + 2 behaviors + 6 recipes + 4 context + 2 Python modules (pyproject.toml + __init__.py each) + 1 bundle.md)

# Count by category:
ls agents/ | wc -l   # Expected: 5 agents
ls modes/  | wc -l   # Expected: 6 modes
ls behaviors/ | wc -l # Expected: 2 behaviors
ls recipes/ | wc -l  # Expected: 6 recipes
ls context/ | wc -l  # Expected: 4 context files
ls modules/ | wc -l  # Expected: 2 module directories (tool-fidelity-state, hooks-fidelity-reporter)
```

### 2. Mode shortcuts

Verify all six crew commands are registered:

```bash
grep -r 'shortcut:' modes/
# Expected output (6 lines):
#   crew.md:  shortcut: crew
#   crew-build.md:  shortcut: crew-build
#   crew-content.md:  shortcut: crew-content
#   crew-platform.md:  shortcut: crew-platform
#   crew-product.md:  shortcut: crew-product
#   crew-research.md:  shortcut: crew-research
```

### 3. Agent wiring

Confirm all five agents are referenced in the behaviors:

```bash
grep 'zerovector:' behaviors/zerovector-crew.yaml
# Expected: intent-analyst, architect, builder, critic, shipper
```

### 4. Recipe validation

Validate the core recipes:

```
recipes(operation="validate", recipe_path="zerovector:recipes/intent-to-artifact.yaml")
recipes(operation="validate", recipe_path="zerovector:recipes/fidelity-convergence.yaml")
# Expected: valid, 0 warnings
```

### 5. Bundle entry point

Confirm bundle.md declares the correct name, version, and includes:

```bash
head -10 bundle.md
# Expected: name: zerovector, version: 0.3.0, includes amplifier-foundation
```

### 6. Python modules

Confirm both Python packages are installed or installable:

```bash
ls modules/
# Expected: hooks-fidelity-reporter  tool-fidelity-state

cat modules/tool-fidelity-state/pyproject.toml | grep name
cat modules/hooks-fidelity-reporter/pyproject.toml | grep name
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Invocation | Mode shortcuts (`/crew-*`) | Matches Superpowers UX; uses existing mode system; no kernel changes |
| Architecture | Fidelity convergence over linear pipeline | ZVD philosophy compliance — POSIWID requires scoring outputs, not checking boxes |
| Universal fidelity | Extractable `behaviors/fidelity` layer | Ecosystem composability — any bundle gets fidelity diagnostics without the full crew |
| Orchestrator | No custom orchestrator | Power through content, not machinery — agents + recipes replace custom control logic |
| Python modules | Two modules only (hooks-fidelity-reporter + tool-fidelity-state) | Minimal surface area; one module per concern; no framework bloat |
| Agent count | 5 core agents | 1:1 with ZVD pipeline stages; no agent explosion |
| Crew differentiation | Mode context injection into shared pipeline | Same 5 agents, domain-tuned prompts per crew |
| Foundation dependency | `includes:` in bundle.md | Standard thin-bundle pattern |

## Philosophy

Zero-Vector Design rests on seven principles:

1. **Work in the medium** — build the thing, not a picture of the thing
2. **Boundaryless by nature** — disciplinary walls are optional
3. **The medium shapes thought** — working in real artifacts changes what you see
4. **Intentional impermanence** — regenerate from spec, don't patch
5. **POSIWID** — judge systems by outputs, not intentions
6. **Compound your leverage** — early precision compounds downstream
7. **Venture beyond "possible"** — the old ceiling was set by the translation chain

This is NOT vibe coding. It is rigorous, intentional, crew-directed work.

## Version

`0.3.0` — Fidelity convergence architecture: 5 agents, 6 crews, 6 recipes, 2 Python modules.
