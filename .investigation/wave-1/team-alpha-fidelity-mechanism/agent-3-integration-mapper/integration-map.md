# Integration Map: Fidelity Mechanism Cross-Boundary Analysis

> Agent: Integration Mapper (WHERE/WHY)  
> Investigation: team-alpha-fidelity-mechanism, wave-1  
> Date: 2026-03-09

---

## Mechanisms in Scope

| # | Mechanism | Type | Location |
|---|-----------|------|----------|
| A | `hooks-fidelity-reporter` | Hook module | `modules/hooks-fidelity-reporter/` |
| B | `tool-fidelity-state` | Tool module | `modules/tool-fidelity-state/` |
| C | `hooks-crew-gate` | Hook module | `modules/hooks-crew-gate/` |
| D | Crew mode definitions | Mode YAML | `modes/crew*.md` |
| E | Context files (fidelity-framework, crew-instructions, using-zerovector) | Context injection | `context/` |
| F | Behavior composition (fidelity.yaml, zerovector-crew.yaml) | Bundle layer | `behaviors/` |
| G | Amplifier kernel hook system | Kernel | `amplifier-core/amplifier_core/hooks.py` |
| H | Amplifier kernel coordinator | Kernel | `amplifier-core/amplifier_core/coordinator.py` |
| I | Amplifier session system | Kernel | `amplifier-core/amplifier_core/session.py` |
| J | Sub-agent sessions (critic, builder, etc.) | Runtime | Spawned by orchestrator |
| K | Recipe engine (fidelity-convergence.yaml) | Orchestration | `recipes/` |

---

## Boundary 1: Fidelity Hook ↔ Kernel Hook Pipeline

### CRITICAL FINDING: `action="continue"` drops ephemeral context injection

**What crosses the boundary:** The fidelity reporter hook returns a `HookResult` to the kernel's `emit()` pipeline.

**The mismatch:** Both `hooks-fidelity-reporter` (line 310) and `hooks-crew-gate` (line 181) return:
```python
HookResult(
    action="continue",          # ← THIS IS THE PROBLEM
    context_injection=text,     # Ephemeral routing advice for the LLM
    ephemeral=True,
    user_message=dashboard,
    user_message_level="info",
)
```

But the kernel's `emit()` method (`hooks.py:162-164`) only collects `context_injection` from results with `action="inject_context"`:
```python
# hooks.py:162-164
if result.action == "inject_context" and result.context_injection:
    inject_context_results.append(result)
```

And the coordinator's `process_hook_result()` (`coordinator.py:361`) also gates on the action:
```python
# coordinator.py:361
if result.action == "inject_context" and result.context_injection:
    await self._handle_context_injection(result, hook_name, event)
```

For `action="continue"`, none of these branches execute. The ephemeral routing advice is **silently dropped**.

Furthermore, the `emit()` method returns a fresh `HookResult(action="continue", data=current_data)` when no special actions occurred (`hooks.py:186`). This new HookResult has `context_injection=None` and `user_message=None`. So even the `user_message` from individual hooks is lost in the pipeline.

**What still works:** Both hooks write to `sys.stdout` directly (`fidelity-reporter:304`, `crew-gate:169-178`), bypassing the kernel pipeline entirely. The visual ANSI dashboard renders because it doesn't depend on HookResult processing.

**What is lost:**
1. **Ephemeral routing advice** — The fidelity reporter's plain-text routing guidance (e.g., "Priority gap: implementation (0.40) — Route to builder") never reaches the LLM's context. The LLM sees the visual dashboard (via stdout) but doesn't get machine-readable routing state injected into its conversation.
2. **Crew gate warnings** — The crew gate's `_SOFT_REMINDER` and `_HARD_WARNING` injections (telling the LLM to suggest a crew mode) never reach the LLM's context window.
3. **User messages** — The `user_message` field from both hooks is lost in the emit() pipeline.

