# Evidence: D-04 `prompt:complete` Emission & CU-1 Ephemeral Drop

All claims backed by specific file:line citations from primary source code.

---

## Claim: `prompt:complete` constant is defined but not emitted by the orchestrator

### `PROMPT_COMPLETE` constant defined at
- `amplifier_core/amplifier_core/events.py:13` — `PROMPT_COMPLETE = "prompt:complete"`
- `amplifier_core/amplifier_core/events.py:68` — included in `ALL_EVENTS` list

### `prompt:complete` is NOT in the orchestrator's import list
- `amplifier_module_loop_streaming/amplifier_module_loop_streaming/__init__.py:19-29` — imports from `amplifier_core.events` include `CONTENT_BLOCK_END`, `CONTENT_BLOCK_START`, `ORCHESTRATOR_COMPLETE`, `PROMPT_SUBMIT`, `PROVIDER_REQUEST`, `TOOL_ERROR`, `TOOL_POST`, `TOOL_PRE` — `PROMPT_COMPLETE` is absent

### `prompt:complete` search across amplifier-core yields only definition + test
- `amplifier_core/amplifier_core/events.py` — constant definition only
- `amplifier_core/tests/test_events_smoke.py` — smoke test only

---

## Claim: `prompt:complete` IS emitted — by the app layer (main.py), not the orchestrator

### Emission site 1 — interactive REPL path
- `amplifier_app_cli/amplifier_app_cli/main.py:1623` — comment: `# Emit prompt:complete event`
- `amplifier_app_cli/amplifier_app_cli/main.py:1624` — `hooks = session.coordinator.get("hooks")`
- `amplifier_app_cli/amplifier_app_cli/main.py:1626` — `from amplifier_core.events import PROMPT_COMPLETE`
- `amplifier_app_cli/amplifier_app_cli/main.py:1628-1635` — `await hooks.emit(PROMPT_COMPLETE, {"prompt": prompt_text, "response": response, "session_id": actual_session_id})`
- Context: called inside `_execute_with_interrupt()` after `response = await execute_task` — after `session.execute()` has fully returned

### Emission site 2 — one-shot CLI `run` command path
- `amplifier_app_cli/amplifier_app_cli/main.py:1867` — comment: `# Emit prompt:complete (canonical kernel event) BEFORE formatting output`
- `amplifier_app_cli/amplifier_app_cli/main.py:1869` — `hooks = session.coordinator.get("hooks")`
- `amplifier_app_cli/amplifier_app_cli/main.py:1871` — `from amplifier_core.events import PROMPT_COMPLETE`
- `amplifier_app_cli/amplifier_app_cli/main.py:1873-1880` — `await hooks.emit(PROMPT_COMPLETE, {"prompt": prompt, "response": response, "session_id": actual_session_id})`
- Context: called after `response = await session.execute(prompt)` — after the orchestrator has fully returned

### Critically: both sites DISCARD the hook return value
- `amplifier_app_cli/amplifier_app_cli/main.py:1628` — `await hooks.emit(...)` — return value not assigned, not processed
- `amplifier_app_cli/amplifier_app_cli/main.py:1873` — `await hooks.emit(...)` — return value not assigned, not processed
- Contrast: `loop-streaming/__init__.py:205` — `result = await hooks.emit(PROVIDER_REQUEST, ...)` — return value IS captured and processed

---

## Claim: `action="continue"` with `context_injection` is silently dropped at `hooks.emit()` level

### The fidelity reporter returns `action="continue"` with `context_injection`
- `amplifier_module_hooks_fidelity_reporter/__init__.py:310-317` — `return HookResult(action="continue", context_injection=ephemeral_text, context_injection_role="system", ephemeral=True, user_message=dashboard, user_message_level="info")`

### `hooks.emit()` only collects `inject_context` results — not `continue`
- `amplifier_core/amplifier_core/hooks.py:162-165` —
  ```python
  if result.action == "inject_context" and result.context_injection:
      inject_context_results.append(result)
  ```
  Since fidelity reporter uses `action="continue"`, this condition is False. The `context_injection` value on the returned HookResult is **never added to `inject_context_results`**.

### `hooks.emit()` returns `HookResult(action="continue")` with no injection
- `amplifier_core/amplifier_core/hooks.py:182-186` — `if special_result: return special_result` — `special_result` is None because no `inject_context` was collected; falls through to `return HookResult(action="continue", data=current_data)` with no `context_injection`

### Secondary drop: orchestrator `tool:post` ephemeral check also guards on `action`
- `amplifier_module_loop_streaming/amplifier_module_loop_streaming/__init__.py:846-857` —
  ```python
  if (
      post_result.action == "inject_context"
      and post_result.ephemeral
      and post_result.context_injection
  ):
      self._pending_ephemeral_injections.append(...)
  ```
  Even if `hooks.emit()` returned the injection, the orchestrator also requires `action == "inject_context"`.

### Tertiary drop: coordinator also guards on `action`
- `amplifier_core/amplifier_core/coordinator.py:361` — `if result.action == "inject_context" and result.context_injection:` — coordinator requires `action == "inject_context"` to route to `_handle_context_injection`

---

## Claim: Gamma team's `loop-streaming/__init__.py:216-260` check is real (minor line correction)

### The actual ephemeral-injection block
- `amplifier_module_loop_streaming/amplifier_module_loop_streaming/__init__.py:222-260` — the check:
  ```python
  if (
      result.action == "inject_context"
      and result.ephemeral
      and result.context_injection
  ):
  ```
  This applies to the `PROVIDER_REQUEST` hook result (not `TOOL_POST`). Lines 216–221 are about `get_messages_for_request()`, not the injection check. The block starts at line 222.

