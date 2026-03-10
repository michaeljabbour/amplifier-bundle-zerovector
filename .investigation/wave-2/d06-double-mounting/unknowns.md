# Unknowns — D-06 / HU-1
**Wave 2 — Code Tracer (HOW agent)**

---

## What I Could Not Determine

### U-1: The Specific Bug in Commit 6a0999e

**What I know:** The commit message says "transitive include doesn't merge hooks." The current code in `registry.py:_compose_includes()` and `bundle.py:Bundle.compose()` DOES correctly merge hooks via `merge_module_lists()`. The workaround (direct declaration) is now redundant — or it was fixing a different code path.

**What I could not find:** The diff of commit 6a0999e itself. I cannot determine:
- Whether `_compose_includes()` was added or fixed in that commit
- Whether there is an alternative composition code path (e.g., an app-layer that constructs mount plans directly from YAML without going through `BundleRegistry`) where the bug still exists
- Whether the bug was in an older version of `_compose_includes()` that didn't call `Bundle.compose()` properly

**Risk:** If any app-layer constructs mount plans from `zerovector-crew.yaml` by a path OTHER than `BundleRegistry._load_single()` → `_compose_includes()` → `Bundle.compose()`, deduplication would not occur. The direct declarations in `zerovector-crew.yaml` would then be necessary (not redundant).

---

### U-2: The tool-fidelity-state Module's Internal FidelityState Architecture

**What I know:** `tool-fidelity-state` mounts as a tool with `module_id = "tool-fidelity-state"`. Its `FidelityState` is what the hook reads.

**What I could not trace:** The actual `mount()` function inside `amplifier-bundle-zerovector/modules/tool-fidelity-state/`. Specifically:
- Where is `FidelityState` stored after mount? Is it registered as a `capability` via `coordinator.register_capability()`? Stored in `coordinator.mount_points["tools"]["tool-fidelity-state"]`? Both?
- How does `hooks-fidelity-reporter` find the `FidelityState` — via `coordinator.get_capability("fidelity_state")`? Via `coordinator.get("tools", "tool-fidelity-state")`?
- This matters for assessing the state-orphaning risk IF double-mounting ever occurred

**Why I stopped:** The investigation question (D-06) is resolved at the bundle composition layer without needing to know the internal architecture of `tool-fidelity-state`. If double-mounting doesn't happen (confirmed), the internal wiring is irrelevant to D-06.

---

### U-3: Whether Any App-Layer Bypasses BundleRegistry

**What I know:** The `BundleRegistry` / `_compose_includes()` / `Bundle.compose()` path is the documented, canonical way to load bundles. The kernel (`AmplifierSession`) accepts any mount plan dict without validating it.

**What I could not determine:** Whether the zerovector app layer (or any Amplifier app) constructs mount plans by:
- Reading `zerovector-crew.yaml` and merging manually (bypassing `Bundle.compose()`)
- Injecting the fidelity modules into the mount plan via some side-channel
- Using `Bundle.from_dict()` directly without calling `_compose_includes()`

If such a path exists, `merge_module_lists()` would not be called, and double-declarations COULD produce double entries in the mount plan. I found no evidence of such a path in the codebase I reviewed, but I did not exhaustively search all app-layer entry points.

---

### U-4: The includes List Format Assumption

**What I confirmed:** `_parse_include()` at `registry.py:432–440` handles both string includes (`"zerovector:behaviors/fidelity"`) and dict includes (`{bundle: "zerovector:behaviors/fidelity"}`).

**What I did not verify:** Whether the `zerovector:` namespace is pre-registered in `BundleRegistry` before `_load_single()` is called on `zerovector-crew.yaml`. If `zerovector` is not in `self._registry`, `_resolve_include_source()` at `registry.py:374–430` will log a debug message and return `None` — the include is silently skipped.

If includes are silently skipped due to missing namespace registration, the YAML declaration becomes the only way the modules are present — making the workaround functionally necessary (not just a duplicate).

---

### U-5: Loader Cache Scope

**What I confirmed:** `ModuleLoader._loaded_modules` is an instance-level cache.

**What I could not determine:** Whether the same `ModuleLoader` instance is reused across sessions (session pool), or whether each `AmplifierSession` gets a fresh loader. From `session.py:81`: `self.loader = loader or ModuleLoader(coordinator=self.coordinator)` — a new loader is created per session unless one is injected. This means the loader cache is per-session and does NOT accumulate state across sessions. Confirmed safe for multi-session scenarios.

---

## Questions This Investigation Raises

1. **Is the direct declaration in `zerovector-crew.yaml` still needed?** If `_compose_includes()` now works correctly (as the code shows), the direct declarations are redundant. Removing them would be cleaner but requires verifying commit 6a0999e didn't fix `_compose_includes()` itself.

2. **Why does `coordinator.mount()` not warn on duplicate tool registration?** `coordinator.py:159–163` warns when replacing `orchestrator` or `context`, but `coordinator.py:166–176` silently overwrites tools. This asymmetry seems like a gap — a duplicate tool mount would silently orphan state.

3. **Should `merge_module_lists()` be called in `session.py` as a defensive measure?** The kernel currently trusts the mount plan. Adding dedup in `session.py` would protect against app layers that bypass `Bundle.compose()`.
