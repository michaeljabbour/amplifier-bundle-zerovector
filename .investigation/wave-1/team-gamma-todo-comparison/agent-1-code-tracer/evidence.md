# Evidence — Code Tracer (agent-1-code-tracer)

File:line citations for every claim in findings.md.

---

## Claim: Todo tool is NOT in amplifier-core

- `amplifier-core/amplifier_core/models.py:148` — The word "todo" appears only in documentation of the `ephemeral` field: *"Use for transient state like todo reminders that update frequently."* No todo tool implementation in the kernel.
- `amplifier-core/amplifier_core/session.py:1-289` — Session initialization loads orchestrator, context, providers, tools, and hooks from config. No built-in tool named "todo." Tools come from the `tools:` mount plan section.
- `amplifier-core/amplifier_core/coordinator.py:67-74` — Mount points: `orchestrator`, `providers`, `tools`, `context`, `hooks`, `module-source-resolver`. No special "todo" mount point.

---

## Claim: Todo is an external module pair declared in foundation base profile

- `amplifierd/registry/profiles/foundation/base.md:36-37` — `tool-todo` included as a standard tool:
  ```yaml
  - module: tool-todo
    source: git+https://github.com/microsoft/amplifier-module-tool-todo@main
  ```
- `amplifierd/registry/profiles/foundation/base.md:57-61` — `hooks-todo-reminder` included as a standard hook:
  ```yaml
  - module: hooks-todo-reminder
    source: git+https://github.com/microsoft/amplifier-module-hooks-todo-reminder@main
    config:
      inject_role: user
      priority: 10
  ```
- `amplifier-foundation/behaviors/todo-reminder.yaml:1-14` — The behavior YAML that groups them:
  ```yaml
  tools:
    - module: tool-todo
      source: git+https://github.com/microsoft/amplifier-module-tool-todo@main
  hooks:
    - module: hooks-todo-reminder
      source: git+https://github.com/microsoft/amplifier-module-hooks-todo-reminder@main
      config:
        inject_role: user
        priority: 10
  ```

---

## Claim: Zerovector bundle inherits foundation, so todo is always present in zerovector sessions

- `amplifier-bundle-zerovector/bundle.md:7-9` — Includes foundation bundle:
  ```yaml
  includes:
    - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  ```
  Since foundation includes the base profile (which includes tool-todo + hooks-todo-reminder), zerovector sessions inherit both.

---

## Claim: hooks-todo-reminder triggers on provider:request

- `amplifier-docs/docs/modules/hooks/todo_reminder.md:36-42` — Documented behavior:
  > 2. **Triggers** on `provider:request` event (before each LLM call)
  > 3. **Checks** for `coordinator.todo_state` (populated by tool-todo)
  > 4. **Generates adaptive reminder**
- `amplifier-core/amplifier_core/events.py:20` — `PROVIDER_REQUEST = "provider:request"` is the canonical event constant

---

## Claim: provider:request fires at the top of every orchestrator iteration

- `amplifier-module-loop-streaming/amplifier_module_loop_streaming/__init__.py:204-214` — Inside the main `while` loop:
  ```python
  # Emit provider request BEFORE getting messages (allows hook injections)
  result = await hooks.emit(
      PROVIDER_REQUEST, {"provider": provider_name, "iteration": iteration}
  )
  if coordinator:
      result = await coordinator.process_hook_result(
          result, "provider:request", "orchestrator"
      )
  ```
- `amplifier-module-loop-streaming/amplifier_module_loop_streaming/__init__.py:196` — The outer loop: `while self.max_iterations == -1 or iteration < self.max_iterations:`

---

## Claim: Orchestrator appends ephemeral injection to message list BEFORE LLM call

- `amplifier-module-loop-streaming/amplifier_module_loop_streaming/__init__.py:216-260` — After `get_messages_for_request()`, before `provider.complete()`:
  ```python
  # Append ephemeral injection if present (temporary, not stored)
  if (
      result.action == "inject_context"
      and result.ephemeral
      and result.context_injection
  ):
      if result.append_to_last_tool_result and len(message_dicts) > 0:
          last_msg = message_dicts[-1]
          if last_msg.get("role") == "tool":
              message_dicts[-1] = {
                  **last_msg,
                  "content": f"{original_content}\n\n{result.context_injection}",
              }
      else:
          message_dicts.append({"role": ..., "content": result.context_injection})
  ```
