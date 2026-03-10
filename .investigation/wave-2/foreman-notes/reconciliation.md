# Wave 2 Reconciliation — Lead Investigator

**Investigation:** Zerovector fidelity mechanism inconsistent behavior  
**Wave:** 2 (Verification & Design)  
**Reconciler:** Lead Investigator  
**Date:** 2026-03-09  
**Investigations reconciled:** 4  
**Artifacts read:** 14 files across 4 investigation directories + Wave 1 reconciliation

---

## 0. Wave 2 Context

Wave 2 was a targeted verification wave. Instead of broad triplicate investigation, it dispatched focused agents to resolve the highest-priority discrepancies and unknowns from Wave 1, plus one new design investigation:

| Investigation | Wave 1 Source | Agent Type | Outcome |
|---|---|---|---|
| `d01-action-mismatch` | D-01 (HIGH) | Code Tracer | **RESOLVED** — definitive verdict |
| `d04-prompt-complete` | D-04 (MEDIUM), CU-1 (CRITICAL) | Code Tracer | **RESOLVED** — definitive verdict + new finding |
| `d06-double-mounting` | D-06 (MEDIUM), HU-1 (HIGH) | Code Tracer | **RESOLVED** — definitive verdict |
| `new01-provider-request-design` | Wave 1 §5.3 recommendation | Integration Mapper | **COMPLETED** — design with full boundary analysis |

Additionally, the bundle owner made significant changes **between waves**: heavy context files moved to on-demand skills (~19K–23K tokens removed from always-loaded context), thin `crew-routing.md` (~36 lines) now guides skill loading.

---

## 1. Resolution Status for Each Wave 1 Discrepancy

### D-01: Whether `action="continue"` with `context_injection` Is a Bug or by Design

**Status: RESOLVED — It is a hook bug (Position A)**

The Wave 2 `d01-action-mismatch` investigation provides exhaustive, definitive evidence. The failure is traced through **four independent layers**, each with file:line citations:

| Layer | Gate Check | Location |
|---|---|---|
| 1. HookRegistry.emit() | `result.action == "inject_context"` | `hooks.py:163-164` |
| 2. coordinator.process_hook_result() | `result.action == "inject_context"` | `coordinator.py:361` |
| 3. loop-streaming (tool:post path) | `post_result.action == "inject_context"` | `__init__.py:846-850` |
| 4. loop-streaming (provider:request path) | `result.action == "inject_context"` | `__init__.py:222-226` |

**Why each competing position from Wave 1 was evaluated:**
- **Position A (Hook bug):** CORRECT. The hook should use `action="inject_context"`.
- **Position B (Kernel design tension):** WRONG. `inject_context` is non-blocking — only `deny` short-circuits (`hooks.py:154-156`). The name describes what the hook contributes, not how disruptive it is.
- **Position C (Deliberate but wrong):** PARTIALLY CORRECT as characterization — the module docstring at line 14 shows it was a conscious choice. But the distinction the author drew does not map to kernel semantics.
- **Position D (Documentation gap):** The documentation is unambiguous — `models.py:128-136` explicitly states `context_injection` is "for `action='inject_context'`." The hook ignores it.

**Critical new insight:** `user_message` IS processed regardless of action (`coordinator.py:369-370`). This means the ANSI terminal dashboard renders correctly today, which **masked the injection bug during development**. The hook appeared to work because the dashboard appeared — but the agent-facing `context_injection` was silently dropped on every invocation.

**Fix:** Single-line change at `hooks-fidelity-reporter/__init__.py:311`: `action="continue"` → `action="inject_context"`. Also update module docstring at line 14. The `_CONTINUE` sentinel for early no-op returns (lines 296, 300) should remain `action="continue"` — those genuinely have nothing to inject.

**Live runtime confirmation:** The `hooks-todo-reminder` hook fired during the d01 investigation session using `action="inject_context"` with `ephemeral=True`, and the injection reached the agent. This is direct execution-based proof that the `inject_context` pathway functions end-to-end.

---

### D-02: Whether Context Files Are Mode-Gated or Always Present

**Status: PARTIALLY RESOLVED — Superseded by context diet changes**

This discrepancy was not directly reinvestigated in Wave 2, but the bundle owner's changes between waves partially invalidate the question:

