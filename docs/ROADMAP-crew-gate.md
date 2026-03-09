# Crew Gate — Roadmap & Current State

## Problem

When a user asks to build something without first activating a `/crew-*` mode,
the LLM bypasses the fidelity convergence engine entirely — no intent analysis,
no spec, no quality gates, no translation-loss tracking. The artifact gets built
but with zero fidelity measurement.

## What We Shipped (v0.3.1)

### 1. Mandatory post-delegation fidelity updates (`crew-instructions.md`)

**Status: Working.**

Added a `<CRITICAL>` block to the convergence protocol requiring the orchestrator
to call `update_fidelity` immediately after every agent delegation returns — not
just after the critic. Includes exact scoring guidance per agent, two concrete
examples, and a critic-failure fallback protocol.

This fixed the frozen dashboard problem: previously the fidelity display stayed
at 0.00 for all lenses except intent while real work was happening.

### 2. Standing order in bundle.md

**Status: Partially effective.**

Added `<STANDING-ORDER>` to the bundle's top-level system prompt requiring the
LLM to suggest a crew mode before creating artifacts. The LLM acknowledges
reading it in its thinking but rationalizes past it ("the requirements are
straightforward enough"). Works as a soft nudge, not a hard gate.

## What We Attempted But Didn't Ship

### 3. Pre-prompt crew gate hook (`hooks-crew-gate`)

**Status: Module doesn't load. Root cause unknown.**

Built a hook module following the exact pattern of `hooks-fidelity-reporter`:
- Same pyproject.toml structure
- Same mount/register pattern
- Same HookResult return type
- Registered on `prompt:complete` and `tool:post` (known-working events)

The module never loads — no `mount()` call, no stderr debug output, no errors.
The Amplifier loader silently skips it. Other modules with identical `source:`
patterns (`../modules/hooks-fidelity-reporter`) load fine.

**Source preserved at:** `modules/hooks-crew-gate/` (not wired into any behavior)

### Approaches tried for the hook:

| Attempt | Event | Result |
|---------|-------|--------|
| 1 | `tool:pre` with `action="block"` on `apply_patch`/`write_file` | Module didn't load. Also, `tool:pre` may not be dispatched by the runtime. |
| 2 | `prompt:complete` + `tool:post` with context injection + stdout banner | Module didn't load. Events are valid (fidelity-reporter uses them). |
| 3 | Added stderr debug output to `mount()` | No output — confirms module is never imported. |

## Next Phase

### Investigation needed

1. **Why doesn't the hook module load?**
   - Compare the module discovery path between `hooks-fidelity-reporter` (works)
     and `hooks-crew-gate` (doesn't) — same `source: ../modules/...` pattern.
   - Check if the Amplifier loader requires pre-installation (`pip install -e .`)
     or if it resolves from source paths directly.
   - Check if there's a module registry or manifest that needs updating.
   - Try adding the module to `behaviors/fidelity.yaml` instead of
     `behaviors/zerovector-crew.yaml` to rule out a behavior-level issue.

2. **Does `tool:pre` actually dispatch events?**
   - The mode system uses tool gating (`default_action: block`) but this may be
     built into the mode engine, not the hook system.
   - If `tool:pre` doesn't dispatch, only `prompt:complete` and `tool:post` are
     available for hooks — making hard-blocking impossible via hooks alone.

### Options once the hook loads

**Option A: Soft gate (prompt:complete injection)**
- Every turn without a crew mode → inject ephemeral reminder into LLM context
- After creation tools used → escalate to hard warning + user-visible banner
- Pro: Uses known-working events. Con: One turn of untracked work before catch.

**Option B: Hard gate (tool:pre block — if supported)**
- Block `apply_patch`, `write_file`, `edit_file` when no mode is active
- LLM physically cannot create files until mode is activated
- Pro: Deterministic, can't be rationalized past. Con: May not be supported.

**Option C: Auto-activate crew mode**
- Instead of suggesting a mode, have the bundle auto-activate `/crew-build`
  when the first creation tool is called.
- Requires understanding the `tool-mode` module's API for programmatic activation.
- Pro: Zero friction. Con: User loses choice to opt out.

### Workaround (current)

User types `/crew-build` before giving the build prompt. The convergence engine
then works correctly with all five lenses measured and the dashboard updating
after every delegation.
