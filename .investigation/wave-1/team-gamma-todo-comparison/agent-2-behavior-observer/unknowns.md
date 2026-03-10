# Unknowns: What I Couldn't Determine and Why

---

## Unknown 1: Actual Todo Tool and Hook Source Code

**What I tried**: The todo tool (`tool-todo`) and hook (`hooks-todo-reminder`) are referenced as external GitHub repos:
- `git+https://github.com/microsoft/amplifier-module-tool-todo@main`
- `git+https://github.com/microsoft/amplifier-module-hooks-todo-reminder@main`

These modules are not checked out locally in any of the repositories I searched. I could only examine them through their documentation (`amplifier-docs/docs/modules/tools/todo.md`, `amplifier-docs/docs/modules/hooks/todo_reminder.md`) and through the behavior patterns visible in consuming code (the Kepler sidecar, frontend store, TUI widget).

**Why it matters**: I cannot confirm exactly how the hook determines "recently used" (the `recent_tool_threshold` parameter), how it formats the injection, or whether it has additional logic beyond what's documented. My findings about the hook's behavior are based on documentation and downstream consumers, not primary source code.

**Confidence**: High confidence in behavioral description (downstream tests confirm behavior), medium confidence in implementation details.

---

## Unknown 2: How the Orchestrator Handles Fidelity Updates from Critic

**What I tried**: The `critic.md` agent prompt (line 263) says: "You do NOT need to call update_fidelity yourself — the orchestrator handles this after your delegation returns." I searched for how the orchestrator does this but found no orchestrator source code that parses critic JSON output and calls `update_fidelity`.

The recent git commit `1ed8932` says "fix: enforce mandatory fidelity updates after every agent delegation" which suggests this was recently added or fixed. But I could not find the actual orchestrator code implementing this.

**Why it matters**: If the orchestrator does automatically call `update_fidelity` after critic delegations, the feedback loop is partially closed (at least for critic assessments). This would make the fidelity system more reliable than my analysis suggests — though still dependent on someone delegating to the critic in the first place.

**Confidence**: Low confidence. The git commit suggests the mechanism exists, but I couldn't verify the implementation.

---

## Unknown 3: How Often Todo vs Fidelity Are Actually Used in Practice

**What I tried**: I looked for usage logs, analytics, or telemetry that would show how often each tool is called in real sessions. Found none.

**Why it matters**: My analysis is structural — I can see that the todo tool has more reliability layers. But I cannot confirm whether these layers actually translate to higher usage rates. It's possible that the fidelity tool is used reliably within zerovector sessions despite its architectural disadvantages, or that the todo tool is ignored despite its nudges.

**Confidence**: Cannot assess. No telemetry data available.

---

## Unknown 4: The `hooks-todo-display` Module

**What I tried**: The fidelity reporter's source code references "hooks-todo-display" in two comments:
- Line 7: "same technique as hooks-todo-display"
- Line 53: "follows hooks-todo-display Colors class pattern"
- Line 72: "follows hooks-todo-display Symbols pattern"
- Line 302: "same pattern as hooks-todo-display"

This suggests there is a separate `hooks-todo-display` module that renders todo state to the terminal, similar to how `hooks-fidelity-reporter` renders fidelity state. I could not find this module in any local repository.

**Why it matters**: If `hooks-todo-display` exists as a separate module from `hooks-todo-reminder`, the todo ecosystem has even more components than I cataloged — a display hook for terminal output AND a reminder hook for LLM injection. This would further widen the gap with fidelity's single hook.

**Confidence**: High confidence that the module exists (referenced in code), low confidence on its exact behavior.

---

## Unknown 5: The `coordinator.todo_state` Capability Registration

**What I tried**: The `hooks-todo-reminder` documentation says it "Checks for `coordinator.todo_state` (populated by tool-todo)." I looked for the capability registration in the todo tool but couldn't find the source (it's an external GitHub repo). I also couldn't find `todo_state` referenced in the amplifier-core or amplifier-foundation codebases.

**Why it matters**: Understanding exactly how `todo_state` is registered and structured would confirm whether the todo tool uses the same capability pattern as the fidelity tool (`coordinator.register_capability`). If it does, the architectural difference is purely in the layers built on top.

**Confidence**: Medium. The pattern likely mirrors `zerovector.fidelity_state` but I cannot confirm.

---

## Unknown 6: Kepler WebSocket Todo Nesting Test Contents

**What I tried**: Found `amplifier-distro-kepler/src/hooks/__tests__/useWebSocket.todo-nesting.test.ts` in the file listing but did not read it (prioritized other files for breadth).

**Why it matters**: This test likely covers how nested child-agent todos are handled in the WebSocket layer, which would round out the picture of todo's child-agent support.

**Confidence**: High confidence this is a minor gap (other hierarchy tests cover the same territory from different angles).

---

## Unknown 7: Whether Fidelity's "Universal" Design Was Intentional or Aspirational

**What I tried**: The `fidelity.yaml` description says "Universal fidelity diagnostic capability for any Amplifier session." The `bundle.md` says the behavior is "an extractable, standalone layer that can be included by any Amplifier bundle." But it is NOT included in the foundation bundle.

The implementation plan (`2026-03-08-tool-fidelity-state.md`) and the v0.3 design docs focus on the zerovector use case. There's no plan to move fidelity to the foundation.

**Why it matters**: If the design intent was always "universal but opt-in," the reliability gap is a conscious trade-off. If the intent was to eventually promote fidelity to foundation-level, the current state is an incomplete migration.

**Confidence**: Medium. The "universal" language in the description suggests aspiration, but I found no migration plans.

---

## Questions Raised by These Findings

1. **Should fidelity adopt the todo pattern?** Could a `hooks-fidelity-reminder` hook fire on `provider:request` and nudge the LLM to run fidelity assessments when none have occurred recently?

2. **Is the orchestrator's automatic `update_fidelity` (commit 1ed8932) sufficient to close the loop?** Or does it only close the loop for critic delegations, leaving other agents' work untracked?

3. **Would promoting fidelity to foundation-level work?** The fidelity tool requires the zerovector critic agent and context files. Could a minimal fidelity behavior work without the full crew infrastructure?

4. **Does the todo tool's "VERY IMPORTANT" prompt reinforcement actually change LLM behavior?** Or are the 4 static prompt mentions equivalent to 1 once the context is long enough?

5. **Is there a performance cost to the todo hook's `provider:request` timing?** Running at priority 10 before every LLM call adds latency. Is this negligible or measurable?
