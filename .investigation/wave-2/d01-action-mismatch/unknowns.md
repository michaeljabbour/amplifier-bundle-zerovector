# Unknowns — D-01 Action Mismatch

## What I tried to find but could not locate

### hooks-todo-reminder source code
- **Searched**: `find` over `/Users/michaeljabbour/dev` for `*todo*reminder*` directories
  and `*todo*reminder*` Python files — zero results.
- **Searched**: grep in `amplifier-dev` and `amplifier-collections` for `inject_context` and
  `todo_reminder` — zero matches.
- **What I have instead**: Live runtime evidence. During this investigation session, the
  `hooks-todo-reminder` hook fired and injected a system message into this agent's context
  (visible as `source="hooks-todo-reminder"` in the system reminder). That injection
  demonstrably reached this agent, which proves the `inject_context` + `ephemeral=True`
  pathway is end-to-end functional. The specific file couldn't be traced, but its behavior
  was directly observed.
- **Impact on verdict**: None. The verdict does not depend on seeing the todo-reminder source.
  The runtime observation is stronger evidence than source code alone.

### amplifier-app-cli loop path
- The `amplifier-dev/amplifier_app_cli/` contains an application-level CLI with its own
  session management. I read the loop-streaming orchestrator (the module being used in
  the zerovector bundle) but did not trace whether the app-cli's own session loop has a
  separate hook-result handling path.
- **Risk**: If the app-cli has a custom orchestrator loop that handles `continue` results
  differently (i.e., inspects `context_injection` regardless of action), the bug might be
  partially mitigated in that deployment. This seems unlikely given the consistent pattern
  across all three layers I traced, but cannot be confirmed without reading the app-cli
  session runner.

### prompt:complete event path
- The fidelity reporter registers on both `tool:post` and `prompt:complete`. I traced the
  `tool:post` path exhaustively through loop-streaming. The `prompt:complete` path was not
  separately traced because `prompt:complete` is not emitted by loop-streaming's standard
  iteration loop — it appears to be an app-layer event. If app-layer code calls
  `coordinator.process_hook_result()` on `prompt:complete` results, the same gate-check
  at `coordinator.py:361` applies and the injection is still dropped.

---

## What I suspect but cannot confirm

### Whether `inject_context` was a later addition to the action enum
- The `HookResult.action` field at `models.py:110` is a `Literal` type with five values:
  `continue`, `deny`, `modify`, `inject_context`, `ask_user`. The fidelity reporter's
  module docstring says "never modifies action away from continue," which could mean
  `inject_context` was added to the kernel *after* the fidelity reporter was written,
  leaving the hook's implementation stale.
- **Evidence for this hypothesis**: The module docstring reads like a design principle from
  an earlier era when only `continue` and `deny` existed.
- **Evidence against**: I couldn't find git history for the fidelity reporter or models.py
  within this investigation scope.

### Whether other hooks in the zerovector bundle have the same bug
- `hooks-crew-gate` (the other hook in the bundle) was found at
  `modules/hooks-crew-gate/amplifier_module_hooks_crew_gate/__init__.py` (9,609 bytes).
  I did not read it. If it also returns `action="continue"` with `context_injection`, it
  has the same class of bug.
- **Recommendation for Wave 3**: Audit `hooks-crew-gate` for the same pattern.

---

## Questions raised by this investigation

1. **Why does `HookResult` allow `context_injection` on any action?** The Pydantic model
   does not validate that `context_injection` is only set when `action == "inject_context"`.
   A model-level validator (e.g., `@model_validator`) could raise an error when
   `context_injection` is non-None but `action != "inject_context"`, making this class of
   bug impossible to write silently.

2. **Should `ephemeral` be an action modifier rather than a flag?** Given that `ephemeral`
   only matters when `action == "inject_context"`, having it as a separate bool field
   creates a dependency that is not enforced. An `action="inject_context_ephemeral"` value
   in the Literal would make the pairing explicit.

3. **Is the `user_message` field also affected?** `coordinator.py:369-370` processes
   `user_message` regardless of action — so `user_message` works even with `action="continue"`.
   This means the ANSI dashboard renders in the terminal correctly today, which may have
   hidden the injection bug during development (the hook *appears* to work because the
   dashboard appears, but the agent-facing injection is silently dropped).
