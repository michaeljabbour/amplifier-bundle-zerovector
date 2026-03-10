# Lead Investigator Process Notes — Wave 1

**Date:** 2026-03-09  
**Reconciliation session for:** Wave 1, all 3 teams (9 agents, 36 artifacts)

---

## Reading Order and Methodology

I read all 36 artifacts in team order (Alpha → Beta → Gamma), within each team reading agent-1 (code tracer) first, then agent-2 (behavior observer), then agent-3 (integration mapper). This mirrors the natural investigation flow: HOW → WHAT → WHERE/WHY.

### Observation: The Triplicate Pattern Works

Each team's three agents produced genuinely complementary findings:

- **Code tracers** found the exact bug (`action="continue"` drops `context_injection`), with file:line citations. They are the ground truth for mechanism behavior.
- **Behavior observers** found the systemic patterns (instruction scatter, fix chain narrative, dual tracking systems, test coverage gaps). They see the forest.
- **Integration mappers** found the boundary failures (session isolation, composition bugs, hook timing gaps). They see where the seams are.

No single agent type could have produced the full picture. The code tracer finds BUG-1; the behavior observer explains why the fix attempts didn't work (prompt engineering instead of architecture); the integration mapper shows why the architecture makes the problem hard (session isolation is a feature that creates the LLM-mediated bridge requirement).

### Observation: Cross-Team Convergence Is the Strongest Signal

The most valuable findings emerged from convergence across teams, not within them:

- **Alpha found the `action="continue"` bug.** Beta flagged it as an unknown. Gamma found the todo tool uses `action="inject_context"`.** Only by reading all three do you see that this is a one-line fix with a proven working alternative.

- **Alpha found session isolation.** Beta found the context injection chain. Gamma found the todo tool's `provider:request` timing. Together, these reveal the Three-Defect Model — three co-located defects at different layers, each requiring a different fix type.

- **The Bootstrapping Paradox (XC-2)** was discovered independently by Beta-IM ("chicken-and-egg"), Alpha-BO ("silent failure"), and Gamma-BO ("Anti-Pattern 3: Ephemeral Injection Can't Bootstrap"). No single team named it as a cross-cutting concern. It only becomes visible when you read all three together.

### Observation: Discrepancies Were Rare and Mostly Methodological

I found only 7 discrepancies, and most were due to different counting methodologies (D-05) or different levels of analysis (D-02). The one genuine code-level discrepancy (D-01: bug vs design tension) is the most important to resolve because it determines the fix approach.

D-03 (orchestrator handling of ephemeral injections) was effectively **resolved during reconciliation** by cross-referencing Gamma-CT's findings with Alpha-CT and Beta-CT's unknowns. Gamma-CT had the answer that the other two were looking for, because Gamma traced the `loop-streaming` orchestrator code that Alpha and Beta couldn't find. This is the Parallax method working as designed — different vantage points finding different parts of the answer.

### Observation: Unknowns Cluster Around External Dependencies

The unknowns that persist across all agents cluster around:
1. **External modules** (`hooks-mode`, `tool-mode`, `hooks-todo-reminder`, `tool-todo`) — sourced from git URLs, not available locally
2. **The orchestrator module** — loaded dynamically, not in the zerovector or amplifier-core repos
3. **The bundle loader** — app-layer code that processes `includes:` directives

These are the "dark matter" of the investigation — components that affect behavior but aren't directly observable from the workspace. Wave 2 should prioritize tracing these external dependencies.

## Quality Assessment of Agent Artifacts

### Strongest Artifacts
- **Alpha-CT findings.md** — 5 bugs with exact file:line citations, clear symptom→cause→fix structure. Gold standard for code tracing.
- **Gamma-CT findings.md** — Comparative architecture analysis with live empirical evidence. The "I witnessed this mechanism firing live" section is uniquely valuable.
- **Alpha-BO patterns.md** — 10 patterns with quantitative evidence. The fix-chain-as-architecture-discovery pattern (Pattern 8) is an insight no other agent produced.
- **Beta-IM integration-map.md** — "Session boundary is the governing constraint" is the single most architecturally important sentence in the entire wave.

### Artifacts That Surprised Me
- **Gamma-BO catalog.md** — Examined 27+ files across 6 repositories. The breadth of the todo ecosystem analysis (Kepler sidecar, TUI, frontend store) was unexpected and extremely valuable for the comparison.
- **Alpha-IM integration-map.md** — The "stdout bypass pattern" cross-cutting concern (§2) explains WHY the dashboard works when everything else fails. This is a key insight for stabilization.

### Gaps I'd Like Wave 2 to Fill
1. **No agent tested the actual fix.** Alpha-CT identified BUG-1 and proposed changing `action="continue"` to `action="inject_context"`, but no agent verified this works end-to-end.
2. **No agent read the `loop-streaming` orchestrator code completely.** Gamma-CT read through line 880 of ~1052. The remaining ~172 lines might contain relevant handler logic.
3. **No agent examined the recipe engine's interaction with the hook system.** Alpha-BO identified the dual tracking systems but the recipe engine's event emission behavior is still unknown.

## Methodology Reflections

### What Worked Well
- **Three teams with different scopes** (mechanism internals, context injection, todo comparison) provided genuinely different perspectives on the same problem. The todo comparison team (Gamma) was the most valuable for stabilization because it provides a working reference architecture.
- **The unknowns.md artifacts** were as valuable as findings.md. Unknowns from one team were often answered by another team's findings (e.g., D-03 resolved by Gamma-CT).
- **The discrepancy tracking methodology** (assign IDs, record both sides, don't reconcile by fiat) preserved the signal in D-01, which is the most important design decision for Wave 2.

### What I'd Adjust for Wave 2
- **Assign one code tracer to external dependencies.** The biggest knowledge gap is `hooks-mode`, `tool-mode`, and the orchestrator module. These should be fetched and traced.
- **Include an execution-based verification agent.** Wave 1 was entirely analytical. Wave 2 needs an agent that applies the proposed fix and runs the system to verify behavior.
- **Focus Gamma team on designing the fix,** not further comparison. The todo comparison is complete. Gamma's understanding of the todo pattern should now inform a concrete design for `hooks-fidelity-reminder`.
