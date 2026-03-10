# Patterns and Anti-Patterns: Fidelity Mechanism

> Agent: Behavior Observer (WHAT)
> Source: Catalog of 30+ artifacts, 1,770 fidelity mentions, 10 fix commits

---

## Pattern 1: Instruction Scatter (Anti-Pattern)

**Where observed**: context/crew-instructions.md (4 locations), context/fidelity-framework.md (1 location), agents/critic.md (1 contradicting location)

**Frequency**: The instruction "call update_fidelity" appears in 6 places across 3 files. The counter-instruction "do NOT call update_fidelity" appears in 1 place (critic.md).

**Description**: The behavioral contract for when to call `update_fidelity` is scattered across ~51KB of context text. No single authoritative location contains the complete rule. The orchestrator must synthesize instructions from crew-instructions.md (CRITICAL block at line 134, Loop Rules at line 131, Delegation Contract at line 249, Anti-rationalization at lines 328-329) and fidelity-framework.md (Calling section at line 172). Meanwhile, critic.md (line 263) contradicts the generic guidance.

**Implication**: An LLM loading all this context may follow any single instruction fragment in isolation, producing inconsistent behavior. The CRITICAL block is the strongest signal, but if the LLM's attention is drawn to fidelity-framework.md's example first (which shows calling update_fidelity from the assessor's perspective), it may fire from the wrong session.

**Quantitative**: 6 "do it" instructions + 1 "don't do it" instruction across 3 files spanning 27,403 bytes of instructional text.

---

## Pattern 2: Consistent Tool Policy (Pattern)

**Where observed**: All 6 mode files (crew.md, crew-build.md, crew-product.md, crew-platform.md, crew-research.md, crew-content.md)

**Frequency**: 6 of 6 modes (100%)

**Description**: Every crew mode file lists `update_fidelity` in the `tools.safe` section, uses `default_action: block`, and follows the same YAML frontmatter structure. This was not always the case -- commit `55866e1` ("add update_fidelity to crew mode safe tools") added it to all 6 modes simultaneously.

**Implication**: This is a positive pattern. The tool is uniformly available. Before this fix, the tool was blocked by the mode's default policy, making the fidelity mechanism silently impossible even when the LLM tried to comply.

---

## Pattern 3: Double-Declaration Defensive Fix (Anti-Pattern)

**Where observed**: behaviors/zerovector-crew.yaml declares hooks-fidelity-reporter and tool-fidelity-state directly AND includes behaviors/fidelity.yaml which also declares them.

**Frequency**: 1 instance, but affects all crew sessions.

**Description**: The `zerovector-crew.yaml` behavior both:
- `includes: zerovector:behaviors/fidelity` (which contains the same modules)
- Directly declares `hooks-fidelity-reporter` and `tool-fidelity-state` in its own sections

This is a workaround for a discovered bug: "transitive include doesn't merge hooks" (commit `6a0999e`). The direct declaration ensures the modules load regardless of whether the transitive include works.

**Implication**: If the transitive include bug is ever fixed, the modules will be declared twice. For hooks-fidelity-reporter, this could mean the dashboard renders twice per event ("fires twice" from the user report). For tool-fidelity-state, the tool might be mounted twice or the second mount might silently fail/override.

---

## Pattern 4: Silent Failure Mode (Anti-Pattern)

**Where observed**: modules/hooks-fidelity-reporter (handle_event method), modules/tool-fidelity-state (mount function)

**Frequency**: Both modules exhibit this pattern.

**Description**: 
- `hooks-fidelity-reporter.handle_event()`: If `zerovector.fidelity_state` capability is None or has no lens_scores, returns `continue` with no output. No warning, no placeholder dashboard.
- `tool-fidelity-state.mount()`: All three registration steps (mount tool, register capability, register callable) are wrapped in `try/except Exception` with only `_log.debug()` logging. If any fails, the module silently continues.

**Implication**: When the fidelity mechanism fails, it fails invisibly. The user sees no dashboard (not even a "waiting for first assessment" message). The developer sees no errors unless debug logging is enabled. This makes diagnosis extremely difficult -- the symptom is "nothing happens" rather than an error message.

**Quantitative**: 3 silent try/except blocks in tool-fidelity-state.mount(), 1 silent early-return in hooks-fidelity-reporter.handle_event().

---

## Pattern 5: Uniform Agent Fidelity Awareness (Pattern)

**Where observed**: All 5 agent files (critic.md, intent-analyst.md, architect.md, builder.md, shipper.md)

**Frequency**: 5 of 5 agents (100%)

**Description**: Every agent has a `## Fidelity Context` section explaining which lens it serves and how it relates to the fidelity framework. Each non-critic agent mentions being "routable via fidelity priority gap." This awareness was added systematically across two commits (`b4d8511` for intent-analyst + architect, `ee277c0` for builder + shipper).

**Implication**: Good hygiene. Each agent knows its role in the fidelity system. However, none of the non-critic agents are told to call `update_fidelity` -- that responsibility is solely on the orchestrator. The agents produce work; the orchestrator scores it.

---

## Pattern 6: Structural Tests Without Behavioral Tests (Anti-Pattern)

**Where observed**: All 17 test files (~434 tests)

**Frequency**: 434 of 434 tests are structural (100%). 0 of 434 test runtime behavior (0%).

**Description**: Tests verify that:
- Files exist at expected paths
- YAML has correct keys and values  
- Markdown contains specific phrases ("fidelity", "update_fidelity", lens names)
- Dataclass computes correctly (FidelityState.update_fidelity math)
- Reporter renders correctly given state dicts

Tests do NOT verify that:
- The LLM calls update_fidelity when instructed
- The dashboard appears at the right time
- The convergence loop converges
- Recipe and tool tracking systems interact
- Context files produce the intended LLM behavior

**Implication**: The test suite validates the building materials but not the building. All 434 tests can pass while the fidelity mechanism fails in every user session. The 8 fix commits were all discovered through manual testing, not automated tests.

---

## Pattern 7: Dual Tracking System Disconnect (Anti-Pattern)

**Where observed**: 
- System A: modules/tool-fidelity-state + modules/hooks-fidelity-reporter (tool-based)
- System B: recipes/fidelity-convergence.yaml + recipes/intent-to-artifact.yaml (recipe context variables)

**Frequency**: 2 parallel systems with 0 integration points.

**Description**: System A uses `FidelityState` dataclass on the coordinator, updated by the `update_fidelity` tool, displayed by the reporter hook. System B uses `{{fidelity_score}}` and `{{target_fidelity}}` recipe context variables, updated by `update_context` in the recipe YAML, evaluated by the recipe engine's `while_condition`.

These systems share no state. A score in System A doesn't propagate to System B and vice versa.

**Implication**: Users running crew modes (interactive) get System A. Users running recipes (automated) get System B. The two experiences may diverge. If someone tries to mix them (e.g., running a recipe from within a crew mode), the fidelity tracking is fragmented.

---

## Pattern 8: Fix-Chain as Architecture Discovery (Pattern)

**Where observed**: Git history, 8 fix commits from `1315378` to `1ed8932`

**Frequency**: 8 sequential fixes over ~2 days

**Description**: Each fix revealed the next failure mode in a serial dependency chain:
1. Module wouldn't mount (async bug) -> fixed
2. Module couldn't be found (URI bug) -> fixed
3. Critic and orchestrator both called update_fidelity (double-fire) -> fixed
4. Tool blocked by mode policy (tool not in safe list) -> fixed
5. Critic still had phantom instruction (contradiction) -> fixed
6. Hooks didn't load from transitive include (composition bug) -> fixed
7. LLM bypassed crew mode entirely (no enforcement) -> partially fixed
8. Orchestrator only updated after critic (frozen dashboard) -> fixed with CRITICAL block

**Implication**: The fidelity mechanism has at least 8 independent failure modes. Fixing one reveals the next. This is characteristic of a system with a long serial dependency chain where every component must work correctly. The fix history IS the architecture documentation of failure modes.

---

## Pattern 9: Escalating Instruction Emphasis (Pattern)

**Where observed**: context/crew-instructions.md evolution across commits

**Frequency**: 3 escalation levels observed in the final state

**Description**: The instructions to call `update_fidelity` escalate in emphasis:
1. **Level 1** (normal): "The `update_fidelity` tool must be called after each assessment" (line 131, Loop Rules)
2. **Level 2** (bold + section): "## MANDATORY: Update Fidelity After Every Delegation" (line 134)
3. **Level 3** (CRITICAL tags): `<CRITICAL>` wrapper around the entire mandatory section (lines 133-196)

The anti-rationalization table also escalated, adding two fidelity-specific entries (lines 328-329) that directly address observed LLM failures.

**Implication**: The escalating emphasis is a sign that softer instructions didn't work. The authors had to progressively increase signal strength to get LLM compliance. This is a known pattern in prompt engineering: when the LLM ignores an instruction, you make it louder rather than architecturally enforcing it.

---

## Pattern 10: The Critic as Single Point of Coupling (Pattern)

**Where observed**: agents/critic.md, context/crew-instructions.md, recipes/fidelity-convergence.yaml

**Frequency**: The critic appears in every fidelity flow path.

**Description**: The critic is:
- The only agent that produces structured fidelity JSON
- The assessor delegated to before and after every convergence iteration
- Both a fidelity assessor (Pass 1) and quality validator (Pass 2)
- The source of truth for the orchestrator's update_fidelity call
- The source of the VERDICT line that the recipe engine parses

If the critic delegation fails, produces malformed JSON, or the orchestrator doesn't parse its output correctly, the entire fidelity mechanism stalls.

**Implication**: The critic is a single point of failure for fidelity assessment. The crew-instructions.md addresses this with a "If the Critic Delegation Fails" fallback (lines 186-195) instructing the orchestrator to estimate scores itself. But this fallback is itself another natural-language instruction the LLM may or may not follow.
