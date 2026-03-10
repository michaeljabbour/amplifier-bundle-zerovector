# Wave 1 Reconciliation — Lead Investigator

**Investigation:** Zerovector fidelity mechanism inconsistent behavior  
**Wave:** 1  
**Reconciler:** Lead Investigator  
**Date:** 2026-03-09  
**Agents reconciled:** 9 (3 teams × 3 agents)  
**Artifacts read:** 36 files (12 per team)

---

## 1. Unified Understanding — What ALL Agents Agree On

The following findings were independently confirmed by multiple agents across multiple teams. These are the highest-confidence findings of the investigation.

### U-1: The `action="continue"` Bug Is the Primary Code-Level Defect

**Confirmed by:** Alpha-CT (BUG-1), Alpha-IM (Boundary 1), Beta-CT (§5, Unknown 5)

Both `hooks-fidelity-reporter` (`__init__.py:310`) and `hooks-crew-gate` (`__init__.py:181`) return `HookResult(action="continue", context_injection=...)`. The kernel's `HookRegistry.emit()` (`hooks.py:162-165`) only collects `context_injection` from results where `action == "inject_context"`. The coordinator's `process_hook_result()` (`coordinator.py:361`) has the identical guard. Result: **ephemeral routing advice is silently discarded on every invocation.** Only the ANSI dashboard (written directly to `sys.stdout`) works because it bypasses the kernel entirely.

The todo tool's `hooks-todo-reminder` uses `action="inject_context"` (confirmed by Gamma-CT §3b, Gamma-BO Finding 1, Gamma-IM Boundary 3). This is the correct action for the hook's intent.

**Confidence:** VERY HIGH — traced to exact file:line by 3+ agents independently, with kernel source confirmation.

### U-2: The Fidelity Mechanism Depends Entirely on LLM Compliance

**Confirmed by:** Alpha-BO (Finding 1, 4, 6), Alpha-IM (Boundary 6, Cross-Cutting §1), Beta-IM (Boundary 3, 6), Beta-BO (Finding 2, Anti-Pattern 1), Gamma-BO (Finding 1, Synthesis)

The entire lifecycle — from "critic produces scores" to "orchestrator calls `update_fidelity`" to "dashboard updates" — depends on the LLM following natural-language instructions. There is no programmatic enforcement at any point. The 8 fix commits in 2 days are evidence that this compliance fails repeatedly.

**Confidence:** VERY HIGH — convergent finding across all 9 agents.

### U-3: Session Isolation Creates a Mandatory LLM-Mediated Bridge

**Confirmed by:** Alpha-IM (Boundary 6), Beta-IM (Boundary 3), Gamma-IM (Boundary 5)

Each `AmplifierSession` has its own `ModuleCoordinator` with its own `FidelityState`. Child sessions (critic, builder, etc.) have isolated state. The ONLY mechanism for scores to reach the root session's dashboard is: critic produces JSON → text returns to root → orchestrator LLM parses it → orchestrator calls `update_fidelity`. This is deliberately architectural (session isolation is a feature), but the bridge is the weakest possible mechanism (LLM text parsing + instruction following).

**Confidence:** VERY HIGH — all 3 integration mappers confirmed independently with matching diagrams.

### U-4: The Double-Declaration Workaround (Commit `6a0999e`)

**Confirmed by:** Alpha-CT (BUG-2), Alpha-BO (Finding 5), Alpha-IM (Boundary 3), Beta-CT (§1), Beta-BO (Finding 6), Beta-IM (Boundary 5), Gamma-IM (Boundary 1)

`zerovector-crew.yaml` both includes `fidelity.yaml` transitively AND declares the same modules directly. This is a workaround for a confirmed composition bug: "transitive include doesn't merge hooks." All 7 agents who examined this agree on the current state and its fragility.

**Confidence:** VERY HIGH — confirmed by git commit message and source analysis across all teams.

### U-5: The Fidelity Reporter Silently No-Ops When State Is Empty

**Confirmed by:** Alpha-CT (§7), Alpha-BO (Finding 4), Alpha-IM (Boundary 4), Beta-CT (§5), Beta-IM (Boundary 4), Gamma-CT (§5), Gamma-BO (Finding 1, Anti-Pattern 3)

