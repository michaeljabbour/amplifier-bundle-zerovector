# 02 — Amplifier Alignment Analysis

> Mapping Zero-Vector Design principles to Amplifier's architecture, identifying deep alignments, partial overlaps, and genuine gaps

---

## 1. Summary Verdict

**Amplifier is already the closest thing the AI agent world has to a ZVD-native platform — but it doesn't know it yet.**

The philosophical alignment is striking. The last mile is unbuilt. The core tension: ZVD is a **design-led** philosophy; Amplifier is an **engineering-led** platform. The bridge between them is buildable entirely within Amplifier's existing module/bundle system — no kernel changes needed.

---

## 2. Principle-by-Principle Alignment

| ZVD Principle | Amplifier Equivalent | Alignment | Notes |
|---------------|---------------------|-----------|-------|
| Intent to Artifact directly | "Regenerate, don't patch" (Bricks & Studs) | Deep | Both treat the spec as truth and the artifact as a derived instance |
| Agents as crew, not assistants | Agent spawning + tool-task delegation | Structural | Amplifier agents have defined roles, contracts, and delegation patterns |
| Compound your leverage | Bundle composition + behaviors | Core mechanic | Behaviors compose; each layer amplifies the last |
| Boundaryless by nature | Module protocols (any type, same contract) | By design | Modules are type-agnostic; the protocol is the interface |
| Intentional impermanence | Regeneratable modules from spec | Exact match | Amplifier's "bricks" are explicitly designed to be rebuilt from spec |
| Work in the medium | *Gap: no live artifact feedback loop* | Partial | Amplifier builds real artifacts but has no built-in preview/screenshot/feedback mechanism |
| Living systems over static artifacts | Event-first observability + hooks | Partial | Mechanism exists (hooks, events), but no policy/pattern for continuous artifact lifecycle |
| The medium is the message | *Gap: no design-system-as-context* | Not addressed | No built-in way to inject design tokens, component conventions, or interaction rules as agent context |

---

## 3. Deep Alignments (Green)

### 3A. Regeneratable Artifacts = Intentional Impermanence

This is the strongest alignment. Amplifier's entire module philosophy is built on regeneratability:

| Amplifier Concept | ZVD Equivalent |
|-------------------|----------------|
| Brick = self-contained module with one responsibility | Artifact = working thing built from spec |
| Stud = public contract others connect to | Pipeline stage output = defined interface for next stage |
| README.md is the spec; implementation is an instance | Spec is truth; artifact is an instance |
| "Can be rebuilt from spec without breaking connections" | "Don't patch — regenerate" |

The language differs but the structural principle is identical. Both argue that the specification (not the running artifact) is the source of truth, and that artifacts should be cheap to regenerate.

### 3B. Agent Delegation = Crew Model

Amplifier's agent system already implements the core crew pattern:

- **Named agents** with defined roles and contracts (`.md` files with system prompts)
- **Delegation protocol** where the orchestrator routes to specialists
- **Context passing** between agents (delegation carries accumulated context)
- **Quality gates** via hooks and approval mechanisms

The mapping is direct:

| ZVD Crew Role | Amplifier Pattern |
|---------------|-------------------|
| Intent Analyst | Specialist agent with decomposition prompt |
| Architect | Specialist agent with specification-writing prompt |
| Builder | Implementation agent (like `foundation:modular-builder`) |
| Critic | Validation agent (like `recipes:result-validator`) |
| Shipper | Delivery agent (like `foundation:git-ops` + `post-task-cleanup`) |

### 3C. Bundle Composition = Compound Leverage

Amplifier's bundle system is a direct implementation of compound leverage:

- Thin bundles include foundation + add only unique capabilities
- Behaviors compose onto bundles (each behavior adds a capability layer)
- Each layer amplifies the last: foundation provides base, behavior provides methodology, agents provide specialization, recipes provide automation

---

## 4. Partial Alignments (Yellow)

### 4A. Work in the Medium — Partial

**What Amplifier has:** Tools that produce real artifacts (file creation, code generation, test execution, git operations). Agents build actual working things, not mockups.

**What's missing:** No feedback loop from artifact back to agent. The builder creates files but doesn't see the running result. No screenshot capture, no browser preview, no live validation against visual intent.

