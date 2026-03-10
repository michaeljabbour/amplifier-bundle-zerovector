# Evidence — D-06 / HU-1
**Wave 2 — Code Tracer (HOW agent)**

Every claim in `findings.md` has a citation here.

---

## Double-Declaration in YAML Files

### Both modules declared in zerovector-crew.yaml directly
- `behaviors/zerovector-crew.yaml:10` — `includes: - bundle: zerovector:behaviors/fidelity` — triggers transitive include of fidelity.yaml
- `behaviors/zerovector-crew.yaml:15–16` — `module: hooks-fidelity-reporter` / `source: ../modules/hooks-fidelity-reporter` — **direct** declaration of the hook
- `behaviors/zerovector-crew.yaml:23–24` — `module: tool-fidelity-state` / `source: ../modules/tool-fidelity-state` — **direct** declaration of the tool

### Both modules declared in fidelity.yaml (the included bundle)
- `behaviors/fidelity.yaml:11–12` — `module: hooks-fidelity-reporter` / `source: ../modules/hooks-fidelity-reporter` — declared in fidelity behavior
- `behaviors/fidelity.yaml:15–16` — `module: tool-fidelity-state` / `source: ../modules/tool-fidelity-state` — declared in fidelity behavior

### Source paths are identical
Both `zerovector-crew.yaml` and `fidelity.yaml` use `source: ../modules/hooks-fidelity-reporter` and `source: ../modules/tool-fidelity-state` — same relative paths, same physical modules.

---

## Bundle Composition Pipeline

### _load_single() detects includes and triggers _compose_includes()
- `amplifier_foundation/registry.py:282–284` — `if auto_include and bundle.includes: bundle = await self._compose_includes(bundle)` — includes processing is triggered here, after parsing the YAML into a Bundle

### _compose_includes() loads included bundles and composes
- `amplifier_foundation/registry.py:337–341` — function signature and guard: `if not bundle.includes: return bundle`
- `amplifier_foundation/registry.py:343–362` — for-loop loads each include via `_load_single()` (recursive, with `auto_include=True` so transitive includes are followed)
- `amplifier_foundation/registry.py:364–365` — `if not included_bundles: return bundle` — if includes failed to resolve, bundle is returned as-is
- `amplifier_foundation/registry.py:367–372` — **composition order**: includes are `result` (parent), main bundle is the `bundle` passed to `result.compose(bundle)` (child). Main bundle wins on conflicts.
  ```python
  result = included_bundles[0]
  for included in included_bundles[1:]:
      result = result.compose(included)
  return result.compose(bundle)   # ← main bundle overrides includes
  ```

### _parse_include() extracts the bundle reference from dict syntax
- `amplifier_foundation/registry.py:432–440` — handles `{bundle: "zerovector:behaviors/fidelity"}` dict format by returning `str(bundle_ref)` — the `zerovector:behaviors/fidelity` string

### Bundle.compose() calls merge_module_lists() for tools and hooks
- `amplifier_foundation/bundle.py:61–67` — docstring confirms: "providers/tools/hooks: merge by module ID"
- `amplifier_foundation/bundle.py:120–123` — actual calls:
  ```python
  # Module lists: merge by module ID
  result.providers = merge_module_lists(result.providers, other.providers)
  result.tools = merge_module_lists(result.tools, other.tools)
  result.hooks = merge_module_lists(result.hooks, other.hooks)
  ```
- `amplifier_foundation/bundle.py:90–104` — result Bundle is initialized from `self` (fidelity) with its existing tools/hooks lists before merging with `other` (zerovector-crew)

---

## merge_module_lists() Deduplication Semantics (HU-1 Answer)

- `amplifier_foundation/dicts/merge.py:37–40` — function signature: takes `parent` list and `child` list of module configs
- `amplifier_foundation/dicts/merge.py:41–45` — docstring: "If both lists have config for the same module ID, deep merge them (child overrides parent)"
- `amplifier_foundation/dicts/merge.py:54–59` — **indexes parent by `module` key**: `by_id[module_id] = config.copy()` — one slot per module ID
- `amplifier_foundation/dicts/merge.py:61–72` — processes child list:
  - Line 67: `if module_id in by_id:` — detects duplicate
  - Line 69: `by_id[module_id] = deep_merge(by_id[module_id], config)` — child **overrides** parent via deep_merge
  - Lines 70–72: `else: by_id[module_id] = config.copy()` — new modules are added
