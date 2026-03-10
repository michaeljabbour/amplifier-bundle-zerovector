# Code Tracer — HOW the Todo Tool Achieves Reliable Invocation

**Agent:** agent-1-code-tracer  
**Investigation:** team-gamma-todo-comparison  
**Focus:** HOW does the todo tool achieve reliable, consistent invocation across all sessions?

---

## Executive Summary

The todo tool's reliability is **not an accident** — it is the result of a precise architectural pattern: a **mandatory two-part module pair** deployed at the kernel level, with one part (`tool-todo`) storing state in-session and the other (`hooks-todo-reminder`) injecting that state ephemerally into **every single LLM call** via the `provider:request` event. The fidelity tool lacks the second part, making it invisible unless explicitly invoked.

**I witnessed this mechanism firing live** during this investigation: between every tool call, `hooks-todo-reminder` emitted a `<system-reminder>` block with the current todo list, injected as an ephemeral `user`-role message appended to the last tool result. The injection is never stored in conversation history, yet the LLM sees it before every call.

---

## 1. Where Is the Todo Tool Defined?

The todo tool is **not built into amplifier-core**. It is an external module:

- **Tool module:** `tool-todo` — `git+https://github.com/microsoft/amplifier-module-tool-todo@main`
- **Reminder hook:** `hooks-todo-reminder` — `git+https://github.com/microsoft/amplifier-module-hooks-todo-reminder@main`

Both are declared together as a behavior unit in:
- `amplifier-foundation/behaviors/todo-reminder.yaml` — the behavior YAML that pairs them

They are included in the **foundation base profile** (`amplifierd/registry/profiles/foundation/base.md`, lines 36-61), meaning every session that uses any standard foundation profile automatically gets both modules mounted. This is why todo is "always available" regardless of mode or bundle — it is wired into the base mount plan, not the user's bundle.

The module type marker is `__amplifier_module_type__ = "tool"` (consistent with other tool modules). The tool exposes three actions: `create`, `update`, `list`.

---

## 2. State Persistence

The todo tool uses **in-memory session-level state**. Per the `hooks-todo-reminder` documentation:

> Checks for `coordinator.todo_state` (populated by tool-todo)

The state is held in the `ModuleCoordinator` instance (session-scoped), meaning:
- **Session-scoped**: todos exist only for the duration of the current session  
- **Not file-based**: no disk writes
- **Not cross-session**: every new session starts with no todos
- The hook reads state directly from the coordinator object, not from a capability registration

This is the simplest possible state model. The data is transient by design — the `hooks-todo-reminder` documentation explicitly says "Session-scoped — Todos live only during current session."

---

## 3. The Injection Mechanism: provider:request → ephemeral inject_context

This is the architectural core. The complete flow:

### 3a. Event Trigger

`hooks-todo-reminder` registers on the `provider:request` event (`loop-streaming/__init__.py:206`). This event fires **at the top of every orchestrator iteration**, before the message list is built for the LLM call.

The orchestrator loop at `loop-streaming/__init__.py:196-314`:
```
while max_iterations == -1 or iteration < max_iterations:
    iteration += 1
    
    # STEP 1: Fire provider:request → hooks get their chance to inject
    result = await hooks.emit(PROVIDER_REQUEST, {...})
    if coordinator:
        result = await coordinator.process_hook_result(result, "provider:request", ...)
    
    # STEP 2: Get messages (doesn't include ephemeral injections yet)
    message_dicts = await context.get_messages_for_request(provider=provider)
    
    # STEP 3: Append ephemeral injection BEFORE sending to LLM
    if result.action == "inject_context" and result.ephemeral and result.context_injection:
        # append to last tool result OR as new message
        message_dicts.append({...})
    
    # STEP 4: Call the LLM with the augmented message list
    response = await provider.complete(ChatRequest(messages=message_dicts, ...))
```

**Critical**: The injection happens after `get_messages_for_request()` but before the LLM call. This means the injected state is never stored in the persistent context — it's appended only for the immediate request.

### 3b. HookResult Model

`hooks-todo-reminder` returns a `HookResult` with:
- `action = "inject_context"`
- `ephemeral = True` — prevents storage in context history (`coordinator.py:411-412`: "Add to context with provenance (ONLY if not ephemeral)")
- `context_injection_role = "user"` (configurable, default `user`)
- `append_to_last_tool_result = True` — appends to the last `role=tool` message for contextual placement (`loop-streaming/__init__.py:228-252`)

The `ephemeral` field exists specifically for this use case. From `models.py:145-151`:
> "If True, injection is temporary (only for current LLM call, not stored in history). Use for transient state like todo reminders that update frequently."

### 3c. Adaptive Reminder Content

The hook also listens on `tool:post` to track whether the `todo` tool was used recently. Based on that:
- **If todo not used recently**: injects a nudge + current list
- **If todo was used recently**: injects only the current list (no nudge)

This is configured via `recent_tool_threshold: 3` — checks last 3 tool calls.

### 3d. The Feedback Loop (State → Inject → LLM → Update)

```
LLM decides to create todos
  → calls tool-todo (create)
  → tool:post fires, updates coordinator.todo_state
  → pending ephemeral injection stored for next iteration (loop-streaming:845-857)

Next LLM iteration:
  → provider:request fires
  → hooks-todo-reminder reads coordinator.todo_state
  → returns inject_context(ephemeral=True) with current list
  → orchestrator appends to message_dicts
  → LLM sees "[in_progress] Step 2..." in its context
  → LLM updates todo → feedback loop continues
```

