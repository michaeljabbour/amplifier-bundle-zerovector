# Unknowns: What I Couldn't Determine and Why

## Unknown 1: Exact `hooks-todo-reminder` Source Code

**What**: The todo reminder hook module (`hooks-todo-reminder`) is sourced from `git+https://github.com/microsoft/amplifier-module-hooks-todo-reminder@main`. I could not read the actual source code — only the documentation (`amplifier-docs/docs/modules/hooks/todo_reminder.md`) and a related but different module (`hooks-todo-display` from an audit snapshot).

**Why it matters**: The documentation says the hook fires on `provider:request` and uses `append_to_last_tool_result=True`. If the actual implementation differs, the timing analysis in Boundary 3 could be wrong. The documentation also mentions `coordinator.todo_state` as the state access mechanism — I need to confirm whether this is a capability registration (like fidelity) or a direct attribute (like `tool._todos`).

**What I used instead**: Documentation + the `hooks-todo-display` module (which IS available locally in `_audit/amplifier-foundation-main/`) as an analog. The display hook shows the same `tool:pre`/`tool:post` event pattern with priority 5, confirming the general hook wiring approach.

**Confidence**: Medium-high. The documentation is detailed and specific, and the foundation's behavior YAML confirms `inject_role: user` and `priority: 10`.

---

## Unknown 2: Exact `tool-todo` Source Code and State Access Pattern

**What**: The todo tool module (`tool-todo`) is also a git module. I couldn't read its `mount()` function or confirm exactly how it registers state. The Kepler sidecar accesses `tool._todos` directly (`getattr(tool, "_todos", [])`), which implies the tool stores its state as a public attribute. But I don't know if it ALSO registers a capability like fidelity does.

**Why it matters**: If `tool-todo` registers a `todo_state` capability (as the documentation suggests with `coordinator.todo_state`), then the state access pattern is actually symmetric with fidelity. The difference would then be that Kepler's sidecar uses the INFORMAL path (`tool._todos`) instead of the formal one.

**What I used instead**: The Kepler sidecar code (`routes/todos.py:99`) which proves that `tool._todos` exists as a direct attribute, and the documentation which mentions `coordinator.todo_state`.

**Confidence**: High that `_todos` exists as an attribute. Medium on whether a capability is also registered.

---

## Unknown 3: `merge_module_lists()` Implementation and the Transitive Bug

**What**: Commit `6a0999e` proves that transitive includes don't merge hooks properly, requiring redundant declarations. But I couldn't read the `merge_module_lists()` function (in `amplifier_foundation/dicts/merge.py`) to understand WHY the merge fails at depth 3.

**Why it matters**: Understanding the root cause would tell us whether this is:
- A fundamental limitation of the merge algorithm (e.g., it only merges one level deep)
- A bug in how `includes` are resolved recursively
- A race condition in async bundle loading
- A namespace collision (fidelity modules have relative `../modules/` sources that might not resolve from the crew behavior's context)

**Hypothesis**: The most likely cause is that relative source paths (`../modules/hooks-fidelity-reporter`) resolve differently when included transitively. When `fidelity.yaml` is loaded directly, `../modules/` resolves relative to `behaviors/fidelity.yaml` → `modules/`. When included via `zerovector-crew.yaml` which includes `fidelity.yaml`, the resolution base might shift to `behaviors/zerovector-crew.yaml`, making `../modules/` resolve incorrectly.

**Confidence**: Low. This is speculation — I need the merge function source to confirm.

---

## Unknown 4: Orchestrator Handling of Ephemeral Injections Across Turn Boundaries

**What**: Both todo and fidelity use `ephemeral=True` injections. The kernel's `coordinator.py:411-412` shows that ephemeral injections are NOT added to the context manager (`if not result.ephemeral: ... await context.add_message(message)`). But what happens to them? The orchestrator must handle them specially — but which orchestrator, and how?

**Why it matters**: If the orchestrator discards ephemeral injections after one LLM call, then:
- Todo's `provider:request` timing guarantees visibility (injected right before the call)
- Fidelity's `tool:post`/`prompt:complete` timing creates a gap (injected after one call, needs to survive to the next)

If the orchestrator carries ephemeral state across calls within a turn, both would be equally visible.

**What I used instead**: Architectural reasoning about the `provider:request` vs `tool:post`/`prompt:complete` timing difference. The coordinator code confirms ephemeral injections skip context storage, but I don't know how the streaming loop orchestrator handles them.

**Confidence**: Medium. The timing difference is real, but the actual impact depends on orchestrator behavior I couldn't trace.

---

## Unknown 5: Whether Foundation's Bundle Composition Includes Todo Unconditionally

**What**: The foundation `bundle.md` is a markdown file with YAML frontmatter that declares `includes`. I read the `todo-reminder.yaml` behavior, but I didn't read the full `foundation/bundle.md` to confirm it includes this behavior. The Kepler desktop.yaml comment says "inherited from foundation" which strongly implies it's included, but I should verify.

**Why it matters**: If todo-reminder is NOT in foundation's includes but is instead added by a different layer (e.g., Kepler's overlay), the composition story changes significantly.