**Impact on reported symptoms:**
- "Sometimes it only picks up intent" — Without routing advice, the LLM doesn't know which lens to address next.
- "Sometimes it skips entirely" — Without crew gate warnings reaching the LLM, there's no programmatic nudge to suggest a mode or call update_fidelity.

**Evidence chain:**
- Hook side: `hooks-fidelity-reporter/__init__.py:310` returns `action="continue"`
- Hook side: `hooks-crew-gate/__init__.py:181` returns `action="continue"`
- Kernel side: `hooks.py:163` checks `result.action == "inject_context"`
- Kernel side: `coordinator.py:361` checks `result.action == "inject_context"`
- Kernel side: `hooks.py:186` returns bare `HookResult(action="continue", data=current_data)`
- Kernel model: `models.py:131` documents that `context_injection` is "for action='inject_context'"

**Root cause:** The hooks were designed as "non-blocking observers" (fidelity-reporter docstring: "never modifies `action` away from `continue`"). But the kernel treats `inject_context` as a non-blocking action that ALSO proceeds normally — it's not `deny`. The hooks should use `action="inject_context"` to get their context delivered.

---

## Boundary 2: Fidelity Hook ↔ Crew-Gate Hook (Same-Event Cohabitation)

**What crosses the boundary:** Both hooks register for the same two events: `tool:post` and `prompt:complete`. They share the kernel's sequential execution pipeline.

### Priority Ordering
| Hook | Priority | Events |
|------|----------|--------|
| `hooks-crew-gate` | 10 (default from config) | `prompt:complete`, `tool:post` |
| `hooks-fidelity-reporter` | 50 (default from config) | `tool:post`, `prompt:complete` |

Crew-gate fires first (lower priority number = earlier execution). Since crew-gate always returns `action="continue"`, fidelity-reporter always gets to execute.

### Latent Risk: Short-Circuit Denial
If crew-gate were ever changed to return `action="deny"` (e.g., to block tool execution without a crew mode), the kernel's `emit()` would short-circuit at `hooks.py:155-156`:
```python
if result.action == "deny":
    return result
```
This would prevent the fidelity reporter from ever firing on that event. The dashboard would go silent without any error — a silent failure mode.

### State Independence
Both hooks read coordinator capabilities but don't write to shared state:
- Fidelity reporter reads: `coordinator.get_capability("zerovector.fidelity_state")`
- Crew gate reads: `coordinator.get_capability("modes.active")` (and fallbacks)

No data flows between the two hooks. They are independently correct but interact through the shared event pipeline.

### Double-Rendering on Same Turn
When `update_fidelity` is called (a tool), both hooks fire on `tool:post`. Then when the LLM's response completes, both fire again on `prompt:complete`. In a single turn where `update_fidelity` is called:
1. `tool:post` → crew-gate fires → fidelity-reporter fires (dashboard renders)
2. `prompt:complete` → crew-gate fires → fidelity-reporter fires (dashboard renders again)

This produces **two dashboard renders** per turn when `update_fidelity` is called. The user may perceive this as "fires twice."

---

## Boundary 3: Behavior Composition ↔ Module Loading (Double Declaration)

**What crosses the boundary:** `zerovector-crew.yaml` BOTH includes the fidelity behavior AND directly declares the same modules.

```yaml
# zerovector-crew.yaml
includes:
  - bundle: zerovector:behaviors/fidelity   # Declares hooks-fidelity-reporter + tool-fidelity-state

hooks:
  - module: hooks-fidelity-reporter          # ALSO declares hooks-fidelity-reporter
    source: ../modules/hooks-fidelity-reporter

tools:
  - module: tool-fidelity-state              # ALSO declares tool-fidelity-state
    source: ../modules/tool-fidelity-state
```

**Historical context:** Commit `6a0999e` explains: "declare fidelity modules directly in crew behavior (transitive include doesn't merge hooks)". This means the bundle loader does NOT merge hooks from transitive includes. Only direct declarations work.

