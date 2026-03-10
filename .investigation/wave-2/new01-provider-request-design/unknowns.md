# NEW-01: Unknowns & Open Questions

---

## Confirmed Unknowns

### U1: `append_to_last_tool_result` Lost in Merge

**What:** The hook registry's `_merge_inject_context_results` (`hooks.py:188-219`) combines multiple `inject_context` results but does NOT propagate `append_to_last_tool_result` from any result. The merged HookResult gets the default `False`, even when the first handler (todo-reminder at priority 10) sets it to `True`.

**Why it matters:** This changes todo-reminder's placement behavior when fidelity is also firing. Currently, todo appends its reminder to the last tool result message. With fidelity added, the merged injection becomes a new standalone message. This may reduce the LLM's contextual association between the todo reminder and the preceding tool execution.

**What I can't determine:** Whether this behavioral change is noticeable in practice. The content still reaches the LLM — only its position in the message list changes. This needs empirical testing.

**Recommendation:** File a follow-up to fix the merge logic in `amplifier-core/hooks.py` to propagate `append_to_last_tool_result` from the first result, consistent with how it handles `context_injection_role`, `ephemeral`, and `suppress_output`.

---

### U2: Who Emits `prompt:complete`?

**What:** The streaming orchestrator (`amplifier-module-loop-streaming`) does NOT emit `PROMPT_COMPLETE`. The event is defined in the taxonomy (`amplifier-core/events.py:13`) but I found no emitter in the orchestrator module.

**What I can't determine:** Whether another component (the app layer, CLI, or desktop app) emits `prompt:complete`. The fidelity reporter registers a handler for it, suggesting someone expected it to fire. But if it only fires at the app layer (outside the orchestrator loop), the hook result would NOT be processed by the orchestrator's ephemeral injection logic — making it useless for context injection even if it does fire.

**Searched:** `amplifier-module-loop-streaming/` — zero occurrences. Did not search `amplifier-app-cli/` or `amplifier-desktop/` due to scope.

**Recommendation:** Remove the `prompt:complete` handler. Even if it fires somewhere, it can't produce ephemeral injections (no orchestrator processing). The `provider:request` handler covers all cases.

---

### U3: Fidelity Hook Loads Twice in Crew Behavior

**What:** The `zerovector-crew.yaml` behavior both `includes` the fidelity behavior (line 10) AND directly declares `hooks-fidelity-reporter` (line 15-16):

```yaml
includes:
  - bundle: zerovector:behaviors/fidelity    # <-- includes fidelity behavior (has the hook)

hooks:
  - module: hooks-fidelity-reporter          # <-- also declares the hook directly
    source: ../modules/hooks-fidelity-reporter
```

**What I can't determine:** Whether this causes double-mounting (two handler registrations for the same events). If so, the fidelity reporter would fire twice on every `provider:request` — doubling its injection and doubling dashboard rendering. This was flagged as D-06 in Wave 2 but I did not read that investigation's findings (independence constraint).

**Risk:** If double-mounting is real, adding `provider:request` would produce doubled injections in the merged result.

---

### U4: Sub-Session Hook Inheritance

**What:** When the crew orchestrator delegates to sub-agents (e.g., `zerovector:critic`), does the sub-session inherit the `provider:request` hooks from the parent? If so, the fidelity injection would fire in sub-sessions too — which may or may not be desirable.

**What I can't determine:** The hook inheritance model for sub-sessions. The todo-reminder presumably fires in sub-sessions (it's in the foundation base profile). If fidelity fires in sub-sessions, the critic agent would see fidelity state while performing its assessment — which could create a feedback loop (critic sees state → assesses → updates state → sees updated state).

**Recommendation:** Investigate the sub-session hook model. If hooks are inherited, consider whether the fidelity injection should be suppressed in sub-sessions (e.g., by checking for a parent session ID in the event data).

---

### U5: Coordinator Budget Reset Timing

**What:** The coordinator's injection budget is reset per-turn via `reset_turn()` (`coordinator.py:338-340`). But the `provider:request` event fires multiple times per turn (once per orchestrator iteration). Each iteration's injection counts against the same turn budget.

**What I can't determine:** When exactly `reset_turn()` is called relative to the orchestrator loop. If it's called at the start of each user message, a long multi-tool turn could accumulate many injections (one per iteration). With todo + fidelity firing on every iteration, a 20-iteration turn would use ~4,000 tokens of budget (200 tokens × 20). Still well within the 10,000 limit, but worth monitoring.

---

## Suspected Composition Effects

### S1: Merge Role Override May Affect LLM Behavior

**Suspicion:** The fidelity injection originally wanted `role="system"` for authoritative positioning. In the merged result, it gets `role="user"` (from todo). User-role messages may be weighted differently by the LLM than system-role messages. The XML `source` tag mitigates this, but the behavioral difference hasn't been tested.

**Testable:** Compare LLM adherence to fidelity routing advice when injected as `role="system"` vs `role="user"`.

### S2: Empty-State Nudge May Be Noisy in Non-Crew Sessions

**Suspicion:** The proposed empty-state nudge fires before EVERY LLM call when no fidelity scores exist. In non-crew sessions (where fidelity isn't relevant), this could be wasted context. The todo reminder has the same issue but its nudge is lighter ("consider using the todo tool").

**Mitigation:** The nudge should check whether a crew mode is active before firing. If no crew mode is active, return `action="continue"` (no-op). This requires access to mode state, which may not be available via the coordinator.

### S3: Dashboard Rendering Frequency

**Suspicion:** The `tool:post` dashboard handler fires after EVERY tool call, not just `update_fidelity`. This means the dashboard renders after `read_file`, `bash`, `grep`, etc. — potentially dozens of times per turn. This is noisy for the user's terminal.

**Not in scope:** This is a display concern, not an injection concern. But worth noting as a follow-up optimization (filter `tool:post` to only render dashboard when `data.tool_name == "update_fidelity"`).

---

## Questions for Other Agents

### For Code Tracer (HOW)
1. Does the orchestrator's `_pending_ephemeral_injections` mechanism interact with `provider:request` injections? Could a tool:post ephemeral injection from a previous iteration conflict with a provider:request injection in the next iteration?
2. What is the exact call sequence: does `process_hook_result` always complete before the orchestrator reads `result.action`?

### For Behavior Observer (WHAT)
1. In live sessions, does the todo-reminder consistently fire with `action="inject_context"`, or does it sometimes return `action="continue"`? (This affects how often the merge path is exercised.)
2. Has the fidelity dashboard ever appeared in terminal output? (If the `tool:post` handler with `action="continue"` still renders the dashboard via `sys.stdout.write`, the visual path may work even though the injection path is broken.)

---

## Scope Boundaries

**What I traced:** All boundaries between mechanisms A-H listed in integration-map.md. Every file:line citation was verified by reading the source.

**What I did NOT trace:**
- App-layer event emission (amplifier-app-cli, amplifier-desktop) — could not determine if `prompt:complete` fires there
- Sub-session hook inheritance model — would require reading the session spawning logic
- Production injection budget configuration — the 10,000-token default may be overridden in session config
- Other hooks registered on `provider:request` beyond todo-reminder — there may be hooks from other bundles