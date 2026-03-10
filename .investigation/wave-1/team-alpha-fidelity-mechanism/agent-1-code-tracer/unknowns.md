# Unknowns — Code Tracer
## Team: alpha-fidelity-mechanism | Wave 1

Things I could not confirm from source code, with specific reasons.

---

## UNKNOWN-1: Whether the App Layer Loads Both fidelity.yaml and zerovector-crew.yaml Hooks Sections

**What I found:** Both `behaviors/fidelity.yaml:25-27` and `behaviors/zerovector-crew.yaml:15-16` declare `hooks-fidelity-reporter` directly. The `HookRegistry` has no deduplication.

**What I couldn't confirm:** The app-layer bundle loader that processes the `includes:` directive and assembles the session config from behavior YAMLs is NOT in `amplifier-core`. It lives in the app layer (e.g., `amplifier` CLI, MCP server, or similar). I could not find this code in the workspace.

**Why it matters:** This is the difference between BUG-2 being active (double registration) or theoretical. If the app layer correctly de-duplicates the `hooks:` entries by `module` name before building the session config, double registration does not occur. If it doesn't de-duplicate, it does.

**What I suspect:** The user report of "fires twice" plus git commit `6a0999e` ("transitive include doesn't merge hooks") suggests the double registration is real and has been observed. But I cannot cite the de-duplication code (or lack thereof).

---

## UNKNOWN-2: How Behaviors Are Scoped to Modes

**What I found:** The user reports "only works in crew-build mode." I found the STANDING-ORDER in `bundle.md:14-24` requiring a `/crew-*` mode before artifact creation. I found `hooks-mode` registered in `zerovector-crew.yaml:13-14` (sourced from `amplifier-bundle-modes`). The `CrewGate._is_mode_active()` checks capabilities named `modes.active`, `modes.active_mode`, `modes.state`.

**What I couldn't confirm:** Whether the app layer only activates certain behavior YAML files when a specific mode is active. If behaviors (and their hooks sections) are mode-scoped, then `zerovector-crew.yaml`'s hooks would only be registered when a `/crew-*` mode is set — explaining why fidelity hooks are absent outside crew mode.

**Why it matters:** If this mechanism exists, it fully explains "only works in crew-build mode." Without it, the hooks should always be registered regardless of mode state.

**What I'd check:** The `hooks-mode` module source at `git+https://github.com/microsoft/amplifier-bundle-modes@main#subdirectory=modules/hooks-mode` — this is an external dependency I could not fetch. It likely manages mode activation and potentially gating behavior includes.

---

## UNKNOWN-3: Whether the Orchestrator Calls process_hook_result()

**What I found:** `coordinator.process_hook_result()` exists at `coordinator.py:342` and is designed to route HookResult actions to subsystems (context injection, approval, display). The `AmplifierSession.execute()` at `session.py:260-267` passes `coordinator=self.coordinator` to `orchestrator.execute()`.

**What I couldn't confirm:** Whether the orchestrator (which processes the result of `hooks.emit()`) actually calls `coordinator.process_hook_result()` on the results. The orchestrator module is not in this repo — it's loaded at runtime. If the orchestrator does call `process_hook_result()` on individual handler results (rather than just the merged emit() result), some behaviors might be different. But even so, BUG-1 holds: `process_hook_result()` guards on `action=="inject_context"` at `coordinator.py:361`, same as `emit()`.

**Why it matters:** The `user_message` field processing in `process_hook_result()` at `coordinator.py:368-370` does NOT guard on action — it processes `user_message` regardless. If the orchestrator calls `process_hook_result()` on the merged emit() result, the `user_message` would be routed to the display system (if one is mounted). But the merged result from `emit()` has `user_message=None` (it only preserves data from special actions, not from `continue` results), so this is still a no-op.

---

## UNKNOWN-4: What Fires prompt:complete and Whether It's Used in Production

**What I found:** `prompt:complete` is defined as `PROMPT_COMPLETE = "prompt:complete"` in `events.py:13`. The `hooks-fidelity-reporter` registers a handler for this string. The `HookRegistry` class body does NOT define `PROMPT_COMPLETE` as a class constant (unlike `TOOL_PRE`, `TOOL_POST`, etc. at `hooks.py:43-44`).

**What I couldn't confirm:** Whether the orchestrator actually emits `prompt:complete` during execution. If this event is not emitted by the orchestrator in production, the `prompt:complete` handler never fires. This would explain a partial "sometimes fires" pattern — only `tool:post` fires (after `update_fidelity`), but `prompt:complete` does not.

**Why it matters:** If `prompt:complete` is not emitted, the "fires twice" observation has a different explanation (two `tool:post` firings in a multi-tool turn) vs. one `tool:post` + one `prompt:complete`.