- **Before:** 5+ heavy context files (fidelity-framework.md, crew-instructions.md, domain-tuning.md, etc.) totaling ~51KB always loaded. Whether they were mode-gated was important.
- **After:** Heavy files moved to on-demand skills. Only thin `crew-routing.md` (~36 lines) is always loaded via `context.include`. The remaining always-loaded content is dramatically reduced.

The original question (Beta-CT's "always present" vs Alpha-IM's "mode-gated") was about the OLD configuration. In the NEW configuration, the always-loaded content is lightweight enough that mode-gating is less critical. The `fidelity-framework` skill is loaded on-demand during assessments, guided by `crew-routing.md`.

**Remaining gap:** Beta-CT's Wave 1 finding that `Bundle.compose()` → `PreparedBundle.create_session()` has no conditional loading is likely still accurate for the remaining context files. But the practical impact is small now that the heavy content is skill-based.

---

### D-03: Whether the Orchestrator Handles Ephemeral Injections from `action="continue"` Results

**Status: RESOLVED (Wave 1 cross-team, Wave 2 triple-confirmed)**

Already resolved in Wave 1 by Gamma-CT's code trace. Wave 2 independently confirmed at THREE layers:
- d01 traced all four gate-checks exhaustively
- d04 confirmed from the `prompt:complete` angle
- new01 mapped it across all integration boundaries

The routing advice **NEVER** reaches the LLM. The first drop occurs at `hooks.emit():163` — nothing escapes to the orchestrator or coordinator.

---

### D-04: Whether `prompt:complete` Is Actually Emitted by the Orchestrator

**Status: RESOLVED — Not emitted by orchestrator; emitted by app layer as fire-and-forget**

The Wave 2 `d04-prompt-complete` investigation provides the definitive answer with a complete event inventory.

**Finding 1:** The streaming orchestrator (`loop-streaming/__init__.py`) does NOT import or emit `PROMPT_COMPLETE`. Full event inventory confirmed:

| Event | Emitted | Result Captured? |
|---|---|---|
| `prompt:submit` | Yes (line 163) | Yes — coordinator processes |
| `session:start` | Yes (line 173) | No |
| `provider:request` | Yes (lines 205, 604) | **Yes — captured + coordinator-processed** |
| `content_block:start` | Yes (line 364) | No |
| `content_block:end` | Yes (line 382) | No |
| `tool:pre` | Yes (lines 777, 898) | Yes — deny supported |
| `tool:post` | Yes (lines 830, 948) | Yes — coordinator processes |
| `tool:error` | Yes (lines 797, 870) | No |
| `orchestrator:complete` | Yes (line 138) | No |
| `session:end` | Yes (line 668) | No |
| **`prompt:complete`** | **ABSENT** | **N/A** |

**Finding 2:** `prompt:complete` IS emitted by the **app layer** (`amplifier_app_cli/main.py`) at lines 1628 (REPL path) and 1873 (one-shot CLI path). BUT: both emission sites **discard the return value** — bare `await hooks.emit(...)` with no result capture or `coordinator.process_hook_result()` call.

**Conclusion:** `prompt:complete` is a **fire-and-forget observability event**. It can never deliver context injection in the current architecture, regardless of what action the handler returns. The fidelity reporter's `prompt:complete` handler is dead code.

**Wave 1 confirmation:** Three agents (Alpha-CT U4, Alpha-IM U1, Beta-IM U1) correctly flagged that `prompt:complete` was not found in the orchestrator. They were right.

---

### D-05: Discrepancy in Fidelity Instruction Count

**Status: RESOLVED in Wave 1 — no real discrepancy, different counting methodologies**

Not reinvestigated. Wave 1's assessment stands.

---

### D-06: Whether Double-Mounting of `tool-fidelity-state` Causes State Orphaning

**Status: RESOLVED — No double-mounting occurs**

The Wave 2 `d06-double-mounting` investigation traced the full bundle composition pipeline and provides a definitive answer.

**The deduplication chain:**
1. `BundleRegistry._load_single()` (`registry.py:217-289`) detects includes → calls `_compose_includes()`
2. `_compose_includes()` (`registry.py:337-372`) loads included bundles, composes with parent-child semantics (include=parent, main=child, child wins)
3. `Bundle.compose()` (`bundle.py:61-146`) calls `merge_module_lists()` for tools and hooks
4. `merge_module_lists()` (`merge.py:37-74`) indexes by `module:` key, deep-merges conflicts (child wins), returns **exactly one entry per module ID**