**Current state:** The double declaration is harmless because the include's hooks are silently ignored. But this is architecturally fragile:
- If the bundle loader is ever fixed to merge transitive hooks, both declarations take effect, and the hook registers **twice** — producing **four** dashboard renders per turn (2 registrations × 2 events).
- The `tool-fidelity-state` tool would also mount twice. The second `mount()` would call `coordinator.mount("tools", tool, name="update_fidelity")`, which logs a warning ("Replacing existing update_fidelity") and replaces the first instance. This means the first `FidelityState` (and its capability registration) would be orphaned — the hook reads from capability `zerovector.fidelity_state` which points to the FIRST instance, but the tool writes to the SECOND instance. **Scores updated via the tool would not be visible to the hook.**

**Impact on reported symptoms:**
- "Sometimes it fires twice" — If the bundle loader partially merges (hooks but not tools, or vice versa), you get double-fired hooks.

---

## Boundary 4: Fidelity Tool ↔ Mode Tool Policies

**What crosses the boundary:** Mode definitions include `update_fidelity` in their `tools.safe` list, and set `default_action: block`.

All six crew modes (`crew`, `crew-build`, `crew-product`, `crew-platform`, `crew-research`, `crew-content`) declare:
```yaml
tools:
  safe:
    - update_fidelity
  default_action: block
```

**When a crew mode is active:** `update_fidelity` is explicitly in the safe list → allowed without warning.

**When NO mode is active:** The mode tool policy doesn't apply. Tools are governed by the kernel's default policy. `update_fidelity` is available as long as the `tool-fidelity-state` module is mounted.

**Key insight:** The tool itself has NO dependency on mode state. The `UpdateFidelityTool.execute()` method doesn't check for active modes. It always works if mounted.

But the CONTEXT that tells the LLM to CALL the tool depends heavily on mode state (see Boundary 5).

---

## Boundary 5: Fidelity Context ↔ Crew Instructions Context (Mode-Gated Knowledge)

**What crosses the boundary:** Context files are included at different layers, creating mode-dependent knowledge availability.

### Context Availability Matrix

| Context File | Always Available | Crew Mode Required |
|---|---|---|
| `using-zerovector.md` | ✅ (via fidelity behavior) | — |
| `fidelity-framework.md` | ✅ (via fidelity behavior) | — |
| `crew-instructions.md` | — | ✅ (via zerovector-crew behavior) |
| `domain-tuning.md` | — | ✅ (via zerovector-crew behavior) |
| `zerovector-principles.md` | ✅ (via bundle.md) | — |

**The critical gap:** `crew-instructions.md` contains the **MANDATORY update_fidelity protocol**:
```
EVERY time a delegate() call returns, your NEXT action MUST be update_fidelity.
No exceptions.
```

