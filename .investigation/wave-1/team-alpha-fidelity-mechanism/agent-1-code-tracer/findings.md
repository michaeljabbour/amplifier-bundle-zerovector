# Code Tracer — HOW Agent Findings
## Team: alpha-fidelity-mechanism | Wave 1

**Investigation:** Zerovector fidelity mechanism — inconsistent hook firing behavior  
**Traced by:** agent-1-code-tracer  
**Date:** 2026-03-09

---

## Executive Summary

The fidelity mechanism has **five distinct code-level defects** that together explain every symptom the user reported. The most critical is a silent action mismatch: both hooks return `action="continue"` with `context_injection` set, but the kernel only processes injections when `action="inject_context"`. This means the ephemeral routing advice the agent is supposed to receive **never reaches it** — it is silently discarded on every invocation. The ANSI dashboard is the only output that actually works (because it writes directly to stdout). The remaining bugs cause double-fire, silent failure of the crew gate, and an undeployed module.

---

## 1. Module Architecture Overview

Three Python modules compose the fidelity system. They interact through the kernel's `ModuleCoordinator` capability registry and `HookRegistry`.

### 1.1 tool-fidelity-state
- **Entry point:** `amplifier_module_tool_fidelity_state:mount`
- **Type:** `tool`
- **What it does:** Creates a `FidelityState` dataclass (in-process, Python heap) and an `UpdateFidelityTool` wrapper. Mounts the tool at `coordinator.mount_points["tools"]["update_fidelity"]` and registers three capabilities:
  - `zerovector.fidelity_state` → the `FidelityState` instance
  - `zerovector.update_fidelity` → the `FidelityState.update_fidelity` method
- **Persistence:** In-memory only. Scoped to the `AmplifierSession`. Lost on session end.
- **Config:** Accepts `target` (float, default 0.85) and `domain` (str, default "general") from the behavior YAML config block.

### 1.2 hooks-fidelity-reporter
- **Entry point:** `amplifier_module_hooks_fidelity_reporter:mount`
- **Type:** `hook`
- **Events registered:** `tool:post` and `prompt:complete` (both at priority 50)
- **What it does on each event:**
  1. Calls `coordinator.get_capability("zerovector.fidelity_state")` — if `None`, returns `_CONTINUE`
  2. Calls `fidelity_state.get_state()` — if `lens_scores` empty, returns `_CONTINUE`
  3. Renders ANSI dashboard → writes to `sys.stdout` directly
  4. Renders plain-text ephemeral routing advice
  5. Returns `HookResult(action="continue", context_injection=ephemeral_text, ephemeral=True, user_message=dashboard)`

### 1.3 hooks-crew-gate
- **Entry point:** `amplifier_module_hooks_crew_gate:mount`
- **Type:** `hook`
- **Events registered:** `prompt:complete` (priority 10) and `tool:post` (priority 10)
- **Status: UNTRACKED — not committed, not referenced by any behavior YAML**
- **What it attempts to do:** Detect when no `/crew-*` mode is active and inject a warning. Uses `CrewGate._is_mode_active()` which probes three capability names (`modes.active`, `modes.active_mode`, `modes.state`) and falls back to `getattr(coordinator, "modes", None)`.

---

## 2. Kernel Hook Loading Sequence

**AmplifierSession.initialize()** (`session.py:95-222`) loads modules in this fixed order:
1. Orchestrator (required)
2. Context manager (required)
3. Providers
4. **Tools** ← `tool-fidelity-state` loaded here
5. **Hooks** ← `hooks-fidelity-reporter` and `hooks-crew-gate` loaded here

Each module is loaded via `ModuleLoader.load()` which tries:
1. `ModuleSourceResolver.resolve()` if a resolver is mounted
2. Entry point discovery (`importlib.metadata.entry_points(group="amplifier.modules")`)
3. Filesystem import of `amplifier_module_{module_id_underscored}`

Each module's `mount()` function is called with `(coordinator, config)`. The returned cleanup callable is registered with `coordinator.register_cleanup()`.

**Critical ordering implication:** `tool-fidelity-state` is mounted (registering the `zerovector.fidelity_state` capability) **before** `hooks-fidelity-reporter` is loaded. So by the time the first hook fires, the capability exists — unless the tool mount silently failed.

---

## 3. Hook Dispatch: How emit() Works

`HookRegistry.emit(event, data)` (`hooks.py:111-186`) executes handlers sequentially by priority (lower number = earlier). For each handler result:

| Action | Behavior |
|--------|----------|
| `deny` | Short-circuits immediately, returns that result |
| `modify` | Updates `current_data` passed to subsequent handlers |
| `inject_context` | Collected into `inject_context_results` list for merging |
| `ask_user` | Stored as `special_result` (first one wins) |
| `continue` | **Passes through — context_injection field is IGNORED** |

After all handlers run: if `inject_context_results` is non-empty, merges them into a single result. Otherwise returns `HookResult(action="continue", data=current_data)`.

---

## 4. Bug Catalog