**Result:** The mount plan passed to `AmplifierSession` contains each module exactly once. The double-declaration in `zerovector-crew.yaml` (both include AND direct declaration) is safe — `merge_module_lists()` collapses them.

**HU-1 (Wave 1 HIGH unknown) RESOLVED:** The deduplication behavior is `merge_module_lists()` in `amplifier-foundation/dicts/merge.py`. Four agents flagged this in Wave 1; now definitively answered.

**Theoretical analysis (IF double-mounting occurred):**
- **Tools:** `coordinator.mount()` uses dict assignment — second mount silently overwrites first (state orphaning, no warning for tools mount point)
- **Hooks:** `HookRegistry.register()` appends to handler list — second registration would fire twice (no overwrite)
- **Capabilities:** `register_capability()` uses dict assignment — silent overwrite

**Architecture insight:** Deduplication is entirely in the **foundation layer** (`Bundle.compose()`), not the **kernel layer** (`session.py`). The kernel trusts the mount plan blindly. Any code path that bypasses foundation-layer composition would be vulnerable.

**Commit 6a0999e workaround status:** Safe but potentially redundant. The direct declarations serve as insurance against composition failures. Whether to remove them depends on whether the original bug (in an older `_compose_includes()`) has been fixed at the foundation level.

---

### D-07: Whether the Critic Calls `update_fidelity` Directly

**Status: UNRESOLVED — Not investigated in Wave 2**

Wave 1 established that the critic is explicitly told NOT to call it (critic.md line 263), and the orchestrator is told to call it (commit `1ed8932`). But whether the orchestrator LLM reliably does so remains unverified. This requires execution-based testing, not code reading.

---

## 2. Wave 1 Critical/High Unknowns — Resolution Status

| ID | Unknown | Status | Resolved By |
|---|---|---|---|
| **CU-1** | Does the orchestrator emit `prompt:complete`? | **RESOLVED** | d04 — No. App layer emits, fire-and-forget. |
| **CU-2** | How does the orchestrator handle ephemeral HookResults? | **RESOLVED** | d01 + d04 — Three gate-checks, all require `action="inject_context"` |
| **CU-3** | Does the LLM orchestrator actually call `update_fidelity` after critic delegation? | **UNRESOLVED** | Not investigated. Requires execution testing. |
| **HU-1** | Bundle loader deduplication behavior? | **RESOLVED** | d06 — `merge_module_lists()` deduplicates by module ID |
| **HU-2** | Does `hooks-mode` inject mode file body as ephemeral context? | **UNRESOLVED** | Not investigated. |
| **HU-3** | Actual LLM compliance rates for `update_fidelity`? | **UNRESOLVED** | Cannot determine from code reading. |
| **HU-4** | Does context compaction drop fidelity-critical instructions? | **PARTIALLY ADDRESSED** | Context diet changes (~19K-23K tokens removed) reduce compaction pressure significantly. |

---

## 3. New Findings from Wave 2

These findings were not known in Wave 1 and emerge from Wave 2's deeper verification.

### N-1: The `prompt:complete` Handler Is a Dual-Bug (Dead Event + Wrong Action)

The fidelity reporter's `prompt:complete` handler has **two independent bugs stacked on top of each other**:
1. The event is never emitted by the orchestrator (app layer emits, but fire-and-forget)
2. Even if it fired and the result were processed, `action="continue"` would silently drop the injection

This means the `prompt:complete` handler was **never functional** for context injection. The fidelity reporter has been operating with only ONE injection pathway (`tool:post`), and that pathway was also broken by the action bug. **Zero** injection pathways ever worked.

*Sources: d04/findings.md §Summary, d01/findings.md §Layer 3*

### N-2: The `user_message` Masking Effect

The `coordinator.process_hook_result()` at `coordinator.py:369-370` processes `user_message` **regardless of action**. This means:
- The ANSI terminal dashboard renders correctly today (via `sys.stdout.write` AND `user_message` routing)
- The hook **appears** to work during development because the visual dashboard appears
- But the agent-facing `context_injection` is silently dropped

This masking effect likely prevented the bug from being discovered during initial development and testing.

*Source: d01/findings.md §What the `user_message` Field Situation Is, d01/evidence.md §coordinator.py:368-370*

