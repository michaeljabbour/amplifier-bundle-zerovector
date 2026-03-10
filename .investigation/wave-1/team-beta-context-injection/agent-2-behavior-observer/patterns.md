# Patterns & Anti-Patterns: Fidelity Instruction Distribution

> Agent: Behavior Observer (WHAT)
> Investigation: team-beta-context-injection
> Date: 2026-03-09

---

## Pattern 1: Single-Point-of-Authority for update_fidelity

**Where observed:** Root orchestrator session only
**Frequency:** Architectural invariant — 1 of 1 session layers is authorized
**Description:** Only the root orchestrator (the LLM in a `/crew-*` mode) calls `update_fidelity`. All 5 sub-agents are explicitly prohibited or uninstructed. The critic produces JSON scores; the orchestrator extracts and persists them.

**Evidence:**
- `agents/critic.md` line 263: "You do NOT need to call `update_fidelity` yourself"
- 4 other agents: zero mentions of `update_fidelity`
- `context/crew-instructions.md` lines 133-196: MANDATORY section addresses the orchestrator directly
- Commit `9a49682`: "remove phantom update_fidelity instruction from critic"
- Commit `b2a15a1`: "constrain critic to single update_fidelity call"

**Implication:** This is a deliberate architectural choice. The `update_fidelity` tool updates the ROOT session's fidelity state object. If a child agent called it, the update would go to the child's session state, invisible to the user dashboard. The pattern is sound but creates a single point of failure: if the orchestrator forgets, nothing else in the system will call it.

---

## Pattern 2: Escalating Emphasis ("Say It Louder")

**Where observed:** `context/crew-instructions.md`, `context/fidelity-framework.md`
**Frequency:** 2 of 19 files, with 3 escalation levels within crew-instructions.md
**Description:** The instruction to call `update_fidelity` is repeated with increasing urgency, suggesting repeated LLM non-compliance:

| Level | Location | Language |
|-------|----------|----------|
| 1. Moderate | fidelity-framework.md:174 | "Always call `update_fidelity` after a fidelity assessment." |
| 2. Critical wrapper | crew-instructions.md:133 | `<CRITICAL>` block, bold "MANDATORY" heading |
| 3. Absolute imperative | crew-instructions.md:140 | "**EVERY time a delegate() call returns, your NEXT action MUST be `update_fidelity`.** No exceptions." |
| 4. Anti-rationalization | crew-instructions.md:328-329 | Two table entries about NOT skipping update_fidelity |
| 5. Failure recovery | crew-instructions.md:188-196 | "If the Critic Delegation Fails" — "Do NOT leave all lenses at 0.00" |

**Git trail:** Commits `55866e1` → `b2a15a1` → `1ed8932` show 3 successive attempts to make the LLM comply, each adding stronger language.

**Implication:** The LLM is not reliably following the instruction despite 5 escalation levels. This suggests the problem is not instruction clarity but rather instruction salience — the instruction competes with ~17K tokens of other context.

---

## Pattern 3: Triple-Injection Redundancy

**Where observed:** `crew-instructions.md` and `domain-tuning.md`
**Frequency:** 2 of 5 context files are injected through all 3 composition layers
**Description:** Two context files are referenced in 3 independent injection paths:

| File | Layer 1: bundle.md @include | Layer 2: behavior YAML | Layer 3: mode text reference |
|------|---------------------------|----------------------|---------------------------|
| crew-instructions.md | YES | YES (zerovector-crew) | YES (all 6 modes) |
| domain-tuning.md | YES | YES (zerovector-crew) | YES (all 6 modes) |

**Implications:**
- If Amplifier deduplicates, only 1 copy reaches the LLM — redundancy is harmless but wasteful
- If Amplifier does NOT deduplicate, these files consume 3x their token budget (~24K tokens instead of ~8K)
- The behavior of Amplifier's deduplication is UNKNOWN to this observer (see unknowns.md)

---

## Pattern 4: Mode File Template Cloning

**Where observed:** All 6 mode files
**Frequency:** 6 of 6 mode files (100%)
**Description:** The 6 mode files share ~72% identical content. They appear to be created by cloning a template and substituting domain-specific values.

**Shared sections (identical across all 6):**
- Tool policy YAML (with minor LSP/python_check variation)
- Convergence loop description
- Initial assessment delegation pattern
- Convergence loop delegation pattern
- "When Convergence Is Reached" section
- "When the Loop Exhausts" section
- 4 of 6 anti-rationalization entries

**Domain-specific sections (differ):**
- Opening announcement (1 line)
- `<CRITICAL>` agent tuning list (5 lines)
- Lens tuning table (5 rows)
- 1-2 domain-specific anti-rationalization entries
- Transitions section (2-3 lines)

**Token cost:** ~2,760 tokens of duplicated boilerplate across the 6 modes. Only ~450 tokens per mode are truly unique.

**Implication:** Only 1 mode is active at a time, so the duplication doesn't multiply in-session. But it creates maintenance burden: a convergence loop change requires editing 6+ files.

---

## Pattern 5: Fidelity-Aware But Not Fidelity-Updating Agents

**Where observed:** All 5 agent files
**Frequency:** 5 of 5 agents (100%)
**Description:** Every agent has a "Fidelity Context" section explaining which lens it serves, but NONE of them are instructed to update fidelity scores.

