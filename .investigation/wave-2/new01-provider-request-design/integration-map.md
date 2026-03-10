# NEW-01: `provider:request` Design for Fidelity Reporter

## Integration Mapper — Cross-Boundary Analysis

---

## Executive Summary

The fidelity reporter's context injection is **currently broken on all pathways**. It uses `action="continue"` with `context_injection` set, but the hook merge system and orchestrator both gate on `action="inject_context"`. Additionally, its `prompt:complete` handler is dead — the streaming orchestrator never emits that event. Migrating to `provider:request` with `action="inject_context"` is both correct and necessary. The hook merge system already supports multiple `inject_context` handlers on the same event, so coexistence with todo-reminder is architecturally sound, with one caveat around merged result settings.

---

## 1. Mechanisms in Scope

| # | Mechanism | Location | Role |
|---|-----------|----------|------|
| A | **Orchestrator loop** | `amplifier-module-loop-streaming/__init__.py` | Emits `provider:request`, processes result, builds messages |
| B | **Hook registry** | `amplifier-core/hooks.py` | Routes events to handlers, merges `inject_context` results |
| C | **Coordinator** | `amplifier-core/coordinator.py` | Validates injection size/budget, routes user messages |
| D | **Todo reminder hook** | `amplifier-module-hooks-todo-reminder/__init__.py` | Reference `provider:request` handler at priority 10 |
| E | **Fidelity reporter hook** | `modules/hooks-fidelity-reporter/__init__.py` | Current `tool:post`/`prompt:complete` handler (broken) |
| F | **Fidelity state tool** | `modules/tool-fidelity-state/__init__.py` | Manages `FidelityState`, registers capability |
| G | **Crew-routing context** | `context/crew-routing.md` | Thin routing table, guides skill loading |
| H | **Skills system** | `fidelity-framework` skill (on-demand) | Full scoring rubric, loaded when needed |

---

## 2. Boundary Analysis

### Boundary A↔B: Orchestrator → Hook Registry (`provider:request` emission)

**What crosses:** The orchestrator emits `PROVIDER_REQUEST` with `{"provider": provider_name, "iteration": iteration}` at the **start of every LLM iteration**, before `get_messages_for_request()` is called.

**Evidence:**
```python
# amplifier-module-loop-streaming/__init__.py:204-211
# Emit provider request BEFORE getting messages (allows hook injections)
result = await hooks.emit(
    PROVIDER_REQUEST, {"provider": provider_name, "iteration": iteration}
)
if coordinator:
    result = await coordinator.process_hook_result(
        result, "provider:request", "orchestrator"
    )
```

**Data flow direction:** Orchestrator → HookRegistry.emit() → returns single merged HookResult → Coordinator.process_hook_result() → Orchestrator processes injection.

**Critical:** The orchestrator captures the return value and acts on it. This is in contrast to many other event emissions where the return is ignored.

### Boundary B↔B: Hook Merge Logic (multiple `inject_context` on same event)

**What crosses:** When multiple handlers return `action="inject_context"` for the same event, the hook registry **merges** them into a single result.

**Evidence:**
```python
# amplifier-core/hooks.py:142-178
# Collect ALL inject_context results to merge them
inject_context_results: list[HookResult] = []
...
# Collect inject_context actions for merging
if result.action == "inject_context" and result.context_injection:
    inject_context_results.append(result)
...
# If multiple inject_context results, merge them
if inject_context_results:
    special_result = self._merge_inject_context_results(inject_context_results)
```

**Merge behavior** (`hooks.py:188-219`):
- Content: concatenated with `"\n\n"` separator
- `context_injection_role`: taken from **first** result (lowest priority number)
- `ephemeral`: taken from **first** result
- `suppress_output`: taken from **first** result
- `append_to_last_tool_result`: **NOT propagated** (defaults to `False`)

**Integration implication:** If todo-reminder (priority 10, `role="user"`) and fidelity (priority 20, `role="system"`) both return `inject_context`, the merged result uses `role="user"`. Fidelity's desired `role="system"` is silently overridden. Both injections' content IS preserved, but the delivery wrapper changes.

### Boundary A↔E: Orchestrator → Fidelity Reporter (CURRENT — BROKEN)

**What crosses:** Currently, the fidelity reporter fires on `tool:post` and `prompt:complete`.

