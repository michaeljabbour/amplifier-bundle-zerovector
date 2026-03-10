# Unknowns: Fidelity Mechanism

> Agent: Behavior Observer (WHAT)
> Investigation: team-alpha-fidelity-mechanism, wave-1

---

## 1. Does the Transitive Include Bug Still Exist?

**What I know**: Commit `6a0999e` ("transitive include doesn't merge hooks") added direct module declarations to `zerovector-crew.yaml` as a workaround. Both the transitive include AND the direct declarations remain in the current code.

**What I don't know**: Is the Amplifier runtime's behavior deterministic here? Does it:
- Load modules from the direct declaration only (ignoring transitive)?
- Load from both (causing double registration)?
- Vary by Amplifier version?

**Why it matters**: If modules load twice, the hooks-fidelity-reporter fires twice per event (the "fires twice" symptom). If the transitive include is eventually fixed without removing the direct declarations, this will silently become a double-fire bug.

**What would answer this**: Amplifier runtime source code showing how `includes:` merges hooks/tools from included behaviors. Or runtime logs showing module mount counts.

---

## 2. What Happens When update_fidelity Is Called From a Child Session?

**What I know**: The critic agent is told NOT to call update_fidelity (agents/critic.md line 263). But fidelity-framework.md (loaded into the critic's context) says to call it after assessment. If the critic calls it from a child session, where does the state go?

**What I don't know**: 
- Does the child session have access to the same `FidelityState` instance as the root session?
- If the child session calls `update_fidelity`, does it update the root session's coordinator capability or a separate instance?
- Is the `update_fidelity` tool even available to child sessions (delegated agents)?

**Why it matters**: This directly explains the "fires twice" and "fires from wrong place" symptoms. If child sessions share state, a critic calling update_fidelity would work but the dashboard might not render in the right session. If they don't share state, the call silently updates a throwaway instance.

**What would answer this**: Amplifier runtime documentation on coordinator capability sharing across parent/child sessions. Or empirical testing: have the critic call update_fidelity and observe whether the root session's dashboard updates.

---

## 3. How Does the LLM Actually Process 51KB of Context Instructions?

**What I know**: The fidelity mechanism depends on the LLM reading and correctly prioritizing instructions scattered across 5 context files (~51KB). The `<CRITICAL>` block is the strongest signal.

**What I don't know**: 
- Does the `<CRITICAL>` tag have special meaning to the Amplifier runtime (e.g., priority injection) or is it just emphasized text?
- Where in the context window do these files appear? (Early context has more influence on LLM behavior than late context.)
- How does context window pressure affect compliance? (More tools loaded = more context = more instruction dilution)

**Why it matters**: The "fires sometimes" and "skips entirely" symptoms may correlate with context window load. Sessions with more tools, more history, or longer conversations may be more likely to skip fidelity updates.

**What would answer this**: Amplifier runtime documentation on context assembly order. Empirical testing with context window utilization metrics correlated with fidelity compliance rates.

---

## 4. What Is the hooks-crew-gate Module's Actual Status?

**What I know**: The module exists at `modules/hooks-crew-gate/` (9,609 bytes), is mentioned in `docs/ROADMAP-crew-gate.md` as "Module doesn't load. Root cause unknown." It's not wired into any behavior file. The git status shows it as untracked (`?? modules/hooks-crew-gate/`).

**What I don't know**:
- Is this module complete and functional but just not loading?
- Was it abandoned or is it being actively developed?
- Could it provide the programmatic enforcement that the current mechanism lacks?

**Why it matters**: The ROADMAP document describes this module as a potential hard gate that could prevent artifacts without crew mode activation. If it could be made to work, it would address the "skips entirely" failure mode at the infrastructure level rather than relying on LLM compliance.

**What would answer this**: Reading the full module source code, attempting to install it, and investigating the Amplifier module loading mechanism.

---

## 5. Are There Actual User Session Logs Showing the Failure Modes?

**What I know**: The user reports "sometimes the fidelity hook fires, sometimes it fires twice, sometimes it only picks up intent, sometimes it skips entirely." The fix commits describe specific scenarios (frozen dashboard, double-fire, etc.).

**What I don't know**: 
- Are there saved session transcripts showing each failure mode?
- What is the approximate failure rate? (Every time? 50%? 10%?)
- Do failures correlate with specific modes, domains, or conversation lengths?
- Have the 8 fixes actually resolved the issues or just reduced frequency?

**Why it matters**: Without empirical failure rates, I can't distinguish between "architecturally impossible to work" and "works 80% of the time with occasional failures." The fix chain suggests persistent issues, but the ROADMAP doc says the mandatory update fix is "Working."

**What would answer this**: Session logs, user reports with timestamps, or systematic testing across multiple sessions.

---

## 6. Does the Recipe Engine's fidelity_score Track Actually Work?

**What I know**: The fidelity-convergence recipe uses `{{fidelity_score}}` context variables and a shell script to extract scores from critic output. The while_condition compares this against `{{target_fidelity}}`.

**What I don't know**:
- Has anyone actually run the recipe end-to-end?
- Does the shell score extraction (`echo "{\"fidelity_score\": \"$SCORE\"}"`) reliably parse critic JSON output?
- What happens if the critic's output format doesn't match the expected extraction pattern?

**Why it matters**: System B (recipe-based tracking) is presented as a complete convergence engine, but I found no evidence of end-to-end testing. If the score extraction is fragile, the while_condition never evaluates correctly, and the loop either runs forever (8 max iterations) or exits immediately.

**What would answer this**: Running the recipe with a test intent and observing whether the loop actually converges.

---

## 7. What Is the update_fidelity Tool's Input Schema Mismatch?

**What I know**: The `update_fidelity` tool (as defined in `tool-fidelity-state`) expects:
```json
{"lens_scores": {"intent_clarity": 0.8, ...}, "domain": "build", "target": 0.85}
```

But the fidelity-framework.md shows the full assessment JSON with `lenses`, `overall`, `priority_gap`, and `evidence` fields. The crew-instructions.md examples show a simplified call with just `lens_scores`, `domain`, and `target`.

**What I don't know**: When the LLM reads fidelity-framework.md's JSON example (which uses `lenses` as the key), does it try to pass the full JSON to update_fidelity (which expects `lens_scores`)? Does the tool silently drop the extra fields or error?

**Why it matters**: A key name mismatch (`lenses` vs `lens_scores`) could cause silent failures where the tool receives `{}` for lens_scores (because the LLM passed `lenses` instead) and returns an error, which the LLM may or may not surface.

**What would answer this**: Testing the tool with the exact JSON format shown in fidelity-framework.md. Or checking whether the LLM consistently uses `lens_scores` vs `lenses`.

---

## 8. Why Doesn't the Dashboard Show a "Waiting" State?

**What I know**: The hooks-fidelity-reporter silently returns `continue` when no fidelity state exists or no scores have been set. The user sees nothing.

**What I don't know**: Was this a deliberate design choice or an oversight? A "Fidelity: Awaiting first assessment..." placeholder would:
- Confirm the hook is loaded and working
- Signal to the user that fidelity tracking is active
- Distinguish "mechanism not loaded" from "mechanism loaded but no scores yet"

**Why it matters**: Silent failure is the worst failure mode for diagnosis. A visible "waiting" state would immediately surface loading failures and reduce user confusion.

**What would answer this**: Asking the module author. Or checking if there's a PR/issue discussing this behavior.
