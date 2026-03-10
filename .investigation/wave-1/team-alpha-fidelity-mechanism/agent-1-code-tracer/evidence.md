# Evidence — Code Tracer
## Team: alpha-fidelity-mechanism | Wave 1

All claims cite exact `file:line` or `file:line-range`. Every citation was read directly from source.

---

## Module Entry Points and Registration

### hooks-fidelity-reporter registers via Python entry point
- `modules/hooks-fidelity-reporter/pyproject.toml:12-13` — `[project.entry-points."amplifier.modules"]` declares `hooks-fidelity-reporter = "amplifier_module_hooks_fidelity_reporter:mount"`. This is how the kernel discovers and loads this hook.

### tool-fidelity-state registers via Python entry point
- `modules/tool-fidelity-state/pyproject.toml:10-11` — `[project.entry-points."amplifier.modules"]` declares `tool-fidelity-state = "amplifier_module_tool_fidelity_state:mount"`.

### hooks-crew-gate registers via Python entry point (but is never mounted)
- `modules/hooks-crew-gate/pyproject.toml:12-13` — `[project.entry-points."amplifier.modules"]` declares `hooks-crew-gate = "amplifier_module_hooks_crew_gate:mount"`.
- Git status: `?? modules/hooks-crew-gate/` — untracked. No behavior YAML references this module.

---

## BUG-1: Action Mismatch — context_injection Is Discarded

### Hooks return `action="continue"` with context_injection set
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:310-317` — `handle_event()` returns `HookResult(action="continue", context_injection=ephemeral_text, context_injection_role="system", ephemeral=True, user_message=dashboard, user_message_level="info")`. Action is `"continue"`, not `"inject_context"`.

### Kernel emit() only processes inject_context when action matches
- `amplifier_core/amplifier_core/hooks.py:162-165` — The collection guard: `if result.action == "inject_context" and result.context_injection: inject_context_results.append(result)`. A `"continue"` result with `context_injection` set never enters this branch.
- `amplifier_core/amplifier_core/hooks.py:154-156` — `deny` short-circuits. `modify` and `inject_context` have special handling. `continue` falls through with no processing of `context_injection`.
- `amplifier_core/amplifier_core/hooks.py:176-183` — After all handlers: `if inject_context_results: special_result = self._merge_inject_context_results(inject_context_results)`. If `inject_context_results` is empty (because no handler returned `action="inject_context"`), this block is skipped entirely.
- `amplifier_core/amplifier_core/hooks.py:185-186` — Final return: `return HookResult(action="continue", data=current_data)`. The `context_injection` and `user_message` from individual handlers are lost.

### coordinator.process_hook_result() has the same action guard
- `amplifier_core/amplifier_core/coordinator.py:360-362` — `if result.action == "inject_context" and result.context_injection: await self._handle_context_injection(...)`. Same pattern — only processes injection when action is `"inject_context"`.

### Dashboard writes to stdout directly — this IS why it appears
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:303-305` — `sys.stdout.write(f"\n{dashboard}\n")` followed by `sys.stdout.flush()`. This bypasses the kernel entirely. The visual dashboard output works precisely because it does not go through HookResult.

### user_message on a continue action IS processed by coordinator
- `amplifier_core/amplifier_core/coordinator.py:368-370` — `if result.user_message: self._handle_user_message(result, hook_name)`. This guard does NOT check `action` — it fires on any action. However, this processing happens on the merged result returned by `emit()`, not on individual handler results. Since `emit()` returns `HookResult(action="continue")` with no `user_message`, `_handle_user_message` is never called for the fidelity reporter's user_message.

---

## BUG-2: Double Registration

### fidelity.yaml declares hooks-fidelity-reporter
- `behaviors/fidelity.yaml:25-27` — `hooks: - module: hooks-fidelity-reporter, source: ../modules/hooks-fidelity-reporter`. Direct declaration.

### zerovector-crew.yaml also declares hooks-fidelity-reporter directly
- `behaviors/zerovector-crew.yaml:15-16` — `- module: hooks-fidelity-reporter, source: ../modules/hooks-fidelity-reporter`. Second direct declaration.

### zerovector-crew.yaml also includes fidelity.yaml via includes
- `behaviors/zerovector-crew.yaml:9-10` — `includes: - bundle: zerovector:behaviors/fidelity`. If the app layer loads both behaviors and processes their hooks sections independently, double registration results.

