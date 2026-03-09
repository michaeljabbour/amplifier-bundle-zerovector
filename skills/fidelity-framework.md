---
name: fidelity-framework
description: "Universal fidelity scoring model — five lenses, scoring rubric (0-1), structured assessment JSON format, priority gap routing, evidence requirements. Load during fidelity assessments."
version: 0.3.0
---

# Fidelity Framework

> Universal model. Works on any Amplifier session regardless of bundle, domain, or crew composition.

## What Is Fidelity?

Fidelity is translation loss between intent and artifact. Quality asks: *is this well-made?* Fidelity asks: *does this faithfully represent what was intended?*

## The Five Lenses

| Lens | Measures | Translation Loss When |
|------|----------|-----------------------|
| Intent Clarity | How well the original vision has been captured | Intent is vague, ambiguous, or missing key constraints |
| Specification | How completely intent has been translated into a buildable spec | Spec omits requirements, adds unrequested scope, or leaves decisions ambiguous |
| Implementation | How faithfully the spec has been translated into a working artifact | Code/artifact deviates from spec, misses features, or adds unspecified behavior |
| Quality | How robust, maintainable, and well-crafted the artifact is | Artifact has bugs, poor error handling, missing tests, or unreadable structure |
| Ship-Readiness | How ready the artifact is for its intended audience | Artifact is incomplete, undocumented, or has unresolved delivery blockers |

## Scoring Rubric

| Range | Interpretation |
|-------|----------------|
| 0.80-1.00 | **Strong** — Translation is faithful. Minor refinements only. |
| 0.60-0.79 | **Moderate** — Meaningful translation loss. Targeted improvements needed. |
| 0.30-0.59 | **Significant gap** — Substantial translation loss. Rework required. |
| 0.00-0.29 | **Critical gap** — Not meaningfully addressed. Immediate attention required. |

**Overall score** = arithmetic mean of all five lens scores.
**Converged** when overall >= target (default: 0.85).

## Per-Lens Scoring Guidance

### Intent Clarity (0-1)
- **0.90-1.00**: Explicit, constrained, testable. Anti-goals stated. Success criteria measurable.
- **0.70-0.89**: Clear but some constraints unstated. Skilled builder could infer them.
- **0.50-0.69**: Significant gaps. Multiple reasonable interpretations exist.
- **Below 0.50**: Vague or missing. Building would be guesswork.

### Specification (0-1)
- **0.90-1.00**: Every intent requirement has a spec element. No unrequested scope.
- **0.70-0.89**: Covers intent well but minor requirements lack explicit criteria.
- **0.50-0.69**: Notable gaps or untraced additions.
- **Below 0.50**: Substantially incomplete or disconnected from intent.

### Implementation (0-1)
- **0.90-1.00**: All spec requirements implemented. All acceptance tests pass. No scope creep.
- **0.70-0.89**: Most requirements implemented. Minor deviations.
- **0.50-0.69**: Notable features missing or significant deviations.
- **Below 0.50**: Artifact does not match spec in material ways.

### Quality (0-1)
- **0.90-1.00**: Comprehensive tests, clean code, proper error handling, typed interfaces.
- **0.70-0.89**: Solid quality with minor gaps.
- **0.50-0.69**: Functional but brittle.
- **Below 0.50**: Significant quality issues.

### Ship-Readiness (0-1)
- **0.90-1.00**: Clean commits, documentation complete, deployment-ready.
- **0.70-0.89**: Nearly ready. Minor documentation gaps.
- **0.50-0.69**: Works but delivery incomplete.
- **Below 0.50**: Not shippable. Major blockers remain.

## Domain Calibration

| Domain | Target | Rationale |
|--------|--------|-----------|
| `build` | 0.85 | Code artifacts require strong implementation and quality. |
| `product` | 0.80 | Product artifacts prioritize intent clarity and specification. |
| `research` | 0.80 | Research artifacts prioritize intent clarity and evidence quality. |
| `content` | 0.75 | Written artifacts have more subjective quality criteria. |
| `platform` | 0.88 | Platform artifacts have the highest bar. |
| `general` | 0.85 | Default target when domain is unspecified. |

## Priority Gap Routing

| Gap Lens | Routing Action |
|----------|----------------|
| Intent Clarity | Return to intent capture. Clarify with user. |
| Specification | Revise spec. Fill gaps, add missing criteria. |
| Implementation | Continue building. Implement missing features. |
| Quality | Improve craftsmanship. Add tests, fix bugs. |
| Ship-Readiness | Prepare for delivery. Complete docs, clean commits. |

When multiple lenses tie, prioritize earlier in pipeline (Intent > Spec > Implementation > Quality > Ship).

## Structured Assessment Output

Every fidelity assessment produces this JSON:

```json
{
  "domain": "build",
  "target": 0.85,
  "lenses": {
    "intent_clarity": 0.90,
    "specification": 0.85,
    "implementation": 0.78,
    "quality": 0.82,
    "ship_readiness": 0.70
  },
  "overall": 0.81,
  "priority_gap": {
    "lens": "ship_readiness",
    "score": 0.70,
    "recommendation": "Documentation is incomplete."
  },
  "evidence": {
    "intent_clarity": "...",
    "specification": "...",
    "implementation": "...",
    "quality": "...",
    "ship_readiness": "..."
  }
}
```

## Calling update_fidelity

After every assessment, persist the result:

```js
update_fidelity({
  "domain": "build",
  "target": 0.85,
  "lens_scores": {
    "intent_clarity": 0.90,
    "specification": 0.85,
    "implementation": 0.78,
    "quality": 0.82,
    "ship_readiness": 0.70
  }
})
```

## Evidence Before Claims

Every lens score MUST have specific evidence. A score without evidence is a guess.

| Lens | Evidence Required |
|------|-------------------|
| **Intent Clarity** | Cite specific requirements, constraints, anti-goals present. Name remaining ambiguities. |
| **Specification** | Reference spec sections. Trace each intent req to its spec counterpart. |
| **Implementation** | Reference test results (pass/fail counts), file paths, acceptance criteria status. |
| **Quality** | Report actual metrics — test coverage %, linter output, type checker results. |
| **Ship-Readiness** | Cite commit hashes, documentation files, deployment status, specific blockers. |