`hooks-fidelity-reporter` returns `_CONTINUE` (no output, no injection, no dashboard) when either (a) the `zerovector.fidelity_state` capability is missing, or (b) `lens_scores` is empty. This means the mechanism is **invisible** until `update_fidelity` is called at least once. No "waiting for assessment" placeholder. No diagnostic signal.

**Confidence:** VERY HIGH — traced to `__init__.py:293-300` by 7+ agents.

### U-6: The Todo Tool's Reliability Comes From `provider:request` + Closed Loop

**Confirmed by:** Gamma-CT (§3, §5, §7), Gamma-BO (Finding 1, 2), Gamma-IM (Boundary 3)

The todo tool's `hooks-todo-reminder` fires on `provider:request` — **before every LLM call** — and uses `action="inject_context"` with `ephemeral=True`. It fires even when state is empty (nudge behavior). It's included at the foundation level (always-on). The fidelity hook fires on `tool:post` and `prompt:complete` (after events), uses `action="continue"` (wrong), silently no-ops when empty, and requires bundle-level opt-in.

**Confidence:** HIGH — Gamma team convergent, with live empirical observation by Gamma-CT.

### U-7: Context Files Are Always Present Regardless of Mode

**Confirmed by:** Beta-CT (§2, §10), Beta-BO (Finding 3), Beta-IM (Boundary 1)

`fidelity-framework.md`, `crew-instructions.md`, `domain-tuning.md`, and other context files are loaded into the system prompt during session initialization via `Bundle.compose()` and `PreparedBundle.create_session()`. They are **always present** regardless of which mode is active. The mode system adds behavioral framing (mode file body), not the core instructions.

**Confidence:** HIGH — Beta-CT traced the full code path with file:line citations.

### U-8: The `hooks-crew-gate` Module Is Untracked and Non-Functional

**Confirmed by:** Alpha-CT (BUG-3, BUG-4), Alpha-IM (Boundary 7)

`hooks-crew-gate` exists on disk but is (a) not committed to git (`?? modules/hooks-crew-gate/`), (b) not declared in any behavior YAML, (c) has a Pydantic validation bug (`"warn"` vs `"warning"`) that causes it to silently fail even if mounted. The module has no observable effect on any session.

**Confidence:** HIGH — confirmed by git status and source analysis.

### U-9: 8 Fix Commits in 2 Days Document a Serial Dependency Chain

**Confirmed by:** Alpha-BO (Finding 7, Pattern 8), Beta-BO (Finding 9), Beta-IM (Cross-Cutting §2)

The commits from `1315378` through `1ed8932` each fixed one failure mode, revealing the next. The fidelity mechanism has at least 8 independent failure modes, each independently capable of breaking the system. The fix pattern is prompt engineering (more/stronger instructions), not architectural change.

**Confidence:** HIGH — git log independently examined by 5+ agents with matching chronologies.

---

## 2. Cross-Cutting Insights — Findings That Span Teams

These insights emerge from looking ACROSS the 9 agents. No single agent could see them.

### XC-1: The Three-Defect Model

Combining all three teams' findings, the fidelity mechanism's inconsistency can be attributed to **three co-located defects** operating at different architectural layers:

| Layer | Defect | Discovered By |
|-------|--------|---------------|
| **Kernel** | `action="continue"` drops `context_injection` | Alpha-CT, Alpha-IM |
| **Context** | LLM compliance with 51KB of scattered instructions is unreliable | Alpha-BO, Beta-BO, Beta-IM |
| **Architecture** | No closed feedback loop — open loop with conditional guards | Gamma-CT, Gamma-BO, Gamma-IM |

Fixing ANY ONE of these in isolation would improve reliability, but all three need addressing for parity with the todo tool. The kernel defect (U-1) is the most actionable. The architecture defect (XC-1 layer 3) is the most impactful.

### XC-2: The Bootstrapping Paradox

Cross-referencing Beta-IM (Boundary 4, "chicken-and-egg problem"), Alpha-BO (Finding 4), and Gamma-BO (Anti-Pattern 3):

The fidelity ephemeral injection — which would REMIND the LLM about fidelity state — only activates AFTER `update_fidelity` has been called at least once. But getting `update_fidelity` called the first time is the hardest part (no hook nudge, no visible dashboard, just buried context instructions). The todo tool has no bootstrapping problem because its hook fires even when state is empty, injecting a "consider using the todo tool" nudge.

