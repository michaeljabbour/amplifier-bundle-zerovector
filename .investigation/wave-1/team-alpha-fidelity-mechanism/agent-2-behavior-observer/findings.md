# Findings: Fidelity Mechanism Behavioral Analysis

> Agent: Behavior Observer (WHAT)
> Investigation: team-alpha-fidelity-mechanism, wave-1
> Artifacts examined: 30+ files, 1,770 fidelity mentions, 10 fix commits, 17 test files (~434 tests)

---

## Executive Summary

The zerovector fidelity mechanism is architecturally sound but operationally fragile. The reported inconsistencies -- fires sometimes, fires twice, only picks up intent, skips entirely -- trace to a **single root cause**: the fidelity mechanism depends entirely on LLM compliance with natural-language instructions scattered across multiple context files, with no programmatic enforcement. Eight fix commits in two days addressed symptoms of this fundamental design gap.

---

## Finding 1: The "Who Calls update_fidelity" Contradiction

**The core confusion**: Three different documents give three different answers about who calls `update_fidelity`.

| Document | Says Who Calls It | Actual Instruction |
|----------|-------------------|--------------------|
| `context/fidelity-framework.md` (line 174) | The assessor (generic) | "After completing a fidelity assessment, persist the result using the `update_fidelity` tool" |
| `context/crew-instructions.md` (line 140) | The orchestrator | "EVERY time a delegate() call returns, your NEXT action MUST be `update_fidelity`" |
| `agents/critic.md` (line 263) | NOT the critic | "You do NOT need to call `update_fidelity` yourself -- the orchestrator handles this" |

The fidelity-framework.md speaks generically about "after completing a fidelity assessment" -- this reads as an instruction to whoever just assessed. The crew-instructions.md says the orchestrator must call it after every delegation. The critic.md explicitly says the critic should NOT call it.

**Impact**: When the LLM is acting as orchestrator, it must read crew-instructions.md and follow the CRITICAL block. But when it delegates to itself as critic (sub-session), that sub-session reads fidelity-framework.md which says to call update_fidelity after assessment. The critic.md countermands this, but only if the LLM reads and follows that specific paragraph.

**Evidence of confusion**: Commit `9a49682` ("remove phantom update_fidelity instruction from critic") explicitly fixed the critic calling update_fidelity when it shouldn't. Commit `b2a15a1` ("constrain critic to single update_fidelity call") addressed the same issue from a different angle. Two separate fix attempts for the same contradiction.

---

## Finding 2: Six Places Say "Call It" -- Scattered Across 51KB of Context

The LLM receives instructions about `update_fidelity` from **6 different locations** across 4 files:

1. `crew-instructions.md` CRITICAL block (lines 134-196) -- strongest, most detailed
2. `crew-instructions.md` Loop Rules (line 131) -- single line, easily missed
3. `crew-instructions.md` Delegation Contract (line 249) -- buried in another section
4. `crew-instructions.md` Anti-rationalization table (lines 328-329) -- two entries
5. `fidelity-framework.md` Calling section (lines 172-203) -- tutorial with code example
6. Each mode file's `tools.safe` list (6 files) -- enables the tool but doesn't instruct

**Total context loaded for a crew session**: ~51,753 bytes across 5 context files. The critical "call update_fidelity after every delegation" instruction is in one `<CRITICAL>` block within 15,462 bytes of crew-instructions.md. The LLM must both notice this block AND prioritize it over the more generic guidance in fidelity-framework.md.

**This explains "fires sometimes"**: The LLM sometimes follows the CRITICAL block (fires correctly), sometimes follows fidelity-framework.md's generic guidance (fires from the critic sub-session where it's invisible to the dashboard), and sometimes simply loses track across 50KB of context (skips entirely).

---

## Finding 3: Two Parallel Fidelity Tracking Systems

The bundle contains **two independent fidelity tracking mechanisms** that do not interact:

### System A: Tool-Based (Runtime)
- `tool-fidelity-state` module registers `FidelityState` on coordinator
- `update_fidelity` tool writes to this state
- `hooks-fidelity-reporter` reads from this state and renders dashboard
- **Trigger**: LLM voluntarily calls `update_fidelity` tool
- **Visible**: ANSI dashboard in terminal + ephemeral context injection

### System B: Recipe-Based (Declarative)
- `fidelity-convergence.yaml` recipe uses `{{fidelity_score}}` context variable
- `while_condition: "{{fidelity_score}} < {{target_fidelity}}"` drives the loop
- Score extracted via shell: `echo "{\"fidelity_score\": \"$SCORE\"}"`
- **Trigger**: Recipe engine evaluates context variables
- **Visible**: Recipe step output

These systems have **no shared state**. Calling `update_fidelity` (System A) does not update `{{fidelity_score}}` (System B). Running the recipe convergence loop (System B) does not update the dashboard (System A). A user running `/crew` mode gets System A. A user running the recipe directly gets System B.

**This explains "only picks up intent"**: If the orchestrator calls `update_fidelity` after the intent-analyst returns but then loses the instruction for subsequent delegations, only the intent_clarity lens gets updated. The dashboard shows intent at 0.75+ but everything else at 0.00.

---

## Finding 4: The Dashboard Depends on a Voluntary LLM Action

