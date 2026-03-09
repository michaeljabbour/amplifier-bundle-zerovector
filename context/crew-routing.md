# Crew Routing

When any `/crew*` mode activates, load these skills BEFORE starting the convergence loop:

| Skill | Content | When |
|-------|---------|------|
| `crew-operating-instructions` | Convergence protocol, delegation contract, approval points | Every crew session |
| `domain-tuning` | Per-domain fidelity criteria for all 5 lenses | Every crew session |
| `fidelity-framework` | Scoring rubric, assessment JSON format, evidence requirements | During fidelity assessments |

## Quick Reference

| Gap Lens | Route To | Agent |
|----------|----------|-------|
| Intent Clarity | Intent capture | `zerovector:intent-analyst` |
| Specification | Spec revision | `zerovector:architect` |
| Implementation | Build/fix | `zerovector:builder` |
| Quality | Quality pass | `zerovector:critic` |
| Ship-Readiness | Delivery prep | `zerovector:shipper` |

## Domain Targets

| Domain | Mode | Target | Emphasis |
|--------|------|--------|----------|
| build | `/crew-build` | 0.85 | Implementation + Quality |
| product | `/crew-product` | 0.80 | Intent + Specification |
| platform | `/crew-platform` | 0.88 | Quality + Ship-Readiness |
| research | `/crew-research` | 0.80 | Intent + Quality |
| content | `/crew-content` | 0.75 | Specification + Quality |

## Convergence Loop

```
ASSESS → priority gap → ROUTE to serving agent → ACT → RE-ASSESS → loop until target met (max 8)
```

MANDATORY: Call `update_fidelity` after EVERY delegation return. The dashboard freezes without it.