**This is a reinforcing failure mode:** The very mechanism designed to maintain LLM engagement with fidelity only works once engagement has already been established.

### XC-3: The Instruction Corpus Growth Paradox

Cross-referencing Beta-IM (Cross-Cutting §4, "Instruction Corpus Growth Problem"), Alpha-BO (Pattern 9, "Escalating Instruction Emphasis"), and Beta-BO (Finding 5, "Escalating Emphasis"):

Each time fidelity fails, the fix adds more instructions. The instruction corpus has grown to ~780+ lines across 5+ context files. But more instructions = more context competition = lower salience per instruction = more failures = more instructions. This is a positive feedback loop that degrades, not improves, reliability. The todo tool breaks this cycle by using a programmatic mechanism (hook injection) instead of instruction accumulation.

### XC-4: The Two Parallel Fidelity Systems Are Disconnected

Cross-referencing Alpha-BO (Finding 3), Alpha-IM (Boundary 8), and Beta-BO (Finding 7):

The bundle contains two independent fidelity tracking mechanisms:
- **System A** (tool-based): `tool-fidelity-state` + `hooks-fidelity-reporter` — interactive crew sessions
- **System B** (recipe-based): `fidelity-convergence.yaml` with `{{fidelity_score}}` context variables

These share **no state**. Calling `update_fidelity` (System A) does not update `{{fidelity_score}}` (System B). This was discovered by Alpha-BO and confirmed by Alpha-IM, but Beta-BO also noted it in Finding 7. Gamma team did not investigate this (outside scope), but it reinforces the fragmentation narrative.

### XC-5: The `fidelity-framework.md` API Example Mismatch

Cross-referencing Alpha-BO (Unknown 7) and Beta-BO (Unknown 8, Anti-Pattern 2):

The code example in `fidelity-framework.md` shows a JSON object with fields `lenses`, `overall`, `priority_gap`, and `evidence` — but the actual `update_fidelity` tool schema only accepts `lens_scores`, `domain`, and `target`. The key name mismatch (`lenses` vs `lens_scores`) could cause silent failures. Both Alpha-BO and Beta-BO independently flagged this.

### XC-6: The Todo Architecture Provides a Complete Design Template

Cross-referencing all Gamma findings with the defect model from XC-1:

The todo tool addresses every failure mode identified in the fidelity system:
- **Kernel defect**: Uses `action="inject_context"` (correct)
- **Context compliance**: Foundation-level deployment + 5 prompt reinforcement layers + adaptive nudging
- **Architecture**: Closed feedback loop via `provider:request` (proactive, pre-LLM injection)
- **Bootstrapping**: Hook fires even when state is empty
- **Silent failure**: Always produces output

The todo architecture is a proven, working template for the exact problem the fidelity mechanism needs to solve.

---

## 3. Discrepancy List

### D-01: Whether `action="continue"` with `context_injection` Is a Bug or by Design

**Priority:** HIGH — affects whether the fix is "change action to inject_context" or "change the kernel"

| Position | Agent | Reference |
|----------|-------|-----------|
| **It's a bug in the hook** — the hook should use `action="inject_context"` | Alpha-CT (BUG-1), Alpha-IM (Boundary 1) | findings.md §4 BUG-1, integration-map.md Boundary 1 |
| **It's a kernel design tension** — `inject_context` sounds aggressive but is non-blocking; hooks gravitate to `continue` | Alpha-IM (Design Implications §3) | integration-map.md Design Implications §3 |
| **The hook's docstring explicitly says "never modifies action away from continue"** — this is deliberate self-description | Alpha-IM (Boundary 1) | integration-map.md Boundary 1 root cause |
| **It's a documentation gap** — `models.py:131` documents that `context_injection` is "for action='inject_context'" but the hook ignores this | Beta-CT (Unknown 5) | unknowns.md §5 |

**Status:** IDENTIFIED — Wave 2 should determine whether to fix the hook (change action) or the kernel (process context_injection on any action). The todo hook's use of `action="inject_context"` suggests the hook should change.

### D-02: Whether Context Files Are Mode-Gated or Always Present

**Priority:** HIGH — affects understanding of "only works in crew-build mode"

