# Catalog: Fidelity Mechanism Behavioral Instances

> Agent: Behavior Observer (WHAT)
> Scope: Every artifact that instructs, implements, tests, or composes the fidelity mechanism
> Method: Full-text search across 123 files (1,770 fidelity-related matches), followed by individual file reads of 30+ artifacts

---

## 1. Instructions That Tell the LLM to Call `update_fidelity`

These are the specific locations where the LLM is told *when* and *how* to invoke the `update_fidelity` tool. This is the core behavioral contract.

| # | File | Lines | Instruction Summary | Strength |
|---|------|-------|---------------------|----------|
| 1 | `context/crew-instructions.md` | 134-196 | **CRITICAL block**: "EVERY time a delegate() call returns, your NEXT action MUST be `update_fidelity`." Includes exact scoring guidance per agent type, two concrete examples, and critic-failure fallback. | **Strongest** -- `<CRITICAL>` tags, bold emphasis, examples |
| 2 | `context/crew-instructions.md` | 131 | "The `update_fidelity` tool must be called after each assessment to persist state" | Medium -- single line in Loop Rules |
| 3 | `context/crew-instructions.md` | 249 | "After each critic assessment, call `update_fidelity` to persist the fidelity state." | Medium -- in Delegation Contract section |
| 4 | `context/crew-instructions.md` | 328 | Anti-rationalization: "The scores look fine -- no need to call update_fidelity" -> "Always persist." | Medium -- negative reinforcement |
| 5 | `context/crew-instructions.md` | 329 | Anti-rationalization: "I'll update fidelity after routing to the next agent" -> "No. update_fidelity is your FIRST action." | Medium -- negative reinforcement |
| 6 | `context/fidelity-framework.md` | 172-203 | "Calling update_fidelity" section with full JSON example and "Always call `update_fidelity` after a fidelity assessment." | Medium -- tutorial style, code example |
| 7 | `agents/critic.md` | 260-268 | **Step 6**: "You do NOT need to call `update_fidelity` yourself -- the orchestrator handles this after your delegation returns." | **Contradictory** -- tells critic NOT to call it |
| 8 | `modes/crew.md` | 20 | `update_fidelity` listed in `tools.safe` | Enabling -- makes tool available |
| 9 | `modes/crew-build.md` | 20 | `update_fidelity` listed in `tools.safe` | Enabling |
| 10 | `modes/crew-product.md` | 18 | `update_fidelity` listed in `tools.safe` | Enabling |
| 11 | `modes/crew-platform.md` | 20 | `update_fidelity` listed in `tools.safe` | Enabling |
| 12 | `modes/crew-research.md` | 18 | `update_fidelity` listed in `tools.safe` | Enabling |
| 13 | `modes/crew-content.md` | 18 | `update_fidelity` listed in `tools.safe` | Enabling |

**Key observation**: 6 places tell the LLM TO call it, 1 place tells the critic NOT to call it, and 6 mode files enable the tool. The "call it" instructions are scattered across 3 different sections of crew-instructions.md plus fidelity-framework.md.

---

## 2. Mode Files and Tool Policies

All 6 crew modes examined. Every mode has identical tool policy structure for fidelity.

| # | Mode File | `update_fidelity` in safe? | `default_action` | LSP/python_check? | Lines |
|---|-----------|---------------------------|-------------------|-------------------|-------|
| 1 | `modes/crew.md` | Yes (line 20) | block | Yes | 184 |
| 2 | `modes/crew-build.md` | Yes (line 20) | block | Yes | 156 |
| 3 | `modes/crew-product.md` | Yes (line 18) | block | No | 150 |
| 4 | `modes/crew-platform.md` | Yes (line 20) | block | Yes | 167 |
| 5 | `modes/crew-research.md` | Yes (line 18) | block | No | 164 |
| 6 | `modes/crew-content.md` | Yes (line 18) | block | No | 164 |

**Key observation**: `update_fidelity` is uniformly in `safe` tools across all 6 modes. Product, research, and content lack LSP/python_check but that's domain-appropriate. The fidelity tool availability is perfectly consistent.

---

## 3. Behavior Composition Files

| # | Behavior File | Modules Included | Agents | Context | Includes |
|---|---------------|-----------------|--------|---------|----------|
| 1 | `behaviors/fidelity.yaml` | hooks-fidelity-reporter, tool-fidelity-state | critic only | using-zerovector.md, fidelity-framework.md | None (self-contained) |
| 2 | `behaviors/zerovector-crew.yaml` | hooks-mode, **hooks-fidelity-reporter** (again), tool-mode, **tool-fidelity-state** (again) | intent-analyst, architect, builder, shipper (NOT critic) | using-zerovector.md, crew-instructions.md, domain-tuning.md, modes-instructions.md | `zerovector:behaviors/fidelity` |