- `amplifier-module-loop-streaming/amplifier_module_loop_streaming/__init__.py:314` — LLM call happens after: `chat_request = ChatRequest(messages=messages_objects, tools=tools_list)` then `provider.complete(chat_request, ...)`

---

## Claim: ephemeral=True prevents storage in context history

- `amplifier-core/amplifier_core/models.py:145-151` — HookResult field definition:
  ```python
  ephemeral: bool = Field(
      default=False,
      description=(
          "If True, injection is temporary (only for current LLM call, not stored in history). "
          "Use for transient state like todo reminders that update frequently. "
          ...
      ),
  )
  ```
- `amplifier-core/amplifier_core/coordinator.py:411-426` — `_handle_context_injection` only calls `context.add_message()` when NOT ephemeral:
  ```python
  # 3. Add to context with provenance (ONLY if not ephemeral)
  if not result.ephemeral:
      context = self.mount_points["context"]
      if context and hasattr(context, "add_message"):
          message = {"role": result.context_injection_role, "content": content, ...}
          await context.add_message(message)
  ```

---

## Claim: inject_context action enables hook-to-LLM feedback loops

- `amplifier-core/amplifier_core/models.py:109-117` — HookResult action literal includes `"inject_context"`:
  ```python
  action: Literal["continue", "deny", "modify", "inject_context", "ask_user"]
  ```
- `amplifier-core/amplifier_core/models.py:46-49` — Docstring: *"inject_context: Add content to agent's context (enables feedback loops)"*
- `amplifier-core/amplifier_core/hooks.py:162-165` — Hook registry collects all `inject_context` results and merges them:
  ```python
  if result.action == "inject_context" and result.context_injection:
      inject_context_results.append(result)
  ```
- `amplifier-core/amplifier_core/hooks.py:176-179` — Merges multiple inject_context results if >1 hook returns them

---

## Claim: hooks-todo-reminder also reads recent tool usage to adapt its message

- `amplifier-docs/docs/modules/hooks/todo_reminder.md:36` — *"1. Tracks tool usage via `tool:post` events"*
- `amplifier-docs/docs/modules/hooks/todo_reminder.md:32` — Configuration: `recent_tool_threshold: 3` — number of recent tool calls to check for todo usage

---

## Claim: tool:post ephemeral injections are stored for the NEXT iteration

- `amplifier-module-loop-streaming/amplifier_module_loop_streaming/__init__.py:72-73` — Instance variable: `self._pending_ephemeral_injections: list[dict[str, Any]] = []`
- `amplifier-module-loop-streaming/amplifier_module_loop_streaming/__init__.py:844-860` — In `_execute_tool_only()`, after tool:post fires:
  ```python
  # Store ephemeral injection from tool:post for next iteration
  if (
      post_result.action == "inject_context"
      and post_result.ephemeral
      and post_result.context_injection
  ):
      self._pending_ephemeral_injections.append({
          "role": post_result.context_injection_role,
          "content": post_result.context_injection,
          "append_to_last_tool_result": post_result.append_to_last_tool_result,
      })
  ```
- `amplifier-module-loop-streaming/amplifier_module_loop_streaming/__init__.py:263-297` — Applied at start of next iteration, before LLM call; then `self._pending_ephemeral_injections = []`

---

## Claim: hooks-todo-reminder fires even when state is empty (nudge behavior)

- `amplifier-docs/docs/modules/hooks/todo_reminder.md:46-58` — Injection format for "when todo tool not used recently" shows an active reminder with content. The hook always produces output — it doesn't silently return `_CONTINUE`.
- `amplifier-docs/docs/modules/hooks/todo_reminder.md:97-101` — Key features listed: *"Graceful degradation — Failures don't crash session"* — note: graceful degradation handles failures, NOT empty state. Empty state still triggers nudge.

---

## Claim: fidelity tool stores state via capability registration (not coordinator attribute)

- `amplifier-bundle-zerovector/modules/tool-fidelity-state/amplifier_module_tool_fidelity_state/__init__.py:180` — Mount function:
  ```python
  coordinator.register_capability("zerovector.fidelity_state", state)
  ```
- `amplifier-bundle-zerovector/modules/tool-fidelity-state/amplifier_module_tool_fidelity_state/__init__.py:187-193` — Also registers the update function as a capability:
  ```python
  coordinator.register_capability("zerovector.update_fidelity", state.update_fidelity)
  ```