| Position | Agent | Reference |
|----------|-------|-----------|
| **Context files are ALWAYS present** (loaded during session init, no filtering) | Beta-CT (§2, §10), Beta-IM (Boundary 1) | findings.md §10, integration-map.md Boundary 1 |
| **`crew-instructions.md` is mode-gated** — only available via zerovector-crew behavior | Alpha-IM (Boundary 5, Context Availability Matrix) | integration-map.md Boundary 5 |
| **It depends on whether behavior context includes are mode-scoped** | Alpha-CT (UNKNOWN-2) | unknowns.md UNKNOWN-2 |

**Resolution path:** Beta-CT traced the actual `Bundle.compose()` and `PreparedBundle.create_session()` code paths, finding NO conditional loading. Alpha-IM's "Context Availability Matrix" may be describing logical availability (which file comes from which behavior) rather than runtime filtering. Beta-CT's code-level trace has stronger evidence. However, the question of whether the app layer adds any filtering BEYOND what the kernel does remains open (Alpha-CT UNKNOWN-2).

**Status:** IDENTIFIED — likely resolvable by re-examining Beta-CT's code traces vs Alpha-IM's matrix. A code tracer should verify the `create_session()` path has no mode-conditional filtering.

### D-03: Whether the Orchestrator Handles Ephemeral Injections from `action="continue"` Results

**Priority:** HIGH — determines whether the fidelity routing advice EVER reaches the LLM

| Position | Agent | Reference |
|----------|-------|-----------|
| **The orchestrator MIGHT have its own pathway** for `context_injection` on `continue` results | Beta-CT (Unknown 5) | unknowns.md §5 |
| **The orchestrator uses `process_hook_result()` which gates on action** — so `continue` injections are lost | Alpha-CT (UNKNOWN-3) | unknowns.md UNKNOWN-3 |
| **The orchestrator (`loop-streaming`) explicitly handles `inject_context` + `ephemeral` only** | Gamma-CT (§3a, code evidence) | findings.md §3a, evidence.md (loop-streaming lines 216-260) |

**Resolution:** Gamma-CT found the actual orchestrator code (`loop-streaming/__init__.py:216-260`) and it explicitly checks `result.action == "inject_context" and result.ephemeral and result.context_injection`. This confirms that `action="continue"` with `context_injection` is silently dropped by the orchestrator too. **D-03 is effectively resolved by Gamma-CT's code trace.**

**Status:** RESOLVED by cross-team evidence — the routing advice NEVER reaches the LLM.

### D-04: Whether `prompt:complete` Is Actually Emitted by the Orchestrator

**Priority:** MEDIUM — affects "fires twice" vs "fires once" analysis

| Position | Agent | Reference |
|----------|-------|-----------|
| **Unknown — not found in amplifier-core codebase** | Alpha-CT (UNKNOWN-4), Alpha-IM (Unknown 1), Beta-IM (Unknown 1) | Multiple unknowns.md files |
| **`prompt:complete` is defined in events.py but NOT in HookRegistry class constants** | Alpha-CT (evidence.md, events.py section) | evidence.md "events.py: prompt:complete Is a Canonical Event" |

**Status:** IDENTIFIED — 3 agents flagged this independently. A code tracer should examine the orchestrator module (`loop-streaming` or similar) to verify whether `prompt:complete` is emitted.

### D-05: Discrepancy in Fidelity Instruction Count

**Priority:** LOW — affects context analysis but not mechanism understanding

| Position | Agent | Reference |
|----------|-------|-----------|
| **6 instruction locations** in 3 files tell the LLM to call `update_fidelity` | Alpha-BO (Finding 2, Catalog §1) | findings.md Finding 2, catalog.md §1 |
| **2 of 19 files** contain the instruction | Beta-BO (Finding 1) | findings.md Finding 1 |
| **5 reinforcement layers** (for comparison, todo has 5) | Gamma-BO (Finding 2) | findings.md Finding 2 |

**Analysis:** These are counting different things — Alpha-BO counts locations within files, Beta-BO counts files, Gamma-BO counts reinforcement layers. All are internally consistent. Alpha-BO also identifies the CRITICAL block (in crew-instructions.md) as the strongest single instruction; Beta-BO identifies it as one of only 2 files with the instruction. These are complementary views, not contradictions.

**Status:** RESOLVED — no real discrepancy, different counting methodologies.