---

## UNKNOWN-5: Full hooks-crew-gate Intended Behavior and Roadmap

**What I found:** Git log shows `1f838c7 docs: add crew-gate roadmap with current state and next phase`. The file `amplifier-roadmap.dot` is untracked. I did not read this file but it likely documents the crew gate's intended integration.

**What I couldn't confirm:** The roadmap for when and how `hooks-crew-gate` will be wired into behaviors. The module is clearly intended to be used (it has substantial implementation and debug logging) but is not yet deployed.

**Why it matters:** The user's "only works in crew-build mode" complaint may be partially what the crew gate is designed to address — enforcing crew mode activation. Understanding the roadmap would clarify whether the current state is intentional incomplete work.

---

## UNKNOWN-6: Whether tool-fidelity-state Can Be Double-Mounted

**What I found:** Both `fidelity.yaml:30-31` and `zerovector-crew.yaml:23-24` declare `tool-fidelity-state`. The `coordinator.mount("tools", tool, name="update_fidelity")` at `coordinator.py:175` would overwrite a previously mounted tool with the same name with a warning (`coordinator.py:161-163`: "Replacing existing {mount_point}"). But tools are a `dict` keyed by name, so the second mount replaces the first.

**What I couldn't confirm:** Whether double-mounting the tool causes any state loss. If both `mount()` calls succeed, the second `FidelityState` instance would be registered as the capability (replacing the first via `self._capabilities[name] = value`), but the hook would be reading the NEW state object while the tool executed previously against the OLD one. This could cause the reporter to show stale/zero data after the second mount.

**Why it matters:** If double-mounting occurs and the capability is replaced, the `hooks-fidelity-reporter` would be reading a fresh `FidelityState` (with empty lens_scores) even after `update_fidelity` has been called on the first state object.

---

## UNKNOWN-7: Does the Critic Actually Call update_fidelity?

**What I found:** `bundle.md:102-105` describes the fidelity behavior wiring the `zerovector:critic` agent with `tool-fidelity-state`. Git commit `9a49682` says "fix: remove phantom update_fidelity instruction from critic (orchestrator handles root session updates)". Git commit `1ed8932` says "fix: enforce mandatory fidelity updates after every agent delegation".

**What I couldn't confirm:** The current state of the `zerovector:critic` agent YAML or system prompt. I did not read `agents/critic.yaml` (or wherever the critic agent is defined). After the commits, it's unclear whether the critic calls `update_fidelity` directly or whether the orchestrator does it on the critic's behalf.

**Why it matters:** If `update_fidelity` is never called (because the critic's instructions were removed and the orchestrator doesn't do it either), `FidelityState.lens_scores` stays empty, the fidelity reporter always returns `_CONTINUE`, and the whole system appears to do nothing — matching the "sometimes skips entirely" report.

---

## UNKNOWN-8: Injection Budget and Whether Ephemeral Would Be Respected

**What I found:** `coordinator.py:109-117` provides `injection_budget_per_turn` (default 10,000 tokens). `coordinator.py:394-409` tracks `_current_turn_injections` and warns if budget exceeded. The `_handle_context_injection` method at `coordinator.py:410-412` skips `context.add_message()` for ephemeral injections but still charges the budget.

**What I couldn't confirm:** Whether the orchestrator calls `coordinator.reset_turn()` at turn boundaries (the method exists at `coordinator.py:338-340`). If `reset_turn()` is never called, the `_current_turn_injections` counter monotonically increases until the budget is hit, at which point ALL context injections would be warned about even in subsequent turns.

**Why it matters:** Even if BUG-1 were fixed, injection budget exhaustion in long sessions could cause the ephemeral fidelity text to be blocked — creating another "sometimes skips" scenario.

---

## Summary Table

| Unknown | Severity | Affects These Symptoms |
|---------|----------|------------------------|
| UNKNOWN-1: Double-loading of behavior hook sections | HIGH | "fires twice" |
| UNKNOWN-2: Mode-scoped behavior activation | HIGH | "only works in crew-build mode" |
| UNKNOWN-3: Orchestrator calling process_hook_result() | MEDIUM | "agent can't act on fidelity" |
| UNKNOWN-4: Whether prompt:complete is emitted | MEDIUM | "fires twice vs once" |
| UNKNOWN-5: Crew gate roadmap | LOW | "only works in crew mode" (future) |
| UNKNOWN-6: Double-mounting tool-fidelity-state | MEDIUM | "skips entirely" (intermittent) |
| UNKNOWN-7: Whether critic calls update_fidelity | HIGH | "sometimes skips entirely", "only picks up intent" |
| UNKNOWN-8: Turn reset for injection budget | LOW | Long-session "skips entirely" |
