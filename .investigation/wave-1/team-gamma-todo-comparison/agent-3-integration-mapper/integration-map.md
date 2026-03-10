# Integration Map: Todo vs Fidelity — Cross-Boundary Analysis

## Executive Summary

The todo tool's reliability stems from its position in the **foundation layer** with **shallow composition depth**, **unconditional inclusion**, and **deep distro-level integration** (REST API, WebSocket events, disk persistence). The fidelity tool lives in the **zerovector bundle layer** with **deep composition depth** (3+ levels), **conditional inclusion**, **zero distro integration**, and a **confirmed composition bug** that required a defensive workaround (commit `6a0999e`). The architectural distance between the two tools is not incremental — it is a full layer-boundary gap.

---

## Boundary 1: Bundle Composition Depth

### Todo Composition Chain (2 levels, unconditional)

```
Kepler desktop.yaml
  └─ includes: foundation (git)
       └─ foundation bundle includes: behaviors/todo-reminder.yaml
            ├─ tool-todo (git module)
            └─ hooks-todo-reminder (git module, priority 10)
```

**Evidence**: `desktop.yaml:92` — `# tool-todo: inherited from foundation — no override needed`
**Evidence**: `foundation/behaviors/todo-reminder.yaml` — flat behavior, 2 modules, no transitive includes

### Fidelity Composition Chain (3+ levels, conditional)

```
ZeroVector bundle.md
  └─ includes: zerovector:behaviors/zerovector-crew
       └─ includes: zerovector:behaviors/fidelity
            ├─ hooks-fidelity-reporter (local module)
            ├─ tool-fidelity-state (local module)
            ├─ context (2 files)
            └─ agents: zerovector:critic
```

**Evidence**: `zerovector-crew.yaml:10` — `includes: - bundle: zerovector:behaviors/fidelity`
**Evidence**: `fidelity.yaml:25-31` — declares hooks and tools

### CONFIRMED COMPOSITION BUG

Commit `6a0999e` (2026-03-08): _"fix: declare fidelity modules directly in crew behavior (transitive include doesn't merge hooks)"_

This commit added **redundant declarations** of `hooks-fidelity-reporter` and `tool-fidelity-state` directly in `zerovector-crew.yaml` because the transitive include from `fidelity.yaml` **was not merging hooks into the mount plan**.

**Diff** (from git):
```yaml
# Added to zerovector-crew.yaml (already declared in fidelity.yaml)
hooks:
  - module: hooks-fidelity-reporter
    source: ../modules/hooks-fidelity-reporter

tools:
  - module: tool-fidelity-state
    source: ../modules/tool-fidelity-state
```

**Cross-boundary implication**: The `Bundle.compose()` method in `amplifier_foundation/bundle.py:121-123` calls `merge_module_lists()` for hooks and tools. At 3 levels of transitive inclusion, this merge is failing to propagate modules from the innermost behavior. The todo behavior never hits this because it's only 1 level deep (direct inclusion by foundation).

**This is the single most architecturally significant finding.** The composition system has a depth-dependent bug that silently drops modules.

---

## Boundary 2: State Persistence

### Todo State Persistence (3 layers)

| Layer | Mechanism | Location | Survives |
|-------|-----------|----------|----------|
| **In-memory** | `tool._todos` (Python list) | Tool instance on coordinator | Session only |
| **Disk (sidecar)** | `_save_todos_for_conversation()` | `~/.kepler/todos/{conversation_id}.json` | App restart |
| **Disk (metadata)** | `todo_meta.json` | `~/.kepler/todo_meta.json` | App restart |

**Evidence**: `stream_translator.py:969-984` — `_save_todos_for_conversation` persists to disk
**Evidence**: `routes/todos.py:46-63` — `_todo_meta` loaded from disk on router creation
**Evidence**: `routes/todos.py:99` — `getattr(tool, "_todos", [])` direct attribute access

### Fidelity State Persistence (1 layer)

