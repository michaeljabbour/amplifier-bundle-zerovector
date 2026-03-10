# Evidence Log — D-01 Action Mismatch

Every claim in findings.md is sourced below. Format: `file:line — what this code shows`.

---

## Claim: `context_injection` is documented as exclusively for `action="inject_context"`

- `amplifier-core/amplifier_core/models.py:128-136` — `context_injection` Field description
  reads: "Text to inject into agent's conversation context **(for action='inject_context')**."
  The parenthetical is not a suggestion — it is the normative statement of the field's
  activation condition.

- `amplifier-core/amplifier_core/models.py:212-220` — `append_to_last_tool_result` field
  description: "Only applicable when **action='inject_context' and ephemeral=True**." Confirms
  that the entire ephemeral injection pathway is gated on `inject_context`.

- `amplifier-core/amplifier_core/models.py:145-152` — `ephemeral` field description: "If True,
  injection is temporary... **Orchestrator must append ephemeral injection to messages without
  storing in context.**" The word "must" establishes a contract — but the orchestrator only
  honors this contract when `action == "inject_context"`.

---

## Claim: `HookRegistry.emit()` silently drops `context_injection` on `action="continue"` results

- `amplifier-core/amplifier_core/hooks.py:162-165` — The injection collection block:
  ```python
  # Collect inject_context actions for merging
  if result.action == "inject_context" and result.context_injection:
      inject_context_results.append(result)
  ```
  A `continue` result with `context_injection` set does not enter this block. The list
  `inject_context_results` remains empty.

- `amplifier-core/amplifier_core/hooks.py:176-186` — After all handlers run:
  ```python
  if inject_context_results:
      special_result = self._merge_inject_context_results(inject_context_results)
  if special_result:
      return special_result
  return HookResult(action="continue", data=current_data)
  ```
  Because `inject_context_results` is empty, `special_result` is never set from the injection
  path. The method returns a bare `HookResult(action="continue")` — all fields from the
  original hook result (`context_injection`, `ephemeral`, `user_message`) are gone.

- `amplifier-core/amplifier_core/hooks.py:141-143` — Comment confirms intent:
  "Collect ALL inject_context results to merge them." The design is explicit that only
  `inject_context` results are tracked. `continue` results are not tracked at all.

---

## Claim: `coordinator.process_hook_result()` also gate-checks action before routing injection

- `amplifier-core/amplifier_core/coordinator.py:360-362` — First branch:
  ```python
  # 1. Handle context injection
  if result.action == "inject_context" and result.context_injection:
      await self._handle_context_injection(result, hook_name, event)
  ```
  Even if `emit()` were to pass through the original `continue` result (e.g. in a code path
  where `emit()` is bypassed), `process_hook_result` would still not call
  `_handle_context_injection`.

- `amplifier-core/amplifier_core/coordinator.py:368-370` — By contrast, `user_message` IS
  processed regardless of action:
  ```python
  # 3. Handle user message (separate from context injection)
  if result.user_message:
      self._handle_user_message(result, hook_name)
  ```
  This explains why the ANSI dashboard display partially works (user_message renders) but
  the agent-facing `context_injection` does not.

- `amplifier-core/amplifier_core/coordinator.py:411-412` — Inside
  `_handle_context_injection()`: "Add to context with provenance (ONLY if not ephemeral)".
  Confirms ephemeral injections are handled specially *within* the function — they skip
  `context.add_message` but are still counted against the budget. This code is never reached
  for the fidelity reporter because the function is never called.

---

## Claim: loop-streaming orchestrator gate-checks action in both injection paths

### Path 1 — provider:request event (ephemeral injection before next LLM call)

- `amplifier-module-loop-streaming/.../amplifier_module_loop_streaming/__init__.py:222-226`:
  ```python
  if (
      result.action == "inject_context"
      and result.ephemeral
      and result.context_injection
  ):
  ```
  The orchestrator only appends the ephemeral injection to `message_dicts` (the messages
  sent to the LLM) when all three conditions are true. A `continue` result never satisfies
  the first condition.

### Path 2 — tool:post event (stores ephemeral injection for next iteration)

- `amplifier-module-loop-streaming/.../amplifier_module_loop_streaming/__init__.py:846-857`:
  ```python
  if (
      post_result.action == "inject_context"
      and post_result.ephemeral
      and post_result.context_injection
  ):
      self._pending_ephemeral_injections.append(...)
  ```
  Same gate-check. Fidelity reporter fires on `tool:post` — this is the exact path that
  would deliver its routing advice. The `_pending_ephemeral_injections` list is never
  populated because `post_result.action` is `"continue"`.

- `amplifier-module-loop-streaming/.../amplifier_module_loop_streaming/__init__.py:71-73`:
  ```python
  # Store ephemeral injections from tool:post hooks for next iteration
  self._pending_ephemeral_injections: list[dict[str, Any]] = []
  ```
  The field is initialized empty and only populated at lines 846-857. Since the condition
  is never met, the agent loop proceeds every iteration with no fidelity routing advice.

---

## Claim: The fidelity reporter deliberately used `action="continue"` and documented it as intentional

- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:14`:
  ```
  Non-blocking observer: never modifies ``action`` away from ``continue``.
  ```
  This is in the module-level docstring — the first substantive documentation a reader sees.
  It is a stated design principle, not a comment about a temporary state or known bug.

- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:49-50`:
  ```python
  # Continue-only sentinel — avoids re-allocating on every no-op event.
  _CONTINUE = HookResult(action="continue")
  ```
  The sentinel reinforces the `continue`-only pattern.

- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:310-317`:
  The actual broken return:
  ```python
  return HookResult(
      action="continue",           # ← the bug
      context_injection=ephemeral_text,
      context_injection_role="system",
      ephemeral=True,
      user_message=dashboard,
      user_message_level="info",
  )
  ```
  `context_injection` and `ephemeral=True` are populated — the intent to inject is clear.
  But `action="continue"` means every layer of the kernel ignores those fields.

---

## Claim: The todo reminder hook (in-session proof) shows inject_context works correctly

- **Live runtime evidence**: The `hooks-todo-reminder` hook fired during this investigation
  session and injected a system message visible in this agent's context, prefixed with
  `source="hooks-todo-reminder"`. This hook uses `action="inject_context"` with
  `ephemeral=True`, and the injection reached this agent. This is direct runtime confirmation
  that the `inject_context` pathway functions end-to-end. The fidelity reporter's identical
  intent (ephemeral context injection) fails only because it uses the wrong action.

---

## Claim: `inject_context` is non-blocking — Position B is factually wrong

- `amplifier-core/amplifier_core/hooks.py:154-156` — Only `deny` short-circuits:
  ```python
  if result.action == "deny":
      logger.info(...)
      return result
  ```
  `inject_context` does NOT short-circuit the handler chain. Handlers after an
  `inject_context` result continue to execute. The action is non-blocking by design.

- `amplifier-core/amplifier_core/hooks.py:162-165` — `inject_context` results are *collected*
  into a list; all handlers still run. Multiple hooks returning `inject_context` have their
  injections merged at line 178 via `_merge_inject_context_results`. This is additive, not
  disruptive.

---

## Claim: The fix is a single-line change to the action field

- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:311`:
  Change `action="continue"` → `action="inject_context"`.

- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:296`:
  The early-return `_CONTINUE` sentinel should stay `action="continue"` (no injection wanted).

- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:300`:
  Same — early-return no-op sentinel stays as-is.

Only the full return at line 310 needs to change. The two early-returns are semantically
correct: they signal "nothing to contribute" and should remain `continue`.