---

## Claim: hooks-fidelity-reporter fires on tool:post and prompt:complete (NOT provider:request)

- `amplifier-bundle-zerovector/modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:355-358` — Mount function registers on:
  ```python
  for event_name, handler in [
      ("tool:post", _on_tool_post),
      ("prompt:complete", _on_prompt_complete),
  ]:
  ```
- `amplifier-bundle-zerovector/modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:1-4` — Module docstring confirms: *"Fires on `tool:post` and `prompt:complete`."*

---

## Claim: fidelity reporter silently does nothing if state has no lens scores

- `amplifier-bundle-zerovector/modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:293-300` — In `handle_event()`:
  ```python
  fidelity_state = coordinator.get_capability("zerovector.fidelity_state")
  if fidelity_state is None:
      return _CONTINUE
  
  state = fidelity_state.get_state()
  if not state.get("lens_scores"):
      return _CONTINUE
  ```
- `amplifier-bundle-zerovector/modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:49-50` — `_CONTINUE = HookResult(action="continue")` — the no-op sentinel

---

## Claim: fidelity tool only writes state when update_fidelity is called explicitly

- `amplifier-bundle-zerovector/modules/tool-fidelity-state/amplifier_module_tool_fidelity_state/__init__.py:59-94` — `FidelityState.update_fidelity()` is the only mutation path; initial state has `lens_scores: {}` (empty dict)
- `amplifier-bundle-zerovector/modules/tool-fidelity-state/amplifier_module_tool_fidelity_state/__init__.py:141-159` — `UpdateFidelityTool.execute()` calls `self.state.update_fidelity(lens_scores, ...)` — this is the only way to populate lens scores

---

## Claim: fidelity behavior is NOT in the base profile — requires opt-in

- `amplifierd/registry/profiles/foundation/base.md:1-70` — Full base profile listing: no mention of `tool-fidelity-state`, `hooks-fidelity-reporter`, or zerovector fidelity behavior
- `amplifier-bundle-zerovector/behaviors/fidelity.yaml:25-32` — The fidelity behavior must be explicitly included:
  ```yaml
  hooks:
    - module: hooks-fidelity-reporter
      source: ../modules/hooks-fidelity-reporter
  tools:
    - module: tool-fidelity-state
      source: ../modules/tool-fidelity-state
  ```

---

## Claim: PROVIDER_REQUEST is defined as a canonical event constant

- `amplifier-core/amplifier_core/events.py:20` — `PROVIDER_REQUEST = "provider:request"`
- `amplifier-core/amplifier_core/events.py:62-95` — Listed in `ALL_EVENTS` as a canonical kernel event

---

## Claim: HookRegistry merges multiple inject_context results

- `amplifier-core/amplifier_core/hooks.py:176-179` — If >1 hook returns inject_context:
  ```python
  if inject_context_results:
      special_result = self._merge_inject_context_results(inject_context_results)
  ```
- `amplifier-core/amplifier_core/hooks.py:188-219` — `_merge_inject_context_results()` concatenates all injections with `\n\n` separator

---

## Claim: hooks-todo-display (archived) also confirms the tool:post tracking pattern

- `_audit/amplifier-foundation-main/modules/hooks-todo-display/amplifier_module_hooks_todo_display/__init__.py:85-96` — `handle_tool_pre()` checks if tool_name == "todo", captures `todos` from input
- `_audit/amplifier-foundation-main/modules/hooks-todo-display/amplifier_module_hooks_todo_display/__init__.py:98-120` — `handle_tool_post()` renders visual display when todo tool returns success
- `_audit/amplifier-foundation-main/modules/hooks-todo-display/amplifier_module_hooks_todo_display/__init__.py:342-345` — Registered on `tool:pre` and `tool:post` at priority 5

---

## Live Evidence: System Reminders Observed During Investigation

During this investigation, the `hooks-todo-reminder` mechanism fired **multiple times**, injecting `<system-reminder>` blocks with:
1. A nudge when todo tool hadn't been used recently
2. The current todo list with status symbols (✓ completed, → in_progress, ☐ pending)
3. The content appended after tool results (append_to_last_tool_result=True path)

This is direct, empirical confirmation that the traced code path is live and functional. The investigation itself is evidence.