### N-3: Foundation-Layer Trust Boundary

Deduplication exists ONLY in the foundation layer. The kernel (`session.py`) has no deduplication guard and trusts whatever mount plan it receives. This creates a safety gap: any code path that constructs mount plans without going through `Bundle.compose()` → `merge_module_lists()` would be vulnerable to double-mounting.

*Source: d06/findings.md §7*

### N-4: Hook Merge Loses `append_to_last_tool_result`

When multiple hooks return `inject_context` on the same event, `_merge_inject_context_results()` (`hooks.py:188-219`) concatenates content and takes `role`/`ephemeral`/`suppress_output` from the first result (lowest priority). BUT: `append_to_last_tool_result` is **not propagated** — it defaults to `False` in the merged result.

**Impact:** Adding fidelity's `inject_context` handler on `provider:request` alongside todo-reminder would cause todo-reminder's `append_to_last_tool_result=True` to be lost. The combined injection becomes a new standalone message instead of appending to the last tool result. The content still reaches the LLM, but its positional context changes.

*Source: new01/integration-map.md §5.1, new01/unknowns.md §U1*

### N-5: The Fidelity Reporter Accesses State More Principally Than Todo-Reminder

The fidelity reporter uses `coordinator.get_capability("zerovector.fidelity_state")` — the formal capability registry. Todo-reminder uses `getattr(self.coordinator, "todo_state", None)` — direct attribute access. The fidelity pattern is more principled, and the new01 design correctly preserves it.

*Source: new01/integration-map.md §Boundary E↔F*

### N-6: Injection Budget Is Not a Concern

Combined todo + fidelity injections total ~200 tokens per iteration. The coordinator budget is 10,000 tokens per turn. Even a 20-iteration turn (200 tokens × 20) would use only 4,000 tokens — 40% of budget. In practice, most turns have 3-5 iterations.

*Source: new01/integration-map.md §5.3, new01/unknowns.md §U5*

---

## 4. Cross-Cutting Insights — Wave 2

### XC-W2-1: All Three Defect Layers Now Have Concrete Solutions

Wave 1's Three-Defect Model (XC-1) identified three co-located defects. Wave 2 + the context diet changes provide concrete solutions for all three:

| Layer | Defect | Solution | Status |
|---|---|---|---|
| **Kernel** | `action="continue"` drops injection | Change to `action="inject_context"` (1-line fix) | **Verified by d01** — ready to implement |
| **Context** | 51KB scattered instructions, unreliable LLM compliance | Context diet: heavy files → on-demand skills (~19K-23K tokens saved) | **Already implemented by owner** |
| **Architecture** | No closed feedback loop, conditional guards | Add `provider:request` handler with empty-state nudge | **Designed by new01** — ready to implement |

This is the first time all three layers have actionable, evidence-backed solutions simultaneously.

### XC-W2-2: The Bootstrapping Paradox (XC-2) Is Solved by Design

Wave 1's XC-2 identified that fidelity injection only activates AFTER `update_fidelity` is called — but getting it called the first time is the hardest part. The new01 design directly addresses this:

- **Empty-state nudge:** `provider:request` handler fires even when `lens_scores` is empty, injecting a reminder to perform fidelity assessment
- **Skill reference:** Nudge tells the LLM to "Load the `fidelity-framework` skill for the scoring rubric"
- **Always-on:** Fires before every LLM call, not just after tool executions

This mirrors the todo-reminder pattern (fires even when empty) that Wave 1 identified as the proven solution.

### XC-W2-3: The Instruction Corpus Growth Paradox (XC-3) Is Broken

Wave 1's XC-3 identified a positive feedback loop: failures → more instructions → more context competition → more failures. Two changes break this cycle:

1. **Context diet:** ~19K-23K tokens removed from always-loaded context. Heavy instruction files are now on-demand skills, loaded only when relevant.
2. **Programmatic injection:** The `provider:request` handler replaces scattered context instructions with a compact, ephemeral, per-iteration injection. The LLM sees current state + routing advice without wading through hundreds of lines of static instructions.

### XC-W2-4: The d01 and d04 Investigations Converge on a Two-Part Bug

Both investigations independently discovered the same structural problem from different angles:
- d01 traced the action mismatch through all four layers
- d04 traced the event emission and discovered `prompt:complete` is fire-and-forget

