# Integration Map: Fidelity Context Injection Chain

> Agent-3 (Integration Mapper) — WHERE/WHY analysis of cross-boundary fidelity tracking

## Executive Summary

The fidelity tracking system spans **six distinct boundaries** between mechanisms. The root cause of inconsistent behavior is a **governing architectural constraint**: fidelity state is session-scoped and never crosses the root→sub-agent boundary automatically. The system relies on an LLM-mediated bridge (the orchestrator parsing critic output and calling `update_fidelity`) with no programmatic enforcement. The git history documents at least four confirmed boundary failures that were patched via prompt engineering rather than architectural fixes.

---

## Boundary Map

### Boundary 1: Bundle Composition → Context Loading

**What crosses:** Context file paths accumulate during `Bundle.compose()` calls. Each behavior YAML declares `context.include` entries that become entries in the composed bundle's `context` dict.

**Direction:** Behavior YAMLs → Bundle.compose() → PreparedBundle.create_session() → system instruction

**Mechanism in code:**
- `fidelity.yaml` (lines 37-40) declares context: `using-zerovector.md`, `fidelity-framework.md`
- `zerovector-crew.yaml` (lines 33-38) declares context: `using-zerovector.md`, `crew-instructions.md`, `domain-tuning.md`, `modes:context/modes-instructions.md`
- `zerovector-crew.yaml` includes `zerovector:behaviors/fidelity` (line 10)
- `Bundle.compose()` in `bundle.py` (lines 128-136) accumulates context with bundle-prefixed keys

**What gets loaded:** In `PreparedBundle.create_session()` (lines 529-533), ALL context files from ALL composed bundles are read from disk and appended to the combined system instruction:
```python
for context_name, context_path in self.bundle.context.items():
    if context_path.exists():
        content = context_path.read_text()
        instruction_parts.append(f"# Context: {context_name}\n\n{content}")
```

**Finding — NO filtering step:** There is no conditional loading based on mode or session type. Every context file from every composed behavior is loaded into every session. The `fidelity-framework.md` and `crew-instructions.md` are ALWAYS present in the root session's system prompt, regardless of whether a crew mode is active.

**Implication:** This means fidelity context is always available to the LLM. The inconsistency is NOT caused by missing context files. It's downstream.

---

### Boundary 2: Mode Activation → Context Injection

**What crosses:** When a mode activates, the mode file's markdown body is injected as additional context. The mode's frontmatter `tools.safe` list controls which tools the LLM can call.

**Direction:** User `/crew-build` command → hooks-mode module → mode body injected into prompt + tool safety enforced

**The critical interaction:**
- Mode files (e.g., `crew-build.md` lines 7-26) define `tools.safe` as a whitelist
- The mode body (lines 29-156) adds domain-specific orchestration instructions
- The mode body says `Read crew-instructions.md` — this is **prose**, not an @mention. The actual content is already loaded via behavior composition (Boundary 1).

**CONFIRMED BUG — commit `55866e1`:**
> "fix: add update_fidelity to crew mode safe tools and orchestrator instructions"

Before this fix, `update_fidelity` was **not in the safe tools list** for any crew mode. The mode system's `default_action: block` meant the orchestrator was BLOCKED from calling `update_fidelity` when a crew mode was active. The tool existed, the instructions said to call it, but the mode's security policy prevented the call.

**Current state:** All six mode files now include `update_fidelity` in `tools.safe`. But this reveals a class of bug: **any new tool needed by the convergence loop must be manually added to every mode file's safe list**.

**Without a mode active:** No tool safety enforcement. The orchestrator can freely call `update_fidelity`. But WITHOUT a mode, the crew-gate hook (priority 10) fires on every turn injecting "suggest a mode" warnings, potentially competing with fidelity instructions for LLM attention.

---

### Boundary 3: Root Session → Sub-Agent (THE GOVERNING BOUNDARY)

**What crosses:** Nothing automatic. Fidelity state does NOT cross this boundary.

**Direction:** Root session ←(manual bridge)→ child session

**Architecture:**
Each `AmplifierSession` has its own `ModuleCoordinator` (session.py line 71). Each coordinator has its own mount points (coordinator.py line 67-74). When `tool-fidelity-state` mounts (tool module `__init__.py` lines 165-184), it creates a NEW `FidelityState` instance and registers it as capability `zerovector.fidelity_state` on THAT coordinator:

```python
state = FidelityState(target=target, domain=domain)
tool = UpdateFidelityTool(state)
await coordinator.mount("tools", tool, name=tool.name)
coordinator.register_capability("zerovector.fidelity_state", state)
```

When `PreparedBundle.spawn()` creates a child session (bundle.py line 662), it creates a fresh `AmplifierSession` with its own coordinator. The child gets its own `FidelityState` — empty, disconnected from the parent's.

**The LLM-mediated bridge:**
The ONLY mechanism for fidelity scores to reach the root session's dashboard is:
1. Critic agent (child session) produces JSON with lens scores in its text output
2. Child session returns the text to the root session
3. The orchestrator LLM **parses the text** and **extracts the scores**
4. The orchestrator LLM **calls `update_fidelity`** with those scores