### D-06: Whether Double-Mounting of `tool-fidelity-state` Causes State Orphaning

**Priority:** MEDIUM — could explain intermittent "skips entirely" 

| Position | Agent | Reference |
|----------|-------|-----------|
| **Double-mounting would orphan the first FidelityState** — hook reads capability (second), but first tool's state is lost | Alpha-CT (UNKNOWN-6), Alpha-IM (Boundary 3, Unknown 7) | Multiple unknowns.md |
| **Double-mounting would work correctly** — because both capability and active tool point to the second instance | Alpha-IM (Unknown 7, "The scenario" analysis) | unknowns.md Unknown 7, steps 1-5 |

**Status:** IDENTIFIED — Alpha-IM analyzed both outcomes and concluded it would likely work correctly IF both registrations complete. But the `zerovector.update_fidelity` capability (bound method) might still reference the first instance. Wave 2 should test this path.

### D-07: Whether the Critic Calls `update_fidelity` Directly

**Priority:** HIGH — affects understanding of the "who calls it" contract

| Position | Agent | Reference |
|----------|-------|-----------|
| **The critic is explicitly told NOT to call it** (critic.md line 263) | Alpha-BO (Finding 1), Beta-BO (Finding 2, catalog §12), Gamma-BO (Finding 2) | Multiple findings.md |
| **The critic USED TO call it** before commits `9a49682` and `b2a15a1` fixed it | Alpha-BO (Finding 1, Fix Chain), Alpha-CT (UNKNOWN-7) | Multiple files |
| **It's unknown whether the orchestrator actually parses critic JSON and calls it** | Alpha-CT (UNKNOWN-7), Gamma-BO (Unknown 2) | unknowns.md |

**Analysis:** All agents agree on the CURRENT state (critic told not to call, orchestrator should call). The open question is whether the orchestrator actually does. Commit `1ed8932` added CRITICAL instructions but this is still prompt engineering, not programmatic enforcement.

**Status:** IDENTIFIED — Wave 2 should verify whether the orchestrator (as an LLM following instructions) reliably calls `update_fidelity` after receiving critic output.

---

## 4. Consolidated Unknowns

Unknowns from all 9 agents, deduplicated and prioritized by impact on stabilization.

### CRITICAL — Must Resolve for Stabilization

| ID | Unknown | Raised By | Notes |
|----|---------|-----------|-------|
| CU-1 | **Does the orchestrator (`loop-streaming` or similar) emit `prompt:complete`?** | Alpha-CT U4, Alpha-IM U1, Beta-IM U1 | If not emitted, fidelity hook fires only on `tool:post` — not after text-only turns |
| CU-2 | **How does the orchestrator handle ephemeral HookResults?** | Beta-CT U3, Beta-IM U2, Alpha-CT U3 | **Partially resolved by Gamma-CT** — `loop-streaming` only processes `inject_context` + `ephemeral`, confirming `continue` injections are lost |
| CU-3 | **Does the LLM orchestrator actually call `update_fidelity` after critic delegation?** | Alpha-CT U7, Gamma-BO U2 | The CRITICAL block was added in commit `1ed8932` but compliance is unverified |

### HIGH — Important for Design Decisions

| ID | Unknown | Raised By | Notes |
|----|---------|-----------|-------|
| HU-1 | **What is the app-layer bundle loader's deduplication behavior for hooks?** | Alpha-CT U1, Alpha-IM U2, Beta-IM U3, Gamma-IM U3 | 4 agents flagged this. Determines if BUG-2 (double registration) is active or theoretical |
| HU-2 | **Does `hooks-mode` (external) inject mode file body as ephemeral context?** | Beta-CT U1, Beta-CT U2 | Determines mode activation's effect on fidelity instructions |
| HU-3 | **What are the actual LLM compliance rates for `update_fidelity`?** | Alpha-BO U5, Beta-BO U4 | Without telemetry, can't distinguish "never works" from "works 80% of the time" |
| HU-4 | **Does context compaction drop fidelity-critical instructions mid-loop?** | Alpha-IM U6, Beta-IM U4 | Would explain "works at first then stops" patterns in long sessions |

### MEDIUM — Useful Context