**Key observation -- DOUBLE DECLARATION**: `zerovector-crew.yaml` includes `fidelity.yaml` via `includes:` (which should bring hooks-fidelity-reporter and tool-fidelity-state transitively) AND ALSO declares them directly in its own `hooks:` and `tools:` sections. This was an intentional fix (commit `6a0999e`): "transitive include doesn't merge hooks." This means the fidelity modules are declared **twice** when using the full crew behavior.

---

## 4. Context Files With Fidelity Instructions

| # | Context File | Size | Fidelity Mentions | Primary Purpose |
|---|-------------|------|-------------------|-----------------|
| 1 | `context/fidelity-framework.md` | 11,941 bytes (225 lines) | ~90 | Universal lens model, scoring rubric, JSON format, `update_fidelity` calling instructions |
| 2 | `context/crew-instructions.md` | 15,462 bytes (345 lines) | ~80 | Orchestrator operating manual: convergence loop, mandatory update protocol, approval points |
| 3 | `context/domain-tuning.md` | 17,566 bytes (453+ lines) | ~60 | Domain-specific fidelity criteria per lens (build, product, platform, research, content) |
| 4 | `context/using-zerovector.md` | 2,657 bytes | ~5 | Nudge to suggest crew mode before artifact creation |
| 5 | `context/zerovector-principles.md` | 4,127 bytes | ~3 | ZVD philosophy, agent roles, anti-craft framing |

**Key observation**: Fidelity instructions are spread across 5 context files totaling ~51,753 bytes (~850 lines) of context. The LLM must internalize instructions from at least 3 files (crew-instructions, fidelity-framework, domain-tuning) to correctly operate the fidelity mechanism.

---

## 5. Agent Files With Fidelity Awareness

| # | Agent File | Fidelity Lens Served | Has `## Fidelity Context` Section? | Calls `update_fidelity`? |
|---|-----------|---------------------|-----------------------------------|-----------------------|
| 1 | `agents/critic.md` | All 5 (assessor) | Yes (Fidelity Assessment Protocol) | **Explicitly told NOT to** (line 263) |
| 2 | `agents/intent-analyst.md` | Intent Clarity | Yes | No |
| 3 | `agents/architect.md` | Specification | Yes | No |
| 4 | `agents/builder.md` | Implementation | Yes | No |
| 5 | `agents/shipper.md` | Ship-Readiness | Yes | No |

**Key observation**: Only the orchestrator (crew mode) is supposed to call `update_fidelity`. The critic explicitly produces the JSON assessment but does NOT call the tool -- the orchestrator extracts scores and calls it. All other agents have no fidelity-calling responsibility.

---

## 6. Module Source Code

| # | Module | Type | File Size | Key Classes | Capability Registered |
|---|--------|------|-----------|-------------|----------------------|
| 1 | `modules/tool-fidelity-state/` | tool | 6,607 bytes (198 lines) | `FidelityState`, `UpdateFidelityTool` | `zerovector.fidelity_state`, `zerovector.update_fidelity` |
| 2 | `modules/hooks-fidelity-reporter/` | hook | 13,566 bytes (380 lines) | `FidelityReporter` | None (reads `zerovector.fidelity_state` capability) |
| 3 | `modules/hooks-crew-gate/` | hook | 9,609 bytes (untracked) | Unknown | **NOT LOADED** -- module never mounts |

**Key observation about tool-fidelity-state**: The `UpdateFidelityTool.execute()` method accepts `lens_scores`, `domain`, and `target`. The `FidelityState.update_fidelity()` method computes `overall` as arithmetic mean and identifies `priority_gap` as the minimum-scoring lens. The tool schema requires `lens_scores` but `domain` and `target` have defaults ("general", 0.85).

**Key observation about hooks-fidelity-reporter**: Reads from `zerovector.fidelity_state` capability. If the capability doesn't exist or has no lens_scores, it silently returns `continue` with no output. This means if `update_fidelity` was never called, the dashboard never appears.

---

## 7. Recipe Files

| # | Recipe | Has fidelity_score context? | Has while_condition? | References update_fidelity? |
|---|--------|---------------------------|---------------------|---------------------------|
| 1 | `recipes/fidelity-convergence.yaml` | Yes (fidelity_score: "0", target_fidelity: "0.85") | Yes: `{{fidelity_score}} < {{target_fidelity}}` | No -- uses recipe context variables, not the tool |
| 2 | `recipes/intent-to-artifact.yaml` | Yes (same variables) | Yes (embedded convergence loop) | No -- same pattern |
| 3 | `recipes/decode-intent.yaml` | No | No | No |
| 4 | `recipes/finish-artifact.yaml` | No | No | No |
| 5 | `recipes/verify-artifact.yaml` | No | No | No |

