# Unknowns: Fidelity Context Injection Chain

> Agent-3 (Integration Mapper) — What I couldn't determine and why

---

## 1. Whether `prompt:complete` Is Actually Emitted by the Orchestrator

**What I found:** `prompt:complete` is defined as a canonical event in `amplifier_core/events.py` (line 13: `PROMPT_COMPLETE = "prompt:complete"`). Both `hooks-fidelity-reporter` and `hooks-crew-gate` register handlers for this event.

**What I couldn't determine:** Whether the orchestrator module (loaded externally, likely `loop-basic` or similar) actually emits `prompt:complete`. I searched the entire `amplifier-core` codebase and found NO code that emits this event — only the constant definition and test assertions. The orchestrator is an external module loaded at runtime, and I don't have its source.

**Why it matters:** If the orchestrator never emits `prompt:complete`, the fidelity reporter and crew-gate hooks would ONLY fire on `tool:post`. This means:
- Turns where the LLM produces text without calling any tools would get NO hook injection
- The fidelity dashboard and routing advice would only appear after tool calls
- The first turn of a conversation (before any tools are called) would have no fidelity feedback

**Risk level:** High. This could explain some of the "sometimes works" behavior — turns without tool calls might silently skip fidelity injection.

---

## 2. How Ephemeral Injections Are Handled by the Orchestrator

**What I found:** The coordinator explicitly skips adding ephemeral injections to the context manager (coordinator.py lines 411-412). The `HookResult` documentation says: "Orchestrator must append ephemeral injection to messages without storing in context."

**What I couldn't determine:** Whether the actual orchestrator module correctly implements ephemeral injection handling. The orchestrator receives `HookResult` from `coordinator.process_hook_result()`, but the ephemeral content is already skipped at that point. The orchestrator would need to separately collect ephemeral injections and append them to the messages array.

**Why it matters:** If the orchestrator doesn't handle ephemeral injections, ALL fidelity routing advice is silently lost. The dashboard would still render to stdout (visible in terminal), but the LLM would never see the plain-text routing advice that tells it which lens to work on next.

**Risk level:** Critical. This is the mechanism by which fidelity state feeds back into LLM behavior. If it's broken, the convergence loop has no automated guidance.

---

## 3. The Exact Module Merge Behavior for Transitive Includes

**What I found:** Commit `6a0999e` says "transitive include doesn't merge hooks." The fix was to duplicate hook/tool declarations. I read `Bundle.compose()` and `merge_module_lists()` but both look correct for direct composition.

**What I couldn't determine:** The exact code path for transitive includes. The `includes` field in behavior YAMLs uses URIs like `zerovector:behaviors/fidelity`. The resolution of these includes — loading the included YAML, parsing it, composing it — happens in the bundle loading code (likely in `amplifier_foundation/discovery/` or the registry). I didn't trace the full include resolution chain to find where hooks get lost.

**Why it matters:** The current fix (duplicating declarations) works but is fragile. Understanding the root cause would tell us whether this is a general composition bug that could affect other modules, or a specific edge case with self-referential bundle includes.

**Risk level:** Medium. The fix is in place, but the underlying bug may resurface if new modules are added only to `fidelity.yaml` without duplicating to `zerovector-crew.yaml`.

---

## 4. Context Window Pressure Under Deep Convergence Loops

**What I found:** The system prompt is 780+ lines of fidelity-related content before conversation begins. Each delegation adds the full delegation result to context. With up to 8 convergence iterations, each involving 2+ delegations (act + re-assess), context grows rapidly.

