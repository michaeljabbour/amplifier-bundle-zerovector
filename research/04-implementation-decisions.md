# 04 — Implementation Decisions

> Every structural choice made during bundle construction, with rationale and alternatives considered

---

## 1. Architecture Decision Record

### Problem Statement

Build an Amplifier bundle that implements the Zero-Vector Design philosophy: a five-stage intent-to-artifact pipeline with domain-specific crews, invocable via slash commands, with automated recipe execution and human approval gates.

### Constraints

1. **No kernel changes** — everything must be implementable at the bundle/module/recipe layer
2. **Thin bundle pattern** — include foundation, add only unique capabilities
3. **Match Superpowers UX** — slash commands, familiar invocation patterns
4. **Support both interactive and automated modes** — crew modes for interactive, recipe for automated
5. **Maintainable** — 5 agents, not 30; shared context, not duplicated prompts

---

## 2. Decision Log

### D1: Bundle Structure — Thin Bundle with Single Behavior

**Decision:** One `bundle.md` that includes foundation + one behavior YAML.

**Alternatives:**

| Option | Description | Rejected Because |
|--------|-------------|------------------|
| Monolithic bundle | Everything in `bundle.md` | Too large; doesn't compose well |
| Multiple behaviors | Separate behaviors for agents, modes, recipes | Over-fragmented; these are one methodology |
| **Single behavior** | **One `zerovector-methodology.yaml` wires everything** | **Chosen — cohesive, discoverable, matches superpowers pattern** |

**Implementation:**
```yaml
# bundle.md
includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: zerovector:behaviors/zerovector-methodology
```

This is 2 lines of includes. The behavior YAML does all the wiring.

---

### D2: Mode System — Reuse `hooks-mode` + `tool-mode` from `amplifier-bundle-modes`

**Decision:** Import the existing mode infrastructure rather than building custom slash-command handling.

**Rationale:** The modes bundle (`amplifier-bundle-modes`) provides:
- `hooks-mode`: Discovers mode files from a search path, activates on `/slash-command`
- `tool-mode`: Allows programmatic mode transitions (agent can switch modes)

This is the exact same pattern Superpowers uses. Reusing it means:
- Zero new code for command discovery
- Familiar UX for users already using Superpowers
- Tested infrastructure (modes bundle is production-proven)

**Implementation in behavior YAML:**
```yaml
hooks:
  - module: hooks-mode
    source: git+https://github.com/microsoft/amplifier-bundle-modes@main#subdirectory=modules/hooks-mode
    config:
      search_paths:
        - "@zerovector:modes"

tools:
  - module: tool-mode
    source: git+https://github.com/microsoft/amplifier-bundle-modes@main#subdirectory=modules/tool-mode
    config:
      gate_policy: "warn"
```

---

### D3: Agent Prompts — Markdown Files with Structured Sections

**Decision:** Each agent is a `.md` file in `agents/` with a consistent structure: role definition, input contract, output format, quality bar, iron laws.

**Why markdown (not YAML, not Python):**

| Format | Pros | Cons |
|--------|------|------|
| **Markdown** | **Human-readable, easy to edit, supports rich formatting, standard Amplifier pattern** | Not machine-parseable for validation |
| YAML frontmatter + markdown | Machine-parseable header | Over-engineering for agent prompts; frontmatter rarely consumed programmatically |
| Python classes | Type-checked, testable | Overkill; agents are prompt text, not executable code |

**Consistent agent file structure:**
```markdown
# Role Name

## Your Role
[One-paragraph role definition]

## You Receive
[Explicit input contract]

## You Produce
[Explicit output format with template]

## Quality Bar
[The minimum standard — expressed as a question]

## Iron Laws
[Non-negotiable behavioral rules]

## Domain-Specific Tuning
[How domain context modifies behavior]
```

---

### D4: Context Files — Two Files, Not One

**Decision:** Split context into `zerovector-principles.md` (philosophy) and `crew-instructions.md` (operations).

**Rationale:** These serve different purposes:
- **Principles** = WHY (the philosophical grounding agents need to understand the methodology)
- **Instructions** = HOW (the operational rules the orchestrator follows to run the pipeline)

Combining them would create a single file that's too long and mixes concerns. Separating them means:
- An agent that needs to understand "why do we have quality bars?" reads principles
- The orchestrator that needs to know "what do I pass to the Critic?" reads instructions

**Alternative rejected:** Three files (principles, pipeline-contract, domain-tuning). The domain tuning is small enough to live in the crew-instructions file.

---

### D5: Recipe Design — Three Stages with Two Approval Gates

