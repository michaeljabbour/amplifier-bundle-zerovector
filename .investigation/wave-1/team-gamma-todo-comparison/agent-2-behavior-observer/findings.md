# Behavior Observer Findings: Todo vs Fidelity Tool Reliability

## Executive Summary

The Amplifier todo tool's reliability stems from a **closed feedback loop at the foundation level** with **four reinforcement mechanisms**, while the fidelity tool operates as an **open loop in a single bundle** with **one reinforcement mechanism**. After examining 27+ real artifacts across 6 repositories, the behavioral difference is stark: the todo tool doesn't need the LLM to remember it exists, while the fidelity tool depends entirely on LLM initiative.

---

## Finding 1: Closed Loop vs Open Loop — The Decisive Architectural Difference

### Todo: Closed Feedback Loop

```
LLM creates todos → State stored in coordinator.todo_state
                     ↓
Hook fires on provider:request (BEFORE every LLM call)
                     ↓
Hook reads todo_state → Injects status into context
                     ↓
LLM sees "[completed] X, [in_progress] Y, [pending] Z"
                     ↓
LLM updates todos (loop repeats)
```

The hook fires on `provider:request` — **before every LLM call**. The LLM cannot avoid seeing its todo state. Even if the LLM forgets to use the todo tool, the hook injects a gentle reminder: "The todo tool hasn't been used recently. If you're working on tasks that would benefit from tracking progress, consider using the todo tool."

This is **proactive injection**. The system pushes state to the LLM.

### Fidelity: Open Feedback Loop

```
Critic agent produces fidelity assessment → calls update_fidelity tool
                                            ↓
State stored in zerovector.fidelity_state capability
                                            ↓
Hook fires on tool:post / prompt:complete (AFTER turns)
                                            ↓
Hook reads state → Injects routing advice + renders dashboard
                                            ↓
LLM sees routing advice... but nothing forces LLM to call update_fidelity again
```

The hook fires on `tool:post` and `prompt:complete` — **after the action**. The fidelity state only updates when the LLM (or critic agent) explicitly calls `update_fidelity`. There is **no nudge** to call it. There is no "fidelity tool hasn't been used recently" reminder.

This is **reactive display**. The system shows whatever was last written, but doesn't push the LLM to update.

**Evidence**: `hooks-todo-reminder` config has `inject_role: user`, `priority: 10` (runs early). `hooks-fidelity-reporter` has `priority: 50` (runs late, after other hooks).

---

## Finding 2: Four Layers of Prompt Reinforcement vs One

The todo tool is mentioned in **4 distinct locations** in the system prompt chain. The fidelity tool has **1**.

### Todo Prompt Reinforcement (4 of 4 layers active)

| Layer | Location | Exact Text |
|-------|----------|------------|
| 1. Agent Base | `common-agent-base.md:57` | "Use the todo tool to plan the task if required" |
| 2. Agent Base | `common-agent-base.md:143` | "IMPORTANT: Always use the todo tool to plan and track tasks throughout the conversation" |
| 3. Bundle Instructions | `foundation/bundle.md:80` | "IMPORTANT: For anything more than trivial tasks, make sure to use the todo tool" |
| 4. Bundle Instructions | `foundation/bundle.md:154` | "VERY IMPORTANT: Make sure to use the actual todo tool for todo lists, don't do your own task tracking, there is code behind use of the todo tool that is invisible to you" |
| 5. Hook Reminder | `hooks-todo-reminder` | Adaptive reminder injected when tool not recently used |

Layer 4 is particularly striking — it explicitly tells the LLM that there is "code behind use of the todo tool that is invisible to you." This creates a sense of obligation.

### Fidelity Prompt Reinforcement (1 of 4 layers active)

| Layer | Location | Exact Text |
|-------|----------|------------|
| 1. Context File | `fidelity-framework.md:203` | "Always call update_fidelity after a fidelity assessment" |
| 2. Critic Agent | `critic.md:263` | "You do NOT need to call update_fidelity yourself — the orchestrator handles this" |