This instruction is only available when a crew mode is active (it's included via `zerovector-crew.yaml` → `context: include: crew-instructions.md`).

**Without a crew mode active:**
- The LLM has `using-zerovector.md` (which says "suggest a crew mode before creating artifacts")
- The LLM has `fidelity-framework.md` (which describes lenses and says "Always call update_fidelity after a fidelity assessment")
- The LLM does NOT have the convergence loop protocol or the mandatory update checklist

**Reinforcement analysis:**
- `using-zerovector.md` and the `bundle.md` STANDING-ORDER both say "suggest crew mode first" → **reinforcing**
- `fidelity-framework.md` says "call update_fidelity after every assessment" → **partial**
- `crew-instructions.md` says "call update_fidelity after EVERY delegation" → **the strongest instruction, but mode-gated**

**The contradiction that isn't:** The critic agent says "You do NOT need to call update_fidelity yourself — the orchestrator handles this." This is a deliberate SEPARATION OF CONCERN, not a contradiction. The critic produces scores; the orchestrator persists them. But this means the orchestrator (root session LLM) MUST have the crew-instructions context to know this responsibility exists.

**Impact on reported symptoms:**
- "Sometimes it works only in crew-build mode" — The MANDATORY update_fidelity instructions are only injected when a crew mode is active. Without them, the LLM may not call update_fidelity consistently.
- "Sometimes it skips entirely" — Without crew-instructions.md, the LLM has no convergence protocol to follow.

---

## Boundary 6: Root Session ↔ Sub-Agent Session (FidelityState Isolation)

**What crosses the boundary:** Each session has its own `ModuleCoordinator`, which has its own capabilities registry, which has its own `FidelityState` instance.

### The Session Boundary Problem

When `tool-fidelity-state` mounts, it:
1. Creates a `FidelityState` instance (`__init__.py:171`)
2. Registers it as capability `zerovector.fidelity_state` (`__init__.py:180`)
3. Registers `state.update_fidelity` as capability `zerovector.update_fidelity` (`__init__.py:188`)
4. Mounts the `UpdateFidelityTool` (`__init__.py:175`)

Each session does this independently. The root session's FidelityState is a DIFFERENT object from any child session's FidelityState.

```
Root Session
├── Coordinator
│   ├── FidelityState(A)         ← root's state
│   ├── update_fidelity tool     ← writes to A
│   └── fidelity-reporter hook   ← reads from A
│
├── Child Session (critic)
│   ├── Coordinator
│   │   ├── FidelityState(B)     ← critic's state (DIFFERENT OBJECT)
│   │   └── update_fidelity tool ← writes to B (NOT to A)
│   │
│   └── (critic produces JSON scores in its text output)
│
└── Orchestrator (root LLM)
    └── Must parse critic's output → call update_fidelity → writes to A → dashboard updates
```

**The deliberate design:** The critic produces structured JSON scores. The orchestrator (root session LLM) is instructed to parse these and call `update_fidelity` in the root session. This ensures the dashboard (which reads from the root's FidelityState) reflects the latest scores.

**The fragile link:** This depends ENTIRELY on the LLM following context instructions. There is NO programmatic mechanism to propagate child session scores to the root session. If the LLM:
- Forgets to call `update_fidelity` after delegation → dashboard stays frozen
- Passes wrong scores → dashboard shows incorrect state
- Skips the critic entirely → no scores at all

Commit `1ed8932` ("enforce mandatory fidelity updates after every agent delegation") added stronger context instructions. Commit `9a49682` ("remove phantom update_fidelity instruction from critic") clarified that only the orchestrator should call it. But these are both context-level fixes, not programmatic guarantees.

**Impact on reported symptoms:**
- "Sometimes the fidelity hook fires" — Hook fires but FidelityState has no data (update_fidelity not called), so it returns `_CONTINUE` (no-op) at line 299: `if not state.get("lens_scores"): return _CONTINUE`
- "Dashboard stays at 0.00" — The orchestrator didn't call update_fidelity after delegation
- "Sometimes it fires twice" — Hook fires on both tool:post and prompt:complete but with stale state

---

## Boundary 7: Crew-Gate ↔ Bundle Composition (Not Yet Wired)

**What crosses the boundary:** `hooks-crew-gate` exists as code in `modules/hooks-crew-gate/` but is NOT declared in any behavior YAML.

**Evidence:**
- Git status shows `?? modules/hooks-crew-gate/` (untracked)
- `fidelity.yaml` declares only `hooks-fidelity-reporter`
- `zerovector-crew.yaml` declares `hooks-mode` and `hooks-fidelity-reporter` — no crew-gate
- Commit `1f838c7` ("add crew-gate roadmap") suggests it's in development

**The implication:** The crew-gate hook's `_SOFT_REMINDER` and `_HARD_WARNING` context injections are NOT being delivered to ANY session. The module exists but has no mount path. Even if it were mounted, the `action="continue"` issue (Boundary 1) would prevent its context injections from reaching the LLM.

**Current state of mode-gate enforcement:** Without the crew-gate hook, the only mode-gate is the `using-zerovector.md` context instruction (which says "suggest crew mode before creating artifacts") and the `bundle.md` STANDING-ORDER. Both are soft context — no programmatic enforcement.

---

## Boundary 8: Recipe Engine ↔ Fidelity Convergence (Parallel Path)

**What crosses the boundary:** The fidelity-convergence recipe (`recipes/fidelity-convergence.yaml`) implements the convergence loop as a recipe, while the crew modes implement it as LLM-orchestrated delegation.

These are **two parallel implementations** of the same conceptual loop:

| Aspect | Recipe Path | Mode Path |
|--------|------------|-----------|
| Orchestration | Recipe engine steps | LLM follows crew-instructions.md |
| Score extraction | `parse_json: true` + bash `extract-score` | LLM parses critic output |
| update_fidelity | NOT called (recipe doesn't call tools) | LLM must call manually |
| Dashboard | NOT updated (no tool:post event for recipe steps) | Updated when LLM calls update_fidelity |
| Max iterations | `max_while_iterations: 8` | Context instruction: "Maximum iterations: 8" |
| Convergence check | `while_condition` in YAML | LLM judgment |

**The recipe path bypasses fidelity tracking.** The recipe uses `agent: "zerovector:critic"` to assess lenses and `parse_json: true` to extract scores, but it never calls `update_fidelity`. The fidelity dashboard stays at 0.00 for the entire recipe execution.

This means: if a user uses the recipe instead of the mode, they get convergence but NO visible fidelity dashboard, NO ephemeral routing advice, and NO integration with the hook system.

---

## Cross-Cutting Concerns

### 1. The "Soft Enforcement" Problem
Every enforcement mechanism in the fidelity system is context-based (LLM instructions) rather than programmatic:
- "Call update_fidelity after every delegation" — context instruction, not code
- "Suggest crew mode before creating artifacts" — context instruction, not code
- "Don't declare convergence without evidence" — context instruction, not code

The only programmatic elements are:
- The hook reads FidelityState and renders if data exists
- The tool writes to FidelityState when called
- The kernel emits events that trigger hooks

The entire loop between "scores produced" → "scores persisted" → "dashboard updated" depends on LLM compliance.

### 2. The stdout Bypass Pattern
Both hooks discovered independently that writing to `sys.stdout` directly is the only reliable display path. The kernel's HookResult pipeline doesn't reliably deliver `context_injection` or `user_message` from hooks using `action="continue"`. This suggests a systemic issue with the hook API's design — the most common use case (observe + inject context) requires using `action="inject_context"`, but hooks that want to be "non-blocking" gravitate toward `action="continue"`.

### 3. The Deduplication Gap
The bundle composition layer doesn't deduplicate module declarations across `includes` and direct declarations. This creates a maintenance burden where developers must manually ensure modules aren't declared at multiple levels. The current workaround (transitive includes don't merge hooks) prevents double registration but means the `includes` relationship is broken for hooks.

---

## Design Implications

### 1. The Fidelity Mechanism Is a Distributed System
The fidelity mechanism spans 4 layers: context (instructions) → tool (state management) → hook (display) → kernel (event pipeline). No single layer owns the complete lifecycle. This is architecturally clean but creates failure modes at every boundary.

### 2. The LLM Is a Load-Bearing Architectural Element
The orchestrator LLM is not just a user of the fidelity system — it IS the convergence engine. It reads scores, decides routing, calls tools, and manages state. If the LLM fails to follow instructions, the entire mechanism silently degrades. There is no health check, no watchdog, no fallback.

### 3. The Hook API Has a Design Tension
`action="continue"` means "proceed, I have nothing to add." `action="inject_context"` means "proceed AND deliver my content." The naming makes `inject_context` sound more aggressive than it is — it doesn't block or modify. Hooks that want to be "polite observers" choose `continue` and accidentally silence themselves.

### 4. Session Isolation Is Both Feature and Limitation
Session-scoped FidelityState prevents child sessions from interfering with the root dashboard (good). But it also prevents programmatic score propagation from child to parent (limitation). The bridge is the LLM's attention span.
