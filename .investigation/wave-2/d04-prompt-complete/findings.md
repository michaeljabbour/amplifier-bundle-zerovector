# D-04 Investigation: `prompt:complete` Emission & CU-1 Ephemeral Drop

**Wave 2 verification by Code Tracer (HOW agent)**
**Date:** 2026-03-09
**Files examined:** 4 primary source files, full read

---

## VERDICTS

### Verdict 1: Does the orchestrator emit `prompt:complete`?

**VERDICT: NO — the orchestrator (loop-streaming) does NOT emit `prompt:complete`.**

However, `prompt:complete` IS emitted — by the **app layer** (`amplifier_app_cli/main.py`), not by the orchestrator module.

**Two emission sites in main.py:**
- **Line 1628** — inside `_execute_with_interrupt()` (the interactive REPL path), emitted after `response = await execute_task`
- **Line 1873** — inside the one-shot `run` CLI command handler, emitted after `response = await session.execute(prompt)`

**What the orchestrator (loop-streaming) actually emits** (`amplifier_module_loop_streaming/__init__.py`):
| Event | Line(s) |
|---|---|
| `prompt:submit` | 163 |
| `session:start` | 173 |
| `provider:request` | 205–206, 604–611 |
| `content_block:start` | 364–372 |
| `content_block:end` | 374–382 |
| `tool:pre` | 777–785, 898–905 |
| `tool:post` | 830–838, 948–955 |
| `tool:error` | 797–805, 870–878 |
| `orchestrator:rate_limit_delay` | 95–103 |
| `orchestrator:complete` | 138–145 |
| `session:end` | 668 |

**`prompt:complete` is absent from this list.** Wave 1's three agents were correct.

---

### Verdict 2: Does `action="continue"` with `context_injection` get silently dropped?

**VERDICT: YES — and the drop happens at the `hooks.emit()` level, earlier than Wave 1 suspected.**

**The drop path:**

1. The fidelity reporter returns:
   ```python
   HookResult(action="continue", context_injection="...", ephemeral=True)
   ```
   — `hooks_fidelity_reporter/__init__.py:310-317`

2. Inside `hooks.emit()` (the aggregation layer), the handler result is evaluated:
   ```python
   if result.action == "inject_context" and result.context_injection:
       inject_context_results.append(result)
   ```
   — `amplifier_core/hooks.py:163-164`

   Because `action="continue"`, this condition is **False**. The `context_injection` field is **never collected**. It is gone.

3. `hooks.emit()` returns `HookResult(action="continue")` with **no `context_injection`**.
   — `amplifier_core/hooks.py:186`

4. The orchestrator and coordinator never see the injection at all — the value is lost before it exits the hook registry.

**Secondary confirmation — orchestrator also guards on `action`:**
Even if `hooks.emit()` passed through the injection, the orchestrator's pending-injection logic (lines 846–857 and 962–977) requires `post_result.action == "inject_context"`. A `continue` action would still fail.

**Tertiary confirmation — coordinator also guards on `action`:**
`coordinator.process_hook_result()` at line 361 checks `result.action == "inject_context"`. Same failure.

**Three independent drop points, in order:**
```
hooks.emit():163 → orchestrator:846 → coordinator.py:361
         ↑ FIRST DROP — nothing escapes this
```

---

### Verdict 3: What events does the orchestrator emit, and which is best for fidelity injection?

**Events emitted by loop-streaming** — see table in Verdict 1.

**Best trigger for ephemeral fidelity injection: `provider:request`**

Reasons:
1. Emitted at the **start of every LLM iteration**, covering both tool-using turns and text-only turns (Wave 1's concern about text-only turns is valid for `tool:post` but `provider:request` solves it).
2. The orchestrator **captures and processes** the return value:
   ```python
   result = await hooks.emit(PROVIDER_REQUEST, {...})
   if coordinator:
       result = await coordinator.process_hook_result(result, "provider:request", "orchestrator")
   ```
   — `loop-streaming/__init__.py:205-214`
3. The orchestrator **explicitly handles ephemeral injections** from `provider:request` results at lines 222–260 — exactly the block the Gamma team identified.
4. The hooks-todo-reminder module already uses `provider:request` for its injections (confirmed: it fired in this session).

**However:** The fidelity reporter must change `action="continue"` → `action="inject_context"` for ANY of this to work. The current `action="continue"` causes silent drops at `hooks.emit():163`.

---

### Verdict 4: `prompt:complete` hook result processing — a compounding problem

Even if the fidelity reporter fixed its action field, `prompt:complete` still cannot deliver context injection. The main.py emission sites do **not capture or process** the hook return value:

```python
# main.py line 1628 — return value discarded
await hooks.emit(
    PROMPT_COMPLETE,
    {"prompt": prompt_text, "response": response, ...},
)

# main.py line 1873 — return value discarded
await hooks.emit(
    PROMPT_COMPLETE,
    {"prompt": prompt, "response": response, ...},
)
```

Compare with how `provider:request` is handled:
```python
result = await hooks.emit(PROVIDER_REQUEST, {...})  # CAPTURED
result = await coordinator.process_hook_result(...)  # PROCESSED
```

`prompt:complete` is a **fire-and-forget** observability event. It can never deliver context injection in the current architecture.

---

## Gamma Team Claim Verification

Wave 1's Gamma team found: `loop-streaming/__init__.py:216-260` checks `result.action == "inject_context" and result.ephemeral and result.context_injection`.

**VERIFIED — with minor correction on line numbers.**
The actual lines are **222–260**, not 216–260 (line 216 begins message retrieval). The check is real and correct — but it applies to `provider:request` hook results, not `tool:post` hook results. The Gamma team's structural finding is accurate.

---

## Summary

The system has a **two-part bug:**

1. **Wrong action field:** The fidelity reporter returns `action="continue"` but the hook infrastructure requires `action="inject_context"` to route context injections. This causes silent drops at `hooks.emit():163`.

2. **Wrong event for context injection:** `prompt:complete` is a fire-and-forget app-layer event with no result processing. Any hook registered on it can observe but cannot inject. The correct event for ephemeral pre-LLM injection is `provider:request`, which the orchestrator actively processes.

**Fix path:** Change `hooks-fidelity-reporter` to register on `provider:request` (not `prompt:complete`) and return `action="inject_context"` (not `action="continue"`).
