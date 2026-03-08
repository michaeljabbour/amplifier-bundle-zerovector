# ZeroVector v0.3 Design: Fidelity-First Convergence

**Date:** 2026-03-08
**Status:** Approved via brainstorm session
**Branch:** main (v0.2 validated at commits b7f0da5, 54b4979)

---

## 1. Vision

ZeroVector v0.3 replaces the linear pipeline model (discover -> specify -> build -> review -> ship) with a **fidelity convergence engine** that measures and reduces translation loss between intent and artifact.

The core question shifts from *"which phase are you in?"* to **"how much translation loss exists between your intent and your current artifact, and which lens would reduce it most?"**

This is a fundamental reframe driven by three findings:

1. **ZVD philosophy demands it.** A 5-phase linear model contradicts "Boundaryless by Nature" (re-erects disciplinary walls), "Work in the Medium" (prevents build-to-think), and "The Zero Vector" itself (adds translation-loss arrows). The source material uses the word "continuous" at nearly every pipeline stage — these are concurrent streams, not sequential gates.

2. **The ecosystem already owns linear workflows.** Superpowers (brainstorm -> write-plan -> execute-plan -> verify -> finish) and IDD (decompose -> ground -> execute -> verify) already provide sequenced methodology. Rebuilding this under ZVD labels would be "old wine in new bottle."

3. **ZeroVector's genuine differentiation is fidelity.** No existing Amplifier bundle measures translation loss, detects artifact state, or applies domain-specific semantic readiness criteria. This is unclaimed territory.

---

## 2. Conceptual Model: Concurrent Fidelity Lenses

Five **lenses** replace five phases. All lenses are always active — the system assesses all simultaneously, then acts on the weakest one. Over iterations, all dimensions converge toward the target fidelity.

```
         ┌─────────────────────────────────────────┐
         │           FIDELITY STATE                 │
         │                                          │
         │   Intent Clarity ████████░░  0.82        │
         │   Specification  ██████░░░░  0.61        │
         │   Implementation ████░░░░░░  0.40  ← gap│
         │   Quality        ██████░░░░  0.58        │
         │   Ship-Readiness ██░░░░░░░░  0.23        │
         │                                          │
         │   Overall Fidelity: 0.53                 │
         │   Target: 0.85 (domain: build)           │
         └──────────────────┬──────────────────────┘
                            │
                    critic assesses all lenses
                    routes to weakest
                            │
              ┌─────────┬───┴───┬─────────┬──────────┐
              ▼         ▼       ▼         ▼          ▼
          intent-   architect  builder   critic    shipper
          analyst                      (quality)
```

### The Five Lenses

| Lens | Assesses | Served By | Translation Loss Detected When |
|------|----------|-----------|-------------------------------|
| **Intent Clarity** | Is the goal unambiguous and complete? | intent-analyst | Ambiguity, missing scope, unspoken assumptions |
| **Specification** | Is there a concrete, actionable plan? | architect | Spec gaps, undefined interfaces, missing acceptance criteria |
| **Implementation** | Does the artifact match what was specified? | builder | Drift from spec, missing features, unfinished work |
| **Quality** | Does the artifact meet domain standards? | critic | Test failures, lint issues, unclear prose, weak evidence |
| **Ship-Readiness** | Is the artifact deliverable? | shipper | Missing docs, broken CI, no delivery path |

### How This Differs From Everything Else

| System | Core Question | Model |
|--------|---------------|-------|
| **IDD** | "What is this task?" | Task grammar — 5 orthogonal primitives |
| **Superpowers** | "What discipline do you need?" | Methodology enforcement — TDD/review/evidence |
| **ZeroVector v0.3** | "How faithful is artifact to intent?" | Fidelity convergence — reduce translation loss |

IDD decomposes the *task*. Superpowers enforces *discipline*. ZeroVector measures and closes the *gap between what you meant and what exists*.

---

## 3. Architecture: No Custom Orchestrator

### Key Lesson from IDD

IDD v0.1-0.2 built a custom orchestrator module. It was fragile and fought the kernel. IDD v0.3 deleted it entirely and achieved the same power through context + tools + hooks on the standard `loop-streaming` orchestrator. This is the "power through content, not machinery" principle.

**ZeroVector v0.3 uses no custom orchestrator.** Standard `loop-streaming` runs the session.

### Two Execution Paths

**Interactive mode (crew modes):**
The orchestrator IS the loop. On each turn:
1. Crew mode instructions tell the LLM to assess fidelity state
2. Route to the agent that serves the weakest lens
3. After the agent acts, re-assess on the next turn
4. The human can redirect at any point

No machinery. The LLM reads context, delegates to agents, and converges.

