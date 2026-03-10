# Evidence — File:Line Citations
**Agent:** agent-1-code-tracer  
**Investigation:** Context injection chain for zerovector crew mode + fidelity

---

## Claim: bundle.md is the root of the composition chain

- `bundle.md:2-9` — YAML frontmatter declares `bundle.name = "zerovector"` and `includes` two bundles: `git+https://github.com/microsoft/amplifier-foundation@main` and `zerovector:behaviors/zerovector-crew`

---

## Claim: `zerovector:behaviors/zerovector-crew` resolves to `behaviors/zerovector-crew.yaml`

- `behaviors/zerovector-crew.yaml:1-3` — frontmatter opens with `bundle: name: zerovector-crew version: 0.3.0`
- `behaviors/zerovector-crew.yaml:9-10` — includes `zerovector:behaviors/fidelity`

---

## Claim: `zerovector:behaviors/fidelity` resolves to `behaviors/fidelity.yaml`

- `behaviors/fidelity.yaml:1-2` — frontmatter: `bundle: name: fidelity-behavior`

---

## Claim: `fidelity-framework.md` is declared in `fidelity.yaml` context.include and is therefore always in the system prompt

- `behaviors/fidelity.yaml:37-40` — `context: include: - zerovector:context/using-zerovector.md - zerovector:context/fidelity-framework.md`
- `behaviors/zerovector-crew.yaml:9-10` — zerovector-crew includes fidelity transitively
- `bundle.md:9` — zerovector-crew included in root bundle

---

## Claim: `Bundle.compose()` accumulates context files from all composed bundles without overwriting