**Bug 1 — `action="continue"` silently drops injection:**
```python
# hooks-fidelity-reporter/__init__.py:310-317
return HookResult(
    action="continue",         # <-- THIS IS THE BUG
    context_injection=ephemeral_text,
    context_injection_role="system",
    ephemeral=True,
    user_message=dashboard,
    user_message_level="info",
)
```

The hook registry's merge logic (hooks.py:162-164) only collects results with `action="inject_context"`:
```python
if result.action == "inject_context" and result.context_injection:
    inject_context_results.append(result)
```

The orchestrator's tool:post ephemeral storage (loop-streaming:846-849) also gates on `action="inject_context"`:
```python
if (
    post_result.action == "inject_context"
    and post_result.ephemeral
    and post_result.context_injection
):
```

**Result: The fidelity injection is silently dropped. It never reaches the LLM.**

**Bug 2 — `prompt:complete` is never emitted:**
The streaming orchestrator imports `PROVIDER_REQUEST`, `TOOL_POST`, `TOOL_PRE`, etc. but does NOT import or emit `PROMPT_COMPLETE`:
```python
# amplifier-module-loop-streaming/__init__.py:19-26
from amplifier_core.events import CONTENT_BLOCK_END
from amplifier_core.events import CONTENT_BLOCK_START
from amplifier_core.events import ORCHESTRATOR_COMPLETE
from amplifier_core.events import PROMPT_SUBMIT
from amplifier_core.events import PROVIDER_REQUEST
from amplifier_core.events import TOOL_ERROR
from amplifier_core.events import TOOL_POST
from amplifier_core.events import TOOL_PRE
# PROMPT_COMPLETE is absent
```

Confirmed by grep: zero occurrences of `PROMPT_COMPLETE` or `prompt:complete` in the orchestrator module.

**Result: The `prompt:complete` handler is dead code.**

### Boundary E↔F: Fidelity Reporter → Fidelity State (capability access)

**What crosses:** The hook reads state via coordinator capability:
```python
# hooks-fidelity-reporter/__init__.py:294
fidelity_state = coordinator.get_capability("zerovector.fidelity_state")
```

The state is registered by the tool module:
```python
# tool-fidelity-state/__init__.py:180
coordinator.register_capability("zerovector.fidelity_state", state)
```

**Key detail:** The capability returns a `FidelityState` dataclass instance. The hook calls `fidelity_state.get_state()` which returns a plain dict snapshot (copies, not references). This is safe for concurrent access.

**Contrast with todo:** The todo-reminder accesses state differently:
```python
# hooks-todo-reminder/__init__.py:99
todos = getattr(self.coordinator, "todo_state", None)
```
Todo uses `getattr` on the coordinator directly, while fidelity uses the capability registry. Both work, but the fidelity pattern (capability registry) is the more principled approach.

### Boundary A↔C: Orchestrator → Coordinator (injection validation)

**What crosses:** The coordinator validates and budgets injections before the orchestrator applies them.

**Evidence:**
```python
# amplifier-core/coordinator.py:361-362
if result.action == "inject_context" and result.context_injection:
    await self._handle_context_injection(result, hook_name, event)
```

Validation chain:
1. **Size limit:** 10,240 bytes per injection (coordinator.py:128). Hard error if exceeded.
2. **Budget:** 10,000 tokens per turn (coordinator.py:117). **Warning only** if exceeded (coordinator.py:398-407).
3. **Ephemeral skip:** If `ephemeral=True`, coordinator does NOT store in context (coordinator.py:411-412). Orchestrator handles ephemeral injection to messages directly.

**Budget analysis for fidelity:**
- Fidelity `render_ephemeral` output: ~250-300 chars (~75 tokens)
- Todo reminder: ~300-500 chars (~125 tokens)
- Combined: ~600-800 chars (~200 tokens)
- Budget: 10,000 tokens → **2% utilization**. No budget concern.

### Boundary G↔H: Crew-Routing → Skills System (loading interaction)

**What crosses:** The thin `crew-routing.md` (always loaded via `context.include`) tells the LLM when to load skills:

```markdown
# context/crew-routing.md:9
| `fidelity-framework` | Scoring rubric, assessment JSON format, evidence requirements | During fidelity assessments |
```

