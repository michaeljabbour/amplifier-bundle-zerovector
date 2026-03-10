# Findings: Context Injection Chain for Fidelity Instructions

> Agent: Behavior Observer (WHAT)
> Investigation: team-beta-context-injection
> Artifacts examined: 19 files (5 context, 6 modes, 5 agents, 2 behaviors, 1 bundle root) + 2 module source files + git log
> Date: 2026-03-09

---

## Executive Summary

The zerovector bundle's context injection chain distributes fidelity instructions across 19 files totaling ~34,000 tokens. The instruction "call `update_fidelity`" exists in exactly **2 of 19 files** (crew-instructions.md and fidelity-framework.md), but only reaches the LLM through an indirect path: context files are injected into the root orchestrator session, which must then manually pass fidelity context forward to sub-agents via delegation instructions. Sub-agents (critic, builder, architect, intent-analyst, shipper) **never see the update_fidelity instruction** — they only see their own agent definition. The entire fidelity update mechanism depends on the orchestrator (root LLM) remembering to call `update_fidelity` after every delegation return, based solely on instructions it read in context files.

---

## Finding 1: The "Call update_fidelity" Instruction Exists in Only 2 of 19 Files

Of the 19 files in the injection chain, only 2 contain actual instructions telling the LLM to call the `update_fidelity` tool:

| File | Mentions | Nature of Instruction |
|------|----------|-----------------------|
| `context/crew-instructions.md` | 11 | `<CRITICAL>` section: "MANDATORY: Update Fidelity After Every Delegation" — detailed rules, examples for each agent type, anti-rationalization entries |
| `context/fidelity-framework.md` | 4 | "Calling update_fidelity" section — code example, rule "Always call update_fidelity after a fidelity assessment" |

The remaining 17 files either:
- List `update_fidelity` as a safe tool (6 mode files — tool POLICY, not instruction)
- Explicitly say NOT to call it (1 file: `agents/critic.md`)
- Don't mention it at all (10 files)

**Implication:** If either `crew-instructions.md` or `fidelity-framework.md` fails to reach the LLM's active context, the instruction to call `update_fidelity` is absent from the session.

---

## Finding 2: Sub-Agents Cannot See Fidelity Update Instructions

The 5 agent files are self-contained definitions that run in child sessions. When the orchestrator delegates to `zerovector:critic`, the critic's session receives:

1. The critic agent definition (`agents/critic.md` — 304 lines)
2. Its own declared tools (filesystem, bash, search, python-check)
3. Whatever the orchestrator manually includes in the `instruction` parameter

The critic's session does **NOT** receive:
- `context/crew-instructions.md` (the file with the MANDATORY update_fidelity section)
- `context/fidelity-framework.md` (the file with the update_fidelity calling convention)
- `context/domain-tuning.md`
- Any mode file
- Any behavior context

This is **architecturally intentional**. The critic's agent definition (line 263) explicitly states:
> "You do NOT need to call `update_fidelity` yourself — the orchestrator handles this after your delegation returns."

The same pattern holds for all 5 agents: 4 of 5 agents (intent-analyst, architect, builder, shipper) have zero mentions of `update_fidelity`. They are **fidelity-aware** (each knows which lens it serves) but not **fidelity-updating**.

**Architecture:** Only the root orchestrator calls `update_fidelity`. Sub-agents produce structured output (e.g., JSON fidelity scores from the critic) which the orchestrator then extracts and passes to the tool.

---

## Finding 3: The Injection Chain Has 3 Composition Layers With Significant Overlap

Context reaches the LLM through 3 independent composition mechanisms, which overlap:

### Layer 1: bundle.md @includes (root session)
```
bundle.md @zerovector:context/zerovector-principles.md
bundle.md @zerovector:context/crew-instructions.md
bundle.md @zerovector:context/domain-tuning.md
```

### Layer 2: Behavior YAML context includes (root session)
```
zerovector-crew.yaml → using-zerovector.md, crew-instructions.md, domain-tuning.md, modes-instructions.md
fidelity.yaml → using-zerovector.md, fidelity-framework.md
```

### Layer 3: Mode file text references (root session, mode active)
```
All 6 modes → "Read crew-instructions.md" / "Read fidelity-framework.md" / "Read domain-tuning.md"
```