Steps 2-4 are entirely dependent on the LLM following instructions. There is no programmatic enforcement.

**CONFIRMED BUG — commit `9a49682`:**
> "fix: remove phantom update_fidelity instruction from critic (orchestrator handles root session updates)"

The critic was initially told to call `update_fidelity` itself. But `update_fidelity` in the critic's child session updates the CHILD's FidelityState — invisible to the user. The fix was to remove the instruction from the critic and add it to the orchestrator's instructions instead. The critic now says (critic.md lines 263-264):

> "You do NOT need to call `update_fidelity` yourself — the orchestrator handles this after your delegation returns."

**CONFIRMED BUG — commit `1ed8932`:**
> "fix: enforce mandatory fidelity updates after every agent delegation"

This commit added a massive `<CRITICAL>` section to `crew-instructions.md` (lines 133-196) with explicit examples, anti-rationalization patterns, and the rule:

> "EVERY time a delegate() call returns, your NEXT action MUST be `update_fidelity`."

The fact that this needed to be added (and is the most recent fix) confirms this boundary is the primary failure point.

**Design implication:** The system has a hard architectural constraint — fidelity state is session-scoped — and bridges it with prompt engineering. This is inherently unreliable. The LLM may:
- Forget to call `update_fidelity` (especially under complex multi-step orchestration)
- Parse the critic's JSON incorrectly
- Call `update_fidelity` with wrong score mappings
- Skip the call when the critic delegation fails

---

### Boundary 4: Hook Injection → Prompt (Ephemeral Injection)

**What crosses:** The fidelity reporter hook produces ephemeral context injection (plain-text routing advice) and a user-visible ANSI dashboard.

**Direction:** `FidelityState` → `hooks-fidelity-reporter` → `HookResult(ephemeral=True)` → orchestrator → LLM prompt

**Mechanism:**
1. Hook fires on `tool:post` and `prompt:complete` events (hook module lines 355-358)
2. Hook reads `zerovector.fidelity_state` capability from coordinator (line 294)
3. If state has no `lens_scores`, returns `_CONTINUE` — **no injection** (line 299-300)
4. Otherwise, renders ANSI dashboard to stdout AND returns ephemeral context injection (lines 303-317)

**Ephemeral handling in coordinator:**
In `coordinator.py` lines 411-412:
```python
if not result.ephemeral:
    # ... add to context manager
```
When `ephemeral=True`, the coordinator **skips** adding the injection to the context manager. The injection must be handled by the orchestrator module — appended to the current messages array for the next LLM call without being stored in history.

**Finding — Chicken-and-egg problem:**
Before the first `update_fidelity` call, `FidelityState.lens_scores` is empty. The hook checks `if not state.get("lens_scores")` and returns `_CONTINUE`. This means:
- **Before first `update_fidelity`**: No fidelity dashboard, no ephemeral routing advice
- **After first `update_fidelity`**: Dashboard appears, routing advice injected
- The ephemeral injection that would REMIND the LLM to call `update_fidelity` only starts working AFTER the LLM has already called it at least once

This is a bootstrapping problem. The very mechanism designed to remind the orchestrator about fidelity only activates after fidelity has already been updated.

---

### Boundary 5: Behavior Composition → Module Deduplication

**What crosses:** Hook and tool module declarations traverse from behavior YAMLs through `Bundle.compose()` via `merge_module_lists()`.

**Direction:** fidelity.yaml → (included by) zerovector-crew.yaml → Bundle.compose() → mount plan hooks/tools lists

**CONFIRMED BUG — commit `6a0999e`:**
> "fix: declare fidelity modules directly in crew behavior (transitive include doesn't merge hooks)"

The diff shows `hooks-fidelity-reporter` and `tool-fidelity-state` being added directly to `zerovector-crew.yaml`, even though they were already declared in the transitively-included `fidelity.yaml`.

**Root cause:** The `includes` directive in a behavior YAML was not properly merging hooks from transitively included bundles. The `merge_module_lists()` function in the foundation works correctly for direct composition, but the transitive include resolution had a gap.

**Current state:** Both `fidelity.yaml` and `zerovector-crew.yaml` now redundantly declare the same modules. This works but creates a maintenance burden — if the module source changes in one file, it must change in both.

**Implication for the inconsistency report:** Before commit `6a0999e`, crew mode sessions might NOT have had the fidelity hook or tool loaded. This would cause: no dashboard, no `update_fidelity` tool, no ephemeral routing advice. But the context files (with instructions to call `update_fidelity`) would still be present — creating a contradiction where the LLM is told to use a tool that doesn't exist.

---

### Boundary 6: Context Instructions → LLM Behavior

**What crosses:** Natural language instructions telling the LLM what to do, competing with each other for attention in a massive system prompt.

**Direction:** System prompt (all context files + mode body + ephemeral injections) → LLM attention → tool calls