### HookRegistry has no deduplication
- `amplifier_core/amplifier_core/hooks.py:85-86` — `self._handlers[event].append(hook_handler)`. Plain list append. No check whether a handler with the same name already exists.
- `amplifier_core/amplifier_core/hooks.py:83` — `name=name or handler.__name__` is stored for debugging only; it is not used to prevent duplicates.

### ModuleLoader cache is keyed by module_id but per-session
- `amplifier_core/amplifier_core/loader.py:167-169` — `if module_id in self._loaded_modules: return self._loaded_modules[module_id]`. The cache prevents the Python module from being imported twice per `ModuleLoader` instance. But if `mount()` is called twice for the same module_id (e.g., from two behavior YAML hooks sections), the second call uses the cached mount function and calls `mount(coordinator, config)` again — resulting in a second `coordinator.hooks.register()` call.

### Git commit acknowledges the transitive-include issue
- Git log entry `6a0999e` — "fix: declare fidelity modules directly in crew behavior (transitive include doesn't merge hooks)". This explains why `zerovector-crew.yaml` has its own direct declaration. But `fidelity.yaml` was not cleaned up, leaving both with declarations.

---

## BUG-3: Invalid Pydantic Literal in hooks-crew-gate

### Both handlers use "warn" instead of "warning"
- `modules/hooks-crew-gate/amplifier_module_hooks_crew_gate/__init__.py:187` — `user_message_level="warn"` in `on_prompt_complete()` return.
- `modules/hooks-crew-gate/amplifier_module_hooks_crew_gate/__init__.py:217` — `user_message_level="warn"` in `on_tool_post()` return.

### HookResult model only accepts "info", "warning", "error"
- `amplifier_core/amplifier_core/models.py:203-208` — `user_message_level: Literal["info", "warning", "error"] = Field(default="info", ...)`. Pydantic enforces this literal at construction time.

### Both handlers wrap their return in try/except that silently returns _CONTINUE
- `modules/hooks-crew-gate/amplifier_module_hooks_crew_gate/__init__.py:189-191` — `except Exception: log.debug(...); return _CONTINUE` catches the Pydantic ValidationError that occurs when `"warn"` is rejected.
- `modules/hooks-crew-gate/amplifier_module_hooks_crew_gate/__init__.py:219-221` — Same pattern in `on_tool_post()`.

### Test environments use a dataclass fallback that hides the bug
- `modules/hooks-crew-gate/amplifier_module_hooks_crew_gate/__init__.py:22-36` — Guard import: `try: from amplifier_core.models import HookResult except ImportError: @dataclass(frozen=True) class HookResult: ...`. The dataclass fallback stores `user_message_level` as a plain string with no validation — tests pass `"warn"` without error.

---

## BUG-4: hooks-crew-gate Never Deployed

### Module is untracked in git
- Git status output: `?? modules/hooks-crew-gate/`. Not committed.

### Neither behavior YAML references it
- `behaviors/fidelity.yaml:25-27` — Only declares `hooks-fidelity-reporter`. No `hooks-crew-gate`.
- `behaviors/zerovector-crew.yaml:12-16` — Declares `hooks-mode` and `hooks-fidelity-reporter`. No `hooks-crew-gate`.

### bundle.md only includes zerovector-crew (not crew-gate directly)
- `bundle.md:7-9` — `includes: - bundle: git+https://github.com/microsoft/amplifier-foundation@main - bundle: zerovector:behaviors/zerovector-crew`. No direct hook declaration.

---

## BUG-5: Fires on Every tool:post

### Hook registers on all tool:post events, not filtered
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:355-358` — Registration loop: `for event_name, handler in [("tool:post", _on_tool_post), ("prompt:complete", _on_prompt_complete)]`. Both events registered.
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:1-16` — Module docstring confirms: "Fires on `tool:post` and `prompt:complete`." No filtering by tool name.

