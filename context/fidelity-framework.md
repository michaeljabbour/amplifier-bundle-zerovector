# Fidelity Framework

> Universal model. Works on any Amplifier session regardless of bundle, domain, or crew composition.

---

## What Is Fidelity?

Fidelity is translation loss between intent and artifact.

Every step from "what you meant" to "what was built" is a potential lossy compression. Fidelity measures how much of the original intent survives into the final artifact.

Quality asks: *is this well-made?*
Fidelity asks: *does this faithfully represent what was intended?*

A beautifully crafted artifact that solves the wrong problem has high quality but low fidelity. A rough prototype that nails exactly what was intended has low quality but high fidelity. The goal is both — but fidelity comes first, because quality without fidelity is wasted effort.

---

## The Five Lenses

| Lens | Measures | Translation Loss When |
|------|----------|-----------------------|
| Intent Clarity | How well the original vision has been captured and articulated | Intent is vague, ambiguous, or missing key constraints |
| Specification | How completely and precisely the intent has been translated into a buildable spec | Spec omits requirements, adds unrequested scope, or leaves decisions ambiguous |
| Implementation | How faithfully the spec has been translated into a working artifact | Code/artifact deviates from spec, misses features, or adds unspecified behavior |
| Quality | How robust, maintainable, and well-crafted the artifact is | Artifact has bugs, poor error handling, missing tests, or unreadable structure |
| Ship-Readiness | How ready the artifact is for its intended audience or deployment target | Artifact is incomplete, undocumented, or has unresolved delivery blockers |

### Intent Clarity (0–1)

Measures the gap between what the user actually wants and what has been captured in writing. A score of 1.0 means the intent document is specific enough that two independent teams would build the same thing from it. A score below 0.5 means critical ambiguity remains — the intent could be interpreted multiple ways with materially different outcomes.

Scoring guidance:
- **0.90–1.00**: Intent is explicit, constrained, and testable. Anti-goals are stated. Success criteria are measurable.
- **0.70–0.89**: Intent is clear but some constraints or edge cases are unstated. A skilled builder could infer them.
- **0.50–0.69**: Intent has significant gaps. Multiple reasonable interpretations exist.
- **Below 0.50**: Intent is vague or missing. Building would be guesswork.

### Specification (0–1)

Measures the gap between captured intent and the buildable specification. A score of 1.0 means the spec is complete, unambiguous, and traceable back to every intent requirement. A score below 0.5 means the spec is missing major sections or introduces scope not present in the intent.

Scoring guidance:
- **0.90–1.00**: Every intent requirement has a corresponding spec element. No unrequested scope. Acceptance criteria are concrete.
- **0.70–0.89**: Spec covers intent well but minor requirements lack explicit acceptance criteria.
- **0.50–0.69**: Spec has notable gaps or includes untraced additions.
- **Below 0.50**: Spec is substantially incomplete or disconnected from intent.

### Implementation (0–1)

Measures the gap between specification and working artifact. A score of 1.0 means every spec requirement is implemented, nothing unspecified is added, and all acceptance tests pass. A score below 0.5 means major spec requirements are unimplemented or the artifact deviates significantly from the spec.

Scoring guidance:
- **0.90–1.00**: All spec requirements implemented. All acceptance tests pass. No scope creep.
- **0.70–0.89**: Most requirements implemented. Minor deviations or untested edge cases.
- **0.50–0.69**: Notable features missing or significant deviations from spec.
- **Below 0.50**: Artifact does not match the specification in material ways.

### Quality (0–1)

Measures craftsmanship independent of fidelity-to-spec. A score of 1.0 means the artifact is robust, well-tested, readable, and maintainable. A score below 0.5 means the artifact has serious quality issues that would block production use.

Scoring guidance:
- **0.90–1.00**: Comprehensive tests, clean code, proper error handling, typed interfaces, good documentation.
- **0.70–0.89**: Solid quality with minor gaps in test coverage or documentation.
- **0.50–0.69**: Functional but brittle. Missing tests, unclear error handling, or poor readability.
- **Below 0.50**: Significant quality issues. Bugs, no tests, unreadable code, or fragile architecture.

### Ship-Readiness (0–1)

Measures the gap between "working artifact" and "delivered artifact." A score of 1.0 means the artifact is documented, committed, deployable, and ready for its audience. A score below 0.5 means there are significant blockers to delivery.

Scoring guidance:
- **0.90–1.00**: Clean commits, documentation complete, deployment-ready, no blockers.
- **0.70–0.89**: Nearly ready. Minor documentation gaps or cleanup needed.
- **0.50–0.69**: Artifact works but delivery is incomplete. Missing docs, messy commits, or unresolved blockers.
- **Below 0.50**: Not shippable. Major delivery blockers remain.

---

## Scoring Rubric

| Range | Interpretation |
|-------|----------------|
| 0.80–1.00 | **Strong** — Translation is faithful. Minor refinements only. |
| 0.60–0.79 | **Moderate** — Meaningful translation loss detected. Targeted improvements needed. |
| 0.30–0.59 | **Significant gap** — Substantial translation loss. Rework required in this lens. |
| 0.00–0.29 | **Critical gap** — This lens has not been meaningfully addressed. Immediate attention required. |