| Layer | Mechanism | Location | Survives |
|-------|-----------|----------|----------|
| **In-memory** | `FidelityState` dataclass | Capability registry | Session only |

**No disk persistence. No sidecar integration. No REST API.**

**Evidence**: `tool_fidelity_state/__init__.py:180` — `coordinator.register_capability("zerovector.fidelity_state", state)` — capability only
**Evidence**: Search for "fidelity" in Kepler sidecar returns zero matches in Python/YAML files (only vendor library matches)

### Cross-boundary implication

The todo tool's state is accessible via TWO interfaces:
1. **Formal**: `coordinator.get("tools", "todo")` → tool instance → `tool._todos`
2. **Informal**: Direct attribute access by sidecar: `getattr(tool, "_todos", [])`

The fidelity tool's state is accessible via ONE interface:
1. **Formal**: `coordinator.get_capability("zerovector.fidelity_state")` → `FidelityState.get_state()`

The informal interface (#2 for todo) is what enables the Kepler sidecar's deep integration. The fidelity tool's formal-only interface means no external system can observe or persist its state without going through the capability registry — which the Kepler sidecar doesn't know about.

---

## Boundary 3: Hook Timing and Injection Point

### Todo Reminder Hook

| Property | Value | Source |
|----------|-------|--------|
| **Fires on** | `provider:request` | Before every LLM API call |
| **Injection role** | `user` | Configured in behavior YAML |
| **Ephemeral** | `true` | Not stored in history |
| **Placement** | `append_to_last_tool_result` | Contextual, attached to tool output |
| **Priority** | `10` | Runs early |

**Key**: `provider:request` fires RIGHT BEFORE the LLM processes messages. The todo state is injected at the **latest possible moment** before the model sees it. This guarantees visibility.

### Fidelity Reporter Hook

| Property | Value | Source |
|----------|-------|--------|
| **Fires on** | `tool:post`, `prompt:complete` | After tool execution, after assistant response |
| **Injection role** | `system` | Hardcoded |
| **Ephemeral** | `true` | Not stored in history |
| **Placement** | New message | Separate injection, not appended |
| **Priority** | `50` | Runs late |

**Key**: `tool:post` and `prompt:complete` fire AFTER things happen. The ephemeral injection is placed into the context but must survive until the NEXT `provider:request` to be seen by the LLM. Whether the orchestrator preserves ephemeral injections across this gap depends on orchestrator implementation.

### Cross-boundary implication

The todo hook injects at the **consumption boundary** (right before the LLM reads). The fidelity hook injects at the **production boundary** (right after something happens). The gap between production and consumption is where ephemeral state can be lost, depending on orchestrator behavior at turn boundaries.

Additionally, the todo hook uses `append_to_last_tool_result=True` which piggybacks on existing messages. The fidelity hook creates a standalone injection. The `HookResult.append_to_last_tool_result` flag (defined in `models.py:212-220`) was specifically designed for the todo use case — it ensures the reminder appears in the natural flow of tool results, not as a disconnected system message.

---

## Boundary 4: Distro-Level Integration (Kepler)

### Todo: Deep Integration

The Kepler distro has **four distinct integration points** with the todo tool:

1. **REST API** (`routes/todos.py`): Full CRUD — GET/POST/PUT/DELETE for individual todos, bulk operations, stats endpoint. 329 lines of dedicated code.

2. **WebSocket Events** (`stream_translator.py`): `todo_update` event type emitted on every tool:post for the todo tool. Includes `stats`, `conversationId`, `parentTaskId`, `agentName`.

3. **Child Session Nesting** (`stream_translator.py:894-965`): `_emit_child_todo_update` handles child agent todo trees, nesting them under parent tasks with stable `parentTaskId` fallback (`agent-group:{session_id}`).

4. **Cross-Session Persistence** (`stream_translator.py:969-984`): `_save_todos_for_conversation` writes todo state to `~/.kepler/todos/{conversation_id}.json`. The chat route sends `todo_restore` on WebSocket connect.

5. **Frontend Store** (`src/lib/stores/todo-store.ts`): Dedicated Svelte store with tests for persistence, agent names, activeForm rendering.

### Fidelity: Zero Integration

No Kepler sidecar code references the fidelity tool, fidelity state, fidelity hooks, or any `zerovector.*` capability. The fidelity system exists entirely within the amplifier-core session boundary — invisible to the distro layer.

### Cross-boundary implication

This is the **widest gap** between the two tools. Todo has been adopted as a first-class citizen of the desktop application with its own API, persistence, UI store, and test suite. Fidelity is a session-internal module with no external visibility. Making fidelity work "like todo" would require replicating this entire integration surface.

---

## Boundary 5: Session Delegation

### Todo in Child Sessions

When a parent session spawns a child (via `PreparedBundle.spawn()`):
1. Child gets a **fresh** todo tool instance (new `tool._todos = []`)
2. Parent's todos are NOT inherited
3. BUT: The Kepler stream translator **intercepts** child todo events
4. Child todos are emitted as `todo_update` with `parentTaskId` and `agentName`
5. The frontend nests child todos under the parent's in-progress task

**Evidence**: `test_child_todo_merging.py` — extensive test suite for this behavior (287 lines)
**Evidence**: `test_todo_hierarchy.py` — tests for todo nesting across delegation

### Fidelity in Child Sessions

When a parent session spawns a child:
1. Child gets a **fresh** fidelity state (new `FidelityState()`)
2. Parent's fidelity scores are NOT inherited
3. No stream translator integration — child fidelity is invisible to parent
4. No aggregation of child fidelity scores into parent context

### Cross-boundary implication

The todo tool has **bidirectional visibility** across the delegation boundary: parent sees child todos (via stream translator), and each session manages its own. Fidelity has **no cross-session visibility** — each session's fidelity is isolated and invisible to the broader system.

---

## Boundary 6: Mode System Interaction

### Todo: Mode-Independent

The todo tool functions identically regardless of which mode is active. It's composed from foundation, which is included unconditionally. No mode gates, no conditional behavior.

### Fidelity: Mode-Entangled

The fidelity system is composed via `zerovector-crew.yaml`, which also declares the mode system (`hooks-mode`, `tool-mode`). The zerovector bundle has a standing order:

> BEFORE you write ANY code... Suggest the matching `/crew-*` mode to the user... WAIT for the user to activate the mode or explicitly opt out

The fidelity system is architecturally entangled with the crew/mode system even though it's declared as a "universal fidelity diagnostic layer" that "can be included by any Amplifier bundle."

**Evidence**: `fidelity.yaml:20-23` describes itself as extractable, but it's only ever included via `zerovector-crew.yaml` which also includes mode infrastructure.

### Cross-boundary implication

The fidelity behavior claims to be composable independently, but in practice it's only composed through the zerovector crew behavior, which brings mode dependencies, 5 agent definitions, and 4 context files. A bundle that wants JUST fidelity must include `behaviors/fidelity.yaml` directly, bypassing the crew — but this path has the transitive include bug documented above.

---

## Summary Table: Integration Distance from Kernel

| Boundary | Todo | Fidelity | Gap |
|----------|------|----------|-----|
| Composition depth | 2 levels | 3+ levels | Fidelity hits known merge bug |
| Bundle layer | Foundation (always loaded) | ZeroVector (conditional) | Fidelity requires specific bundle |
| State layers | 3 (memory + 2 disk) | 1 (memory only) | No fidelity persistence |
| Injection timing | `provider:request` (before LLM) | `tool:post`/`prompt:complete` (after) | Fidelity injection may be lost |
| Sidecar REST API | Full CRUD (329 LOC) | None | Zero external visibility |
| WebSocket events | `todo_update` with nesting | None | Zero frontend integration |
| Child session support | Stream translator + nesting | None | Fidelity isolated per session |
| Mode dependency | None | Entangled via crew | Not independently composable |
| Distro test coverage | 4 test files (500+ lines) | 0 test files | Untested at distro level |