**Overlap analysis:**

| Context File | Layer 1 (@include) | Layer 2 (behavior) | Layer 3 (mode text) |
|-------------|-------------------|-------------------|-------------------|
| zerovector-principles.md | YES | no | no |
| crew-instructions.md | YES | YES | YES (all 6) |
| domain-tuning.md | YES | YES | YES (all 6) |
| using-zerovector.md | no | YES (both behaviors) | no |
| fidelity-framework.md | no | YES (fidelity only) | YES (all 6) |

`crew-instructions.md` and `domain-tuning.md` are referenced in ALL 3 layers — potentially injected up to 3 times into the root session.

`fidelity-framework.md` is NOT in Layer 1 (not @included from bundle.md) — it enters only via the fidelity behavior and mode text references.

---

## Finding 4: Massive Redundancy in Fidelity Concept Descriptions

The convergence loop (ASSESS → ROUTE → ACT → RE-ASSESS) is described in **at least 8 distinct files**:

1. `bundle.md` (lines 88-98)
2. `context/crew-instructions.md` (lines 80-87, plus 91-113)
3. `context/fidelity-framework.md` (implied in routing table)
4. `modes/crew.md` (lines 49-55, plus 99-130)
5. `modes/crew-build.md` (lines 37-38, plus 97-112)
6. `modes/crew-product.md` (lines 36-37, plus 99-114)
7. `modes/crew-platform.md` (lines 38-39, plus 101-116)
8. `modes/crew-research.md` (lines 36-37, plus 98-113)
(crew-content follows same pattern)

The lens-to-agent routing table appears in **at least 9 files**: all 6 modes, crew-instructions.md, fidelity-framework.md, and bundle.md.

The anti-rationalization entry "Fidelity is 0.78 — close enough to the 0.85 target" appears verbatim in **all 6 mode files** and in `crew-instructions.md` (7 copies total).

**Token cost of redundancy:** The 6 mode files are structurally near-identical, averaging 164 lines each. The domain-specific content (lens tuning table, anti-rationalization table, alternative recipe section) comprises roughly 40-50 lines per file. The remaining ~115 lines are shared boilerplate — ~690 lines of duplicated content across modes (~2,760 tokens).

---

## Finding 5: The Escalating Emphasis Pattern for update_fidelity

Instructions to call `update_fidelity` use progressively stronger language, suggesting repeated failures to comply:

| Source | Emphasis Level | Language |
|--------|---------------|----------|
| `fidelity-framework.md` | Moderate | "Always call `update_fidelity` after a fidelity assessment." |
| `crew-instructions.md` | `<CRITICAL>` wrapper | **"MANDATORY: Update Fidelity After Every Delegation"** |
| `crew-instructions.md` | Bold + ALL CAPS | "**EVERY time a delegate() call returns, your NEXT action MUST be `update_fidelity`.**" |
| `crew-instructions.md` | Anti-rationalization | Two dedicated table entries about NOT skipping update_fidelity |
| `crew-instructions.md` | Fallback protocol | "If the Critic Delegation Fails" section — "Do NOT leave all lenses at 0.00" |

This escalation is consistent with the git log: commit `55866e1` "fix: add update_fidelity to crew mode safe tools and orchestrator instructions" and commit `1ed8932` "fix: enforce mandatory fidelity updates after every agent delegation" suggest the LLM repeatedly failed to call update_fidelity, prompting stronger and stronger language.

---

## Finding 6: Behavior File Duplication Workaround

The `zerovector-crew.yaml` behavior includes `zerovector:behaviors/fidelity` transitively, but ALSO declares the same hooks and tools directly:

```yaml
# zerovector-crew.yaml
includes:
  - bundle: zerovector:behaviors/fidelity    # <-- includes hook and tool

hooks:
  - module: hooks-fidelity-reporter          # <-- ALSO declares same hook
    source: ../modules/hooks-fidelity-reporter

tools:
  - module: tool-fidelity-state              # <-- ALSO declares same tool
    source: ../modules/tool-fidelity-state
```

This was explicitly fixed in commit `6a0999e`: "fix: declare fidelity modules directly in crew behavior (transitive include doesn't merge hooks)". The Amplifier framework apparently does not merge hook/tool declarations from transitively included behaviors, so they must be duplicated.