**Overall score** = arithmetic mean of all five lens scores.

**Converged** when overall >= target (default target: 0.85).

---

## Structured Fidelity Assessment Output

Every fidelity assessment produces a JSON object with this structure:

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
    "recommendation": "Documentation is incomplete. Add usage examples and update CHANGELOG before delivery."
  },
  "evidence": {
    "intent_clarity": "Intent document specifies functional requirements, anti-goals, and success criteria. One ambiguity remains around error retry behavior.",
    "specification": "Spec covers all intent requirements. Acceptance criteria are concrete. Minor gap: no explicit error message format specified.",
    "implementation": "3 of 4 spec requirements implemented and passing. Retry logic not yet implemented per spec.",
    "quality": "Test coverage at 87%. Type hints on all public functions. One untested error path in the retry handler.",
    "ship_readiness": "Code committed but README lacks usage examples. CHANGELOG not updated. No delivery blockers beyond documentation."
  }
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `domain` | string | The active domain. Valid values: `build`, `product`, `research`, `content`, `platform`, `general`. |
| `target` | number | The convergence target for this domain (0–1). |
| `lenses` | object | Scores (0–1) for each of the five lenses: `intent_clarity`, `specification`, `implementation`, `quality`, `ship_readiness`. |
| `overall` | number | Arithmetic mean of the five lens scores. |
| `priority_gap` | object | The lens with the lowest score. Contains `lens` (string), `score` (number), and `recommendation` (string). |
| `evidence` | object | Per-lens justification strings. One entry per lens explaining how the score was determined. |

---

## Priority Gap

The priority gap identifies the weakest lens and routes corrective action:

| Gap Lens | Routing Action |
|----------|----------------|
| Intent Clarity | Return to intent capture. Clarify ambiguities with the user before proceeding. |
| Specification | Revise the spec. Fill gaps, remove untraced scope, add missing acceptance criteria. |
| Implementation | Continue building. Implement missing features, fix deviations from spec. |
| Quality | Improve craftsmanship. Add tests, fix bugs, improve error handling and readability. |
| Ship-Readiness | Prepare for delivery. Complete documentation, clean commits, resolve deployment blockers. |

When multiple lenses tie for lowest, prioritize earlier in the pipeline (Intent > Specification > Implementation > Quality > Ship-Readiness). Upstream fixes compound downstream.

---

## Domain Calibration

Different domains have different convergence targets. A research synthesis does not need the same ship-readiness bar as a platform module.

| Domain | Target | Rationale |
|--------|--------|-----------|
| `build` | 0.85 | Code artifacts require strong implementation and quality. |
| `product` | 0.80 | Product artifacts prioritize intent clarity and specification. |
| `research` | 0.80 | Research artifacts prioritize intent clarity and evidence quality. |
| `content` | 0.75 | Written artifacts have more subjective quality criteria. |
| `platform` | 0.88 | Platform artifacts have the highest bar — other systems depend on them. |
| `general` | 0.85 | Default target when domain is unspecified. |

---

## Calling update_fidelity

After completing a fidelity assessment, persist the result using the `update_fidelity` tool:

```
update_fidelity({
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
    "recommendation": "Documentation is incomplete. Add usage examples and update CHANGELOG before delivery."
  },
  "evidence": {
    "intent_clarity": "Intent document specifies functional requirements, anti-goals, and success criteria.",
    "specification": "Spec covers all intent requirements with concrete acceptance criteria.",
    "implementation": "3 of 4 spec requirements implemented and passing.",
    "quality": "Test coverage at 87%. Type hints on all public functions.",
    "ship_readiness": "Code committed but README lacks usage examples."
  }
})
```

Always call `update_fidelity` after a fidelity assessment. The tool persists the assessment to session state, enabling convergence tracking across pipeline stages and surfacing the fidelity dashboard.

---

## Evidence Before Claims

A score without evidence is a guess. Guesses undermine convergence.

Every lens score must be accompanied by specific evidence justifying the number. The evidence field is not optional — it is the substance of the assessment.

### Per-Lens Evidence Requirements

**Intent Clarity**: Cite specific elements from the intent document. Quote requirements, constraints, and anti-goals that are present. Name ambiguities or gaps that remain.

**Specification**: Reference specific spec sections. Trace each intent requirement to its spec counterpart. Identify any untraced additions or missing requirements.

**Implementation**: Reference concrete artifacts — test results (pass/fail counts), file paths, function signatures. Cite acceptance criteria and their status (met/unmet).

**Quality**: Report actual metrics — test coverage percentage, linter output, type checker results. Reference specific code issues or confirm their absence.

**Ship-Readiness**: Cite delivery artifacts — commit hashes, documentation files, deployment status. Name specific blockers or confirm their resolution.

Evidence must be specific enough that a different assessor reviewing the same artifacts would arrive at a similar score. Vague justifications like "looks good" or "seems complete" are not evidence.