| Agent | Lens Served | Fidelity Context Section | update_fidelity Instruction |
|-------|------------|-------------------------|---------------------------|
| intent-analyst | Intent Clarity | Lines 46-53 | None |
| architect | Specification | Lines 45-55 | None |
| builder | Implementation | Lines 55-72 | None |
| critic | Quality (assessment) | Full protocol | Explicitly NOT ("orchestrator handles this") |
| shipper | Ship-Readiness | Lines 56-73 | None |

**Implication:** Agent fidelity-awareness is for context (understanding WHY they were invoked and what translation loss to address), not for state management. This is clean separation of concerns — but it means the orchestrator is solely responsible for translating agent output into fidelity state updates.

---

## Pattern 6: The Missing @include

**Where observed:** `bundle.md`, `behaviors/fidelity.yaml`
**Frequency:** 1 notable omission
**Description:** `bundle.md` @includes 3 context files but NOT `fidelity-framework.md`:

```
@zerovector:context/zerovector-principles.md     ← @included
@zerovector:context/crew-instructions.md         ← @included
@zerovector:context/domain-tuning.md             ← @included
```

Missing:
```
context/fidelity-framework.md    ← NOT @included from bundle.md
context/using-zerovector.md      ← NOT @included from bundle.md
```

`fidelity-framework.md` reaches the session only via `behaviors/fidelity.yaml` context include. `using-zerovector.md` reaches via both behavior YAML files.

**Implication:** If the behavior chain breaks (e.g., fidelity behavior fails to mount), `fidelity-framework.md` — which contains the `update_fidelity` calling convention with code examples — would be absent from the session entirely. The bundle.md root provides no fallback path for this file.

---

## Pattern 7: Safe-Tool-List as Implicit Instruction

**Where observed:** All 6 mode files
**Frequency:** 6 of 6 modes (100%)
**Description:** All modes list `update_fidelity` in `tools.safe`, which is a TOOL POLICY declaration (the LLM is allowed to use it without warning). This is NOT an instruction to use it, but it serves as a signal that the tool exists and is expected in this context.

The `default_action: block` policy means any tool NOT in the safe/warn lists is blocked. So `update_fidelity` being in `safe` is necessary for the orchestrator to call it — but not sufficient to make it call it.

**Implication:** The mode file's tool policy is a gatekeeper, not a driver. Without the MANDATORY instruction from crew-instructions.md, the tool would be available but unused.

---

## Anti-Pattern 1: Instruction/Enforcement Separation

**Where observed:** Across the entire injection chain
**Description:** The instruction to call `update_fidelity` (in context files) is separated from the enforcement mechanism (tool policy in mode files). No part of the system VERIFIES that `update_fidelity` was actually called after a delegation returns.

| Component | Tells LLM to call it? | Enforces the call? |
|-----------|----------------------|-------------------|
| crew-instructions.md | YES (MANDATORY) | No |
| fidelity-framework.md | YES (Always) | No |
| Mode files | No (just allows it) | No |
| hooks-fidelity-reporter | No (reads state) | No |
| tool-fidelity-state | No (just executes) | No |
| hooks-crew-gate | Not yet implemented | Planned |

The only "enforcement" is the escalating language in crew-instructions.md — which is instruction, not verification.

**Implication:** The system relies entirely on LLM compliance with natural-language instructions. There is no programmatic check. The planned `hooks-crew-gate` module (see `docs/ROADMAP-crew-gate.md`) may address this, but it is not yet implemented.

---

## Anti-Pattern 2: Context-File-as-API-Documentation

**Where observed:** `context/fidelity-framework.md`
**Description:** The `fidelity-framework.md` file serves dual purposes: (1) it teaches the LLM the conceptual fidelity model, and (2) it contains the `update_fidelity` API calling convention with a code example. These two concerns (conceptual understanding vs. tool usage) are mixed in one file.

The "Calling update_fidelity" section (lines 172-203) includes a full JSON example with 7 fields, most of which (`overall`, `priority_gap`, `evidence`) are NOT parameters of the actual `update_fidelity` tool — the tool only accepts `lens_scores`, `domain`, and `target`.

**Implication:** The code example in `fidelity-framework.md` shows a DIFFERENT call signature than what the tool actually accepts. The example passes a JSON object with `overall`, `priority_gap`, and `evidence` fields; the actual tool schema only requires `lens_scores` with optional `domain` and `target`. This mismatch could confuse the LLM about what arguments to pass.

---

## Anti-Pattern 3: Ephemeral Injection Can't Bootstrap

**Where observed:** `modules/hooks-fidelity-reporter`
**Description:** The fidelity reporter hook injects ephemeral routing advice after every assistant turn — but ONLY if `update_fidelity` has been called at least once. If `lens_scores` is empty, the hook returns a no-op `_CONTINUE` sentinel.

```python
state = fidelity_state.get_state()
if not state.get("lens_scores"):
    return _CONTINUE  # No-op — nothing to show
```

**Implication:** The ephemeral injection is a reinforcement mechanism, not a bootstrapping mechanism. It cannot remind the LLM to make the FIRST `update_fidelity` call. The system depends entirely on the static context instructions for bootstrapping, and on the ephemeral injection for ongoing reinforcement. If the first call never happens, the reinforcement loop never activates.
