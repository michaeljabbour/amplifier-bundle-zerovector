# 05 — Roadmap

> What exists today, what's next, and the order in which to build it — grounded in the gap analysis from `02-amplifier-alignment.md`

---

## 1. Current State (v0.1.0)

### What Ships Today

| Component | Status | Notes |
|-----------|--------|-------|
| 5 agents (intent-analyst, architect, builder, critic, shipper) | Complete | All pipeline stages covered |
| 6 modes (/crew, /crew-build, /crew-product, /crew-platform, /crew-research, /crew-content) | Complete | Domain-specific tuning for each |
| 1 recipe (intent-to-artifact.yaml) | Complete | 3 stages, 2 approval gates, validated |
| 2 context files (principles, crew-instructions) | Complete | Philosophy + operations |
| 1 behavior (zerovector-methodology.yaml) | Complete | Wires all components |
| README with smoke tests | Complete | Quick start, crew matrix, verification |
| Research documentation | Complete | This file set (00-05) |

### What Works

- Interactive crew invocation via slash commands
- Automated pipeline via recipe with approval gates
- Domain-specific agent tuning
- Full context passing between pipeline stages
- Builder-Critic failure loop (FAIL then fix then re-validate)

### What Doesn't Work Yet

- No live artifact preview/feedback
- No design-system-as-context
- No translation fidelity scoring
- No automatic intent classification (user must choose crew)
- No parallel variant building
- No cross-session artifact lifecycle

---

## 2. Prioritized Roadmap

### Priority Framework

