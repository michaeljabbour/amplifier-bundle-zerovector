# Lead Investigator Process Notes — Wave 2

## Reading Order

Read Wave 1 reconciliation first to establish the discrepancy/unknown framework. Then read Wave 2 artifacts in investigation order: d01 → d04 → d06 → new01. Within each investigation, read findings → evidence → unknowns → diagram.

## Key Observations During Synthesis

### 1. Wave 2's structure was much more focused than Wave 1

Wave 1 used 9 agents across 3 teams for broad exploration. Wave 2 used 4 targeted investigations. The result was dramatically more decisive — every discrepancy investigated got a definitive verdict, whereas Wave 1 produced mostly "IDENTIFIED" statuses. The lesson: broad exploration for Wave 1, targeted verification for Wave 2, works well.

### 2. The d01 and d04 investigations have significant overlap

Both trace the `action="continue"` failure through the hook registry and orchestrator. d01 focuses on "is it a bug?" while d04 focuses on "does prompt:complete work?" but they cover the same code paths. The overlap is useful for cross-confirmation but represents some redundant work. In future investigations, consider whether discrepancies that share root code paths should be assigned to the same agent.

### 3. The new01 investigation operated under independence constraint

The new01 integration mapper explicitly noted not reading d06's findings (to maintain independence). This caused new01/unknowns.md §U3 to flag double-mounting as an unknown — something already resolved by d06. The independence constraint is correct methodology (prevents bias), but it means the reconciliation layer is doing real synthesis work, not just summarizing.

### 4. The "user_message masking" finding (N-2) was unexpected

No Wave 1 agent identified that the ANSI dashboard's continued functionality was masking the injection bug. This emerged from d01's careful reading of `coordinator.py:369-370` showing that `user_message` is processed regardless of action. This is a genuinely new insight — the hook *appeared* to work during development because the visual output was correct, hiding the silent drop of agent-facing injection.

### 5. Context diet changes shift the investigation landscape

The owner's between-wave changes (moving heavy files to skills) are significant enough to partially invalidate several Wave 1 findings:
- U-7 (context files always present) — less relevant when always-loaded content is thin
- XC-3 (instruction corpus growth) — partially broken by removing instructions from always-loaded context
- HU-4 (compaction dropping instructions) — reduced pressure with smaller context

I chose to note these as "partially addressed" rather than "resolved" because the underlying questions about mode-gating and compaction behavior remain architecturally relevant even if the practical impact is reduced.

### 6. The stabilization plan is now concrete enough to implement

Wave 1's plan was a hypothesis. Wave 2's plan is implementation-ready for Priority 1 (single-line fix) and Priority 2 (provider:request migration). Priority 3 is already done. The remaining blockers are all execution-based: does the LLM comply? Does the nudge bootstrap? These cannot be resolved by more code reading.

## Methodology Notes

### What worked well
- Targeted code tracer investigations for discrepancy resolution — all three got definitive verdicts
- Integration mapper for the design investigation — boundary analysis with file:line citations is exactly what's needed for implementation planning
- Reading unknowns files as carefully as findings — d01's unknowns raised the Pydantic validator idea and the crew-gate audit, both valuable follow-ups

### What could improve for Wave 3
- Wave 3 needs execution evidence, not more code reading. All remaining high-impact unknowns (CU-3, HU-3, RU-4) require running sessions and observing behavior.
- Adversarial framing is important — the antagonist should try to DISPROVE that the fixes work, not confirm they do. This prevents confirmation bias.
- Consider having a behavior observer actually run a session with the fix applied, not just analyze code.