**Integration implication:** The `provider:request` injection does NOT need to replicate the scoring rubric. The routing table already instructs the LLM to load `fidelity-framework` during assessments. The injection should provide only **current state + routing advice** — enough for the LLM to make routing decisions without the full framework.

---

## 3. Proposed Design

### 3.1 Event Registration

```python
def register(self, hooks):
    """Register hooks."""
    # Context injection: fires BEFORE every LLM call
    hooks.register(
        "provider:request",
        self.on_provider_request,
        priority=self.priority,         # 20
        name="fidelity-reporter-injection",
    )
    # Dashboard display: fires AFTER tool execution (visual only)
    hooks.register(
        "tool:post",
        self.on_tool_post,
        priority=50,                    # Keep existing
        name="fidelity-reporter-dashboard",
    )
    # REMOVED: prompt:complete (dead — never emitted by orchestrator)
```

### 3.2 Priority: 20

- **After todo-reminder (10):** Fidelity state is less time-critical than task tracking. Todo nudges help the LLM stay on task; fidelity provides routing context.
- **Before default hooks (50+):** Fidelity injection needs to be in the merge before the orchestrator processes it.
- **Merge consequence:** When todo also fires, merged result uses todo's `role="user"` and `ephemeral=True`. Both injections' content is preserved. The role override is acceptable because both are wrapped in source-attributed XML tags.

### 3.3 Empty-State Behavior (nudge)

When `fidelity_state` capability is not registered, OR `lens_scores` is empty:

```python
async def on_provider_request(self, event, data):
    state = self._get_fidelity_state()
    
    if state is None or not state.get("lens_scores"):
        # Nudge: remind LLM that fidelity tracking is available
        return HookResult(
            action="inject_context",
            context_injection=(
                '<system-reminder source="fidelity-reporter">\n'
                "[FIDELITY] No fidelity assessment performed yet. "
                "If you are in a crew session, perform a multi-lens fidelity "
                "assessment using the update_fidelity tool. Load the "
                "fidelity-framework skill for the scoring rubric.\n"
                "</system-reminder>"
            ),
            context_injection_role="user",
            ephemeral=True,
            suppress_output=True,
        )
    
    # ... non-empty state handling below
```

**Rationale for always-fire nudge:** Matches the todo-reminder pattern. The todo hook fires even when empty to nudge creation. Fidelity should fire even when unscored to nudge assessment. This directly addresses the "silent no-op when empty" gap identified in Wave 1.

### 3.4 Non-Empty-State Behavior

When scores exist, inject compact routing state:

```python
    # Non-empty state: inject compact routing advice
    ephemeral_text = self.render_ephemeral(state)
    
    return HookResult(
        action="inject_context",          # FIXED: was "continue"
        context_injection=(
            '<system-reminder source="fidelity-reporter">\n'
            f'{ephemeral_text}\n'
            '</system-reminder>'
        ),
        context_injection_role="user",    # Match todo-reminder for merge compat
        ephemeral=True,
        suppress_output=True,
    )
```

**Key change:** `action="inject_context"` instead of `action="continue"`. This is the fix for the silent-drop bug.

**Role choice:** `role="user"` instead of `role="system"`. Rationale:
1. Matches todo-reminder, so when merged, there's no conflict
2. The XML `source="fidelity-reporter"` tag provides clear attribution regardless of role
3. User-role injections are more reliably attended to by LLMs

### 3.5 Dashboard-Only `tool:post` Handler

The dashboard rendering stays on `tool:post` but returns `action="continue"` with NO `context_injection`:

```python
async def on_tool_post(self, event, data):
    """Render dashboard to stdout after tool calls (visual only)."""
    state = self._get_fidelity_state()
    if state is None or not state.get("lens_scores"):
        return _CONTINUE
    
    dashboard = self.render_dashboard(state)
    sys.stdout.write(f"\n{dashboard}\n")
    sys.stdout.flush()
    
    return HookResult(
        action="continue",
        user_message=dashboard,
        user_message_level="info",
    )
    # NOTE: No context_injection here. All injection via provider:request.
```

**Separation of concerns:**
- `provider:request` → ephemeral context injection (what the LLM sees)
- `tool:post` → visual dashboard (what the user sees)

### 3.6 Interaction with Skills-Based Loading

The `provider:request` injection is deliberately minimal. It provides:
1. **Current scores** — enough for routing decisions
2. **Priority gap + recommendation** — actionable without the full framework
3. **Skill reference** — "Load `fidelity-framework` skill for the scoring rubric"