**Evidence in favor**: `desktop.yaml:92` — `# tool-todo: inherited from foundation — no override needed` is a strong indicator. Also, `todo-reminder.yaml` lives in `foundation/behaviors/` which is the standard location for included behaviors.

**Confidence**: High that foundation includes it. I just didn't read the specific line.

---

## Unknown 6: Fidelity Behavior's Claim of "Universal" Composability

**What**: `fidelity.yaml:6` describes itself as a "Universal fidelity diagnostic capability for any Amplifier session." But is this claim tested? Has any bundle other than zerovector-crew ever composed it directly?

**Why it matters**: If the standalone composition path (`includes: - bundle: zerovector:behaviors/fidelity`) has never been tested independently of `zerovector-crew.yaml`, then the "universal" claim is aspirational, not proven. The transitive merge bug (Boundary 1) suggests this path may be broken.

**Confidence**: Low. I found no evidence of any other bundle including fidelity directly.

---

## Unknown 7: What Happens to Fidelity State During Context Compaction

**What**: The kernel supports context compaction (`context.should_compact()`, `context.compact()`). The `CONTEXT_PRE_COMPACT` hook event fires before compaction. I don't know if fidelity's ephemeral injections or the fidelity state survive compaction.

**Why it matters**: If context compaction discards ephemeral injections (which makes sense — they're ephemeral), then long sessions with frequent compaction would lose fidelity context entirely. Todo's `provider:request` injection would be re-injected after compaction since it fires on every LLM call. Fidelity's `tool:post`/`prompt:complete` injection would NOT be re-injected unless a tool executes or a turn completes.

**Confidence**: Low-medium. This is an inferred risk, not a confirmed problem.

---

## Suspected Composition Effects (Not Confirmed)

### Effect A: Module ID Collision in Redundant Declarations

The `zerovector-crew.yaml` declares `hooks-fidelity-reporter` and `tool-fidelity-state` both directly AND via the `includes: behaviors/fidelity` transitive path. If `merge_module_lists()` merges by module ID, the later declaration wins. But if both sources resolve to different paths (relative `../modules/` from two different base contexts), the module loader might get confused.

### Effect B: Hook Priority Interaction

The todo reminder hook runs at priority 10 (early). The fidelity reporter runs at priority 50 (late). If both fire on the same event (e.g., `tool:post` for the todo display hook at priority 5 and fidelity reporter at priority 50), the inject_context results are MERGED by `_merge_inject_context_results()` in `hooks.py:188-219`. The merge uses the FIRST result's settings (role, ephemeral, suppress_output). If the first is todo (priority 5, role=user) and the second is fidelity (priority 50, role=system), the fidelity injection would inherit todo's `user` role. This would be incorrect.

### Effect C: Injection Budget Exhaustion

The coordinator enforces `injection_budget_per_turn` (default 10,000 tokens). If todo's injection fires first and uses budget, the fidelity injection might be rejected for exceeding the budget. The coordinator logs a warning (`hooks.py` budget check) but still processes the injection — so this is a warning, not a hard failure. But it signals that the two systems compete for a shared budget.