Together they reveal that the fidelity reporter had **zero working injection pathways**: `tool:post` was broken by wrong action, `prompt:complete` was broken by both wrong action AND dead event. The reporter was functionally limited to the stdout dashboard bypass.

### XC-W2-5: The new01 Design Inherits Proven Patterns

The new01 integration mapper's design closely mirrors the todo-reminder architecture, which Wave 1 identified as a working template (XC-6). Key pattern adoptions:

| Pattern | Todo-Reminder | Proposed Fidelity |
|---|---|---|
| Event | `provider:request` | `provider:request` |
| Action | `inject_context` | `inject_context` |
| Empty-state behavior | Nudge (fire even when empty) | Nudge (fire even when empty) |
| Role | `user` | `user` (merge compatibility) |
| Ephemeral | `True` | `True` |
| State access | `getattr(coordinator, "todo_state")` | `coordinator.get_capability(...)` |
| Priority | 10 | 20 (fires after todo) |

The one divergence (capability registry vs. getattr) is an improvement, not a regression.

---

## 5. Updated Stabilization Plan

Combining Wave 1's hypothesis, Wave 2's verified findings, and the owner's context diet changes into a concrete, prioritized fix list.

### Priority 1: Fix the Action Bug (1-line change) — VERIFIED

**File:** `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py`  
**Change:** Line 311: `action="continue"` → `action="inject_context"`  
**Also:** Update module docstring at line 14 (remove "never modifies action away from continue")

**Expected impact:** The existing `tool:post` handler starts working for context injection. The LLM receives fidelity routing advice after every tool call (when scores exist). ANSI dashboard continues working (independent pathway).

**Evidence quality:** VERY HIGH — traced through 4 layers by d01, confirmed by d04, with live runtime proof from todo-reminder.

### Priority 2: Add `provider:request` Handler (Architecture Fix) — DESIGNED

**File:** `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py`  
**Changes:**
1. Add `provider:request` handler at priority 20 with `action="inject_context"`, `ephemeral=True`, `role="user"`
2. Add empty-state nudge (fires even when no scores exist)
3. Split `tool:post` to dashboard-only (NO `context_injection`, just `user_message` + stdout)
4. Remove dead `prompt:complete` handler
5. Store `coordinator` at init time (like todo-reminder)