---

## Finding 7: The Ephemeral Injection Path (hooks-fidelity-reporter)

Beyond the static context injection chain, there is a **dynamic injection path**: the `hooks-fidelity-reporter` module fires on `tool:post` and `prompt:complete` events and returns:

1. An ANSI dashboard written to stdout (human-visible)
2. A `HookResult` with `context_injection` containing plain-text routing advice, marked `ephemeral=True`

The ephemeral injection looks like:
```
[FIDELITY STATE — ephemeral, auto-updates]
Status: NEEDS_WORK
Overall: 0.53 | Target: 0.85 (domain: build)
Priority gap: implementation (0.40)
Recommendation: Route to builder to address implementation gaps
```

This is the ONLY dynamic fidelity instruction in the chain — everything else is static context. But it only fires AFTER `update_fidelity` has been called at least once (otherwise `lens_scores` is empty and the hook returns a no-op). So it cannot bootstrap the first call.

---

## Finding 8: Token Budget Reality

When a crew mode is active, the root orchestrator's context includes approximately:

| Component | Est. Tokens |
|-----------|------------|
| bundle.md inline + @includes | ~2,500 |
| Behavior context (crew-instructions, domain-tuning, using-zerovector, fidelity-framework, modes-instructions) | ~13,000 |
| Active mode file | ~1,600 |
| foundation bundle context | unknown (external) |
| Ephemeral fidelity injection | ~50 (when active) |
| **TOTAL (zerovector only)** | **~17,150** |

Sub-agent context is much smaller:

| Component | Est. Tokens |
|-----------|------------|
| Agent definition (critic) | ~2,935 |
| Agent's own tool schemas | ~500 (est.) |
| Orchestrator's instruction text | variable |
| **TOTAL per sub-agent** | **~3,500-5,000** |

The root orchestrator carries ~17K tokens of zerovector context. Each sub-agent carries ~3.5-5K. The fidelity update instruction (`<CRITICAL>` section in crew-instructions.md) is roughly 300 tokens — less than 2% of the orchestrator's zerovector context budget.

---

## Finding 9: Git Log Shows Pattern of Fidelity Integration Fixes

The most recent 8 commits (of 20 examined) are all fixes to the fidelity context injection chain:

| Commit | Fix |
|--------|-----|
| `1ed8932` | "enforce mandatory fidelity updates after every agent delegation" |
| `6a0999e` | "declare fidelity modules directly in crew behavior (transitive include doesn't merge hooks)" |
| `9a49682` | "remove phantom update_fidelity instruction from critic (orchestrator handles root session updates)" |
| `b4f52f4` | "add using-zerovector.md context (matches superpowers pattern for reliable mode suggestion)" |
| `37e79f6` | "add STANDING-ORDER to crew-instructions for pre-mode crew suggestion" |
| `55866e1` | "add update_fidelity to crew mode safe tools and orchestrator instructions" |
| `b2a15a1` | "remove search_paths clobber from crew behavior, constrain critic to single update_fidelity call" |
| `1315378` | "await async coordinator.mount() in tool-fidelity-state" |

Of 8 recent fixes, **6 directly concern the update_fidelity injection chain** — suggesting this is the bundle's most fragile integration point.

---

## Finding 10: The Mode Files Are 72% Identical

Comparing the 6 mode files structurally:

| Section | Shared? | Variation |
|---------|---------|-----------|
| YAML frontmatter (tool policy) | Nearly identical | 3 modes omit LSP + python_check |
| Opening announcement | Different per domain | One line each |
| `<CRITICAL>` section | 80% shared | Domain name, agent tuning list differ |
| Todo list | Identical | 5 items, same in all 6 |
| Lens tuning table | Different per domain | 5 rows, domain-specific columns |
| Orchestration section | Identical | Same delegate() patterns |
| Convergence loop section | Identical | Same rules, same max iterations |
| Anti-rationalization table | ~80% shared | 1-2 domain-specific entries, rest shared |
| Transitions section | Different per domain | 2-3 lines each |

Estimated shared content: ~115 of ~160 lines (72%). The 6 mode files contribute ~6,800 tokens of shared content and ~2,700 tokens of domain-specific content.