### The block correctly handles ephemeral injection from `provider:request` hooks
- `amplifier_module_loop_streaming/amplifier_module_loop_streaming/__init__.py:228-260` — checks `append_to_last_tool_result`; either appends to last tool message or creates new message with `context_injection_role`

---

## Claim: The orchestrator emits `PROVIDER_REQUEST` (and hooks-todo-reminder fires on it)

### `PROVIDER_REQUEST` emission site (normal iteration path)
- `amplifier_module_loop_streaming/amplifier_module_loop_streaming/__init__.py:204-214` —
  ```python
  result = await hooks.emit(
      PROVIDER_REQUEST, {"provider": provider_name, "iteration": iteration}
  )
  if coordinator:
      result = await coordinator.process_hook_result(
          result, "provider:request", "orchestrator"
      )
  ```
  Result IS captured and processed — enables context injection.

### `PROVIDER_REQUEST` emission site (max iterations path)
- `amplifier_module_loop_streaming/amplifier_module_loop_streaming/__init__.py:604-611` — additional emission when `max_iterations` reached

### `provider:request` import in loop-streaming confirms intentional use
- `amplifier_module_loop_streaming/amplifier_module_loop_streaming/__init__.py:23` — `from amplifier_core.events import PROVIDER_REQUEST`

### `hooks-todo-reminder` fires on `provider:request`
- Confirmed by live execution: the hooks-todo-reminder hook fired during this investigation session, delivering its reminder via the `provider:request` event before an LLM call — directly demonstrating the mechanism works
- The system reminder content references todo tracking, delivered at iteration boundary before provider call — consistent with `provider:request` trigger

---

## Claim: All orchestrator events — complete inventory

### All `hooks.emit()` calls in `loop-streaming/__init__.py`
- Line 96: `orchestrator:rate_limit_delay` (non-standard, rate limiting only)
- Line 138: `ORCHESTRATOR_COMPLETE` = `"orchestrator:complete"`
- Line 163: `PROMPT_SUBMIT` = `"prompt:submit"` (result processed by coordinator)
- Line 173: `"session:start"` (string literal, result not captured)
- Line 205: `PROVIDER_REQUEST` = `"provider:request"` (result captured + coordinator-processed)
- Line 604: `PROVIDER_REQUEST` again (max_iterations path, result not captured here)
- Line 668: `"session:end"` (string literal, result not captured)
- Line 777: `TOOL_PRE` = `"tool:pre"` (result captured + coordinator-processed, deny supported)
- Line 797: `TOOL_ERROR` = `"tool:error"` (result not captured)
- Line 830: `TOOL_POST` = `"tool:post"` (result captured + coordinator-processed)
- Line 364: `CONTENT_BLOCK_START` = `"content_block:start"` (result not captured)
- Line 382: `CONTENT_BLOCK_END` = `"content_block:end"` (result not captured)
- Line 870: `TOOL_ERROR` again (safety-net path)
- Line 898: `TOOL_PRE` again (legacy `_execute_tool_with_result` path)
- Line 948: `TOOL_POST` again (legacy path)

### `PROMPT_COMPLETE` is absent from all loop-streaming emit calls
- Search of `amplifier_module_loop_streaming/amplifier_module_loop_streaming/__init__.py` for `PROMPT_COMPLETE` or `"prompt:complete"`: **zero matches**

---

## Claim: `prompt:complete` hook result is fire-and-forget — cannot deliver injection

### main.py REPL path — no coordinator.process_hook_result call
- `amplifier_app_cli/amplifier_app_cli/main.py:1628-1635` — bare `await hooks.emit(...)` with no result capture, no `coordinator.process_hook_result()` call anywhere in the surrounding code block

### main.py one-shot path — no coordinator.process_hook_result call  
- `amplifier_app_cli/amplifier_app_cli/main.py:1873-1880` — bare `await hooks.emit(...)` with no result capture, no `coordinator.process_hook_result()` call

### Contrast: events that DO process results
- `loop-streaming/__init__.py:163-167` — `prompt:submit`: result captured AND `coordinator.process_hook_result()` called
- `loop-streaming/__init__.py:205-214` — `provider:request`: result captured AND `coordinator.process_hook_result()` called
- `loop-streaming/__init__.py:777-791` — `tool:pre`: result captured AND `coordinator.process_hook_result()` called, deny supported
- `loop-streaming/__init__.py:830-843` — `tool:post`: result captured AND `coordinator.process_hook_result()` called

---

## Claim: The fidelity reporter registers on both `tool:post` and `prompt:complete`

### Registration code
- `amplifier_module_hooks_fidelity_reporter/__init__.py:355-358` —
  ```python
  for event_name, handler in [
      ("tool:post", _on_tool_post),
      ("prompt:complete", _on_prompt_complete),
  ]:
  ```
- `amplifier_module_hooks_fidelity_reporter/__init__.py:360-366` — `coordinator.hooks.register(event_name, handler, priority=priority, name=...)`

### The two handlers are identical — both call `reporter.handle_event()`
- `amplifier_module_hooks_fidelity_reporter/__init__.py:349-353` — `_on_tool_post` and `_on_prompt_complete` both delegate to `reporter.handle_event(event, data, coordinator)`

### `handle_event` always returns `action="continue"` — the bug
- `amplifier_module_hooks_fidelity_reporter/__init__.py:310-317` — `HookResult(action="continue", context_injection=ephemeral_text, ...)` — uses `"continue"` not `"inject_context"`