The hooks-fidelity-reporter module (System A's display layer) works as follows:

1. It fires on `tool:post` and `prompt:complete` events
2. It reads `zerovector.fidelity_state` capability from the coordinator
3. If the capability exists AND has lens_scores, it renders the dashboard
4. If no capability or no scores, it silently returns `continue` (no output)

**Critical implication**: The dashboard is **invisible** until the LLM calls `update_fidelity` at least once. If the LLM never calls it (skips entirely), the user sees no fidelity dashboard at all -- not even a "0.00" placeholder. The system fails silently.

**Evidence**: Commit `1ed8932` message states: "The orchestrator was only calling update_fidelity after critic returns, leaving the dashboard frozen at 0.00 for specification/implementation/quality/ship-readiness while real work was happening."

---

## Finding 5: The Double-Declaration Fix Reveals a Composition Bug

Commit `6a0999e` ("declare fidelity modules directly in crew behavior") has the message: "transitive include doesn't merge hooks." This means:

- `zerovector-crew.yaml` includes `zerovector:behaviors/fidelity` (which has hooks-fidelity-reporter)
- But the hooks from the transitively-included behavior don't get merged into the session
- The fix was to re-declare `hooks-fidelity-reporter` and `tool-fidelity-state` directly in `zerovector-crew.yaml`

**Current state**: Both `fidelity.yaml` AND `zerovector-crew.yaml` declare the same two modules. This double-declaration works but means:
- Using `fidelity.yaml` standalone: modules load once (correct)
- Using `zerovector-crew.yaml`: modules may load twice (once from direct declaration, once from transitive include if the bug gets fixed)

**This explains "fires twice"**: If the composition bug is intermittently fixed (e.g., different Amplifier versions), both the transitive and direct declarations would load the hook, causing the fidelity reporter to fire twice per event.

---

## Finding 6: 434 Tests, Zero Runtime Behavioral Tests

The test suite is extensive (17 files, ~434 tests) but exclusively structural:

- Tests verify that files exist and contain the right words
- Tests verify YAML structure (correct keys, correct values)
- Tests verify that mode files reference `fidelity-framework.md`
- Tests verify that the `FidelityState` dataclass computes correctly
- Tests verify that `FidelityReporter` renders correctly given state

**What is NOT tested**:
- Whether the LLM actually calls `update_fidelity` after delegations
- Whether the dashboard appears at the right times
- Whether the convergence loop actually converges
- Whether the two tracking systems (tool vs recipe) interact correctly
- Whether the critic's JSON output actually gets parsed by the orchestrator
- End-to-end: intent -> assessment -> routing -> convergence

This is fundamentally untestable with static assertions because the "caller" is an LLM following natural-language instructions. But it means there is zero verification that the behavioral contract works.

---

## Finding 7: The Fix Chain Tells a Story of Discovery

Reading the 8 fix commits chronologically (oldest first) reveals a debugging narrative:

| Order | Commit | Problem Discovered |
|-------|--------|--------------------|
| 1 | `1315378` | Tool module didn't mount (async/await bug) |
| 2 | `a485862` | Module source URIs invalid (couldn't find modules) |
| 3 | `b2a15a1` | Critic called update_fidelity AND orchestrator did too (double-fire) |
| 4 | `55866e1` | update_fidelity not in mode safe tools (tool blocked by mode policy) |
| 5 | `9a49682` | Critic still had phantom update_fidelity instruction (contradiction) |
| 6 | `6a0999e` | Transitive behavior include didn't merge hooks (modules not loaded) |
| 7 | `37e79f6` + `b4f52f4` | LLM bypasses crew mode entirely (no fidelity at all) |
| 8 | `1ed8932` | Orchestrator only updates after critic, not after other agents (frozen dashboard) |

**Pattern**: Each fix addressed one failure mode, revealing the next. The system has at least 8 distinct failure modes, each independently capable of breaking the fidelity mechanism. This is a **serial dependency chain** where every link must hold for the mechanism to work.

---

## Finding 8: The Critic's Dual Role Creates Ambiguity

The critic agent serves two distinct functions:

1. **Fidelity Assessor** (Pass 1): Score all 5 lenses, produce structured JSON
2. **Quality Validator** (Pass 2): Domain-specific quality checks, VERDICT line

These are architecturally different roles. As assessor, the critic produces data the orchestrator consumes. As validator, the critic produces a PASS/FAIL verdict. The same agent, same delegation, same output -- but two different consumers (orchestrator reads JSON for fidelity routing; recipe engine reads VERDICT for flow control).

The critic's Step 6 ("Structured Fidelity Output") says: "You do NOT need to call `update_fidelity` yourself -- the orchestrator handles this." This is correct for the assessor role but creates a dependency: the orchestrator MUST parse the critic's JSON and call update_fidelity. If the orchestrator doesn't (e.g., it gets distracted by the VERDICT), the dashboard stays frozen.

---

## Overall Assessment

The fidelity mechanism's inconsistent behavior is not a single bug but a **systemic fragility** arising from:

1. **Instruction scatter**: Critical behavioral contract spread across 51KB of context
2. **Voluntary compliance**: No programmatic enforcement; LLM can rationalize past any instruction
3. **Dual tracking systems**: Tool-based and recipe-based fidelity with no shared state
4. **Serial dependency chain**: 8+ components must all work correctly for the mechanism to function
5. **Silent failure**: Dashboard is invisible when the mechanism fails, giving no diagnostic signal
6. **Testing gap**: Extensive structural tests but zero behavioral/integration tests

The 8 fix commits in 2 days are evidence that the system's authors encountered every one of these failure modes in practice.