**Decision:** The `intent-to-artifact.yaml` recipe has three stages:

```
Stage 1: decode-and-spec
  -> Intent Analyst -> Architect -> [APPROVAL GATE 1]

Stage 2: build-and-validate
  -> Builder -> Critic -> (loop on FAIL) -> [APPROVAL GATE 2]

Stage 3: ship
  -> Shipper -> Final summary
```

**Why three stages (not five)?**

The five agents map to five pipeline *functions*, but not every function boundary needs a human approval gate. The approval gates are placed at **decision points**:

| Gate | Decision | Why Here |
|------|----------|----------|
| After spec | "Is this specification worth building?" | Building is expensive; catching a bad spec is cheap |
| After validation | "Is this artifact worth shipping?" | Shipping is irreversible; catching a bad build is cheap |

No gate after intent analysis (the Architect validates it implicitly). No gate between Builder and Critic (they loop automatically). This keeps the recipe efficient while preserving human control at the two highest-stakes moments.

**Alternative rejected:** Five stages (one per agent). Too many gates; the human would be clicking "approve" at mechanical checkpoints with no real decision to make.

---

### D6: Approval Gate Design — APPROVE/DENY Only (No "Revise")

**Decision:** Approval gates offer two choices: APPROVE (proceed) or DENY (stop).

**History:** The initial implementation included a "revise" option at Gate 2 (return to builder with critic notes). This was removed during post-implementation review.

**Why removed:**

1. **The Shipper agent's contract says "pipeline ends here"** — routing back to Builder from Stage 3 contradicts the Shipper's role
2. **The recipe engine doesn't natively support stage-looping** — implementing "revise" would require workaround hacks
3. **The Builder-Critic loop already handles revisions** within Stage 2 — if the Critic says FAIL, the Builder fixes and re-submits before the gate
4. **DENY is sufficient** — if the artifact isn't ready at Gate 2, the user can deny and re-run the pipeline with updated intent

**Current gate behavior:**
- Gate 1: APPROVE to proceed to build | DENY to stop, specification needs work
- Gate 2: APPROVE to proceed to ship | DENY to stop, artifact discarded

---

### D7: Mode Files — Domain Context Injection Pattern

**Decision:** Each mode file (e.g., `crew-build.md`) contains domain-specific instructions that the orchestrator uses to tune agent behavior.

**How it works:**
1. User invokes `/crew-build`
2. Mode hook activates `modes/crew-build.md`
3. The mode file's content becomes part of the orchestrator's context
4. When the orchestrator delegates to agents, it includes the domain tuning from the mode
5. Each agent adjusts its focus based on the domain context

**The mode file does NOT:**
- Override agent prompts (agents are domain-agnostic)
- Change the pipeline structure (always 5 stages)
- Add or remove agents (always the same 5)

**The mode file DOES:**
- Specify what the Intent Analyst should focus on for this domain
- Specify what the Architect should prioritize for this domain
- Specify what the Critic should validate for this domain
- Set the domain label passed through the pipeline

---

### D8: The `/crew` (General) Mode — Auto-Adaptation

**Decision:** The `/crew` mode is domain-agnostic. The Intent Analyst surfaces the appropriate domain from the raw intent.

**Why this matters:** Not every intent clearly maps to a single domain. "Build a module that validates bundle schemas and write documentation for it" spans build + content. The general crew lets the Intent Analyst handle domain classification rather than forcing the user to choose.

**Implementation:** The `/crew` mode's context instructs the Intent Analyst to identify the primary domain and note any secondary domains. The orchestrator can then apply appropriate tuning.

---

## 3. What We Explicitly Did NOT Build

| Capability | Why Not (Yet) |
|-----------|---------------|
| Design-system-as-context | Requires defining the context format and injection pattern; v2 concern |
| Live artifact preview | Requires a new tool module (screenshot/render); v2 concern |
| Translation fidelity scoring | Requires defining a meaningful metric; research problem, not engineering |
| Parallel variant building | Recipe supports it but adds complexity; not needed for v1 |
| Custom tool modules | No ZVD-specific tools needed; existing Amplifier tools suffice |
| Continuous artifact lifecycle | Session-scoped workflows are the v1 focus |
| Skill files for ZVD methodology | Could be valuable for discoverability; v2 |

---

## 4. File-by-File Implementation Notes

### bundle.md (65 lines)
- Thin entry point following standard Amplifier pattern
- Includes foundation + single behavior
- Documents the methodology inline (crews, agents, recipe) for context injection
- References both context files via `@zerovector:context/` mentions

