# Unknowns — Code Tracer (agent-1-code-tracer)

What I couldn't determine, what I suspect but can't confirm, and what questions my findings raise.

---

## What I Could NOT Determine

### 1. The actual source code of tool-todo and hooks-todo-reminder

Both modules point to GitHub repositories:
- `git+https://github.com/microsoft/amplifier-module-tool-todo@main`
- `git+https://github.com/microsoft/amplifier-module-hooks-todo-reminder@main`

These are **not present in any local directory** I could search. I searched via glob for `**/amplifier_module_tool_todo*/**/*.py` and `**/amplifier_module_hooks_todo*/**/*.py` — zero results.

**What I could NOT trace from source:**
- The exact state storage mechanism: the docs say `coordinator.todo_state` but I can't confirm whether this is a direct attribute set on the coordinator or a capability registration. Given that the coordinator's `__init__` doesn't declare `todo_state` explicitly (`coordinator.py:67-80`), the tool likely sets it dynamically (`coordinator.todo_state = TodoState()`).
- Whether `hooks-todo-reminder` uses the `provider:request` or a different event: I confirmed this from the documentation (`todo_reminder.md:37`) and live observation, but did not trace the actual handler registration code.
- The exact data model of `coordinator.todo_state`: likely a list of dicts or a Pydantic model, but exact schema unknown without source.
- The precise logic for "recently used" detection: docs say `recent_tool_threshold: 3` checks last 3 tool calls, but the exact implementation (ring buffer? counter? list?) is unknown.

**Workaround I used:** Documentation (`amplifier-docs/docs/modules/hooks/todo_reminder.md`) combined with live empirical observation (seeing reminders fire during this investigation) gave high confidence despite lacking source.

---

### 2. Whether hooks-todo-reminder uses the append_to_last_tool_result path

During this investigation, the reminder appeared to be appended after tool results. The `HookResult.append_to_last_tool_result` field exists (`models.py:212-220`) and the orchestrator handles it (`loop-streaming:228-252`). The foundation docs say "Appends to last tool result for contextual awareness" (`todo_reminder.md:44`). However, without the source I cannot confirm whether the hook sets `append_to_last_tool_result=True` programmatically.

---

### 3. The installed version of tool-todo in the running session