| ID | Unknown | Raised By | Notes |
|----|---------|-----------|-------|
| MU-1 | **The `fidelity-framework.md` API example uses `lenses` key but tool expects `lens_scores`** | Alpha-BO U7, Beta-BO U8 | Potential silent failure if LLM follows documentation literally |
| MU-2 | **What does `modes:context/modes-instructions.md` contain?** | Beta-CT U4, Beta-BO U2 | External dependency, could contain conflicting instructions |
| MU-3 | **Can the injection budget be exhausted by multiple hooks?** | Alpha-CT U8, Gamma-IM (Effect C) | Budget is 10K tokens, injections are ~200 bytes — likely fine but unverified |
| MU-4 | **Does `hooks-crew-gate` interact with `provider:request` in ways that could deny todo injection?** | Gamma-CT U6, Gamma-CT Q1 | Low risk — crew-gate isn't mounted — but worth checking when it is |
| MU-5 | **What happens to FidelityState during child session spawning?** | Alpha-BO U2, Beta-IM U6 | Each child gets fresh state. If child calls `update_fidelity`, it updates invisible state. |

### LOW — Nice to Know

| ID | Unknown | Raised By | Notes |
|----|---------|-----------|-------|
| LU-1 | `hooks-crew-gate` roadmap and intended integration | Alpha-CT U5, Alpha-BO U4 | Module is untracked, not deployed |
| LU-2 | Whether `<CRITICAL>` tags have special Amplifier semantics | Alpha-BO U3, Beta-BO U5 | Likely just prompt engineering conventions |
| LU-3 | `tool-todo` exact state storage mechanism | Gamma-CT U1, Gamma-IM U2 | Documentation + live observation gives high confidence despite missing source |

---

## 5. Recommendations for Wave 2

### 5.1 Priority Investigation: Fix the `action="continue"` Bug (D-01)

**Assign to:** Code tracer  
**Evidence needed:** Change `action="continue"` to `action="inject_context"` in `hooks-fidelity-reporter/__init__.py:310` and verify the injection pipeline works end-to-end.  
**Why:** This is the single most actionable defect. It's a one-line fix with the potential to restore ephemeral routing advice to the LLM. Even if other issues remain, this unblocks the feedback loop.

### 5.2 Priority Investigation: Verify `prompt:complete` Emission (CU-1, D-04)

**Assign to:** Code tracer examining `loop-streaming` or the actual orchestrator module  
**Evidence needed:** File:line citation of `hooks.emit("prompt:complete", ...)` in the orchestrator  
**Why:** 3 agents independently flagged this. If `prompt:complete` is never emitted, the fidelity hook fires only on `tool:post` — meaning text-only turns get no fidelity feedback.

### 5.3 Architectural Exploration: Add `provider:request` Handler to Fidelity Reporter

**Assign to:** Integration mapper + code tracer  
**Evidence needed:** Design analysis comparing the fidelity reporter firing on `provider:request` vs. current `tool:post`/`prompt:complete`. Assess whether the fidelity hook can adopt the todo hook's pattern.  
**Why:** This is XC-6's core recommendation. The todo tool's `provider:request` + always-on pattern is the proven solution to exactly the failure modes the fidelity mechanism exhibits.

### 5.4 Verify Bundle Composition Deduplication (HU-1)

**Assign to:** Code tracer on `amplifier-foundation` bundle loading code  
**Evidence needed:** Trace `merge_module_lists()` and the transitive include resolution to determine if double registration actually occurs  
**Why:** 4 agents flagged this. Understanding the merge behavior determines whether the fidelity system has a latent double-fire bug.

### 5.5 Deprioritize for Wave 2

- **`hooks-crew-gate` investigation** — module is untracked, non-functional, and has no current impact. Address after core mechanism is stabilized.
- **Recipe-based fidelity tracking (System B)** — disconnected from the tool-based system. Address as a separate concern after System A works reliably.
- **Mode file template refactoring** — 72% duplication is a maintenance issue but doesn't cause the inconsistency. Address post-stabilization.
- **Kepler/distro integration for fidelity** — Todo has deep distro integration; fidelity has none. This is important for parity but is a feature, not a bugfix. Address after the core mechanism works.

---

## 6. Preliminary Stabilization Hypothesis

**This is a hypothesis based on Wave 1 convergent findings. Wave 2 must verify it before any implementation.**

