# D-01 Verdict: Action Mismatch in hooks-fidelity-reporter

## Verdict: **Hook Bug (Position A) — with a compounding documentation mismatch (Position D)**

The fidelity reporter's `context_injection` is silently dropped on every single event because
it returns `action="continue"` instead of `action="inject_context"`. This is **not** a kernel
design tension (Position B) and **not** primarily a documentation gap (Position D) — the
documentation is unambiguous, the hook ignores it. Position C (deliberate but wrong) is
accurate as a characterization of the author's *intent*, but doesn't change the fact that
the behavior is wrong.

---

## The Exact Failure Chain

### Layer 1 — HookRegistry.emit() silently ignores the injection

`amplifier-core/amplifier_core/hooks.py:163-164`:

```python
if result.action == "inject_context" and result.context_injection:
    inject_context_results.append(result)
```

The kernel only collects `context_injection` payloads when `action == "inject_context"`. A
result with `action="continue"` and a non-None `context_injection` passes through this block
untouched. The `inject_context_results` list stays empty; `special_result` stays `None`; the
method returns `HookResult(action="continue", data=current_data)` at line 186 — dropping all
fields (`context_injection`, `ephemeral`, `user_message`) from the original hook result.

### Layer 2 — coordinator.process_hook_result() also gate-checks on action

`amplifier-core/amplifier_core/coordinator.py:361`:

```python
if result.action == "inject_context" and result.context_injection:
    await self._handle_context_injection(result, hook_name, event)
```

Even if `emit()` somehow passed through the `continue` result unchanged, `process_hook_result`
would still not call `_handle_context_injection` because the action is wrong.

### Layer 3 — loop-streaming orchestrator gate-checks action twice

`amplifier-module-loop-streaming/.../amplifier_module_loop_streaming/__init__.py:222-226`
(provider:request path — handles ephemeral injection for the upcoming LLM call):

```python
if (
    result.action == "inject_context"
    and result.ephemeral
    and result.context_injection
):
```

And at `__init__.py:846-850` (tool:post path — stores injection for next iteration):

```python
if (
    post_result.action == "inject_context"
    and post_result.ephemeral
    and post_result.context_injection
):
```

Both paths explicitly require `action == "inject_context"`. A `continue` result with
`ephemeral=True` and `context_injection` set hits neither branch. The
`_pending_ephemeral_injections` list is never populated; the agent never sees the fidelity
state.

### Layer 4 — models.py documents the correct action

`amplifier-core/amplifier_core/models.py:128-136`:

```python
context_injection: str | None = Field(
    default=None,
    description=(
        "Text to inject into agent's conversation context (for action='inject_context'). "
        ...
    ),
)
```

The field description is unambiguous: `context_injection` is *for* `action='inject_context'`.
`models.py:212-220` (`append_to_last_tool_result`) reinforces this: "Only applicable when
`action='inject_context'` and `ephemeral=True`."

The `ephemeral` field at `models.py:145-152` says: "Orchestrator must append ephemeral
injection to messages without storing in context." This describes the orchestrator's
*intended* behavior — but the orchestrator only does so after checking
`action == "inject_context"`.

### The hook's stated rationale

`hooks-fidelity-reporter/__init__.py:14`:

```
Non-blocking observer: never modifies ``action`` away from ``continue``.
```

The author conceptualized `inject_context` as an "aggressive" or "blocking" action — something
that modifies the flow. This is a misreading of the action semantics. `inject_context` is
non-blocking; it does not deny or short-circuit the handler chain (see `hooks.py:154-156` —
only `deny` short-circuits). The name describes *what the hook contributes*, not how
disruptive it is. `continue` means "I have nothing to contribute"; `inject_context` means
"I have context to inject, and execution continues normally."

---

## Why Position B (Design Tension) Is Wrong

Position B claims the name `inject_context` "sounds aggressive" and causes hooks to avoid it.
This is not supported by the code. There is nothing aggressive about `inject_context` at the
kernel level — it chains through all handlers exactly like `continue` does (hooks.py:163-165
shows it is collected and merged, never used to short-circuit). The fidelity reporter author's
decision was not forced by kernel naming — it was a private design choice stated explicitly in
the module docstring.

---

## Why Position C (Deliberate But Wrong) Is Partially Correct

The module docstring at line 14 shows this was a conscious choice, not an oversight. The
author wanted to distinguish "observer" hooks from "actor" hooks. But the distinction the
author drew (`continue` vs `inject_context`) does not map to the kernel's actual semantics.
The correct way to be a "non-blocking observer that also injects ephemeral context" is to use
`action="inject_context"` — the kernel treats `inject_context` as non-blocking.

---

## The Correct Fix

**Single-line change** in
`modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:311`:

```python
# BEFORE (broken):
return HookResult(
    action="continue",          # ← wrong: context_injection is silently ignored
    context_injection=ephemeral_text,
    context_injection_role="system",
    ephemeral=True,
    user_message=dashboard,
    user_message_level="info",
)

# AFTER (correct):
return HookResult(
    action="inject_context",    # ← correct: tells every layer to process context_injection
    context_injection=ephemeral_text,
    context_injection_role="system",
    ephemeral=True,
    user_message=dashboard,
    user_message_level="info",
)
```

The module docstring at line 14 should also be updated to remove the "never modifies action
away from continue" claim, since that claim was both wrong and will no longer be true.

---

## What the `user_message` Field Situation Is

Separately: the `user_message=dashboard` field in the returned `HookResult` IS processed
independently of `action` — `coordinator.py:369-370` handles it for any action value. So the
ANSI dashboard display to stdout (via `sys.stdout.write` at line 304) and the `user_message`
routing both work today. Only the `context_injection` / `ephemeral` path is broken. This
means the human-visible dashboard renders correctly, but the agent never receives the
routing advice text.

---

## Secondary Recommendation

The `_CONTINUE` sentinel at line 50 (`HookResult(action="continue")`) is used correctly for
the no-op early returns at lines 296 and 300. Those should remain `action="continue"` because
they genuinely have nothing to inject. Only the full return at line 310-317 needs to change.