- `amplifier_foundation/dicts/merge.py:74` — `return list(by_id.values())` — **returns ONE entry per module ID**, duplicates have been merged

### deep_merge() child-wins semantics
- `amplifier_foundation/dicts/merge.py:8–34` — `deep_merge(parent, child)`: for matching keys, child value wins; for nested dicts, recurses. Child's `source:` path overwrites parent's.

---

## Session.initialize() Has No Deduplication

- `amplifier_core/session.py:173–188` — tools loading: `for tool_config in self.config.get("tools", []):` — plain iteration, no deduplication check
- `amplifier_core/session.py:193–208` — hooks loading: `for hook_config in self.config.get("hooks", []):` — plain iteration, no deduplication check
- `amplifier_core/session.py:181–184` — for each tool: `await self.loader.load(module_id, ...)` then `await tool_mount(self.coordinator)` — two calls that would double-mount if two entries existed

---

## Loader Secondary Cache (Does Not Prevent Double-Mounting)

- `amplifier_core/loader.py:58` — `self._loaded_modules: dict[str, Any] = {}` — in-memory cache keyed by module_id
- `amplifier_core/loader.py:167–169` — cache check: `if module_id in self._loaded_modules: return self._loaded_modules[module_id]` — returns same mount **function**, but does not prevent the function from being called twice and mounting a second instance
- `amplifier_core/loader.py:217–218, 223–224` — cache is populated: `self._loaded_modules[module_id] = mount_fn` — only stores the function, not whether it was already mounted

---

## coordinator.mount() for Tools is Overwrite (No Warning)

- `amplifier_core/coordinator.py:67–74` — `mount_points["tools"]` is initialized as `{}` (dict)
- `amplifier_core/coordinator.py:159–163` — warning IS logged for single-mount-points (orchestrator, context): `if self.mount_points[mount_point] is not None: logger.warning(f"Replacing existing {mount_point}")`
- `amplifier_core/coordinator.py:166–176` — for multi-module mount points including `"tools"`: **no warning** before overwrite. `self.mount_points[mount_point][name] = module` — silent dict assignment, second mount silently orphans first instance

---

## HookRegistry.register() is Append (Not Overwrite)

- `amplifier_core/hooks.py:60–62` — `self._handlers: dict[str, list[HookHandler]] = defaultdict(list)` — handlers stored as **list** per event
- `amplifier_core/hooks.py:83–86` — `self._handlers[event].append(hook_handler)` — **appends** new handler, does not check for duplicates
- `amplifier_core/hooks.py:86` — `self._handlers[event].sort()` — re-sorts by priority after append

This means: if `hooks-fidelity-reporter` were registered twice, it would fire **twice** per event (two entries in `_handlers[event]`).

---

## register_capability() is Overwrite

- `amplifier_core/coordinator.py:231–243` — `register_capability(self, name: str, value: Any)`: `self._capabilities[name] = value` — plain dict assignment, no deduplication, **silent overwrite**
- `amplifier_core/coordinator.py:76` — `self._capabilities = {}` — starts empty

---

## to_mount_plan() Passes Deduplicated Lists Through Unchanged

- `amplifier_foundation/bundle.py:148–172` — `to_mount_plan()`: `mount_plan["tools"] = list(self.tools)` and `mount_plan["hooks"] = list(self.hooks)` — passes the already-deduplicated lists directly into the mount plan dict

---

## Composition Order Evidence

- `amplifier_foundation/registry.py:367` — `result = included_bundles[0]` — starts from the **include** (fidelity) as parent
- `amplifier_foundation/registry.py:372` — `return result.compose(bundle)` — main bundle (zerovector-crew) is the `other`/child argument to `compose()`
- `amplifier_foundation/bundle.py:106–123` — in `compose()`, `other` is the child/override: `merge_module_lists(result.providers, other.providers)` — `result` is current (from include), `other` is the new bundle being composed in
- Therefore: zerovector-crew's direct declarations WIN over fidelity.yaml's declarations when there are conflicts