There are actually TWO injection pathways:
1. **`provider:request` injection** — the reminder hook fires synchronously, result captured immediately
2. **`tool:post` pending injections** — hooks that fire after tool execution can store injections to be applied in the next iteration (`loop-streaming:263-297`, the `_pending_ephemeral_injections` list)

---

## 4. What Makes Todo ALWAYS Available?

Three layered guarantees:

**Layer 1: Base Profile Inclusion**  
`amplifierd/registry/profiles/foundation/base.md` (lines 36-61) includes both `tool-todo` and `hooks-todo-reminder` as standard entries in the tools and hooks sections. Any session using the foundation base profile gets them automatically.

**Layer 2: Bundle Inheritance**  
`amplifier-bundle-zerovector/bundle.md:8` declares:
```yaml
includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
```
The zerovector bundle inherits the foundation bundle, which includes the base profile. Todo is therefore present in zerovector sessions.

**Layer 3: Event-Level Guarantee**  
Even if the tool state is empty, the hook still fires on `provider:request` and can inject a "no todos yet" reminder. The hook is always-on — it doesn't guard on "has the tool been called." This is unlike the fidelity reporter which returns `_CONTINUE` immediately if `zerovector.fidelity_state` has no scores.

---

## 5. The Feedback Loop Architecture: Closed Loop vs. Open Loop

The todo system is a **closed feedback loop**:
- Every LLM call has the current state injected (via `provider:request`)
- Every time the LLM updates state, the next call reflects it (via `coordinator.todo_state`)
- The loop never breaks unless the session ends

The fidelity system is an **open loop with conditions**:
- The LLM must explicitly call `update_fidelity` to write state
- The hook only fires AFTER tool calls (`tool:post`) or after turns (`prompt:complete`) — not before each LLM call
- If `update_fidelity` was never called, `fidelity_state.get_state()` returns `lens_scores: {}` and the hook returns `_CONTINUE` immediately (`hooks-fidelity-reporter/__init__.py:299-300`)
- The hook fires on `tool:post` and `prompt:complete`, not on `provider:request` — so the agent doesn't see fidelity state BEFORE making a decision, only after

---

## 6. Architectural Comparison: Todo vs. Fidelity

| Dimension | `tool-todo` + `hooks-todo-reminder` | `tool-fidelity-state` + `hooks-fidelity-reporter` |
|-----------|--------------------------------------|---------------------------------------------------|
| **Event trigger** | `provider:request` (before every LLM call) | `tool:post` + `prompt:complete` (after events) |
| **Injection timing** | Before each LLM call | After tool calls / turns |
| **Fires if state empty?** | Yes — sends a nudge reminder | No — returns `_CONTINUE` immediately |
| **State persistence** | `coordinator.todo_state` (direct attr) | `zerovector.fidelity_state` capability (registered) |
| **In base profile?** | YES — always present | NO — requires opt-in via zerovector fidelity behavior |
| **Ephemeral?** | Yes — never stored in history | Yes — never stored in history |
| **Dependency direction** | Hook reads tool's state | Hook reads coordinator capability |
| **Feedback loop** | Closed — always-on visibility | Open — conditional, requires explicit invocation |
| **State ownership** | Tool stores in coordinator directly | Tool registers capability pointer |
| **Mount pairing enforced?** | Via behavior YAML + base profile | Via behavior YAML (fidelity.yaml) — optional |

---

## 7. Why This Pattern Works: The Architectural Insight

The todo tool's reliability comes from **three co-located design decisions working together**:

1. **Right event (`provider:request`)**: Fires before the LLM forms its response. The LLM sees its remaining tasks as part of the context it reasons over, not as a reaction to something it already did. This is pre-cognition, not post-hoc reminding.

2. **Right injection type (ephemeral)**: The state is never stored in history, preventing context bloat. Every call gets a fresh snapshot of current state, not accumulating reminders.

3. **Always-on firing (no guards on empty state)**: The hook always fires, even when there are no todos, nudging the LLM to consider whether it should create some. This is the key difference from the fidelity reporter — the fidelity hook silently does nothing when state is empty, while the todo hook actively nudges even in the empty state.

The fidelity system has the right mechanism (ephemeral injection) but wrong trigger timing (`tool:post` instead of `provider:request`) and wrong guard logic (silent when empty). The result is a system that can work beautifully once invoked, but has no self-bootstrapping — it requires the LLM to already know it should use fidelity tracking.

---

## 8. The HookResult.ephemeral Field: Designed for This

The `ephemeral` field in `HookResult` (`models.py:145-151`) and its handling in `coordinator.py:411-412` and `loop-streaming:222-260` form a coherent system specifically designed for recurring transient state injection. The coordinator's `_handle_context_injection` method at lines 411-412:

```python
# 3. Add to context with provenance (ONLY if not ephemeral)
if not result.ephemeral:
    context = self.mount_points["context"]
    if context and hasattr(context, "add_message"):
        await context.add_message(message)
```

Ephemeral injections skip the context store entirely. They only exist in the `message_dicts` list built just before the LLM call, and are discarded after. This is why todo state doesn't grow the conversation history.

---

## 9. Live Evidence: Observed During This Investigation

**This investigation itself is direct empirical evidence.** Between every tool call, `hooks-todo-reminder` injected the current todo list as a `<system-reminder>` block into my context. I observed:

- The reminder fires when the tool hasn't been used recently (shows nudge + list)
- It shows status with symbols: `✓` (completed), `→` (in_progress), `☐` (pending)
- The reminder is ephemeral — it doesn't appear as a persistent message in context history
- The content is appended to the last tool result message (the `append_to_last_tool_result=True` path)

This is the mechanism working exactly as the source code describes.