**Automated mode (recipes):**
A recipe YAML uses `while_condition` + `break_when` + `update_context`:

```yaml
- id: "converge"
  while_condition: "{{fidelity_score}} < {{target_fidelity}}"
  max_while_iterations: 8
  break_when: "{{fidelity_score}} >= {{target_fidelity}}"
  while_steps:
    - id: "assess"          # critic scores all 5 lenses
    - id: "route-intent"    # condition: priority_gap == 'intent'
    - id: "route-spec"      # condition: priority_gap == 'specification'
    - id: "route-build"     # condition: priority_gap == 'implementation'
    - id: "route-quality"   # condition: priority_gap == 'quality'
    - id: "route-ship"      # condition: priority_gap == 'ship_readiness'
  update_context:
    fidelity_score: "{{assessment.overall}}"
```

This promotes the existing v0.2 `while_condition` convergence loop (used for builder<->critic refinement) from a sub-pattern to THE core pattern.

---

## 4. Universal Fidelity Diagnostic Capability

### The Correction: Fidelity Is Universal, Not ZVD-Specific

The fidelity diagnostic modules (live dashboard + state management) are a **universal Amplifier capability**. They work on ANY Amplifier session when installed — with Superpowers, IDD, dev-machine, a plain session, or ZeroVector.

Any bundle benefits from knowing how much translation loss exists. The diagnostic layer doesn't require ZVD's crew, modes, or philosophy. It's infrastructure.

### Two Python Modules (~250 lines total)

| Module | Purpose | Universal? |
|--------|---------|-----------|
| `modules/hooks-fidelity-reporter/` | Reads fidelity state, renders live dashboard to user (`user_message`), injects ephemeral fidelity context to agent (`context_injection` with `ephemeral=True`) | Yes — works on any Amplifier session |
| `modules/tool-fidelity-state/` | Registers `zerovector.fidelity_state` capability on coordinator. Provides `update_fidelity` callable. Stores per-lens scores + overall + priority gap. | Yes — generic state store |

### The Live Dashboard

Follows the `hooks-todo-display` pattern — writes ANSI-formatted output to `sys.stdout`:

```
┌─ Fidelity ─────────────────────────────────────────────────┐
│                                                            │
│ Intent Clarity █████████░  0.87                            │
│ Specification  ██████░░░░  0.61                            │
│ Implementation ████░░░░░░  0.40  ← priority gap           │
│ Quality        ██████░░░░  0.58                            │
│ Ship-Readiness ██░░░░░░░░  0.23                            │
│                                                            │
│ ████████████░░░░░░░░░░░░ 0.53 / 0.85 target (build)      │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Two simultaneous channels:**
- `user_message` — human sees the dashboard
- `context_injection` (ephemeral) — agent gets "Fidelity 0.53. Implementation gap. Route to builder."

### Hook Events

| Event | Trigger | Reporter Action |
|-------|---------|----------------|
| `tool:post` | After agent writes/edits/runs | Refresh dashboard if fidelity state changed |
| `prompt:complete` | After agent finishes a turn | Display summary dashboard |
| `execution:end` | Session ends | Final fidelity report |

---

## 5. Composable Behavior Architecture

### Two Behaviors (Extractable + Full Crew)

```
amplifier-bundle-zerovector/
├── behaviors/
│   ├── fidelity.yaml               ← UNIVERSAL: works on any Amplifier session
│   └── zerovector-crew.yaml        ← ZVD-SPECIFIC: includes fidelity + crew
├── modules/
│   ├── hooks-fidelity-reporter/    ← Universal diagnostic
│   └── tool-fidelity-state/        ← Universal state management
├── agents/
│   ├── critic.md                   ← Shared: fidelity assessor
│   ├── intent-analyst.md           ← Crew-only
│   ├── architect.md                ← Crew-only
│   ├── builder.md                  ← Crew-only
│   └── shipper.md                  ← Crew-only
├── context/
│   ├── fidelity-framework.md       ← Universal: generic lens model + scoring
│   ├── crew-instructions.md        ← Crew-only: orchestration
│   └── domain-tuning.md            ← Crew-only: per-domain criteria
├── modes/                          ← Crew-only: 6 crew modes
└── recipes/                        ← Crew-only: convergence recipes
```

**`behaviors/fidelity.yaml`** — the universal capability:

```yaml
bundle:
  name: fidelity-behavior
  version: 0.3.0
  description: >
    Universal fidelity diagnostic for Amplifier. Measures translation
    loss between intent and artifact across five lenses. Live dashboard
    and ephemeral agent guidance. Works on any session.

hooks:
  - module: hooks-fidelity-reporter
    source: "zerovector:modules/hooks-fidelity-reporter"