**Gap impact:** For code artifacts (CLI tools, modules, configs), this gap is small — tests provide the feedback loop. For visual artifacts (UIs, layouts, design systems), the gap is significant.

**Bridgeable?** Yes, at the edge. A `tool-artifact-preview` module could capture screenshots or render previews and inject them as context. No kernel changes needed.

### 4B. Living Systems — Partial

**What Amplifier has:** Hook system with rich lifecycle events (`tool:pre`, `tool:post`, `session:start`, etc.). Event broadcasting module. Memory system for cross-session persistence.

**What's missing:** No pattern for "continuous artifact lifecycle." Hooks fire during a session, but there's no built-in mechanism for an artifact to be monitored, re-validated, or regenerated automatically over time.

**Gap impact:** Medium. Most ZVD workflows are session-scoped (build this thing now). Continuous lifecycle is a v2+ concern.

**Bridgeable?** Yes. Recipes with scheduled triggers or external webhook integration could implement continuous monitoring. This is a pattern gap, not a mechanism gap.

---

## 5. Genuine Gaps (Red)

### 5A. Design-System-as-Context

**The problem:** ZVD's "medium shapes thought" principle implies that the agent should have the design system (tokens, component conventions, interaction patterns, brand rules) loaded as context when building artifacts. Amplifier has no built-in mechanism for this.

**Why it matters:** Without design context, agents produce technically correct but aesthetically/experientially inconsistent artifacts. The "translation loss" ZVD eliminates in the process pipeline gets reintroduced at the aesthetic layer.

**Solution path:** A context module that loads design system files (JSON tokens, component docs, brand guidelines) into agent context. This is a bundle-level concern — create a `context/design-system/` directory pattern and include it via behavior YAML.

**Complexity:** Low. The mechanism (context injection) exists. The pattern (what to inject and how to structure it) needs to be defined.

### 5B. Translation Fidelity Scoring

**The problem:** ZVD's core metric is "how much of the original intent survived into the final artifact?" Amplifier has no built-in way to measure this.

**Why it matters:** Without measurement, you can't know if your pipeline is actually eliminating translation loss or just moving it to different boundaries.

**Solution path:** A critic agent pattern that explicitly scores fidelity against the intent document. This is already partially implemented in our `zerovector:critic` agent, but it produces qualitative verdicts (PASS/FAIL), not quantitative fidelity scores.

**Complexity:** Medium. Defining a meaningful fidelity metric is a research problem, not just an engineering one.

### 5C. Intent Classification Gateway

**The problem:** Today the user manually selects which crew to invoke (`/crew-build` vs `/crew-research`). ZVD's ideal is: state your intent once, and the system routes appropriately.

**Why it matters:** Manual crew selection is a small translation step — the user has to classify their own intent before stating it.

**Solution path:** A gateway agent or recipe that classifies raw intent and routes to the appropriate crew. Could be implemented as a first step in the `/crew` (general) mode.

**Complexity:** Low-Medium. Intent classification is a well-understood NLP task. The routing mechanism (mode switching) already exists.

---

## 6. Kernel-vs-Edge Analysis

A critical architectural question: do any of these gaps require kernel changes?

| Gap | Kernel Change Needed? | Why / Why Not |
|-----|----------------------|---------------|
| Design-system-as-context | No | Context injection via behavior YAML already works |
| Translation fidelity scoring | No | Agent prompt + structured output; no new primitive needed |
| Intent classification gateway | No | Agent delegation or recipe routing; existing mechanisms |
| Live artifact feedback | No | New tool module; kernel tool protocol unchanged |
| Continuous artifact lifecycle | No | Recipe scheduling or external triggers; no kernel involvement |
| Parallel variant building | No | Recipe parallel steps or parallel agent dispatch; existing mechanism |

**Verdict: Zero kernel changes required.** Every gap is bridgeable at the bundle/module/recipe layer. This is a strong validation of Amplifier's kernel architecture — the "mechanism not policy" principle means ZVD is a policy choice, not a mechanism extension.

---

## 7. Existing Amplifier Patterns That Directly Enable ZVD

### 7A. The Superpowers Pipeline

Amplifier's existing Superpowers bundle already implements a manual version of the ZVD pipeline:

| Superpowers Mode | ZVD Pipeline Stage | Gap |
|-----------------|-------------------|-----|
| `/brainstorm` | Intent capture + refinement | Close but not structured into Intent Document format |
| `/write-plan` | Architecture + specification | Close but TDD-focused rather than intent-fidelity-focused |
| `/execute-plan` | Build | Close — subagent-driven development |
| `/verify` | Validation | Close but evidence-based completion, not intent-fidelity checking |
| `/finish` | Ship | Close — branch completion with merge/PR options |

**Key insight:** Superpowers is the manual-sequencing version of what ZVD automates. The user runs `/brainstorm` then `/write-plan` then `/execute-plan` then `/verify` then `/finish` manually. ZVD collapses this into: state intent, crew handles pipeline, approval gates.

### 7B. IDD Decomposition

Amplifier's IDD (Intent-Driven Decomposition) tool is already an intent capture mechanism:

```
idd_decompose("Build a CLI tool that validates bundle.md")
-> Agent/WHO, Context/WHAT, Behavior/HOW, Intent/WHY, Trigger/WHEN
```

This maps directly to ZVD's Intent Analyst role. The IDD primitives are a structured intent document.

### 7C. Recipes with Approval Gates

Amplifier's recipe system provides exactly the staged-pipeline-with-gates mechanism ZVD needs:

- **Stages** = pipeline phases (decode-and-spec, build-and-validate, ship)
- **Steps** = individual agent delegations within a phase
- **Approval gates** = human review points between phases
- **Context flow** = outputs from prior stages available to subsequent stages

### 7D. Memory System

Amplifier's memory module enables cross-session persistence:

- Intent documents can be stored and retrieved across sessions
- Specifications can persist beyond the session that created them
- Build history and validation reports accumulate over time

This supports ZVD's "living systems" principle — artifacts and their metadata survive beyond individual sessions.

---

## 8. What the Alignment Means Practically

### For Amplifier

The zerovector bundle proves that Amplifier's architecture can host a complete design philosophy without kernel changes. This validates:
- The bundle/behavior composition model
- The agent delegation protocol
- The recipe execution engine
- The "mechanism not policy" kernel principle

### For Zero-Vector

Amplifier provides the most natural implementation substrate for ZVD because:
- Named agents with defined contracts = crew members
- Bundle composition = compound leverage
- Regeneratable modules = intentional impermanence
- Staged recipes = pipeline with quality gates

### For Practitioners

The practical takeaway: you can practice Zero-Vector Design today using Amplifier with:
1. The `zerovector` bundle installed
2. Any of the six `/crew-*` slash commands
3. Optionally, the `intent-to-artifact` recipe for full automation

The gaps (design-system-as-context, live preview, fidelity scoring) are real but don't block the core workflow.

---

## 9. Comparison Matrix: ZVD Concepts to Amplifier Implementation

| ZVD Concept | Amplifier Mechanism | Bundle Implementation | Status |
|-------------|--------------------|-----------------------|--------|
| Intent capture | IDD decompose + agent delegation | `zerovector:intent-analyst` | Implemented |
| Intent document | Structured markdown output | Agent produces structured format | Implemented |
| Specification | Agent-generated spec with tasks | `zerovector:architect` output | Implemented |
| Build from spec | Implementation agent + tools | `zerovector:builder` with file/bash tools | Implemented |
| Intent-fidelity validation | Critic agent with structured verdict | `zerovector:critic` (PASS/CONDITIONAL/FAIL) | Implemented |
| Delivery packaging | Shipper agent with git/docs | `zerovector:shipper` | Implemented |
| Pipeline orchestration | Staged recipe with approval gates | `intent-to-artifact.yaml` | Implemented |
| Crew selection | Mode shortcuts | 6 `/crew-*` modes | Implemented |
| Domain-specific tuning | Mode context injection | Mode `.md` files with domain prompts | Implemented |
| Design-system-as-context | Context module injection | Not yet implemented | Gap |
| Live artifact preview | Tool module for screenshot/render | Not yet implemented | Gap |
| Fidelity scoring | Quantitative critic output | Not yet implemented | Gap |
| Auto intent classification | Gateway agent/recipe | Partially in `/crew` general mode | Partial |

---

*This analysis should be read after `01-philosophy-deep-dive.md` and before `03-crew-design-rationale.md`.*
