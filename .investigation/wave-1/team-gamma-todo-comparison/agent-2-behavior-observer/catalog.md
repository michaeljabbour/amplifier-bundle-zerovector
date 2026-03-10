# Artifact Catalog: Todo Tool vs Fidelity Tool

Side-by-side inventory of every artifact examined. 27+ files read across 6 repositories.

---

## Todo Tool Ecosystem

### Core Modules

| # | Artifact | Path | Lines | Type | Key Attributes |
|---|----------|------|-------|------|----------------|
| 1 | Todo behavior bundle | `amplifier-foundation/behaviors/todo-reminder.yaml` | 15 | YAML config | Bundles tool-todo + hooks-todo-reminder; inject_role: user; priority: 10 |
| 2 | Tool documentation | `amplifier-docs/docs/modules/tools/todo.md` | 102 | Markdown | 3 actions (create/update/list); 3 statuses; "NOT for showing task progress to users" |
| 3 | Hook documentation | `amplifier-docs/docs/modules/hooks/todo_reminder.md` | 106 | Markdown | Triggers on provider:request; tracks tool usage via tool:post; adaptive messaging |

### System Prompt References

| # | Artifact | Path | Lines | Type | Key Attributes |
|---|----------|------|-------|------|----------------|
| 4 | Agent base context | `amplifier-foundation/context/shared/common-agent-base.md` | 152 | Markdown | 2 todo mentions: line 57 "Use the todo tool", line 143 "IMPORTANT: Always use the todo tool" |
| 5 | Foundation bundle | `amplifier-foundation/bundle.md` | 165 | Bundle | Line 11: includes todo-reminder behavior; Line 80: "IMPORTANT: use todo tool"; Line 154: "VERY IMPORTANT: use actual todo tool" |
| 6 | Tool policy | `amplifier-bundle-letsgo/context/tool-policy-awareness.md` | 48 | Markdown | Line 12: todo classified as "Low" risk, executes freely |

### Desktop GUI (Kepler)

| # | Artifact | Path | Lines | Type | Key Attributes |
|---|----------|------|-------|------|----------------|
| 7 | Todo store | `amplifier-distro-kepler/src/lib/stores/todo-store.ts` | 103 | TypeScript | Zustand store; StoreTodo interface with parentId, milestoneId, agentName; mergeTodos() with parent/child scoping; localStorage persistence |
| 8 | Store tests | `amplifier-distro-kepler/src/lib/__tests__/todo-store.test.ts` | 127 | TypeScript | mergeTodos root-scoped and child-scoped; preserves completed/cancelled; preserves agentName when parentId undefined |
| 9 | Persistence tests | `amplifier-distro-kepler/src/lib/__tests__/todo-store-persistence.test.ts` | 28 | TypeScript | Verifies localStorage snapshot keyed by conversationId |
| 10 | ActiveForm tests | `amplifier-distro-kepler/src/lib/__tests__/todo-store-activeform.test.ts` | 21 | TypeScript | Verifies activeForm field in interface and WS handler |
| 11 | AgentName tests | `amplifier-distro-kepler/src/lib/__tests__/todo-agent-name.test.ts` | 28 | TypeScript | Verifies agentName field in StoreTodo and WS mapping |

### Desktop Sidecar (Kepler)

| # | Artifact | Path | Lines | Type | Key Attributes |
|---|----------|------|-------|------|----------------|
| 12 | Persistence tests | `amplifier-distro-kepler/sidecar/tests/test_todo_persistence.py` | 27 | Python | Tests save-on-update, restore-on-connect, frontend todo_restore handling |
| 13 | Hierarchy tests | `amplifier-distro-kepler/sidecar/tests/test_todo_hierarchy.py` | 307 | Python | _current_in_progress_todo tracking; _parent_todo_at_spawn race condition fix; agent-group: fallback; reset clears tracking |
| 14 | Child merging tests | `amplifier-distro-kepler/sidecar/tests/test_child_todo_merging.py` | 287 | Python | Dual emission (agent_tool + todo_update); parentTaskId; agentName from session ID; stats computation; TodoWrite/todo_write variants |

### TUI

| # | Artifact | Path | Lines | Type | Key Attributes |
|---|----------|------|-------|------|----------------|
| 15 | Todo panel widget | `amplifier-tui/amplifier_tui/widgets/todo_panel.py` | 137 | Python | Textual Widget; docked right; auto-shows on items; [x]/[>]/[ ] prefixes; truncates at 50 chars |

### Core Framework

| # | Artifact | Path | Lines | Type | Key Attributes |
|---|----------|------|-------|------|----------------|
| 16 | HookResult model | `amplifier-core/amplifier_core/models.py` | 339 | Python | context_injection, ephemeral, append_to_last_tool_result, context_injection_role fields |
| 17 | Hooks API reference | `amplifier-core/docs/HOOKS_API.md` | 449 | Markdown | Patterns: Context Injection, Approval Gates, Output Control; ephemeral for "todo reminders that update frequently" |

**Todo Artifact Count: 17 files examined**

---

## Fidelity Tool Ecosystem