tools:
  - module: tool-fidelity-state
    source: "zerovector:modules/tool-fidelity-state"

agents:
  include:
    - zerovector:critic

context:
  include:
    - zerovector:context/fidelity-framework.md
```

**`behaviors/zerovector-crew.yaml`** — full ZVD crew (includes fidelity):

```yaml
bundle:
  name: zerovector-crew
  version: 0.3.0
  description: >
    Full Zero-Vector Design crew: 5 agents, 6 domain-tuned modes,
    fidelity convergence recipes, and the universal fidelity layer.

includes:
  - bundle: zerovector:behaviors/fidelity

hooks:
  - module: hooks-mode
    source: "modes:modules/hooks-mode"
    config:
      search_paths: ["@zerovector:modes"]

tools:
  - module: tool-mode
    source: "modes:modules/tool-mode"
    config:
      gate_policy: "warn"

agents:
  include:
    - zerovector:intent-analyst
    - zerovector:architect
    - zerovector:builder
    - zerovector:shipper

context:
  include:
    - zerovector:context/crew-instructions.md
    - zerovector:context/domain-tuning.md
    - modes:context/modes-instructions.md
```

### Three Granularity Levels

| Consumer Wants | Includes | Gets |
|----------------|----------|------|
| Universal fidelity diagnostics | `zerovector:behaviors/fidelity` | Critic + framework + dashboard hook + state tool |
| Full ZVD crew | `zerovector:behaviors/zerovector-crew` | All 5 agents + 6 modes + recipes + fidelity |
| Everything + foundation | `zerovector` (root bundle) | Full bundle with Amplifier Foundation base |

### Ecosystem Composition Examples

**dev-machine** — adds semantic fidelity to structural quality:
```yaml
includes:
  - bundle: zerovector:behaviors/fidelity
```
Gets: fidelity scoring on working sessions (does implementation satisfy spec's intent, not just pass tests?)

**Superpowers** — adds translation-loss measurement to TDD discipline:
```yaml
includes:
  - bundle: zerovector:behaviors/fidelity
```
Gets: fidelity assessment during execute-plan (is the code faithful to the design?)

**IDD** — adds artifact-state awareness to task decomposition:
```yaml
includes:
  - bundle: zerovector:behaviors/fidelity