**What I couldn't determine:** At what point context window pressure causes the LLM to lose track of fidelity instructions. I don't know:
- The exact model being used (context window size)
- Whether the context manager performs compaction (the `CONTEXT_PRE_COMPACT` event exists but I didn't trace whether any compaction module is loaded)
- Whether compaction preserves or drops the fidelity instruction context
- The actual token count of the full system prompt after @mention resolution

**Why it matters:** If context compaction drops fidelity instructions mid-loop, the orchestrator would stop calling `update_fidelity` partway through convergence. This would explain "works at first but stops working" patterns.

**Risk level:** High. This is a likely contributor to inconsistency during longer conversations.

---

## 5. How Mode Activation Interacts with Context Loading Timing

**What I found:** Mode files are loaded by `hooks-mode` (external module from amplifier-bundle-modes). The mode body is injected as context when the mode activates. Context files from behavior composition are loaded during `PreparedBundle.create_session()` — at session start, before any mode activation.

**What I couldn't determine:** The exact mechanism by which mode activation adds context. I don't have the source for `hooks-mode` — it's fetched from `git+https://github.com/microsoft/amplifier-bundle-modes@main`. I can infer that it registers a `mode` tool and hooks that inject the mode body, but I can't verify:
- Whether mode activation replaces or appends to existing system context
- Whether mode deactivation removes the mode body
- Whether mode transitions properly clean up the previous mode's context
- Whether the mode's tool safety list is enforced at the kernel level or the orchestrator level

**Why it matters:** If mode activation replaces rather than appends, it could clobber the fidelity context that was loaded during session init. If tool safety is enforced at the wrong level, it might be bypassed in some scenarios.

**Risk level:** Medium. The `hooks-mode` source is the missing piece for fully understanding the mode boundary.

---

## 6. Whether Sub-Agent Sessions Load the Same Hooks/Tools

**What I found:** `PreparedBundle.spawn()` (bundle.py lines 598-758) creates a new session with the composed bundle's mount plan. The child session goes through `child_session.initialize()` which loads hooks and tools from the mount plan.

**What I couldn't determine:** Whether the child session's mount plan includes the same hooks and tools as the parent. Specifically:
- Does `effective_bundle.to_mount_plan()` include `hooks-fidelity-reporter` and `tool-fidelity-state`?
- If yes, the child session has a `update_fidelity` tool — but calling it updates the CHILD's state (invisible)
- The critic's instructions now say "do NOT call update_fidelity" — but if the tool is available in the child session, could other agents accidentally call it?

**Why it matters:** If agents in child sessions accidentally call `update_fidelity`, they'd update their own invisible FidelityState. This wouldn't directly cause inconsistency (the root state wouldn't change), but it could confuse the agent's behavior if it thinks it updated something meaningful.

**Risk level:** Low-medium. The critic instructions were fixed (commit 9a49682), but other agents (builder, architect) aren't explicitly told NOT to call it.

---

## 7. Race Conditions in Hook Merging

**What I found:** When both `hooks-crew-gate` (priority 10) and `hooks-fidelity-reporter` (priority 50) fire on the same event, the hook registry collects all `inject_context` results and merges them (hooks.py lines 162-179). The merge concatenates content and uses the FIRST result's settings.

**What I couldn't determine:** Whether the merge always behaves correctly when:
- One hook returns `inject_context` and another returns `continue` (non-injection)
- The merged content exceeds the `injection_size_limit` (default 10KB)
- The `injection_budget_per_turn` is exhausted by the first hook's injection

**Why it matters:** If budget enforcement silently drops the fidelity injection because the crew-gate injection consumed the budget, fidelity routing advice would disappear when no mode is active — exactly the "sometimes works without a mode" pattern.

**Risk level:** Medium. The budget is 10,000 tokens by default, and the injections are small (~200 bytes each), so this is likely fine. But I couldn't rule it out.

---

## Suspected Composition Effects (Unconfirmed)

### A. "Instruction Fatigue" Hypothesis
The system prompt contains anti-rationalization tables in at least three places (`crew-instructions.md`, `crew-build.md`, `using-zerovector.md`). Each says something like "do NOT skip fidelity." The repetition may cause the LLM to treat these as formulaic rather than critical, reducing compliance over long conversations.

### B. "First-Turn Silence" Hypothesis  
Before the first `update_fidelity` call, the fidelity hook returns `_CONTINUE` (no injection). The crew-gate hook fires (if no mode) but says "suggest a mode," not "call update_fidelity." There is a gap at conversation start where neither hook provides fidelity guidance. The LLM must rely entirely on the system prompt context — which it may not prioritize in its first response.

### C. "Mode Transition" Hypothesis
If a user activates a mode mid-conversation (e.g., starts without a mode, then activates `/crew-build`), the mode body is injected but the prior crew-gate warnings may still be in context history. The LLM might see conflicting instructions from before and after mode activation.