- `amplifier-foundation/amplifier_foundation/bundle.py:128-136` — loop over `other.context.items()`, prefixing with bundle name if no colon present, adding to `result.context[prefixed_key]`
- `amplifier-foundation/amplifier_foundation/bundle.py:61-62` — docstring: "context: later overrides earlier" (but by key — keys are namespaced so they don't collide)

---

## Claim: `_parse_context()` converts context.include list entries to Path objects

- `amplifier-foundation/amplifier_foundation/bundle.py:360-388` — `_parse_context()`: if `"include"` key present, iterates names, strips bundle prefix via `name.split(":", 1)[-1]`, calls `construct_context_path(base_path, path_part)`

---

## Claim: `PreparedBundle.create_session()` injects all context files as a single system message

- `amplifier-foundation/amplifier_foundation/bundle.py:528-533` — loops `self.bundle.context.items()`, reads each file, appends `f"# Context: {context_name}\n\n{content}"` to `instruction_parts`
- `amplifier-foundation/amplifier_foundation/bundle.py:535` — `combined_instruction = "\n\n---\n\n".join(instruction_parts)`
- `amplifier-foundation/amplifier_foundation/bundle.py:592-594` — `context_manager.add_message({"role": "system", "content": final_instruction})`

---

## Claim: @mentions in the bundle.md body are resolved recursively via `load_mentions()`

- `bundle.md:29` — `@zerovector:context/zerovector-principles.md`
- `bundle.md:30` — `@zerovector:context/crew-instructions.md`
- `bundle.md:31` — `@zerovector:context/domain-tuning.md`
- `bundle.md:118` — `@foundation:context/shared/common-system-base.md`
- `amplifier-foundation/amplifier_foundation/bundle.py:569-573` — `mention_results = await load_mentions(combined_instruction, resolver=resolver, deduplicator=deduplicator)`
- `amplifier-foundation/amplifier_foundation/mentions/loader.py:72-111` — `load_mentions()` parses @mentions, resolves each recursively

---

## Claim: @mention resolution uses namespace:name split to find bundle then file

- `amplifier-foundation/amplifier_foundation/mentions/resolver.py:51-55` — `if ":" in mention_body:` splits on `:`, looks up `self.bundles.get(namespace)`, calls `bundle.resolve_context_path(name)`
- `amplifier-foundation/amplifier_foundation/bundle.py:238-257` — `resolve_context_path()` checks `self.context` dict then falls back to constructing path from `base_path`

---

## Claim: @mentions are deduplicated — the same file loaded from multiple sources appears once

- `amplifier-foundation/amplifier_foundation/mentions/loader.py:145-151` — `if not deduplicator.add_file(path, content): return MentionResult(... content=None ...)` — duplicate returns without content

---

## Claim: Loaded context files are formatted as XML blocks prepended to instruction

- `amplifier-foundation/amplifier_foundation/mentions/loader.py:66` — `block = f'<context_file paths="{paths_attr}">\n{cf.content}\n</context_file>'`
- `amplifier-foundation/amplifier_foundation/bundle.py:586-589` — `if context_block: final_instruction = f"{context_block}\n\n---\n\n{combined_instruction}"`

---

## Claim: `hooks-fidelity-reporter` is mounted during session initialization

- `behaviors/fidelity.yaml:25-27` — `hooks: - module: hooks-fidelity-reporter source: ../modules/hooks-fidelity-reporter`
- `behaviors/zerovector-crew.yaml:15-16` — same hook also declared in zerovector-crew (but deduplicated by module ID on merge)
- `amplifier-core/amplifier_core/session.py:193-208` — session loads all hooks from config, calls `hook_mount(self.coordinator)` which calls `mount(coordinator)`
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:332-382` — `mount()` registers `_on_tool_post` and `_on_prompt_complete` handlers

---

## Claim: `hooks-fidelity-reporter` registers on `tool:post` and `prompt:complete`

- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:355-366` — loop: `[("tool:post", _on_tool_post), ("prompt:complete", _on_prompt_complete)]`, calls `coordinator.hooks.register(event_name, handler, priority=priority)`
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:344` — `priority: int = int(config.get("priority", 50))` — default priority 50

---

## Claim: `hooks-fidelity-reporter` returns `_CONTINUE` (no-op) if fidelity state not yet populated

- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:294-296` — `fidelity_state = coordinator.get_capability("zerovector.fidelity_state"); if fidelity_state is None: return _CONTINUE`
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:298-300` — `state = fidelity_state.get_state(); if not state.get("lens_scores"): return _CONTINUE`

---

## Claim: `hooks-fidelity-reporter` injects plain-text routing advice as ephemeral context_injection

- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:308` — `ephemeral_text = self.render_ephemeral(state)`
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:310-317` — `return HookResult(action="continue", context_injection=ephemeral_text, context_injection_role="system", ephemeral=True, user_message=dashboard, ...)`
- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:249-272` — `render_ephemeral()` produces `"[FIDELITY STATE — ephemeral, auto-updates]\nStatus: ...\nOverall: ...\nPriority gap: ...\nRecommendation: ..."`

---

## Claim: `ephemeral=True` means the injection is NOT stored in conversation history

- `amplifier-core/amplifier_core/coordinator.py:411-426` — `_handle_context_injection()`: `if not result.ephemeral:` guards the `context.add_message()` call — ephemeral content bypasses storage
- `amplifier-core/amplifier_core/models.py:145-152` — `HookResult.ephemeral` docstring: "If True, injection is temporary (only for current LLM call, not stored in history)."

---

## Claim: `tool-fidelity-state` registers the `zerovector.fidelity_state` capability

- `modules/tool-fidelity-state/amplifier_module_tool_fidelity_state/__init__.py:165-193` — `mount()`: creates `FidelityState`, creates `UpdateFidelityTool`, mounts tool, calls `coordinator.register_capability("zerovector.fidelity_state", state)` and `coordinator.register_capability("zerovector.update_fidelity", state.update_fidelity)`

---

## Claim: Calling `update_fidelity` populates lens_scores and computes priority gap

- `modules/tool-fidelity-state/amplifier_module_tool_fidelity_state/__init__.py:69-94` — `FidelityState.update_fidelity()`: clamps scores, computes `self.overall = sum(scores)/len`, finds `min(lens_scores, key=...)`, builds `priority_gap` dict with `lens`, `score`, `recommendation`
- `modules/tool-fidelity-state/amplifier_module_tool_fidelity_state/__init__.py:141-159` — `UpdateFidelityTool.execute()` calls `self.state.update_fidelity(lens_scores, domain, target)` then returns summary string

---

## Claim: `hooks-crew-gate` injects crew mode reminder when no mode is active

- `modules/hooks-crew-gate/amplifier_module_hooks_crew_gate/__init__.py:224-256` — `mount()` registers `_on_prompt_complete` and `_on_tool_post` at priority 10
- `modules/hooks-crew-gate/amplifier_module_hooks_crew_gate/__init__.py:144-191` — `on_prompt_complete()`: calls `_is_mode_active()`, if False injects `_SOFT_REMINDER` or `_HARD_WARNING` as ephemeral context_injection
- `modules/hooks-crew-gate/amplifier_module_hooks_crew_gate/__init__.py:58-77` — `_SOFT_REMINDER` and `_HARD_WARNING` strings defined

---

## Claim: `hooks-crew-gate` checks three capability names to detect active mode

- `modules/hooks-crew-gate/amplifier_module_hooks_crew_gate/__init__.py:96-117` — `_is_mode_active()` tries `coordinator.get_capability("modes.active")`, `"modes.active_mode"`, `"modes.state"`, then falls back to `getattr(coordinator, "modes", None).active_mode`

---

## Claim: `HookRegistry` collects all `inject_context` results from multiple hooks and merges them

- `amplifier-core/amplifier_core/hooks.py:142-164` — `inject_context_results: list[HookResult] = []`, appends each result with `action == "inject_context"`
- `amplifier-core/amplifier_core/hooks.py:177-179` — `if inject_context_results: special_result = self._merge_inject_context_results(inject_context_results)`
- `amplifier-core/amplifier_core/hooks.py:188-219` — `_merge_inject_context_results()` joins content with `"\n\n"` separator, preserves role/ephemeral/suppress from first result

---

## Claim: `behaviors/zerovector-crew.yaml` declares context.include files that are always loaded

- `behaviors/zerovector-crew.yaml:33-38` — `context: include: [zerovector:context/using-zerovector.md, zerovector:context/crew-instructions.md, zerovector:context/domain-tuning.md, modes:context/modes-instructions.md]`

---

## Claim: Mode files have frontmatter that declares tool policies but the body is the instruction

- `modes/crew-build.md:1-27` — YAML frontmatter: `mode: name: crew-build`, `tools: safe: [...] warn: [...] default_action: block`
- `modes/crew-build.md:29-156` — markdown body: actual LLM instruction about BUILD CREW CONTEXT, lens tuning, orchestration flow, anti-rationalization rules
- `modes/crew.md:1-27` — same pattern for general crew
- `modes/crew-product.md:1-25` — same pattern for product crew

---

## Claim: Mode files explicitly direct the LLM to read fidelity-framework.md

- `modes/crew-build.md:32-33` — `"Read crew-instructions.md for the full orchestration protocol. Read fidelity-framework.md for the universal lens model and scoring rubric."`
- `modes/crew.md:32-33` — same two directives
- `modes/crew-product.md:30-31` — same pattern

---

## Claim: The `using-zerovector.md` context file contains the EXTREMELY-IMPORTANT directive

- `context/using-zerovector.md:3-9` — `<EXTREMELY-IMPORTANT>When a user asks you to BUILD, CREATE, WRITE, or PRODUCE any artifact, you ABSOLUTELY MUST suggest the appropriate crew mode BEFORE starting work. YOU DO NOT HAVE A CHOICE...`

---

## Claim: The `HookRegistry` uses `action="continue"` with `context_injection` set for fidelity injection

- `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:310` — `action="continue"` — this is important: the hook does NOT use `action="inject_context"`, it uses `action="continue"` but sets `context_injection`
- `amplifier-core/amplifier_core/hooks.py:162-165` — registry only collects for merging when `result.action == "inject_context"` — but the fidelity reporter uses `action="continue"` with `context_injection` set; this means the hook result is returned as-is, not via the inject_context merge pathway
- `amplifier-core/amplifier_core/coordinator.py:361-362` — `process_hook_result()`: `if result.action == "inject_context" and result.context_injection:` — this handles inject_context action; ephemeral injection via `action="continue"` is handled differently by the orchestrator

---

## Claim: Session loads hooks in sequence after tools

- `amplifier-core/amplifier_core/session.py:173-208` — order: providers (156-171), tools (173-188), hooks (193-208). Each calls `loader.load()` then `hook_mount(coordinator)` then registers cleanup
