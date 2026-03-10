# Unknowns: Boundaries Not Fully Traced

> Agent: Integration Mapper (WHERE/WHY)  
> Investigation: team-alpha-fidelity-mechanism, wave-1  
> Date: 2026-03-09

---

## Unknown 1: Orchestrator Event Emission Completeness

**What I couldn't determine:** Whether the actual orchestrator module (e.g., `loop-basic`) reliably emits both `prompt:complete` and `tool:post` events.

**Why it matters:** The fidelity reporter and crew-gate hooks register for these two events. If the orchestrator doesn't emit them (or emits them inconsistently), the hooks never fire — regardless of whether the HookResult processing works.

**What I know:**
- `prompt:complete` is defined in `events.py:13` as a canonical event
- `tool:post` is defined in `events.py:31` as a canonical event
- The `ORCHESTRATOR_CONTRACT.md` documents that orchestrators SHOULD emit `tool:post`
- The HookRegistry defines `TOOL_POST` (line 43) but does NOT define `PROMPT_COMPLETE` in its class constants (it only exists in events.py)

**What I don't know:**
- The actual orchestrator module code is loaded dynamically and not present in the codebase I examined
- Whether the orchestrator emits `prompt:complete` after every LLM response, or only in certain conditions
- Whether the orchestrator emits `tool:post` for ALL tools (including `update_fidelity`) or only for specific tool categories

**Suspected impact:** If `prompt:complete` is not reliably emitted, the fidelity dashboard would only update on `tool:post` events — meaning it would fire after `update_fidelity` calls but NOT after general LLM responses. This would explain "sometimes it fires, sometimes it doesn't."

**How to resolve:** Examine the actual orchestrator module code (likely `amplifier-module-loop-basic` or similar) and trace all `hooks.emit()` calls.

---

## Unknown 2: Bundle Loader Deduplication Behavior

**What I couldn't determine:** The exact deduplication semantics of the bundle loader when the same module is declared at multiple composition levels.

**Why it matters:** `zerovector-crew.yaml` both includes `fidelity.yaml` (which declares `hooks-fidelity-reporter`) AND directly declares `hooks-fidelity-reporter`. Commit `6a0999e` states "transitive include doesn't merge hooks" — but I couldn't verify the exact mechanism.

**What I know:**
- The commit message says transitive includes don't merge hooks
- The direct declarations exist as a workaround
- Both declarations point to the same source path (`../modules/hooks-fidelity-reporter`)

**What I don't know:**
- Does the bundle loader silently ignore the include's hooks, or does it error?
- Does this behavior apply only to hooks, or also to tools and context?
- If the bundle loader is fixed to merge transitive hooks, would deduplication be by module name, source path, or not at all?
- What happens if `tool-fidelity-state` mounts twice — does `coordinator.mount("tools", tool, name="update_fidelity")` replace or duplicate?

**Suspected impact:** If tools deduplicate by name (replacement) but hooks don't (additive), a future fix to transitive merging could cause hooks to fire twice while the tool only exists once — but the FidelityState capability registration from the first mount would be orphaned (pointing to a replaced tool's state).

**How to resolve:** Examine the bundle loader's merge logic in the app layer (not in amplifier-core — the kernel doesn't handle bundle composition).

---

## Unknown 3: Ephemeral Injection Delivery Path

**What I couldn't determine:** Whether there is an ALTERNATIVE path for ephemeral context injection that bypasses the `emit()` pipeline.

**Why it matters:** Both hooks set `ephemeral=True` on their HookResult. The coordinator's `_handle_context_injection` method (line 412) has special handling for ephemeral injections: `if not result.ephemeral:` gates whether the injection is persisted to context history. But this code is never reached because the action check (`action=="inject_context"`) fails first.

**What I know:**
- The kernel model documents: "Orchestrator must append ephemeral injection to messages without storing in context" (models.py:150-151)
- This suggests the orchestrator, not the coordinator, handles ephemeral injections
- The coordinator's `process_hook_result` is called by the orchestrator after `emit()`

**What I don't know:**
- Does the orchestrator have its own handling for ephemeral injections from hook results?
- Is there a pathway where the orchestrator inspects the INDIVIDUAL handler results (not the combined `emit()` result)?
- Does any orchestrator implementation re-emit or re-process hook results?

**Suspected impact:** If the orchestrator has its own ephemeral handling that examines `context_injection` regardless of action type, the hooks might work through that path. But based on the kernel contracts, this seems unlikely — the kernel is the hook infrastructure layer.

**How to resolve:** Examine the orchestrator module code and trace how it handles the HookResult returned from `hooks.emit()`.

---

## Unknown 4: Mode Activation's Effect on Hook Registration

**What I couldn't determine:** Whether activating a crew mode causes hooks to be re-registered, or whether hooks are registered once at session start and persist regardless of mode changes.

**Why it matters:** The user reports "sometimes it works only in crew-build mode." If hooks are registered at session initialization (from the mount plan), mode activation shouldn't change hook registration. But if modes trigger re-mounting of modules, hooks could be registered or unregistered dynamically.

**What I know:**
- Hook registration happens in `mount()` which is called during session initialization
- The mode system is provided by `amplifier-bundle-modes` (external, not examined)
- Mode definitions affect tool policies (safe/warn/block) but I couldn't trace whether they affect hook lifecycle

**What I don't know:**
- Does mode activation trigger module re-mounting?
- Does the mode system interact with the hook registry at all?
- Could mode activation change the coordinator's capabilities (e.g., `modes.active`) that the crew-gate hook checks?

**Suspected impact:** If mode activation registers `modes.active` as a capability, the crew-gate hook would detect it and suppress its warnings. If mode activation is purely a context/tool-policy mechanism, the crew-gate hook might not detect mode state correctly (it tries multiple capability names: `modes.active`, `modes.active_mode`, `modes.state`).