### behaviors/zerovector-methodology.yaml (63 lines)
- Single behavior wiring all components
- Imports mode infrastructure from `amplifier-bundle-modes`
- Declares all 5 agents via `agents.include`
- Declares both context files via `context.include`
- Mode search path points to `@zerovector:modes`

### agents/*.md (5 files, ~100-150 lines each)
- Consistent structure across all agents
- Each defines: role, inputs, outputs, quality bar, iron laws, domain tuning
- No overlap in responsibilities between agents
- Output format templates ensure structured, parseable results

### modes/*.md (6 files, ~30-50 lines each)
- YAML frontmatter with `shortcut:` for slash-command registration
- Domain-specific tuning instructions for the orchestrator
- Each mode references the same 5-agent pipeline
- The `/crew` (general) mode includes auto-adaptation instructions

### recipes/intent-to-artifact.yaml (303 lines)
- Three stages, two approval gates
- 13 steps across all stages
- Context variables: `intent`, `domain`, `project_path`
- Each agent delegation includes full prior context (no lossy handoffs)
- Bash steps for JSON parsing and action routing
- Final step produces structured summary

### context/zerovector-principles.md (105 lines)
- Seven principles with explanations
- "Is / Is Not" table
- Crew model explanation
- Amplifier integration mapping

### context/crew-instructions.md (152 lines)
- Orchestrator role definition
- Delegation contract (what to pass to each agent)
- Pipeline stage contracts (receives/produces/quality bar)
- Failure handling procedures
- Domain-specific tuning reference
- Context passing pattern with correct/incorrect examples

---

## 5. Validation Process

### What Was Validated

| Check | Method | Result |
|-------|--------|--------|
| File structure (16 content files) | `find` + file count | Pass — 16 files present |
| Mode shortcuts (6 commands) | `grep shortcut:` across modes/ | Pass — all 6 registered |
| Agent wiring (5 agents) | `grep zerovector:` in behavior YAML | Pass — all 5 included |
| Recipe schema | Recipe engine validator | Pass — valid, 0 warnings |
| Bundle entry point | `head bundle.md` inspection | Pass — name: zerovector, includes foundation |
| Approval gates | Line-level inspection | Pass — both have `required: true` |
| Cross-reference coherence | File-ops agent cross-check | Pass — all agent/mode/recipe refs resolve |
| Post-task cleanup | Cleanup agent scan | Pass — clean working tree, no artifacts |

### Issues Found and Fixed During Validation

| Issue | Severity | Fix Applied |
|-------|----------|-------------|
| Approval gates missing `required: true` | Blocking | Added `required: true` to both gates |
| Unsupported top-level `final_output` field in recipe | Blocking | Removed; step-level `output` is correct |
| "Revise" option in approval prompt contradicts Shipper contract | High | Removed revise option; APPROVE/DENY only |
| Behavior comments reference "Skills tool" not included | Low | Removed incorrect comment |

---

## 6. Testing Strategy

### What's Testable Today

- **Structural tests**: File existence, shortcut registration, agent wiring (bash assertions)
- **Schema tests**: Recipe validation via engine validator
- **Coherence tests**: Cross-reference resolution between files

### What Requires Runtime Testing

- **Pipeline execution**: Does the full 5-agent sequence produce useful output?
- **Domain tuning**: Does `/crew-build` produce different (better) results than `/crew` for code tasks?
- **Failure handling**: Does the Builder-Critic loop actually work on FAIL?
- **Approval gates**: Do they pause correctly in the recipe engine?

### Smoke Test Commands (from README.md)

All commands assume you are at the bundle root (`cd` into the repo first).

```bash
# Runtime file count (excludes .gitignore, README, .git, research/)
find . -type f ! -name '.gitignore' ! -name 'README.md' ! -path '*/.git/*' ! -path './research/*' | wc -l
# Expected: 16  (5 agents + 6 modes + 1 behavior + 1 recipe + 2 context + 1 bundle.md)

# Total content files (runtime + research + README)
find . -type f ! -name '.gitignore' ! -path '*/.git/*' | wc -l
# Expected: 23  (16 runtime + 1 README + 6 research)

# Mode shortcuts
grep -r 'shortcut:' modes/
# Expected: 6 lines

# Agent wiring
grep 'zerovector:' behaviors/zerovector-methodology.yaml
# Expected: intent-analyst, architect, builder, critic, shipper

# Recipe validation
recipes(operation="validate", recipe_path="zerovector:recipes/intent-to-artifact.yaml")
# Expected: valid, 0 warnings
```

---

*This document should be read after `03-crew-design-rationale.md` and before `05-roadmap.md`.*