Layer 2 actually **discourages** the LLM from calling the tool. The critic agent prompt says the orchestrator handles it. This creates ambiguity about who owns the update responsibility.

---

## Finding 3: Foundation-Level vs Bundle-Level Deployment

### Todo: Always-on at the foundation level

The `amplifier-foundation/bundle.md` (line 11) includes:
```yaml
includes:
  - bundle: foundation:behaviors/todo-reminder
```

This means **every session using the foundation bundle** (which is every standard Amplifier session) gets the todo tool and its reminder hook. The todo tool is classified as "Low" risk in the LetsGo policy (line 12 of `tool-policy-awareness.md`), executing freely without approval.

### Fidelity: Opt-in at the zerovector bundle level

The `amplifier-bundle-zerovector/bundle.md` (line 9) includes:
```yaml
includes:
  - bundle: zerovector:behaviors/zerovector-crew
```

The fidelity behavior is only included when a zerovector crew mode is activated. It is NOT part of the foundation. The zerovector bundle.md even has a `<STANDING-ORDER>` that says "This is NOT optional" — but the tool itself IS optional because it's not in the foundation.

---

## Finding 4: UI Surface Area — 4 Surfaces vs 2

### Todo UI Surfaces (4)

| Surface | Repository | Technology | Lines |
|---------|-----------|------------|-------|
| 1. LLM context injection | Foundation (hook) | Ephemeral HookResult | Configurable |
| 2. TUI side panel | amplifier-tui | Textual widget | 137 |
| 3. Desktop GUI store | amplifier-distro-kepler | Zustand + React | 103 |
| 4. WebSocket real-time sync | amplifier-distro-kepler | WS events | Multi-file |

The desktop GUI has a dedicated `todo-store.ts` with `mergeTodos()` that handles parent-child scoping, localStorage persistence per `conversationId`, and real-time WebSocket sync.

### Fidelity UI Surfaces (2)

| Surface | Repository | Technology | Lines |
|---------|-----------|------------|-------|
| 1. LLM context injection | zerovector (hook) | Ephemeral HookResult | ~270 |
| 2. ANSI terminal dashboard | zerovector (hook) | sys.stdout.write() | ~240 |

The fidelity dashboard is rendered directly to stdout with ANSI escape codes. No dedicated GUI component, no persistence, no WebSocket sync.

---

## Finding 5: Child Agent Awareness — Elaborate vs None

### Todo: Full Parent-Child Hierarchy

The `StoreTodo` interface (Kepler `todo-store.ts`) has:
- `parentId?: string` — Parent task ID for subtasks
- `milestoneId?: string` — Milestone/epic grouping  
- `agentName?: string` — Child agent identity
- `priority?: 'low' | 'medium' | 'high'`
- `effort?: string` — Effort estimate

The `mergeTodos()` function handles:
- Child-agent scoped updates (replace only todos under a given parent)
- Root-scoped updates (replace root todos, preserve child-agent todos)
- Race condition fix: `_parent_todo_at_spawn` captures parent's in-progress todo at spawn time

There are **307 lines of test code** just for todo hierarchy tracking, plus **287 lines** for child todo merging.

### Fidelity: Session-Level Only

`FidelityState` is a flat dataclass:
- `lens_scores: dict[str, float]`
- `overall: float`
- `target: float`
- `domain: str`
- `priority_gap: dict[str, Any]`

No parent-child awareness. No agent scoping. No multi-session tracking.

---

## Finding 6: Persistence vs Ephemeral

### Todo Persistence

- **Sidecar**: `_save_todos_for_conversation` saves to disk on todo_update events
- **Frontend**: `localStorage.setItem(`kepler_todos_${conversationId}`, ...)` snapshots after every merge
- **Restoration**: `todo_restore` WebSocket event restores on reconnection
- **Tests verify**: `test_stream_translator_saves_todos_on_update`, `test_chat_route_restores_todos_on_connect`, `test_frontend_handles_todo_restore`

