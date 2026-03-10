# Mode Routing

## Available Modes

| You want to... | Type |
|----------------|------|
| Build code, features, apps, tools | `/build` |
| Architect infrastructure, modules, APIs | `/architect` |
| Design products, UX flows, specs | `/design` |
| Write docs, posts, guides, curriculum | `/write` |
| Investigate, analyze, research | `/investigate` |
| Not sure yet | `/make` |

## Skills to Load

When any mode activates, load these skills BEFORE starting:

| Skill | Content |
|-------|---------|
| `crew-operating-instructions` | Convergence protocol, delegation contract, approval points |
| `domain-tuning` | Per-domain fidelity criteria for all 5 lenses |
| `fidelity-framework` | Scoring rubric, assessment JSON format, evidence requirements |

## Routing Table

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
| general | `/make` | 0.85 | Balanced |
| build | `/build` | 0.85 | Implementation + Quality |
| platform | `/architect` | 0.88 | Quality + Ship-Readiness |
| product | `/design` | 0.80 | Intent + Specification |
| content | `/write` | 0.75 | Specification + Quality |
| research | `/investigate` | 0.80 | Intent + Quality |

## Convergence Protocol

```
ASSESS -> priority gap -> ROUTE to serving agent -> ACT -> RE-ASSESS -> loop until target (max 8)
```

**On entry, create this todo:**
- [ ] Assess initial fidelity (critic — multi-lens assessment)
- [ ] Route to weakest lens (convergence loop)
- [ ] Converge to fidelity target (assess -> route -> act -> re-assess)
- [ ] Present artifact at target fidelity (human approval)
- [ ] Ship converged artifact (shipper)

**Initial assessment:**
Delegate to `zerovector:critic` with the human's exact intent, project path, and domain.
Present the fidelity state to the human. Wait for approval before proceeding.

**Each iteration:** Fix exactly one lens (the weakest). Re-assess after every agent action. Call `update_fidelity` after every delegation return.

**When converged:** Present artifact + fidelity state. Wait for explicit human approval. Ship.

**When the loop exhausts (8 iterations):**
Say: "Convergence loop exhausted — 8 iterations, fidelity at X.XX / target Y.YY"
Present choices: Accept current state | Continue with targeted fixes | Stop and revise intent.
Never silently declare convergence.

**On ship:** Announce what was shipped, then `mode(operation='clear')`.

**Recipe alternative:** Any mode can run as a recipe:
```
recipes(operation="execute", recipe_path="zerovector:recipes/fidelity-convergence.yaml",
  context={"intent": "...", "domain": "[domain]"})
```

## Universal Rules

- You orchestrate. You do not build, write, or investigate yourself.
- One priority gap per iteration. Multi-lens jumps cause translation loss.
- Do not reuse prior scores. Always re-assess after each agent acts.
- Never skip approval points. Present fidelity state and wait.
- "0.78 is close enough to 0.85" — No. Route to the priority gap.