### BUG-1: Action Mismatch — context_injection Never Delivered (CRITICAL)

**Symptom:** Agent never sees fidelity routing advice. Only the terminal ANSI dashboard appears.

**Root cause:** `hooks-fidelity-reporter` returns `HookResult(action="continue", context_injection=..., ephemeral=True)`. The kernel's `emit()` only processes `context_injection` when `action == "inject_context"` (`hooks.py:163`). A `"continue"` result with `context_injection` set is silently ignored — the field is never read.

```python
# hooks.py:162-165
if result.action == "inject_context" and result.context_injection:
    inject_context_results.append(result)
    logger.debug(...)
# If action="continue", this branch is skipped entirely.
```

`coordinator.process_hook_result()` has the identical guard (`coordinator.py:361`):
```python
if result.action == "inject_context" and result.context_injection:
    await self._handle_context_injection(...)
```

**What does work:** The `sys.stdout.write(dashboard)` call at `__init__.py:304` writes the ANSI dashboard directly to stdout, bypassing the kernel entirely. This is why the visual dashboard appears but the agent cannot act on fidelity state.

**Fix:** Change `action="continue"` to `action="inject_context"` in `FidelityReporter.handle_event()` return value (`__init__.py:310`). The `user_message` field IS processed regardless of action by `process_hook_result()` (`coordinator.py:369-370`).

---

### BUG-2: Double Registration — Hook Fires Twice

**Symptom:** Fidelity dashboard renders twice per event.

**Root cause:** Both `behaviors/fidelity.yaml` and `behaviors/zerovector-crew.yaml` declare `hooks-fidelity-reporter` in their `hooks:` section. `HookRegistry.register()` (`hooks.py:85`) simply appends to `self._handlers[event]` with no deduplication check. If both behaviors have their hooks loaded in the same session, two handlers are registered for both `tool:post` and `prompt:complete`.

```yaml
# fidelity.yaml:25-27
hooks:
  - module: hooks-fidelity-reporter
    source: ../modules/hooks-fidelity-reporter

# zerovector-crew.yaml:15-16
  - module: hooks-fidelity-reporter   # ← Second registration
    source: ../modules/hooks-fidelity-reporter
```

Git commit `6a0999e` acknowledged "transitive include doesn't merge hooks" and added the direct declaration to `zerovector-crew.yaml`. But `fidelity.yaml` still declares the hook. If the app layer loads both behaviors' hook sections (e.g., when `fidelity` is used as a standalone behavior AND `zerovector-crew` is also active), two registrations occur.

The `ModuleLoader` caches loaded mount functions at `self._loaded_modules[module_id]` (`loader.py:167-169`), but this cache is keyed by `module_id` string. If the same module_id is loaded twice from the same session's config (because it appears in two behaviors), the cache prevents double-loading of the Python module — but `mount()` is called once per registration entry, so two `mount()` calls → two handler registrations.

---

### BUG-3: Invalid Pydantic Literal — Crew Gate Silently Fails

**Symptom:** Crew gate never shows warnings even when no mode is active.

**Root cause:** `hooks-crew-gate/__init__.py:187` and `:217` both return:
```python
HookResult(..., user_message_level="warn")
```

But `HookResult` is a Pydantic model (`models.py:35`) with:
```python
user_message_level: Literal["info", "warning", "error"] = Field(default="info", ...)
```

`"warn"` is not in the Literal. When `amplifier_core` is installed and the real `HookResult` is used, Pydantic raises `ValidationError` on this field. This exception is caught by the `except Exception` block in both `on_prompt_complete()` (`__init__.py:189-191`) and `on_tool_post()` (`__init__.py:219-221`), which silently return `_CONTINUE`.

Result: The crew gate's warning path **always fails and returns _CONTINUE** when a mode is NOT active — the exact opposite of its intended behavior.

The guard import (`__init__.py:22-36`) provides a dataclass fallback `HookResult` when `amplifier_core` is not installed (test environments). The dataclass has no Pydantic validation, so `"warn"` is accepted in tests — masking the bug entirely from the test suite.

---

### BUG-4: hooks-crew-gate Is Untracked and Never Deployed

**Symptom:** Crew gate has no observable effect.

**Root cause:** Git status shows `?? modules/hooks-crew-gate/`. The module exists on disk but is not committed. Neither `behaviors/fidelity.yaml` nor `behaviors/zerovector-crew.yaml` reference `hooks-crew-gate` in their `hooks:` section. It is never mounted in any session.

Additionally: even if it were mounted, BUG-3 would prevent its warning injection from working.

---

### BUG-5: Fidelity Reporter Fires on Every tool:post, Not Just update_fidelity

**Symptom:** "Sometimes fires twice" — one per tool in multi-tool turns.

**Root cause:** The reporter registers on `tool:post` which fires after **every** tool execution, not just `update_fidelity` calls. In a single LLM turn, if the agent calls two tools, `tool:post` fires twice. Combined with the `prompt:complete` registration, a turn with one tool call produces two hook firings: once after the tool, once when the turn completes.

