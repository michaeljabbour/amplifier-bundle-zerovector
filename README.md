# Zero-Vector Design Bundle

An Amplifier bundle that eliminates the translation chain between vision and product. State your intent once — receive a tested artifact.

```
OLD: Intent → Sketch → Wireframe → Mockup → Handoff → Dev Interpretation → Build → Review → Ship
NEW: Intent → Crew → Artifact
```

Built on [Zero-Vector Design](https://zerovector.design/) by Erika Flowers. Implemented as a thin Amplifier bundle: five specialized agents, six crew modes, one staged recipe.

## Quick Start

### Interactive (crew modes)

Activate a crew with a slash command. The orchestrator routes your intent through the full 5-agent pipeline.

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

The orchestrator will run: intent-analyst → architect → builder → critic → shipper, presenting results at each stage.

### Automated (recipe execution)

Run the full pipeline as a staged recipe with approval gates:

```
recipes(operation="execute",
  recipe_path="zerovector:recipes/intent-to-artifact.yaml",
  context={"intent": "Build a CLI tool that validates bundle.md frontmatter", "domain": "build"})
```

The recipe pauses at two gates:
1. **After spec** — review the specification before building starts
2. **After validation** — approve to ship or deny to stop

Valid `domain` values: `build`, `product`, `platform`, `research`, `content`, `general` (default).

## Crew Selection Matrix

| Command | Domain | Best For | Agent Tuning |
|---------|--------|----------|--------------|
| `/crew` | General | Any intent; auto-adapts | Default pipeline |
| `/crew-build` | Code | Features, apps, tools, scripts, modules | TDD tasks, test-first build, spec compliance |
| `/crew-product` | Product | UX flows, specs, strategy, validation | Jobs-to-be-done, user-centricity, decision points |
| `/crew-platform` | Infrastructure | Modules, APIs, architecture, config | Contracts, migration paths, breaking change analysis |
| `/crew-research` | Research | Investigation, analysis, synthesis, papers | Evidence standards, source strategy, actionability |
| `/crew-content` | Content | Documentation, writing, curriculum, posts | Audience-fit, narrative arc, clarity |

**When in doubt, use `/crew`** — the Intent Analyst will surface the correct domain from your intent.

## The Five Agents

Each agent is a pipeline stage with a precise role and quality bar:

| # | Role | Agent | Produces | Quality Bar |
|---|------|-------|----------|-------------|
| 1 | Intent Analyst | `zerovector:intent-analyst` | Intent Document (job, outcome, scope, constraints, anti-goals) | Could the Architect spec from this without questions? |
| 2 | Architect | `zerovector:architect` | Specification (structure, interfaces, ordered tasks + acceptance criteria) | Could the Builder start immediately from this? |
| 3 | Builder | `zerovector:builder` | Built artifact + self-verification report | Every task's acceptance criteria met |
| 4 | Critic | `zerovector:critic` | Validation Report (PASS / CONDITIONAL PASS / FAIL) | Every claim backed by specific evidence |
| 5 | Shipper | `zerovector:shipper` | Delivered artifact + Delivery Report | Artifact is immediately usable |

**Failure handling:**
- **FAIL** → Builder receives Critic's exact findings, fixes, then Critic re-validates
- **CONDITIONAL PASS** → Builder addresses specific issues, Critic re-checks only those
- **PASS** → Proceeds to Shipper

## Bundle Structure

```
amplifier-bundle-zerovector/
├── bundle.md                                  # Thin entry point (includes foundation)
├── behaviors/
│   └── zerovector-methodology.yaml            # Wires agents, modes, hooks, context
├── agents/
│   ├── intent-analyst.md                      # Stage 1: decode intent
│   ├── architect.md                           # Stage 2: produce specification
│   ├── builder.md                             # Stage 3: build artifact
│   ├── critic.md                              # Stage 4: validate fidelity
│   └── shipper.md                             # Stage 5: deliver
├── modes/
│   ├── crew.md                                # /crew — general
│   ├── crew-build.md                          # /crew-build — code
│   ├── crew-product.md                        # /crew-product — UX/product
│   ├── crew-platform.md                       # /crew-platform — infra
│   ├── crew-research.md                       # /crew-research — analysis
│   └── crew-content.md                        # /crew-content — writing
├── recipes/
│   └── intent-to-artifact.yaml               # Staged pipeline (3 stages, 2 gates)
└── context/
    ├── zerovector-principles.md               # 7 ZVD principles + philosophy
    └── crew-instructions.md                   # Orchestration rules + delegation contract
```

## Smoke Tests

Verify the bundle is correctly assembled.

### 1. File tree check

Confirm all 16 content files are present (5 agents + 6 modes + 1 behavior + 1 recipe + 2 context + 1 bundle.md):

```bash
find ~/dev/amplifier-bundle-zerovector -type f ! -name '.gitignore' ! -name 'README.md' ! -path '*/.git/*' | wc -l
# Expected: 16
```

### 2. Mode shortcuts

Verify all six crew commands are registered:

```bash
grep -r 'shortcut:' ~/dev/amplifier-bundle-zerovector/modes/
# Expected output (6 lines):
#   crew.md:  shortcut: crew
#   crew-build.md:  shortcut: crew-build
#   crew-content.md:  shortcut: crew-content
#   crew-platform.md:  shortcut: crew-platform
#   crew-product.md:  shortcut: crew-product
#   crew-research.md:  shortcut: crew-research
```

### 3. Agent wiring

Confirm all five agents are referenced in the behavior:

```bash
grep 'zerovector:' ~/dev/amplifier-bundle-zerovector/behaviors/zerovector-methodology.yaml
# Expected: intent-analyst, architect, builder, critic, shipper
```

### 4. Recipe validation

Validate the recipe schema:

```
recipes(operation="validate", recipe_path="zerovector:recipes/intent-to-artifact.yaml")
# Expected: valid, 0 warnings
```

### 5. Bundle entry point

Confirm bundle.md declares the correct name and includes foundation:

```bash
head -10 ~/dev/amplifier-bundle-zerovector/bundle.md
# Expected: name: zerovector, includes amplifier-foundation
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Invocation | Mode shortcuts (`/crew-*`) | Matches Superpowers UX; uses existing mode system; no kernel changes |
| Pipeline | Staged recipe with approval gates | Composable, resumable, human-in-the-loop |
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

`0.1.0` — Initial release with 5 agents, 6 crews, 1 recipe.