**How to resolve:** Examine `amplifier-bundle-modes/modules/hooks-mode` and `tool-mode` to understand how mode state is propagated to coordinator capabilities.

---

## Unknown 5: Recipe Engine's Interaction with Hooks

**What I couldn't determine:** Whether the recipe engine's steps trigger hook events (`tool:post`, `prompt:complete`).

**Why it matters:** The `fidelity-convergence.yaml` recipe uses agents (which spawn child sessions) and bash steps. If recipe-triggered agent delegations emit hook events in the root session, the fidelity dashboard would update during recipe execution. If they don't, the dashboard stays frozen.

**What I know:**
- Recipe steps use `agent:` keys which spawn sub-sessions
- Recipe steps use `type: "bash"` for direct command execution
- The recipe does NOT call `update_fidelity` explicitly
- The recipe extracts scores via bash/python JSON parsing, not via the fidelity tool

**What I don't know:**
- Does the recipe engine emit `tool:post` events when its steps complete?
- Does the recipe engine emit `prompt:complete` between steps?
- Do recipe-spawned agent sessions have access to the root session's FidelityState?

**Suspected impact:** If the recipe engine doesn't emit hook events, the entire fidelity display layer is invisible during recipe execution. The recipe produces convergence but the human sees no dashboard movement.

**How to resolve:** Examine the recipe engine's step execution code and trace event emission.

---

## Unknown 6: Context Window Pressure on Fidelity Instructions

**What I couldn't determine:** Whether context compaction drops the fidelity-critical instructions before they can be followed.

**Why it matters:** The `crew-instructions.md` CRITICAL section (lines 133-196) contains the MANDATORY update_fidelity protocol. If context compaction drops this section during long convergence loops, the LLM loses its instructions mid-loop.

**What I know:**
- The kernel has a `context:pre-compact` event
- Context files are injected into the conversation
- Long convergence loops (up to 8 iterations) with multiple delegations create significant context pressure
- The CRITICAL and EXTREMELY-IMPORTANT tags might help the compaction algorithm preserve these sections — or might not

**What I don't know:**
- What compaction strategy the context manager uses
- Whether context files are treated differently from conversation messages during compaction
- Whether the CRITICAL/EXTREMELY-IMPORTANT tags influence compaction priority
- At what point in a typical convergence loop context pressure becomes relevant

**Suspected impact:** If the mandatory update_fidelity instructions are compacted away mid-loop, the LLM would stop calling `update_fidelity` after later delegations. The dashboard would freeze partway through convergence, giving the appearance that "it worked for a while then stopped."

**How to resolve:** Examine the context manager module and its compaction strategy. Test with long convergence loops and monitor whether CRITICAL-tagged content survives compaction.

---

## Unknown 7: Multiple Coordinator Capability Registration Semantics

**What I couldn't determine:** Whether `register_capability` overwrites or appends when called with the same name twice.

**Why it matters:** If `tool-fidelity-state` mounts twice (due to composition double-declaration), it calls `register_capability("zerovector.fidelity_state", state)` twice with two DIFFERENT `FidelityState` instances. The hook reads the capability to get state.

**What I know:**
- `coordinator.py:242`: `self._capabilities[name] = value` — this is a simple dict assignment
- Dict assignment overwrites the previous value
- So the SECOND registration would overwrite the FIRST
- But the FIRST `UpdateFidelityTool` instance holds a reference to the FIRST `FidelityState`

**What I partially know:**
- If the tool also mounts twice at `coordinator.mount("tools", tool, name="update_fidelity")`, the coordinator logs a warning and replaces
- But the tool's `execute()` method writes to `self.state` — which is the FidelityState instance it was created with

**The scenario (if double-mounting occurs):**
1. First mount: FidelityState(A) created, tool(A) mounts, capability points to A
2. Second mount: FidelityState(B) created, tool(B) replaces tool(A), capability NOW points to B
3. LLM calls `update_fidelity` → tool(B).execute() → writes to B
4. Hook reads capability → gets B → renders B's state ✓

This would actually work correctly because both the capability and the active tool point to B. But:
5. If `zerovector.update_fidelity` capability (the function) was registered for A's `update_fidelity` method, then anything using that capability directly would write to A while the tool writes to B.

**How to resolve:** Test double-mounting of `tool-fidelity-state` and verify that all capability references are consistent. Alternatively, add idempotency checks to `mount()`.

---

## Composition Effects I Suspect But Cannot Confirm

### A. Context Injection Budget Exhaustion
If the `action="inject_context"` fix is applied to both hooks, they would inject context on EVERY `tool:post` and `prompt:complete` event. The coordinator has an injection budget (`injection_budget_per_turn`, default 10,000 tokens). Two hooks × two events per turn × ~500 tokens per injection = ~2,000 tokens per turn. This seems within budget, but with other hooks also injecting, the budget could be exhausted, causing late-firing hooks to be silently rate-limited.

### B. Timing Between Tool:Post and Prompt:Complete
If the orchestrator emits `tool:post` synchronously during the LLM's response generation, and `prompt:complete` after the full response, the fidelity dashboard could render with STALE state on `tool:post` (because `update_fidelity` hasn't been called yet) and then again with CORRECT state on `prompt:complete` (after `update_fidelity` was called). This would produce a "flicker" effect where the dashboard briefly shows old scores then updates.

### C. Race Between Capability Registration and Hook Execution
During session initialization, tools mount before hooks (per `session.py:174-208`). So `tool-fidelity-state` registers its capability before `hooks-fidelity-reporter` tries to read it. This ordering is correct. But if initialization order ever changes, the hook could fire before the capability is registered, returning `_CONTINUE` (no-op) silently.