**Key observation**: The recipes use a **separate** fidelity tracking mechanism (`{{fidelity_score}}` context variable) from the tool-based mechanism (`update_fidelity` tool -> `FidelityState` -> hooks-fidelity-reporter). These are two parallel systems.

---

## 8. Test Files

| # | Test File | Tests | What It Tests |
|---|-----------|-------|---------------|
| 1 | `tests/modules/test_fidelity_state.py` | 30 | FidelityState defaults, update_fidelity, get_state, UpdateFidelityTool.execute, mount |
| 2 | `tests/modules/test_fidelity_reporter.py` | 35 | render_dashboard, render_ephemeral, handle_event, mount |
| 3 | `tests/behaviors/test_fidelity_behavior.py` | 10 | Structural: YAML valid, correct name, hooks/tools/agents/context references |
| 4 | `tests/behaviors/test_zerovector_crew_behavior.py` | ~12 | Structural: includes fidelity behavior, correct agents list |
| 5 | `tests/agents/test_critic_agent.py` | ~20 | Fidelity Assessment Protocol section, all 5 lenses, two-pass structure, Step 6 update_fidelity |
| 6 | `tests/agents/test_builder_agent.py` | ~18 | Fidelity awareness, Implementation lens, partial spec start |
| 7 | `tests/agents/test_shipper_agent.py` | ~18 | Fidelity awareness, Ship-Readiness lens, early invocation |
| 8 | `tests/agents/test_architect_agent.py` | ~18 | Fidelity awareness, Specification lens |
| 9 | `tests/agents/test_intent_analyst_agent.py` | ~18 | Fidelity awareness, Intent Clarity lens |
| 10 | `tests/modes/test_crew_mode.py` | ~20 | Fidelity convergence terminology, anti-rationalization, approval points |
| 11 | `tests/modes/test_crew_domain_modes.py` | ~80 | Same for all 5 domain modes |
| 12 | `tests/context/test_crew_instructions.py` | ~25 | Fidelity convergence model, 5 lenses, update_fidelity mentioned |
| 13 | `tests/context/test_domain_tuning.py` | ~20 | Fidelity terminology, fidelity-framework reference |
| 14 | `tests/recipes/test_fidelity_convergence.py` | ~30 | Recipe structure, context variables, while_condition, break_when |
| 15 | `tests/recipes/test_intent_to_artifact.py` | ~40 | Stage structure, fidelity-converge stage, convergence loop |
| 16 | `tests/test_bundle.py` | ~15 | Bundle mentions fidelity, references recipe, behaviors exist |
| 17 | `tests/test_readme.py` | ~25 | README has fidelity sections, references modules, Universal Fidelity section |

**Total: ~434 tests across 17 test files.** All tests are structural/text-matching -- they verify that the right words appear in the right files. **Zero tests verify runtime fidelity behavior** (e.g., "when the LLM delegates to critic, does it then call update_fidelity?").

---

## 9. Git Fix Chain (Reverse Chronological)

| # | Commit | Date | Fix Summary |
|---|--------|------|-------------|
| 1 | `1f838c7` | Mar 9 | docs: crew-gate roadmap documenting what works and what doesn't |
| 2 | `1ed8932` | Mar 9 | **fix**: CRITICAL block for mandatory post-delegation update_fidelity |
| 3 | `6a0999e` | Mar 8 | **fix**: declare fidelity modules directly (transitive include broken) |
| 4 | `9a49682` | Mar 8 | **fix**: remove phantom update_fidelity from critic (was causing double-fire) |
| 5 | `b4f52f4` | Mar 8 | fix: add using-zerovector.md context for mode suggestion |
| 6 | `37e79f6` | Mar 8 | fix: add STANDING-ORDER for crew suggestion |
| 7 | `55866e1` | Mar 8 | **fix**: add update_fidelity to all crew mode safe tools |
| 8 | `b2a15a1` | Mar 8 | **fix**: constrain critic to single update_fidelity call |
| 9 | `1315378` | Mar 8 | **fix**: await async coordinator.mount() |
| 10 | `a485862` | Mar 8 | fix: valid module source URIs in behavior files |

**8 fix commits in 2 days**, 6 of which directly address fidelity mechanism failures. This is a system that was extensively debugged post-launch.