The todo tool I'm actively using produces results like:
```json
{"error": null, "output": {"count": 5, "status": "updated", ...}}
```
This suggests a specific output schema, but I couldn't find the tool's `execute()` method to trace the exact output format (important for the reminder hook's state-reading logic).

---

### 4. How the foundation bundle includes the base profile

`amplifier-bundle-zerovector/bundle.md:8` says:
```yaml
includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
```

But the local `amplifier-foundation/` directory doesn't show how the bundle loader resolves includes to profiles. The `amplifier-foundation/amplifier_foundation/bundle.py` and `amplifier-foundation/amplifier_foundation/registry.py` likely handle this, but I didn't trace the include resolution logic. I assumed (from documentation evidence) that the base profile is applied, but the exact resolution mechanism is untraced.

---

### 5. Whether the zerovector modes (crew-*) explicitly exclude or include todo

The zerovector bundle has a `modes/` directory I didn't read in full. It's possible that certain crew modes (like `crew-build`) override the tool list and accidentally exclude todo or its hook, which could create inconsistency. I checked `bundle.md` but didn't examine individual mode YAML files.

---

### 6. The hooks-crew-gate module

`amplifier-bundle-zerovector/modules/hooks-crew-gate/` exists but I didn't read its implementation. It may interact with `provider:request` in ways that could interfere with todo injection (e.g., denying the event or modifying the data). This is worth checking if todo appears unreliable in crew sessions.

---

## What I Suspect But Cannot Confirm

### 1. coordinator.todo_state is set as a dynamic attribute

The `ModuleCoordinator.__init__()` (`coordinator.py:51-91`) doesn't declare `todo_state`. I suspect `tool-todo`'s `mount()` function does:
```python
state = TodoState()
coordinator.todo_state = state  # dynamic attribute assignment
```
This is consistent with how `hooks-todo-reminder` accesses it (`coordinator.todo_state`), and with the Python duck-typing style used throughout the codebase. If this is wrong and it uses `register_capability()` instead, the access pattern would differ.

### 2. The reminder uses a ring buffer or deque for recent tool tracking

The `recent_tool_threshold: 3` suggests the hook maintains a small buffer of recent tool names, checking if `"todo"` appears in the last N. This is the simplest implementation consistent with the documentation.

### 3. The zerovector sessions actually DO have todo working reliably

My evidence shows todo is in the base profile and zerovector inherits foundation. But if the investigation is asking "why does todo work reliably while fidelity doesn't," it implies someone has actually observed this discrepancy. I confirmed the architectural reason but couldn't run a live zerovector session specifically to observe both tools side by side.

### 4. The fidelity tool's "unreliability" is due to missing provider:request hook, not missing base profile

My finding is that the **primary** failure mode for fidelity is:
1. The hook fires on `tool:post`/`prompt:complete` instead of `provider:request`
2. The hook silently does nothing until `update_fidelity` is called

But there might be a secondary failure: if the zerovector fidelity behavior is not included in the active mode, neither the tool nor the hook mounts at all. I couldn't confirm whether the crew modes (`zerovector:behaviors/zerovector-crew`) include the fidelity behavior.

---

## Questions My Findings Raise

### Q1: Could hooks-todo-reminder be made unreliable by priority ordering?

The hook runs at `priority: 10`. If another hook at priority 0-9 returns `action="deny"` on `provider:request`, the todo reminder would never fire (hooks short-circuit on deny per `hooks.py:154-156`). Are there any hooks in the zerovector sessions that deny `provider:request`? The `hooks-crew-gate` module is a candidate worth checking.

### Q2: Should fidelity use provider:request instead of tool:post?

If the investigation's goal is to make fidelity as reliable as todo, the architectural fix is clear: add a `provider:request` handler to `hooks-fidelity-reporter` that injects fidelity state before every LLM call — not just after tool calls. The current `tool:post` + `prompt:complete` registration only provides reactive visibility; a `provider:request` registration would provide proactive visibility.

### Q3: What happens if tool-todo and hooks-todo-reminder are not properly paired?

The behavior YAML (`todo-reminder.yaml`) groups them, but what if someone mounts only `tool-todo` without `hooks-todo-reminder`? The tool would work (todos can be created/read), but the LLM would never be reminded automatically. This is the exact situation the fidelity system is in — it has the tool without an always-on proactive reminder.

### Q4: Does the zerovector fidelity.yaml behavior get applied to crew sessions?

`amplifier-bundle-zerovector/behaviors/zerovector-crew.yaml` (referenced in `bundle.md:9`) likely defines which tools and hooks are available in crew sessions. If it doesn't include `behaviors/fidelity.yaml`, the fidelity modules won't mount. I didn't trace this dependency chain.

### Q5: Can the ephemeral injection budget limit interfere with todo reminders?

`coordinator.py:109-117` shows `injection_budget_per_turn` (default 10,000 tokens). If multiple hooks inject context on `provider:request`, the budget could be exceeded. The coordinator logs a warning but doesn't hard-block (`coordinator.py:398-409`). In very busy sessions with many hooks injecting context, could todo reminders be crowded out? The budget is token-based but the check uses `len(content) // 4` as a rough estimate, not actual tokenization.

### Q6: What's the state of hooks-todo-reminder in sub-sessions spawned by tool-task?

When `tool-task` spawns a child session, does the child inherit the parent's hook configuration? The `AmplifierSession` constructor (`session.py:28-75`) creates a fresh coordinator. Child sessions spawned for delegation likely get a fresh mount plan. Whether that plan includes `hooks-todo-reminder` depends on how `tool-task` builds the child's config. If it doesn't include the hook, sub-agents won't be reminded about their todos.

---

## Paths Not Followed

1. **`amplifier-core/amplifier_core/loader.py`** — The module loader that resolves `source:` URIs and instantiates modules. Understanding it would clarify how `git+https://...` sources are fetched and cached.

2. **`amplifier-module-loop-streaming/__init__.py:880-1052`** — I read through line 880. The rest (~172 lines) likely contains utilities and tests — less likely to have todo-specific logic.

3. **`amplifier-bundle-zerovector/modes/`** — The mode YAML files that activate specific crew configurations. These determine what tools/hooks are active per mode.

4. **`amplifier-bundle-zerovector/behaviors/zerovector-crew.yaml`** — The crew behavior definition that might include/exclude fidelity tools.

5. **`amplifier-foundation/amplifier_foundation/registry.py`** and **`amplifier-foundation/amplifier_foundation/bundle.py`** — Bundle resolution logic.

6. **`.venv/` directories** — Installed package versions of tool-todo and hooks-todo-reminder are not in any local `.venv` I found; the simplecli `.venv` existed but had no todo packages.