**The competition:**
The system prompt includes (at minimum):
1. `bundle.md` body with `<STANDING-ORDER>` (13 lines)
2. `zerovector-principles.md` (referenced via @mention)
3. `crew-instructions.md` (345 lines including the 65-line CRITICAL section)
4. `domain-tuning.md` (referenced)
5. `fidelity-framework.md` (225 lines)
6. `using-zerovector.md` (55 lines with `<EXTREMELY-IMPORTANT>` tag)
7. All @mention-resolved content from the above files
8. Mode body (if active, ~156 lines for crew-build)
9. Foundation common system base (referenced via @mention)

Plus ephemeral injections per turn:
- Crew-gate reminder (if no mode active, ~6 lines, priority 10)
- Fidelity routing advice (if state exists, ~5 lines, priority 50)

**The attention competition:**
When NO mode is active:
- The crew-gate hook fires (priority 10) with `_SOFT_REMINDER`: "You MUST suggest a /crew-* mode"
- The fidelity reporter fires (priority 50) with routing advice
- Both are ephemeral and get merged via `_merge_inject_context_results` (hooks.py lines 188-219)
- The merged injection uses the FIRST result's settings (crew-gate's)
- The LLM sees BOTH "suggest a mode" AND fidelity state — competing instructions

When a mode IS active:
- The crew-gate returns `_CONTINUE` (no injection)
- Only the fidelity routing advice appears
- But the system prompt is LARGER (mode body added)

**Finding — "Sometimes works" explained:**
The inconsistency ("sometimes works in crew-build mode and sometimes doesn't, sometimes works without a mode and sometimes doesn't") maps to attention competition:

| Scenario | Prompt Size | Competing Instructions | Fidelity Likelihood |
|----------|------------|----------------------|-------------------|
| Crew mode active, early in conversation | Large (mode + all context) | Low (only fidelity) | Higher |
| Crew mode active, deep in convergence loop | Very large (accumulated context) | Medium (many delegation results) | Lower — context window pressure |
| No mode, early | Medium | High (crew-gate + fidelity) | Lower — "suggest mode" competes |
| No mode, after first update_fidelity | Medium + ephemeral | High | Medium — routing advice helps |

---

## Cross-Cutting Concerns

### 1. The Session Boundary Is the Governing Constraint

Every other boundary flows from this: fidelity state is session-scoped because `FidelityState` is created per-coordinator, and coordinators are per-session. This is not a bug — it's a deliberate architectural decision (the kernel provides isolation between sessions). But it means ALL fidelity state transfer depends on the LLM-mediated bridge.

### 2. The Fix Pattern Is Prompt Engineering, Not Architecture

The git history shows a clear pattern:
- `55866e1`: Added `update_fidelity` to mode safe tools (mode blocked the tool)
- `6a0999e`: Duplicated module declarations (transitive includes didn't work)
- `9a49682`: Moved `update_fidelity` responsibility from critic to orchestrator (wrong session)
- `1ed8932`: Added massive CRITICAL section with examples (LLM wasn't following instructions)

Each fix patches a boundary failure with more instructions rather than programmatic enforcement. This creates a growing instruction corpus that itself becomes a boundary problem (Boundary 6 — attention competition).

### 3. Bootstrapping Problem

The fidelity reporter hook is the only mechanism that reminds the LLM about fidelity state between turns. But it only activates after `update_fidelity` has been called at least once. Before the first call, there's no ephemeral reminder. This means the first `update_fidelity` call is the hardest to get right — and it's the one with the least support.

### 4. Mode vs. No-Mode Asymmetry

| Mechanism | With Mode | Without Mode |
|-----------|-----------|-------------|
| Tool safety | `update_fidelity` in safe list | No restrictions |
| Crew-gate hook | Returns `_CONTINUE` (silent) | Injects "suggest mode" warning |
| Context instructions | Mode body + behavior context | Only behavior context |
| Fidelity hook | Fires normally | Fires normally |
| LLM attention budget | Split across more text | Less total text, but competing ephemeral |

The asymmetry means the failure modes are DIFFERENT in each case, not just more/less likely.

---

## Design Implications

### The Fundamental Tension

The kernel enforces session isolation (good for security, modularity). The fidelity system requires cross-session state sharing (needed for the convergence loop to be visible to users). These are in tension, and the current resolution — LLM-mediated bridging — is the weakest possible mechanism.

### What Would Fix It

A programmatic bridge mechanism — something like:
- A `session:fork` event handler that links parent/child FidelityState
- A capability that allows child sessions to write to the parent's state
- An automatic `update_fidelity` call when delegation returns with structured output

Any of these would replace the LLM-mediated bridge with a deterministic one. But they would require changes to the kernel or foundation, not just the bundle.

### The Instruction Corpus Growth Problem

Each boundary failure gets patched with more instructions. The instruction corpus is now:
- `crew-instructions.md`: 345 lines
- `fidelity-framework.md`: 225 lines  
- `using-zerovector.md`: 55 lines
- Mode body: ~156 lines
- Anti-rationalization tables in multiple places

Total: ~780+ lines of instructions about fidelity behavior. This creates a paradox: the more instructions you add to fix reliability, the more you compete for the LLM's attention budget, potentially reducing reliability.
