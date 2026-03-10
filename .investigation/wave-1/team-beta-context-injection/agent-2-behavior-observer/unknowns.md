# Unknowns: What I Could Not Determine

> Agent: Behavior Observer (WHAT)
> Investigation: team-beta-context-injection
> Date: 2026-03-09

---

## Unknown 1: Does Amplifier Deduplicate Multi-Path Context Injection?

**What I observed:** `crew-instructions.md` and `domain-tuning.md` are each referenced through 3 independent injection paths (bundle.md @include, behavior YAML context include, mode text reference).

**What I could not determine:** Whether the Amplifier framework deduplicates these injections. If it does, the file appears once in the LLM context (~4K tokens). If it does not, the file appears up to 3 times (~12K tokens).

**Why it matters:** If context is tripled, the orchestrator's zerovector context could be ~34K tokens instead of ~17K. This affects both token budget and instruction salience — the `update_fidelity` MANDATORY section (~300 tokens) would be a smaller fraction of total context.

**How to resolve:** Examine the Amplifier core context assembly code, or instrument a session to dump the actual prompt sent to the LLM API.

---

## Unknown 2: What Does the `modes:context/modes-instructions.md` File Contain?

**What I observed:** `zerovector-crew.yaml` includes `modes:context/modes-instructions.md` in its context list. This file comes from the external `amplifier-bundle-modes` package (referenced via git URL).

**What I could not determine:** The contents of this file. It is not in the zerovector bundle — it's in an external dependency.

**Why it matters:** This is part of the context injection chain. If it contains fidelity-related instructions or tool usage guidance, it's another source of instructions the LLM receives. If it conflicts with zerovector's fidelity instructions, it could cause confusion.

**How to resolve:** Clone and read `amplifier-bundle-modes` from the git URL in the behavior YAML.

---

## Unknown 3: What Does the Foundation Bundle (`amplifier-foundation`) Inject?

**What I observed:** `bundle.md` includes `git+https://github.com/microsoft/amplifier-foundation@main` as a dependency. The bundle.md also references `@foundation:context/shared/common-system-base.md` at line 118.

**What I could not determine:** The full context injected by the foundation bundle. It may include system-level instructions about tool usage, delegation patterns, or other base behaviors.

**Why it matters:** If the foundation bundle includes general instructions about when/how to call tools, these could reinforce or contradict the zerovector-specific `update_fidelity` instructions.

**How to resolve:** Clone and read `amplifier-foundation` from the git URL.

---

## Unknown 4: Actual LLM Compliance Rate for update_fidelity Calls

**What I observed:** The git log shows at least 6 commits specifically fixing the update_fidelity injection chain, and the crew-instructions.md uses escalating emphasis (5 levels of urgency). This strongly suggests the LLM fails to comply.

**What I could not determine:** The actual compliance rate. How often does the orchestrator call `update_fidelity` after a delegation returns? 50% of the time? 10%? Only on the first delegation?

**Why it matters:** Without this data, we can't assess whether the problem is:
- (a) The instruction never reaches the LLM (injection chain broken)
- (b) The instruction reaches but gets lost in ~17K tokens of context (salience problem)
- (c) The instruction is salient but the LLM deprioritizes it (compliance problem)
- (d) The tool call fails silently (runtime problem)

**How to resolve:** Instrument sessions with logging on `update_fidelity` tool calls, or review actual conversation transcripts.

---

## Unknown 5: Does the `<CRITICAL>` Tag Have Special Semantics in Amplifier?

**What I observed:** The `crew-instructions.md` wraps the MANDATORY update_fidelity section in `<CRITICAL>` tags. The `<STANDING-ORDER>` tag is used in bundle.md. The `<EXTREMELY-IMPORTANT>` tag is used in using-zerovector.md.

**What I could not determine:** Whether these XML-style tags have special handling in the Amplifier framework (e.g., elevated priority, always-included in context window, highlighted to the LLM), or whether they are simply prompt engineering conventions that the LLM may or may not respect.