### Fidelity Persistence

None. `FidelityState` lives in memory for the session. When the session ends, state is gone. No save, no restore, no localStorage.

---

## Finding 7: Test Coverage Distribution

### Todo Test Artifacts (8 files across 3 repositories)

| File | Repository | Lines | Focus |
|------|-----------|-------|-------|
| test_todo_persistence.py | kepler/sidecar | 27 | Disk + WS persistence |
| test_todo_hierarchy.py | kepler/sidecar | 307 | Parent-child mapping, race conditions |
| test_child_todo_merging.py | kepler/sidecar | 287 | Dual emission, parentTaskId, agentName |
| todo-store.test.ts | kepler/frontend | 127 | mergeTodos logic |
| todo-store-persistence.test.ts | kepler/frontend | 28 | localStorage snapshot |
| todo-store-activeform.test.ts | kepler/frontend | 21 | activeForm field mapping |
| todo-agent-name.test.ts | kepler/frontend | 28 | agentName field mapping |
| useWebSocket.todo-nesting.test.ts | kepler/frontend | (exists) | WS nesting |

**Total: 825+ lines of todo-specific tests across 8 files in 2 codebases**

### Fidelity Test Artifacts (4 files in 1 repository)

| File | Repository | Lines | Focus |
|------|-----------|-------|-------|
| test_fidelity_state.py | zerovector | 280 | State, tool, mount |
| test_fidelity_reporter.py | zerovector | 364 | Dashboard, ephemeral, handle_event |
| test_fidelity_behavior.py | zerovector | 111 | YAML structure validation |
| test_fidelity_convergence.py | zerovector | 384 | Recipe structure validation |

**Total: 1,139 lines of fidelity-specific tests across 4 files in 1 codebase**

The fidelity tool actually has MORE test lines, but concentrated in structural validation. The todo tool's tests focus on behavioral correctness across system boundaries (sidecar→WS→frontend→localStorage).

---

## Finding 8: Behavioral Simplicity

### Todo: 3 Actions, 3 Statuses, 2 Fields Per Item

```typescript
action: "create" | "update" | "list"
status: "pending" | "in_progress" | "completed"
item: { content: string, activeForm: string, status: string }
```

The entire tool interface is 3 actions. The LLM sends a full list replacement every time. No incremental updates, no complex state transitions.

### Fidelity: 5 Lenses, 6 Domains, Structured JSON, Convergence Loop

```typescript
lens_scores: { intent_clarity, specification, implementation, quality, ship_readiness }
domain: "build" | "product" | "research" | "content" | "platform" | "general"
target: 0.0-1.0
priority_gap: { lens, score, recommendation }
overall: arithmetic_mean(lens_scores)
```

The tool requires the LLM to produce scores for 5 lenses, select a domain, and provide evidence. The convergence recipe adds a while-loop with up to 8 iterations, agent routing per lens, and JSON parsing.

---

## Synthesis: Why Todo Works and Fidelity Struggles

| Dimension | Todo | Fidelity | Impact |
|-----------|------|----------|--------|
| Feedback loop | Closed (hook→LLM→tool→hook) | Open (LLM must initiate) | **Decisive** |
| Prompt mentions | 5 reinforcements | 1 (plus 1 discouraging) | High |
| Deployment | Foundation (always-on) | Bundle (opt-in) | High |
| Complexity | 3 actions, flat list | 5 lenses, convergence loop | Medium |
| UI surfaces | 4 (LLM, TUI, GUI, WS) | 2 (LLM, stdout) | Medium |
| Child agents | Full hierarchy support | None | Medium |
| Persistence | Disk + localStorage | None | Low |
| Hook timing | Before LLM call (proactive) | After turn (reactive) | **Decisive** |

The two decisive factors are both about **automaticity**: the closed feedback loop and the proactive hook timing. The todo system works because the LLM cannot forget about it — the system ensures the state is visible at every decision point. The fidelity system requires the LLM to remember, which is exactly the failure mode that the todo tool was designed to prevent.