The most likely path to making fidelity work "like the todo tool" requires changes at **three levels**, matching the Three-Defect Model (XC-1):

### Level 1: Fix the Kernel-Level Bug (1 line change)

Change `action="continue"` to `action="inject_context"` in `hooks-fidelity-reporter/__init__.py:310`. This restores the ephemeral routing advice pipeline and the `user_message` field processing.

**Expected impact:** The LLM starts receiving fidelity routing advice after `update_fidelity` is called. The ANSI dashboard continues working (stdout bypass is independent). This alone does not fix bootstrapping.

### Level 2: Add a `provider:request` Handler (Todo Pattern Adoption)

Add a `provider:request` event handler to `hooks-fidelity-reporter` (or create a new `hooks-fidelity-reminder` module, mirroring the todo-reminder pattern):
- Fire **before every LLM call** 
- If fidelity state has scores: inject routing advice (current behavior, but with correct action)
- If fidelity state is empty: inject a nudge ("Fidelity hasn't been assessed. If working on artifacts, consider delegating to the critic.")
- Use `action="inject_context"`, `ephemeral=True`
- Consider `append_to_last_tool_result=True` for contextual placement

**Expected impact:** Closes the feedback loop. The LLM sees fidelity state before every decision. The bootstrapping paradox (XC-2) is eliminated because the hook fires even when empty. The instruction corpus growth paradox (XC-3) is broken because the hook replaces scattered context instructions with a programmatic mechanism.

### Level 3: Fix the API Example Mismatch (XC-5)

Update `fidelity-framework.md` to use `lens_scores` (not `lenses`) in the code example, and remove the `overall`, `priority_gap`, and `evidence` fields that are not tool parameters. Ensure the `crew-instructions.md` examples remain authoritative.

**Expected impact:** Reduces silent failures from LLMs following the wrong call signature.

### What This Hypothesis Does NOT Address

- **Cross-session state propagation** — still depends on LLM-mediated bridge. A programmatic solution (e.g., `session:fork` event handler linking parent/child state) would require kernel changes beyond the bundle's scope.
- **Recipe/tool system unification** — System A and System B remain disconnected. Unifying them is a design decision, not a bugfix.
- **Distro-level integration** — No REST API, WebSocket, or frontend store for fidelity. This is a feature gap, not a bug.
- **Double registration risk** — Still depends on bundle loader behavior. The workaround (redundant declarations) is fragile.

---

## Appendix: Agent Artifact Index

### Team Alpha — Fidelity Mechanism Internals
| Agent | Key Artifacts | Key Findings |
|-------|--------------|--------------|
| Agent-1 (Code Tracer) | 5 bugs cataloged, kernel trace | BUG-1 (action mismatch), BUG-2 (double registration), BUG-3 (Pydantic literal), 8 unknowns |
| Agent-2 (Behavior Observer) | 8 findings, 10 patterns, 8 unknowns | Instruction scatter, dual tracking systems, 434 tests all structural, fix chain narrative |
| Agent-3 (Integration Mapper) | 8 boundaries, 4 design implications | Session isolation, stdout bypass pattern, deduplication gap, hook API tension |

### Team Beta — Context Injection Chain
| Agent | Key Artifacts | Key Findings |
|-------|--------------|--------------|
| Agent-1 (Code Tracer) | Full injection chain trace | Context always present, mention resolution, 3-gate model, action="continue" flagged |
| Agent-2 (Behavior Observer) | 19-file catalog, 237-line findings | 2-of-19 files have instruction, 72% mode duplication, triple-injection redundancy |
| Agent-3 (Integration Mapper) | 6 boundaries, 3 cross-cutting | Session boundary is governing constraint, fix pattern is prompt engineering, bootstrapping problem |

### Team Gamma — Todo Tool Comparison
| Agent | Key Artifacts | Key Findings |
|-------|--------------|--------------|
| Agent-1 (Code Tracer) | Todo architecture traced, live evidence | provider:request timing, closed vs open loop, 7-dimension comparison table |
| Agent-2 (Behavior Observer) | 27+ artifacts, 8-layer reliability stack | Todo 8/8 layers, Fidelity 0/8, 825+ lines todo tests across 8 files |
| Agent-3 (Integration Mapper) | 6 boundaries, composition depth analysis | Foundation vs bundle layer gap, zero distro integration, confirmed composition bug |