It does NOT provide:
- The full scoring rubric (that's in the skill)
- Evidence requirements (that's in the skill)
- Assessment JSON format (that's in the skill)

The `crew-routing.md` context (always loaded) tells the LLM WHEN to load the skill. The `provider:request` injection tells the LLM WHAT the current state is. Together, they give the LLM enough context without bloating every request.

---

## 4. Code-Level Integration Points

### 4.1 Files to Change

| File | Change | Reason |
|------|--------|--------|
| `modules/hooks-fidelity-reporter/__init__.py` | Add `provider:request` handler, fix action, split tool:post, remove prompt:complete | Core fix |
| `behaviors/fidelity.yaml` | Optionally add `config.priority: 20` | Make priority configurable |

### 4.2 Mount Signature Change

The current `mount()` receives `coordinator` but the `FidelityReporter` class is stateless — it receives `coordinator` per-call in `handle_event`. For `provider:request`, the hook needs coordinator access at registration time (like todo-reminder stores `self.coordinator`):

```python
async def mount(coordinator, config=None):
    config = config or {}
    priority = int(config.get("priority", 20))
    inject_role = config.get("inject_role", "user")
    
    reporter = FidelityReporter(coordinator, inject_role)
    reporter.register(coordinator.hooks, priority)
    
    return reporter.cleanup
```

### 4.3 Constructor Change

```python
class FidelityReporter:
    def __init__(self, coordinator, inject_role="user"):
        self.coordinator = coordinator
        self.inject_role = inject_role
```

This mirrors the todo-reminder pattern where the hook stores `self.coordinator` at init time and accesses state through it in the handler.

---

## 5. Composition Effects

### 5.1 Todo + Fidelity Merge on `provider:request`

When both hooks fire and return `inject_context`:

| Property | Todo (priority 10) | Fidelity (priority 20) | Merged |
|----------|-------------------|----------------------|--------|
| `action` | `inject_context` | `inject_context` | `inject_context` |
| `context_injection` | todo reminder text | fidelity state text | **both, joined by `\n\n`** |
| `context_injection_role` | `user` | `user` | `user` (from first) |
| `ephemeral` | `True` | `True` | `True` (from first) |
| `suppress_output` | `True` | `True` | `True` (from first) |
| `append_to_last_tool_result` | `True` | `False` | **`False` (default, NOT from first)** |

**The `append_to_last_tool_result` loss is a known issue.** The merge logic (`hooks.py:213-219`) does not propagate this field. When fidelity is added as a second `inject_context` handler, the merged result loses todo's `append_to_last_tool_result=True`. The combined injection becomes a new message instead of appending to the last tool result.

**Impact:** Minor behavioral change for todo-reminder. The todo content still reaches the LLM, but as a separate message rather than appended to the last tool result. This may slightly reduce the contextual association between the todo reminder and the tool that just executed.

**Mitigation:** Fix the merge logic in `hooks.py` to propagate `append_to_last_tool_result` from the first result. This is a core framework change (out of scope for this design, but noted as a follow-up).

### 5.2 When Todo Returns `continue` (no merge)

When todos are empty AND the todo tool was recently used, todo-reminder returns `action="continue"` (hooks-todo-reminder:127-128). In this case, fidelity would be the ONLY `inject_context` result, and its settings are used unmodified. This is the clean path.

### 5.3 Injection Budget Accounting

The coordinator tracks injection budget per-turn across ALL hooks:
```python
# coordinator.py:394-409
budget = self.injection_budget_per_turn  # 10,000 tokens
tokens = len(content) // 4              # Rough estimate
```

With both hooks firing, combined content is ~200 tokens. Budget utilization: **2%**. No concern.

---

## 6. Summary of Changes Required

1. **Fix `action`**: `"continue"` → `"inject_context"` for the injection return path
2. **Add `provider:request` handler**: Priority 20, ephemeral, role="user"
3. **Add empty-state nudge**: Fire even when no scores exist
4. **Split `tool:post`**: Dashboard rendering only, no context injection
5. **Remove `prompt:complete`**: Dead handler (never emitted by orchestrator)
6. **Store coordinator**: Accept at init time, access capability in handler
7. **Match todo-reminder role**: Use `role="user"` for merge compatibility