### handle_event is called regardless of which tool was invoked
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:278-324` — `handle_event()` reads `data` parameter but never inspects `data.get("tool_name")` or similar. It only checks if fidelity_state capability exists and if lens_scores are populated.

### Early exit guards prevent noise before first update_fidelity call
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:294-296` — `if fidelity_state is None: return _CONTINUE` — no-ops when capability not registered.
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:298-300` — `if not state.get("lens_scores"): return _CONTINUE` — no-ops before first update_fidelity call.

---

## tool-fidelity-state: State Structure and Persistence

### FidelityState is an in-memory dataclass
- `modules/tool-fidelity-state/amplifier_module_tool_fidelity_state/__init__.py:59-67` — `@dataclass class FidelityState: lens_scores: dict[str, float] = field(default_factory=dict); overall: float = 0.0; target: float = _DEFAULT_TARGET; domain: str = _DEFAULT_DOMAIN; priority_gap: dict[str, Any] = field(default_factory=dict)`. No persistence.

### update_fidelity clamps scores and computes overall
- `modules/tool-fidelity-state/amplifier_module_tool_fidelity_state/__init__.py:69-94` — `update_fidelity()`: clamps each score `max(0.0, min(1.0, v))`, computes `overall = sum(scores) / len(scores)` (arithmetic mean), finds `lowest_lens = min(scores, key=scores.get)` for `priority_gap`.

### Two capabilities and one tool mounted on session start
- `modules/tool-fidelity-state/amplifier_module_tool_fidelity_state/__init__.py:165-193` — `mount()` calls:
  1. `coordinator.mount("tools", tool, name="update_fidelity")`
  2. `coordinator.register_capability("zerovector.fidelity_state", state)`
  3. `coordinator.register_capability("zerovector.update_fidelity", state.update_fidelity)`
  Each in its own `try/except` block that logs at DEBUG on failure.

### Reporter reads state via capability, not direct import
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:293-295` — `fidelity_state = coordinator.get_capability("zerovector.fidelity_state")`. No import of the tool module. Decoupled via capability name string.

---

## Kernel: Hook Priority and Ordering

### Lower priority number = earlier execution
- `amplifier_core/amplifier_core/hooks.py:27-29` — `def __lt__(self, other): return self.priority < other.priority`. Used for sort.
- `amplifier_core/amplifier_core/hooks.py:86` — `self._handlers[event].sort()` after each registration — keeps list sorted ascending.

### crew-gate priority 10 (runs before fidelity-reporter priority 50)
- `modules/hooks-crew-gate/amplifier_module_hooks_crew_gate/__init__.py:235` — `priority: int = int(config.get("priority", 10))`.
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:344` — `priority: int = int(config.get("priority", 50))`.

### Module loading order: tools before hooks
- `amplifier_core/amplifier_core/session.py:173-208` — Tools loaded at lines 173-188, hooks loaded at lines 193-208. `tool-fidelity-state` mounts before `hooks-fidelity-reporter` registers — capability is available when first hook fires.

### Session.initialize() loads from config keys "tools" and "hooks"
- `amplifier_core/amplifier_core/session.py:174` — `for tool_config in self.config.get("tools", []):`
- `amplifier_core/amplifier_core/session.py:194` — `for hook_config in self.config.get("hooks", []):`

---

## events.py: prompt:complete Is a Canonical Event

### prompt:complete defined in events.py
- `amplifier_core/amplifier_core/events.py:13` — `PROMPT_COMPLETE = "prompt:complete"`. Canonical string.

### HookRegistry class constants do not include PROMPT_COMPLETE
- `amplifier_core/amplifier_core/hooks.py:39-58` — `HookRegistry` class body defines constants: `SESSION_START`, `SESSION_END`, `PROMPT_SUBMIT`, `TOOL_PRE`, `TOOL_POST`, `CONTEXT_PRE_COMPACT`, `AGENT_SPAWN`, `AGENT_COMPLETE`, `ORCHESTRATOR_COMPLETE`, `USER_NOTIFICATION`, and the decision/error events. `PROMPT_COMPLETE` is absent.
- `amplifier_core/amplifier_core/hooks.py:60-62` — `def __init__(self): self._handlers: dict[str, list[HookHandler]] = defaultdict(list)`. Any string is a valid event key — no validation against the constant list. The `"prompt:complete"` string works regardless.

---

## Capability Registry Mechanism

### register_capability stores in plain dict
- `amplifier_core/amplifier_core/coordinator.py:231-243` — `def register_capability(self, name: str, value: Any): self._capabilities[name] = value`. Last writer wins — no protection against overwrite.

### get_capability returns None for unknown names
- `amplifier_core/amplifier_core/coordinator.py:245-255` — `return self._capabilities.get(name)`. Returns `None` (not raises) for unregistered names. This is the safe path the hook checks.

---

## _handle_context_injection: ephemeral skips context storage

### Ephemeral injections never written to context manager
- `amplifier_core/amplifier_core/coordinator.py:410-426` — `if not result.ephemeral: context = self.mount_points["context"]; if context and hasattr(context, "add_message"): await context.add_message(message)`. Ephemeral=True bypasses this block entirely. The text is never stored in the conversation history — it is only available for the current LLM call.
- Note: This correct behavior is MOOT because BUG-1 means `_handle_context_injection()` is never called for the fidelity hook at all.