**Why it matters:** If these tags are just text, their effectiveness depends on LLM training data. If they have framework-level semantics (e.g., Amplifier extracts `<CRITICAL>` sections and places them at the end of the prompt for recency bias), they would be significantly more effective.

**How to resolve:** Read the Amplifier core prompt assembly code to check for special handling of XML tags.

---

## Unknown 6: How Does the hooks-crew-gate Module Work?

**What I observed:** An untracked directory `modules/hooks-crew-gate/` exists (visible in git status). A roadmap document exists at `docs/ROADMAP-crew-gate.md`. This module contains Python code (`__init__.py` at 9,609 bytes).

**What I could not determine:** Whether this module is currently active (it's not referenced in any behavior YAML) and whether it provides programmatic enforcement of `update_fidelity` calls.

**Why it matters:** If `hooks-crew-gate` verifies that `update_fidelity` was called after each delegation, it would close the enforcement gap identified in Anti-Pattern 1. If it's not yet wired in, the enforcement gap remains.

**How to resolve:** Read `modules/hooks-crew-gate/__init__.py` and `docs/ROADMAP-crew-gate.md` to understand its current state and wiring status.

---

## Unknown 7: Does the Builder Agent Exist?

**What I observed:** I found `agents/builder.md` (196 lines) and read it successfully. However, `zerovector-crew.yaml` includes 4 agents: `intent-analyst`, `architect`, `builder`, `shipper` — but NOT `critic`. The `fidelity.yaml` behavior includes `critic`.

**What I confirmed:** All 5 agent files exist: critic.md, intent-analyst.md, architect.md, builder.md, shipper.md. But the agent inclusion is SPLIT across behaviors:
- `zerovector-crew.yaml` → intent-analyst, architect, builder, shipper (4 agents)
- `fidelity.yaml` → critic (1 agent)

**What I could not determine:** Whether this split causes any context inheritance issues. Does the critic agent get the same behavior-level context as the other 4 agents, or does it only get context from the fidelity behavior?

**How to resolve:** Examine Amplifier's agent resolution logic — specifically whether an agent included by a sub-behavior inherits context from the parent behavior.

---

## Unknown 8: The `fidelity-framework.md` API Example Mismatch

**What I observed:** The "Calling update_fidelity" section in `fidelity-framework.md` (lines 176-200) shows a code example that passes `domain`, `target`, `lenses`, `overall`, `priority_gap`, and `evidence` to `update_fidelity()`. But the actual tool schema (from `tool-fidelity-state/__init__.py` lines 120-138) only accepts `lens_scores`, `domain`, and `target`.

**What I could not determine:** Whether the LLM's tool-calling mechanism would strip the extra fields silently, or whether passing `overall`, `priority_gap`, `evidence`, and `lenses` (instead of `lens_scores`) would cause the tool call to fail or behave unexpectedly.

**Why it matters:** If the LLM follows the fidelity-framework.md example literally, it would pass:
- `lenses` (wrong key — tool expects `lens_scores`)
- `overall` (not a tool parameter — ignored or error?)
- `priority_gap` (not a tool parameter)
- `evidence` (not a tool parameter)

This mismatch between documentation and implementation could cause silent failures or confusing error messages.

**How to resolve:** Test what happens when extra/wrong-keyed fields are passed to the UpdateFidelityTool.execute() method. Also check whether the `crew-instructions.md` examples (which use `lens_scores=` correctly) override the fidelity-framework.md examples in the LLM's context.

---

## Questions Raised by These Findings

1. **Is the "single point of authority" pattern (only orchestrator calls update_fidelity) the right architecture, or should agents be able to update their own lens scores directly?** The current architecture is clean in theory but fragile in practice.

2. **Would moving the MANDATORY update_fidelity instruction into the mode files (instead of only context files) improve compliance?** Mode files are more directly "active" when the mode is on, vs. context files which are background material.

3. **Is there a way to make the ephemeral injection bootstrap itself?** Currently it's a dead loop: the hook only fires after update_fidelity is called, but the instruction to call update_fidelity is in static context that may be lost in the noise.

4. **Should the 6 mode files be refactored into a shared template + domain overlays?** The 72% duplication is a maintenance risk and a token waste.