```
Gets: fidelity-informed grounding (what state are existing artifacts in before planning?)

**Any custom bundle** — adds fidelity diagnostics to any workflow.

---

## 6. Dependencies

ZeroVector v0.3 depends on exactly two external bundles:
- `amplifier-foundation` (base Amplifier infrastructure)
- `amplifier-bundle-modes` (mode/hook infrastructure for slash commands)

No dependency on IDD, Superpowers, or dev-machine. Composes with all of them as peers.

---

## 7. What Changes From v0.2

### New Files

| File | Type | Purpose |
|------|------|---------|
| `context/fidelity-framework.md` | Context | The lens model, scoring rubric, domain-specific fidelity criteria |
| `behaviors/fidelity.yaml` | Behavior | Universal extractable fidelity capability |
| `behaviors/zerovector-crew.yaml` | Behavior | Full crew (replaces `zerovector-methodology.yaml`) |
| `recipes/fidelity-convergence.yaml` | Recipe | Core convergence loop: assess -> route -> act -> re-assess |
| `modules/hooks-fidelity-reporter/` | Python module | Live dashboard + ephemeral agent injection (~150 lines) |
| `modules/tool-fidelity-state/` | Python module | Fidelity state capability registration (~100 lines) |

### Modified Files

| File | What Changes |
|------|-------------|
| `context/crew-instructions.md` | Rewrite from "pipeline stages with gates" to "fidelity convergence with lens routing" |
| `context/domain-tuning.md` | Restructured as domain-specific fidelity criteria per lens |
| `agents/critic.md` | Major: enhanced with multi-lens fidelity assessment protocol, structured JSON output |
| `agents/intent-analyst.md` | Minor: awareness of fidelity framework, optional IDD input consumption |
| `agents/architect.md` | Minor: awareness that spec is a lens, not a gate |
| `agents/builder.md` | Minor: can start with partial spec if fidelity routing says so |
| `agents/shipper.md` | Minor: ship-readiness as a lens, can be invoked early |
| `modes/*.md` (all 6) | Orchestration shifts from pipeline to fidelity convergence |
| `recipes/intent-to-artifact.yaml` | Rewrite as convenience wrapper around fidelity-convergence |
| `bundle.md` | Version bump to 0.3.0, updated architecture description |

### Preserved (Unchanged)

| What | Why |
|------|-----|
| 5 agent roles (names and identities) | Same roles map to 5 lenses |
| 6 crew modes (names and domains) | Same domains, different orchestration logic |
| Composable sub-recipes | decode-intent, build-and-review, verify-artifact, finish-artifact |
| Anti-rationalization pattern | Updated content, preserved mechanism |
| Critic verdict protocol (VERDICT line) | Enhanced with fidelity scores alongside |
| Research docs | Untouched design heritage |

### Removed

| What | Replaced By |
|------|-------------|
| `behaviors/zerovector-methodology.yaml` | `behaviors/fidelity.yaml` + `behaviors/zerovector-crew.yaml` |

---

## 8. Confirmed Decisions (Updated)

Decisions 1-9 from the v0.2 milestone handoff, with corrections applied:

| # | Decision | Status |
|---|----------|--------|
| 1 | Primary v0.3 objective: fidelity convergence, not phase progression | **REVISED** — originally "balanced flow across phases" |
| 2 | Core behavior: measure translation loss and route to weakest lens | **REVISED** — originally "detect phase and move to next" |
| 3 | Readiness model: domain-specific fidelity criteria per lens | Confirmed |
| 4 | Assessment model: concurrent lens sweep (not phase detection) | **REVISED** — originally "hybrid infer + confirm" |
| 5 | Architecture: standard orchestrator + content + two small modules | **REVISED** — originally "shared core + recipe-first" (recipe-first preserved, custom core dropped) |
| 6 | Transition policy: fidelity-driven routing (weakest lens gets attention) | **REVISED** — originally "policy-based hybrid" |
| 7 | Fidelity diagnostic: universal Amplifier capability, not ZVD-specific | **REVISED** — originally "single shared policy artifact" |
| 8 | Compatibility stance: clean break acceptable if architecture quality improves | Confirmed |
| 9 | Launch domains: build, product, research, content, platform infra | Confirmed |

---

## 9. Minimum Viable v0.3 Slice

The smallest implementation that proves value across all domains:

1. **Universal fidelity layer** — `tool-fidelity-state` + `hooks-fidelity-reporter` + `fidelity-framework.md` + enhanced `critic.md`
2. **One convergence recipe** — `fidelity-convergence.yaml` with while-loop routing
3. **One updated crew mode** — `/crew` (general) with fidelity-driven orchestration instructions
4. **Two behaviors** — `fidelity.yaml` (extractable) + `zerovector-crew.yaml` (full)

This proves: fidelity assessment works, the dashboard displays, the convergence loop routes correctly, and the fidelity behavior is extractable by other bundles.

Remaining crew modes (crew-build, crew-product, crew-platform, crew-research, crew-content) and remaining recipes are iteration 2 of v0.3.

---

## 10. What ZeroVector Does NOT Rebuild

Learned from ecosystem research:

| Capability | Owned By | ZeroVector's Relationship |
|-----------|----------|--------------------------|
| Task decomposition | IDD | Consumes IDD output as optional intent input |
| TDD methodology | Superpowers | Builder agent can follow TDD when domain is code |
| Code quality review | Superpowers | Critic's quality lens covers this for code domain |
| Git workflow | Superpowers / git-ops | Shipper delegates to git-ops for finish actions |
| Machine manufacturing | dev-machine | dev-machine includes fidelity behavior for semantic quality |

ZeroVector uniquely provides:
- **Fidelity measurement** — the translation-loss metric (universal)
- **Multi-lens convergence** — route to weakest dimension, not next phase
- **Domain-tuned crews** — build/product/platform/research/content
- **Cross-domain artifact lifecycle** — not just code

---

## 11. Patterns Adopted From Ecosystem

| Pattern | Source | How ZeroVector Uses It |
|---------|--------|----------------------|
| Grammar State (shared mutable capability) | IDD | `zerovector.fidelity_state` capability on coordinator |
| Reporter hook (user-visible progress) | IDD | `hooks-fidelity-reporter` with `user_message` |
| Power through content, not machinery | IDD v0.3 lesson | No custom orchestrator. Standard `loop-streaming` |
| Anti-rationalization tables | Superpowers / ZV v0.2 | Preserved and updated for fidelity model |
| Evidence-before-claims gate function | Superpowers | Critic's fidelity assessment requires evidence |
| Methodology calibration | Superpowers | Match crew intensity to task complexity |
| Two-stage review (spec + quality) | Superpowers | Critic's two-pass protocol (intent fidelity + domain quality) |
| Convergence loop (while_condition) | Amplifier recipes / ZV v0.2 | Promoted from sub-pattern to core pattern |
| Extractable behavior | Amplifier Foundation | `behaviors/fidelity.yaml` for cross-bundle composition |
| Ephemeral context injection | Amplifier hooks | Live fidelity state that doesn't pollute history |