**Expected impact:** Closes the feedback loop. Fidelity state is injected before every LLM call. Bootstrapping paradox eliminated. Text-only turns (which don't trigger `tool:post`) now covered.

**Evidence quality:** HIGH — full design with boundary analysis from new01, all integration points verified with file:line citations.

### Priority 3: Context Diet — ALREADY DONE

**Changes already made by owner:**
- Heavy files (fidelity-framework.md, crew-instructions.md, domain-tuning.md) → on-demand skills
- Thin `crew-routing.md` (~36 lines) always loaded, guides skill loading
- `behaviors/fidelity.yaml` stripped of all `context.include` entries
- ~19K-23K tokens removed from always-loaded context

**Impact:** Instruction corpus growth paradox (XC-3) partially broken. Context competition dramatically reduced. Skill-based loading means the full scoring rubric is available when needed without permanent context cost.

### Priority 4: Fix API Example Mismatch (Wave 1 XC-5)

**File:** `fidelity-framework` skill content (formerly `fidelity-framework.md`)  
**Change:** Update code example to use `lens_scores` (not `lenses`), remove non-existent fields (`overall`, `priority_gap`, `evidence`).

**Expected impact:** Reduces silent failures from LLMs following the wrong call signature.

### Priority 5: Framework Follow-ups (Out of Bundle Scope)

These are improvements to `amplifier-core` and `amplifier-foundation`, not the zerovector bundle:

| Item | Location | Impact |
|---|---|---|
| Fix `_merge_inject_context_results` to propagate `append_to_last_tool_result` | `amplifier-core/hooks.py:188-219` | Prevents todo-reminder behavioral change when fidelity is added |
| Add Pydantic model validator to prevent `context_injection` with wrong action | `amplifier-core/models.py` | Makes this class of bug impossible to write silently |
| Add duplicate-mount warning for tools | `amplifier-core/coordinator.py:166-176` | Defensive guard if mount plans bypass foundation layer |

---

## 6. Recommendations for Wave 3 (Adversarial)

Wave 3 should be adversarial: stress-testing claims with execution-based evidence and trying to disprove key assumptions.

### 6.1 Stress-Test: Does the Action Fix Actually Work End-to-End?

**Assign to:** Antagonist (code tracer)  
**Task:** Apply the Priority 1 fix (`action="inject_context"`), run a session, and verify:
1. The `context_injection` text appears in the LLM's message context
2. The `ephemeral=True` flag causes it to NOT persist in stored context
3. The injection appears after `tool:post` events (tool calls)
4. The ANSI dashboard still renders correctly (regression check)

**Evidence needed:** Execution logs showing the injection in `message_dicts` before the provider call.

**Try to disprove:** "Changing the action is sufficient — there are no other gate-checks or filters that would still block the injection."

### 6.2 Stress-Test: Does the LLM Actually Call `update_fidelity`? (CU-3)

**Assign to:** Antagonist (behavior observer)  
**Task:** In a session with the action fix applied, observe whether the orchestrator LLM:
1. Delegates to the critic
2. Receives critic output (JSON scores)
3. Calls `update_fidelity` with parsed scores
4. Does this consistently across 3+ sessions

**Evidence needed:** Tool call logs showing `update_fidelity` invocations (or lack thereof).

**Try to disprove:** "The CRITICAL instructions in crew-instructions are sufficient to ensure the orchestrator calls update_fidelity."

### 6.3 Stress-Test: Does the Empty-State Nudge Bootstrap Fidelity? (XC-2)

**Assign to:** Antagonist (behavior observer)  
**Task:** With the full fix applied (action + `provider:request` + nudge), start a fresh crew session and observe:
1. Does the nudge appear in the LLM's context?
2. Does the LLM respond to the nudge by initiating a fidelity assessment?
3. Does this work WITHOUT the heavy `fidelity-framework.md` in always-loaded context?

**Evidence needed:** Session transcript showing nudge → assessment → `update_fidelity` call.

**Try to disprove:** "The empty-state nudge is sufficient to bootstrap fidelity without always-loaded context."

### 6.4 Stress-Test: Does the Merge with Todo-Reminder Work Correctly?

**Assign to:** Antagonist (code tracer)  
**Task:** With both todo-reminder and fidelity reporter firing on `provider:request`, verify:
1. Both injections' content appears in the merged result
2. The LLM receives both todo and fidelity state
3. The `append_to_last_tool_result` loss doesn't cause todo-reminder to malfunction

**Try to disprove:** "Two `inject_context` handlers on `provider:request` can coexist without interference."

### 6.5 Deprioritize for Wave 3

- **`hooks-crew-gate` audit** — d01/unknowns.md suggests checking for the same action bug, but the module is untracked and not mounted. Low priority.
- **Recipe-based fidelity (System B)** — Remains disconnected from System A. Not blocking stabilization.
- **Sub-session hook inheritance** — new01/unknowns.md §U4 flags this, but it's a design question for after the core fix works.
- **Dashboard rendering frequency** — new01/unknowns.md §S3 notes the dashboard fires after every tool call. Noisy but not blocking.

---

## 7. Remaining Unknowns

### Cannot Determine from Code Reading

| ID | Unknown | Impact | Source |
|---|---|---|---|
| RU-1 | Does the LLM orchestrator reliably call `update_fidelity` after critic delegation? | HIGH — the entire fidelity lifecycle depends on this | Wave 1 CU-3, D-07 |
| RU-2 | What are actual LLM compliance rates for fidelity instructions? | HIGH — "never works" vs "works 80%" is unknowable without telemetry | Wave 1 HU-3 |
| RU-3 | Does context compaction drop fidelity instructions in long sessions? | MEDIUM — context diet reduces this risk but doesn't eliminate it | Wave 1 HU-4 |
| RU-4 | Does the empty-state nudge actually bootstrap first assessment? | HIGH — the entire bootstrapping fix depends on LLM behavior | new01 §3.3 |
| RU-5 | Does the `append_to_last_tool_result` merge loss affect todo-reminder in practice? | LOW — content still reaches LLM, only position changes | new01/unknowns.md §U1 |

### Investigated but Incomplete

| ID | Unknown | Status | Source |
|---|---|---|---|
| RU-6 | Does `hooks-mode` inject mode file body as ephemeral context? | Not investigated in Wave 2 | Wave 1 HU-2 |
| RU-7 | Sub-session hook inheritance model | Not investigated — affects whether fidelity fires in child sessions | new01/unknowns.md §U4 |
| RU-8 | Whether the commit 6a0999e workaround is still needed | d06 shows current code deduplicates correctly, but cannot confirm whether an alternative composition path exists | d06/unknowns.md §U-1, §U-3 |
| RU-9 | Whether `hooks-crew-gate` has the same `action="continue"` bug | Not read in Wave 2; module is untracked and unmounted | d01/unknowns.md |

### Answered by Wave 2 (Removed from Unknown List)

| Former ID | Question | Answer |
|---|---|---|
| CU-1 | Does the orchestrator emit `prompt:complete`? | No — app layer emits, fire-and-forget |
| CU-2 | How does the orchestrator handle ephemeral HookResults? | Three gate-checks, all require `action="inject_context"` |
| HU-1 | Bundle loader deduplication behavior? | `merge_module_lists()` deduplicates by module ID |
| D-01 | Is `action="continue"` a bug or by design? | Bug in the hook |
| D-06 | Does double-declaration cause double-mounting? | No — foundation layer deduplicates |

---

## 8. Investigation Quality Assessment

### What Wave 2 Did Well

1. **Definitive verdicts.** All three discrepancy investigations reached clear, unambiguous conclusions backed by exhaustive file:line evidence. No hedging, no "probably."

2. **Convergent confirmation.** The d01 and d04 investigations independently traced overlapping code paths and arrived at consistent findings. The three-layer drop chain appears in both.

3. **Design grounded in evidence.** The new01 integration map builds its design on verified boundary analysis, not assumptions. Every integration point has a file:line citation.

4. **Unknowns are honest.** Each investigation's unknowns file clearly separates "what I searched for but couldn't find" from "what I suspect but cannot confirm." The d01 agent's note about todo-reminder source code being unlocatable (but behavior confirmed by live evidence) is exemplary.

### What Could Improve

1. **No execution-based evidence.** All four investigations relied on code reading. The action fix, the `provider:request` design, and the merge behavior are all verified structurally but not through execution. Wave 3 should prioritize execution evidence.

2. **Independence constraint limits cross-referencing.** The new01 integration mapper explicitly notes not reading d06's findings (independence constraint). This is correct methodology, but it means new01's unknowns §U3 (double-mounting concern) is already answered by d06. The reconciliation layer resolves this.

3. **No investigation of LLM compliance.** CU-3 and HU-3 from Wave 1 remain unresolved because they require execution testing, not code reading. These are the highest-impact remaining unknowns.

---

## Appendix: Artifact Index

| Investigation | File | Key Content |
|---|---|---|
| d01-action-mismatch | findings.md | Definitive verdict: hook bug, 4-layer failure chain, single-line fix |
| d01-action-mismatch | evidence.md | 7 claims, each with file:line citations |
| d01-action-mismatch | diagram.dot | Flow chart showing all 4 gate-checks + fix path |
| d01-action-mismatch | unknowns.md | Todo-reminder source not found, `inject_context` may be later addition, crew-gate audit needed |
| d04-prompt-complete | findings.md | 4 verdicts: no orchestrator emission, first-drop at hooks.emit, provider:request is best event, prompt:complete is fire-and-forget |
| d04-prompt-complete | evidence.md | Complete event inventory, 2 emission sites in main.py, 3 drop points |
| d04-prompt-complete | diagram.dot | Full system flow: app layer → orchestrator → hooks → handlers |
| d06-double-mounting | findings.md | 7 sections: declaration exists, pipeline deduplicates, session trusts plan, theoretical analysis, workaround safe |
| d06-double-mounting | evidence.md | Full composition chain: registry → compose_includes → Bundle.compose → merge_module_lists |
| d06-double-mounting | diagram.dot | YAML → Foundation → Core layers with dedup at merge_module_lists |
| d06-double-mounting | unknowns.md | 5 unknowns: commit 6a0999e diff, FidelityState architecture, app-layer bypasses, namespace registration, loader cache scope |
| new01-provider-request-design | integration-map.md | 8 mechanisms, 6 boundaries, full design with code examples, merge analysis |
| new01-provider-request-design | diagram.dot | Integration boundary diagram with all components |
| new01-provider-request-design | unknowns.md | 5 confirmed unknowns + 3 suspected effects: merge field loss, prompt:complete emitter, sub-session inheritance, budget timing |
