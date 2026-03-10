# D-06 / HU-1: Double-Mounting Investigation
**Wave 2 — Code Tracer (HOW agent)**
**Date:** 2026-03-09

---

## Verdicts

| Question | Verdict |
|---|---|
| D-06: Does double-declaration cause double-mounting? | **NO** |
| If yes, does double-mounting cause state orphaning? | **N/A** (double-mounting does not occur) |
| HU-1: Bundle loader deduplication behavior? | **Deduplicates by `module:` key via `merge_module_lists()` during `Bundle.compose()`** |

---

## 1. The Double-Declaration Exists — But Is Safe

`zerovector-crew.yaml` does contain genuine double-declarations:

- It includes `zerovector:behaviors/fidelity` (line 10), which declares `hooks-fidelity-reporter` and `tool-fidelity-state`
- It **also** directly re-declares both modules at lines 15–16 and 23–24

`fidelity.yaml` declares:
- `hooks-fidelity-reporter` at `source: ../modules/hooks-fidelity-reporter` (lines 11–12)
- `tool-fidelity-state` at `source: ../modules/tool-fidelity-state` (lines 15–16)

The source paths are **identical** in both files. Both the include and the direct declaration point to the same physical modules.

---

## 2. The Bundle Composition Pipeline Deduplicates

The full execution path when loading `zerovector-crew.yaml`:

### Step 1: `BundleRegistry._load_single()` — `registry.py:217–289`
Loads the YAML, detects `includes:` is non-empty, calls `_compose_includes()` (line 284).

### Step 2: `_compose_includes()` — `registry.py:337–372`
Loads `fidelity.yaml` as a `Bundle` object. Then composes:
```python
# registry.py:367–372
result = included_bundles[0]          # fidelity bundle (parent)
for included in included_bundles[1:]:
    result = result.compose(included)
return result.compose(bundle)         # zerovector-crew bundle (child) overrides
```
The composition order is: **include is parent, direct declaration is child**. Child wins on conflicts.

### Step 3: `Bundle.compose()` — `bundle.py:61–146`
For tools and hooks, calls `merge_module_lists()`:
```python
# bundle.py:121–123
result.providers = merge_module_lists(result.providers, other.providers)
result.tools = merge_module_lists(result.tools, other.tools)
result.hooks = merge_module_lists(result.hooks, other.hooks)
```

### Step 4: `merge_module_lists()` — `merge.py:37–74`
This is the deduplication function. Its exact semantics:

1. **Indexes parent** configs into `by_id` dict keyed by `module:` value (lines 54–59)
2. **For child entries** with a matching module ID: `deep_merge(existing, child_entry)` — child wins on conflicts (lines 67–69)
3. **For new IDs**: simply adds the entry (lines 70–72)
4. **Returns** `list(by_id.values())` — **exactly one entry per module ID** (line 74)

**Result for `tool-fidelity-state`:**
- Parent entry: `{module: tool-fidelity-state, source: ../modules/tool-fidelity-state}` (from fidelity.yaml)
- Child entry: `{module: tool-fidelity-state, source: ../modules/tool-fidelity-state}` (from zerovector-crew.yaml)
- After `deep_merge`: ONE entry, child values win (same in this case — identical source paths)
- `by_id` has exactly one key `"tool-fidelity-state"` → final list has one entry

**Same logic applies to `hooks-fidelity-reporter`.**

The mount plan passed to `AmplifierSession` via `to_mount_plan()` (bundle.py:148–172) contains each module **once**.

---

## 3. Session Initialization Has No Deduplication — But Doesn't Need It

`session.py:174–208` iterates `self.config.get("tools", [])` and `self.config.get("hooks", [])` in plain for-loops with **no deduplication guard**. However, this is not a problem because the mount plan was already deduplicated in Step 4 above. By the time `AmplifierSession.initialize()` runs, each module appears exactly once in the config.

---

## 4. What Would Happen IF Double-Mounting Occurred (Theoretical)

If duplicates somehow reached `session.py` (e.g., bypassing `Bundle.compose()`):

### For `tool-fidelity-state` (tool):
The `ModuleLoader` caches mount functions by module ID (`loader.py:167–169`). Both calls would get the **same mount function** back. That function would be called twice, creating **two separate `FidelityState` instances**. The second call to `coordinator.mount("tools", ...)` would overwrite the first via dict assignment (`coordinator.py:175`). The first instance's state would be **silently orphaned** with no warning logged (the warning at `coordinator.py:162` only fires for single-module mount points like `orchestrator`, not for `tools`).

### For `hooks-fidelity-reporter` (hook):
`HookRegistry.register()` **appends** to `_handlers[event]` (hooks.py:85). A second registration would **not overwrite** — it would add a second handler. The reporter would **fire twice** on every event. This would cause duplicate context injections and duplicate dashboard renders, but NOT state orphaning.

### For `register_capability()`:
`coordinator.py:242` uses plain dict assignment: `self._capabilities[name] = value`. Second registration **overwrites** silently. The first-mounted tool's internal reference (if it stored its own capability name) could become detached.

---

## 5. Loader Secondary Cache

The `ModuleLoader._loaded_modules` dict (`loader.py:58, 167–169`) caches by module ID. This is a second-level defense: if the same module ID is loaded twice, the cached mount **function** is returned. But this cache returns the same function object — calling it again still creates a new instance and mounts it. **The loader cache does not prevent double-mounting; it only prevents re-importing the module from disk.**

---

## 6. The Workaround at Commit 6a0999e is Safe

The workaround (directly declaring fidelity modules in zerovector-crew.yaml) is safe because `merge_module_lists()` properly deduplicates when the composed bundle is built. The direct declarations serve as the "override" child in the `compose()` call, and they survive deduplication intact. No double-mounting occurs.

The workaround was necessary because the transitive-include path alone was failing to propagate hooks — a bug in some app-layer composition path that was NOT using `_compose_includes()` / `Bundle.compose()`. The direct declaration ensures the hook is present in `zerovector-crew.yaml`'s own module list, which survives regardless of whether includes are processed correctly.

---

## 7. Deduplication is Foundation-Layer, Not Kernel-Layer

**Critical architecture note:** Deduplication happens entirely within `amplifier-foundation` (the bundle composition layer), not within `amplifier-core` (the kernel/session layer). The kernel (`session.py`) has no deduplication logic and trusts the mount plan it receives. Any code path that constructs a mount plan WITHOUT going through `Bundle.compose()` → `merge_module_lists()` would be vulnerable to double-mounting.