### Core Modules

| # | Artifact | Path | Lines | Type | Key Attributes |
|---|----------|------|-------|------|----------------|
| 1 | Fidelity behavior bundle | `amplifier-bundle-zerovector/behaviors/fidelity.yaml` | 40 | YAML config | Bundles hooks-fidelity-reporter + tool-fidelity-state + critic agent + 2 context files; version 0.3.0 |
| 2 | Tool source code | `amplifier-bundle-zerovector/modules/tool-fidelity-state/.../init.py` | 198 | Python | FidelityState dataclass; UpdateFidelityTool class; 5 lenses; _RECOMMENDATIONS dict; mount() with 3 capability registrations |
| 3 | Hook source code | `amplifier-bundle-zerovector/modules/hooks-fidelity-reporter/.../init.py` | 383 | Python | FidelityReporter class; render_dashboard (ANSI), render_ephemeral (plain text), handle_event; fires on tool:post + prompt:complete; priority 50 |

### Context & Documentation

| # | Artifact | Path | Lines | Type | Key Attributes |
|---|----------|------|-------|------|----------------|
| 4 | Fidelity framework | `amplifier-bundle-zerovector/context/fidelity-framework.md` | 225 | Markdown | 5 lenses defined; scoring rubric 0-1; domain calibration (6 domains); evidence requirements per lens |
| 5 | Convergence recipe | `amplifier-bundle-zerovector/recipes/fidelity-convergence.yaml` | 239 | YAML | 5 steps; while-loop with max 8 iterations; routes to weakest lens agent; parse_json on assessments |
| 6 | Critic agent | `amplifier-bundle-zerovector/agents/critic.md` | 304 | Markdown | Two-pass protocol; structured JSON output; VERDICT: PASS/CONDITIONAL_PASS/FAIL; line 263: "You do NOT need to call update_fidelity yourself" |
| 7 | ZeroVector bundle | `amplifier-bundle-zerovector/bundle.md` | 118 | Bundle | Includes foundation + zerovector-crew behavior; STANDING-ORDER to suggest crew mode before any work |

### Tests

| # | Artifact | Path | Lines | Type | Key Attributes |
|---|----------|------|-------|------|----------------|
| 8 | State tests | `amplifier-bundle-zerovector/tests/modules/test_fidelity_state.py` | 280 | Python | 31 tests: defaults, update_fidelity, get_state (copy safety), tool execute, mount |
| 9 | Reporter tests | `amplifier-bundle-zerovector/tests/modules/test_fidelity_reporter.py` | 364 | Python | 38 tests: render_dashboard, render_ephemeral (no ANSI), handle_event, mount registration |
| 10 | Behavior tests | `amplifier-bundle-zerovector/tests/behaviors/test_fidelity_behavior.py` | 111 | Python | 11 tests: YAML structure, bundle name/version, hooks/tools/agents/context sections |
| 11 | Convergence tests | `amplifier-bundle-zerovector/tests/recipes/test_fidelity_convergence.py` | 384 | Python | 38 tests: metadata, context vars, step order, convergence loop config, while-steps, parse_json, agent refs |

### Implementation Plans

| # | Artifact | Path | Lines | Type | Key Attributes |
|---|----------|------|-------|------|----------------|
| 12 | Tool plan | `amplifier-bundle-zerovector/docs/plans/2026-03-08-tool-fidelity-state.md` | 986 | Markdown | 12-task TDD plan; quality review exhausted after 3 iterations; 31/31 tests passing |
| 13 | Hook plan | `amplifier-bundle-zerovector/docs/plans/2026-03-08-hooks-fidelity-reporter.md` | 1229 | Markdown | Similar TDD plan; 38/38 tests passing; quality review also exhausted after 3 iterations |

**Fidelity Artifact Count: 13 files examined**

---

## Comparative Metrics

| Metric | Todo | Fidelity |
|--------|------|----------|
| Repositories touched | 5 (foundation, core, docs, kepler, tui) | 1 (zerovector) |
| Source code files | 2 (tool + hook, external repos) | 2 (tool + hook, local modules) |
| Test files | 8 | 4 |
| Test lines | 825+ | 1,139 |
| UI component files | 2 (TUI panel, Kepler store) | 0 |
| Documentation files | 3 (tool doc, hook doc, hooks API) | 3 (framework, critic, bundle) |
| Config files | 1 (behavior YAML) | 3 (behavior YAML, recipe YAML, crew YAML) |
| Prompt reinforcement locations | 4 (agent base x2, bundle x2) + hook nudge | 1 (framework) + 1 contradictory (critic) |
| Bundle level | Foundation (always-on) | ZeroVector (opt-in) |
| Tool complexity | 3 actions | 5 lenses + domain + target |
| Hook trigger event | provider:request (pre-LLM) | tool:post + prompt:complete (post-action) |
| Hook priority | 10 (early) | 50 (late) |
| State persistence | Disk + localStorage + WS | Memory only |
| Child agent support | Full (parentId, agentName, mergeTodos) | None |
| Feedback loop type | Closed (automatic) | Open (LLM-initiated) |