This is intentional by design (the docstring says "Fires on `tool:post` and `prompt:complete`") but creates confusion when the dashboard renders mid-turn for unrelated tools (e.g., `read_file`, `bash`). The early-exit guards (`_CONTINUE` if no capability or empty lens_scores) prevent noise before `update_fidelity` is ever called.

---

## 5. State Persistence and Sharing

`FidelityState` is a Python dataclass held in memory by `UpdateFidelityTool.state`. The reference chain:

```
coordinator._capabilities["zerovector.fidelity_state"]
    → FidelityState instance (same object)
    ← UpdateFidelityTool.state (same reference)
    ← coordinator._capabilities["zerovector.update_fidelity"] = state.update_fidelity (bound method)
```

When the LLM calls `update_fidelity`, `UpdateFidelityTool.execute()` calls `self.state.update_fidelity()`, mutating the shared `FidelityState` in place. When the hook fires, `coordinator.get_capability("zerovector.fidelity_state")` returns the same object, and `get_state()` returns a dict copy of the current values. No locks, no concurrency protection — but the async orchestration loop is single-threaded so this is safe.

**The reporter and the tool share state via the coordinator capability registry — they do NOT import each other.**

---

## 6. The "Only Picks Up Intent" Scenario

When `update_fidelity` is called with only `intent_clarity` in `lens_scores`:

```python
FidelityState.update_fidelity({"intent_clarity": 0.7})
# → self.lens_scores = {"intent_clarity": 0.7}
# → self.overall = 0.7
# → self.priority_gap = {"lens": "intent_clarity", "score": 0.7, ...}
```

The state is valid but incomplete. When the hook fires, it renders this partial state. The dashboard shows five rows but four of them show `0.00` (defaulted by `lens_scores.get(lens_key, 0.0)` in `render_dashboard`). This looks like "only picks up intent" — the other lenses appear zero.

This happens when the critic calls `update_fidelity` only once with partial scores, or when only one assessment has been made in the convergence loop.

---

## 7. The "Sometimes Skips Entirely" Scenario

`handle_event()` returns `_CONTINUE` (no-op) when either:

1. **Capability not registered:** `coordinator.get_capability("zerovector.fidelity_state")` returns `None`. This happens when `tool-fidelity-state` failed during `mount()`. The mount function wraps both `coordinator.mount()` and `coordinator.register_capability()` calls in `try/except` blocks that silently log at DEBUG level (`__init__.py:174-193`). If the coordinator raises during either call, the capability is never registered, and every subsequent fidelity event silently no-ops.

2. **update_fidelity never called:** `state.get("lens_scores")` is `{}` (falsy). This is the normal initial state before the critic makes its first assessment. The hook skips cleanly until the first `update_fidelity` call.

---

## 8. The "Only Works in Crew-Build Mode" Scenario

This cannot be fully confirmed from the kernel code alone (see unknowns.md), but the most likely mechanism:

The `hooks-fidelity-reporter` is declared in `zerovector-crew.yaml`. If the app layer only activates `zerovector-crew.yaml` when a `/crew-*` mode is active (i.e., behavior files are mode-scoped), then the fidelity hooks would only be mounted during crew sessions. Without a crew mode, `zerovector-crew.yaml`'s hooks section is never loaded, and no fidelity hooks are registered.

The `hooks-crew-gate` module (untracked, BUG-4) was designed to address the inverse: warn when no mode is active. Its broken state (BUG-3 and BUG-4) means it provides no enforcement.

---

## 9. Call Flow Diagram

See `diagram.dot` for the full GraphViz diagram.

### Simplified trace — happy path after update_fidelity called:

```
LLM calls update_fidelity(lens_scores={...})
  → orchestrator emits tool:pre → (no fidelity handlers)
  → UpdateFidelityTool.execute(input)
      → FidelityState.update_fidelity(lens_scores, domain, target)
          → clamps scores, computes overall mean, finds lowest lens
      → returns ToolResult("Fidelity NEEDS_WORK: overall=0.62 target=0.85")
  → orchestrator emits tool:post
      → HookRegistry.emit("tool:post", data)
          → Priority 50: fidelity-reporter-tool:post handler
              → coordinator.get_capability("zerovector.fidelity_state") → FidelityState
              → fidelity_state.get_state() → dict snapshot
              → render_dashboard(state) → ANSI string
              → sys.stdout.write(dashboard)  ← VISIBLE in terminal
              → render_ephemeral(state) → plain text
              → return HookResult(action="continue", context_injection=text, ephemeral=True)
          → emit() sees action="continue" → DROPS context_injection  ← BUG-1
          → emit() returns HookResult(action="continue")
      ← agent NEVER receives ephemeral routing advice
LLM completes turn
  → orchestrator emits prompt:complete
      → HookRegistry.emit("prompt:complete", data)
          → Priority 50: fidelity-reporter-prompt:complete handler
          → (same path as above — fires a second time)
```