Items are prioritized by:
1. **Impact on translation fidelity** (ZVD's core metric)
2. **Implementation complexity** (lower is better for early items)
3. **Dependency chain** (items that unblock other items go first)

---

### Phase 1: Sharpen the Pipeline (v0.2.0)

**Goal:** Make the existing pipeline produce better results without adding new capabilities.

| Item | Description | Complexity | Impact |
|------|-------------|------------|--------|
| **P1.1** Intent templates | Structured markdown templates for common intent patterns (feature, bugfix, module, docs, research question) | Low | High — reduces variance in Intent Analyst output |
| **P1.2** Spec templates | Structured specification templates by domain (code-spec, research-spec, content-spec) | Low | High — reduces variance in Architect output |
| **P1.3** Critic rubrics | Domain-specific scoring rubrics the Critic applies (not just PASS/FAIL, but scored dimensions) | Medium | High — makes validation more rigorous and consistent |
| **P1.4** Builder self-check protocol | Explicit pre-submission checklist the Builder runs before handing to Critic | Low | Medium — reduces Critic rejection rate |

**Estimated effort:** 1-2 weeks
**Unblocks:** Fidelity scoring (P1.3 defines the dimensions to score)

---

### Phase 2: Close the Feedback Loop (v0.3.0)

**Goal:** Give agents the ability to see and react to what they've built.

| Item | Description | Complexity | Impact |
|------|-------------|------------|--------|
| **P2.1** Artifact preview tool | Tool module that captures screenshots/renders of built artifacts and injects them as context | Medium-High | High — enables "work in the medium" for visual artifacts |
| **P2.2** Test result injection | Structured injection of test results (not just pass/fail, but output) into Critic context | Low | Medium — Critic can make evidence-based judgments on test quality |
| **P2.3** Build diff summary | After Builder completes, generate a structured diff summary showing what changed | Low | Medium — Critic and human can quickly assess scope of changes |

**Estimated effort:** 2-3 weeks
**Unblocks:** Design-system-as-context (P2.1 proves the visual feedback pattern)

---

### Phase 3: Design-System Integration (v0.4.0)

**Goal:** Eliminate aesthetic/experiential translation loss by giving agents design context.

| Item | Description | Complexity | Impact |
|------|-------------|------------|--------|
| **P3.1** Design token context loader | Context module that loads design tokens (colors, spacing, typography) as agent context | Medium | Medium-High — consistent visual output |
| **P3.2** Component convention context | Documentation of component patterns, interaction rules, and brand guidelines loaded as context | Medium | Medium — agents produce on-brand artifacts |
| **P3.3** Design Critic specialization | Optional critic extension that specifically checks design-system compliance | Medium | Medium — catches visual/UX inconsistencies |

**Estimated effort:** 2-3 weeks
**Depends on:** P2.1 (needs visual feedback to validate design compliance)

---

### Phase 4: Intent Intelligence (v0.5.0)

**Goal:** Remove the last manual translation step — crew selection.

| Item | Description | Complexity | Impact |
|------|-------------|------------|--------|
| **P4.1** Intent classification gateway | First step in `/crew` mode that classifies intent and suggests/auto-selects domain | Low-Medium | Medium — removes manual crew selection |
| **P4.2** Multi-domain intent handling | Support intents that span domains (e.g., "build a module and document it") by routing to multiple crews in sequence | Medium-High | Medium — handles real-world mixed intents |
| **P4.3** Intent refinement dialogue | When intent is ambiguous, the Intent Analyst enters a structured Q&A before producing the Intent Document | Medium | Medium-High — catches ambiguity early |

**Estimated effort:** 2-3 weeks
**Unblocks:** Fully automated "state intent once, get artifact" experience

---

### Phase 5: Fidelity Measurement (v0.6.0)

**Goal:** Measure translation fidelity quantitatively — ZVD's core metric.

| Item | Description | Complexity | Impact |
|------|-------------|------------|--------|
| **P5.1** Fidelity scoring framework | Define dimensions of fidelity (scope coverage, constraint satisfaction, anti-goal avoidance, quality bar met) | Medium | High — makes the core ZVD metric measurable |
| **P5.2** Per-pipeline fidelity report | Each pipeline run produces a fidelity score alongside the Critic's verdict | Medium | High — enables tracking and improvement over time |
| **P5.3** Fidelity trend tracking | Memory-backed tracking of fidelity scores across pipeline runs | Medium | Medium — identifies systematic pipeline weaknesses |

**Estimated effort:** 3-4 weeks
**Depends on:** P1.3 (Critic rubrics define the scoring dimensions)

---

### Phase 6: Advanced Patterns (v1.0.0)

**Goal:** Production-grade ZVD with advanced capabilities.

| Item | Description | Complexity | Impact |
|------|-------------|------------|--------|
| **P6.1** Parallel variant building | Recipe pattern that builds 2-3 approaches in parallel, then Critic compares | High | Medium — explores solution space more effectively |
| **P6.2** Cross-session artifact lifecycle | Memory-backed artifact tracking that persists across sessions; supports re-validation and regeneration | High | Medium — enables "living systems" principle |
| **P6.3** ZVD skills for discoverability | Amplifier skill files that teach the methodology and best practices | Low | Medium — helps new practitioners adopt ZVD |
| **P6.4** Crew composition API | Ability to define custom crews (beyond the 6 built-in) via configuration | Medium | Low-Medium — niche but enables team customization |

**Estimated effort:** 4-6 weeks

---

## 3. Dependency Graph

```
v0.1.0 (current)
  |
  +-- P1.1 Intent templates --------+
  +-- P1.2 Spec templates ----------+
  +-- P1.3 Critic rubrics ----------+-- v0.2.0 (sharpen pipeline)
  +-- P1.4 Builder self-check ------+
                                    |
          +-------------------------+
          |
  +-- P2.1 Artifact preview -------+
  +-- P2.2 Test result injection ---+-- v0.3.0 (feedback loop)
  +-- P2.3 Build diff summary -----+
                                    |
          +-------------------------+
          |
  +-- P3.1 Design tokens ----------+
  +-- P3.2 Component conventions ---+-- v0.4.0 (design system)
  +-- P3.3 Design Critic ----------+
                                    |
  P4.1-4.3 (independent) ----------+-- v0.5.0 (intent intelligence)
                                    |
  P1.3 --> P5.1-5.3 ---------------+-- v0.6.0 (fidelity measurement)
                                    |
  P6.1-6.4 ------------------------+-- v1.0.0 (advanced patterns)
```

**Key dependencies:**
- Fidelity scoring (P5) depends on Critic rubrics (P1.3)
- Design system (P3) depends on Artifact preview (P2.1)
- Intent intelligence (P4) is independent — can be done in parallel with P2/P3

---

## 4. What Requires New Amplifier Modules

| Roadmap Item | New Module Needed? | Type |
|-------------|-------------------|------|
| P1.1-P1.4 (templates, rubrics) | No | Agent prompt updates only |
| P2.1 Artifact preview | Yes | Tool module (screenshot/render) |
| P2.2-P2.3 (test injection, diff) | No | Agent prompt + existing tools |
| P3.1-P3.2 (design context) | No | Context files + behavior config |
| P3.3 Design Critic | No | Agent specialization (prompt update or new agent) |
| P4.1-P4.3 (intent intelligence) | No | Agent prompt + mode logic |
| P5.1-P5.3 (fidelity scoring) | No | Agent prompt + memory integration |
| P6.1 Parallel variants | No | Recipe pattern |
| P6.2 Artifact lifecycle | Maybe | Memory module extension or new hook |
| P6.3 Skills | No | Skill files (markdown) |
| P6.4 Crew composition | Maybe | Mode config extension or new context pattern |

**Summary:** Only 1 item (P2.1) definitely requires a new module. 2 items (P6.2, P6.4) might. Everything else is agent prompts, context files, and recipe patterns.

---

## 5. Success Metrics by Phase

| Phase | Success Metric | How to Measure |
|-------|---------------|----------------|
| v0.2.0 | Critic rejection rate drops by >30% | Track FAIL/CONDITIONAL verdicts across pipeline runs |
| v0.3.0 | Builder iterates on visual artifacts without human describing the problem | Observe if Builder uses preview feedback autonomously |
| v0.4.0 | Artifacts match design system without human reminding agents of brand rules | Compare artifact styles against design token specification |
| v0.5.0 | User can state intent without selecting crew and get correct domain routing | Track classification accuracy of `/crew` general mode |
| v0.6.0 | Every pipeline run produces a quantitative fidelity score | Score exists and correlates with human judgment |
| v1.0.0 | Pipeline handles complex, multi-domain intents end-to-end | Successful completion of cross-domain pipeline runs |

---

## 6. What NOT to Build (Anti-Roadmap)

Some capabilities were explicitly considered and rejected, not deferred:

| Capability | Why Not |
|-----------|---------|
| **Custom kernel extensions** | Violates "no kernel changes" principle; everything must work at bundle layer |
| **Multi-human crew** | ZVD is about individual leverage; multi-human coordination is a different problem |
| **Agent marketplace** | Out of scope — agents are bundle-internal, not publishable/discoverable artifacts |
| **Real-time collaboration** | ZVD's pipeline is sequential by design; real-time collab contradicts the staged model |
| **LLM-agnostic agent definitions** | Amplifier already abstracts provider choice; agent prompts don't need this |
| **Visual pipeline editor** | Engineering effort disproportionate to value; YAML recipes are sufficient |

---

## 7. Migration Path

### For Superpowers Users

If you're currently using Superpowers (`/brainstorm` then `/write-plan` then `/execute-plan` then `/verify` then `/finish`), the migration path is:

1. **Day 1**: Try `/crew-build` for your next feature task. Compare the experience.
2. **Week 1**: Use `/crew-*` for all new tasks. Fall back to Superpowers for edge cases.
3. **Week 2+**: Switch to crew modes as default. Use Superpowers modes only for tasks that genuinely need manual sequencing.

The two bundles coexist — you can have both installed. ZVD crews and Superpowers modes live in different namespaces.

### For Recipe Users

If you prefer recipe-based automation:

1. Start with the `intent-to-artifact` recipe and explicit context params
2. Approval gates let you stay in control
3. Once comfortable, consider automating approval for low-risk domains

---

*This is the final document in the research set. Start with `00-source-material.md` and read in sequence for full context.*
