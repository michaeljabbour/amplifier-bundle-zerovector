# Catalog: Every File in the ZeroVector Context Injection Chain

> Agent: Behavior Observer (WHAT)
> Investigation: Context Injection Chain for Fidelity Instructions
> Date: 2026-03-09
> Method: Exhaustive read of every file in context/, modes/, behaviors/, agents/, and bundle.md

---

## Summary Statistics

| Category | File Count | Total Lines | Total Bytes | Fidelity Mentions | update_fidelity Mentions |
|----------|-----------|-------------|-------------|-------------------|--------------------------|
| Context files | 5 | 1,183 | 51,753 | 112 | 15 |
| Mode files | 6 | 985 | 40,203 | 105 | 6 (all in safe tool lists) |
| Agent files | 5 | 990 | 36,773 | 37 | 1 (says NOT to call it) |
| Behavior files | 2 | 78 | 2,355 | 20 | 1 (in description text) |
| Bundle root | 1 | 118 | 4,884 | 12 | 0 |
| **TOTAL** | **19** | **3,354** | **135,968** | **286** | **23** |

Approximate token budget: ~34,000 tokens across all 19 files (~4 chars/token).

---

## Context Files (5)

### 1. `context/crew-instructions.md`
- **Lines:** 345
- **Bytes:** 15,462 (~3,866 tokens)
- **Fidelity mentions:** 43
- **update_fidelity mentions:** 11 (most of any file)
- **Role:** Primary orchestration protocol. The CORE document that tells the LLM HOW to run the convergence loop.
- **Fidelity content:** Contains a `<CRITICAL>` section titled "MANDATORY: Update Fidelity After Every Delegation" (lines 133-196). Includes exact `update_fidelity()` call examples with lens scores for each agent type. Anti-rationalization table with 2 entries specifically about update_fidelity.
- **Injected via:** `bundle.md` (`@zerovector:context/crew-instructions.md`), `zerovector-crew.yaml` (context include), all 6 mode files (text reference "Read crew-instructions.md")
- **Classification:** PRIMARY FIDELITY INSTRUCTION SOURCE

### 2. `context/domain-tuning.md`
- **Lines:** 454
- **Bytes:** 17,566 (~4,392 tokens)
- **Fidelity mentions:** 57
- **update_fidelity mentions:** 0
- **Role:** Domain-specific scoring criteria for all 5 lenses across 5 domains (build, product, platform, research, content).
- **Fidelity content:** 100% fidelity-related. Every line describes what fidelity means per lens per domain. Does NOT contain update_fidelity instructions.
- **Injected via:** `bundle.md` (`@zerovector:context/domain-tuning.md`), `zerovector-crew.yaml` (context include), all 6 mode files (text reference "Read domain-tuning.md")
- **Classification:** FIDELITY SCORING CRITERIA

### 3. `context/fidelity-framework.md`
- **Lines:** 225
- **Bytes:** 11,941 (~2,985 tokens)
- **Fidelity mentions:** 7 (unexpectedly low — file title is "fidelity" but uses the word sparingly)
- **update_fidelity mentions:** 4
- **Role:** Universal lens model, scoring rubric, and update_fidelity calling convention.
- **Fidelity content:** Defines the 5 lenses, scoring ranges, JSON output format, evidence requirements. Section "Calling update_fidelity" (lines 172-203) with code example and rule "Always call update_fidelity after a fidelity assessment."
- **Injected via:** `fidelity.yaml` (context include), all 6 mode files (text reference "Read fidelity-framework.md")
- **NOT injected via:** bundle.md (no @include for this file)
- **Classification:** SECONDARY FIDELITY INSTRUCTION SOURCE

### 4. `context/using-zerovector.md`
- **Lines:** 55
- **Bytes:** 2,657 (~664 tokens)
- **Fidelity mentions:** 3
- **update_fidelity mentions:** 0
- **Role:** Pre-mode crew suggestion prompt. Forces LLM to suggest `/crew-*` mode before artifact creation.
- **Fidelity content:** Uses `<EXTREMELY-IMPORTANT>` wrapper. Mentions "fidelity convergence" as a reason to suggest crew mode, but no fidelity scoring or update instructions.
- **Injected via:** `fidelity.yaml` (context include), `zerovector-crew.yaml` (context include)
- **NOT injected via:** bundle.md (no @include)
- **Classification:** PRE-MODE GATE (not fidelity instruction)
- **Git note:** Added in commit `b4f52f4`

### 5. `context/zerovector-principles.md`
- **Lines:** 105
- **Bytes:** 4,127 (~1,032 tokens)
- **Fidelity mentions:** 2
- **update_fidelity mentions:** 0
- **Role:** Philosophy document. 7 principles of Zero-Vector Design.
- **Fidelity content:** Mentions "fidelity" only in crew role table (Critic: "Too lenient -> ships translation loss").
- **Injected via:** `bundle.md` (`@zerovector:context/zerovector-principles.md`)
- **Classification:** PHILOSOPHY (not fidelity instruction)

---

## Mode Files (6)

All 6 modes share identical structure: YAML frontmatter with tool policy, followed by markdown body.

### Common Structural Elements (all 6 modes)
- All list `update_fidelity` in `tools.safe` — tool POLICY (allowed), not an instruction to use it
- All use `default_action: block` — tools not listed are blocked
- All contain a `<CRITICAL>` section explaining orchestrator role and convergence loop
- All contain an anti-rationalization table with identical "Fidelity is 0.78" entry
- All reference 3 context docs: "Read crew-instructions.md", "Read fidelity-framework.md", "Read domain-tuning.md"
- All contain a convergence loop description and lens-to-agent routing table

### 6. `modes/crew.md` (General)
- **Lines:** 184 | **Bytes:** 6,511 | **Fidelity mentions:** 20 | **update_fidelity:** 1 (safe tools)
- **Unique:** Domain is "general". Includes transition options: debug, brainstorm, clear.
- **Safe tools:** 12 tools including `update_fidelity`, `LSP`, `python_check`

### 7. `modes/crew-build.md` (Build)
- **Lines:** 156 | **Bytes:** 6,090 | **Fidelity mentions:** 18 | **update_fidelity:** 1 (safe tools)
- **Unique:** Domain is "build", target 0.85. Build-specific lens tuning table. Recipe mode alternative.
- **Safe tools:** 12 tools including `update_fidelity`, `LSP`, `python_check`

### 8. `modes/crew-product.md` (Product)
- **Lines:** 150 | **Bytes:** 6,370 | **Fidelity mentions:** 16 | **update_fidelity:** 1 (safe tools)
- **Unique:** Domain is "product", target 0.80. No `LSP` or `python_check` in safe tools (10 tools).
- **Safe tools:** 10 tools — MISSING `LSP` and `python_check` vs. other code modes

### 9. `modes/crew-platform.md` (Platform)
- **Lines:** 167 | **Bytes:** 7,160 | **Fidelity mentions:** 17 | **update_fidelity:** 1 (safe tools)
- **Unique:** Domain is "platform", target 0.88 (highest). Platform safety rules section. Critic instruction adds "Survey ~/dev/ for related modules."
- **Safe tools:** 12 tools

### 10. `modes/crew-research.md` (Research)
- **Lines:** 164 | **Bytes:** 7,008 | **Fidelity mentions:** 17 | **update_fidelity:** 1 (safe tools)
- **Unique:** Domain is "research", target 0.80. Research integrity rules section.
- **Safe tools:** 10 tools — MISSING `LSP` and `python_check`

### 11. `modes/crew-content.md` (Content)
- **Lines:** 164 | **Bytes:** 7,064 | **Fidelity mentions:** 17 | **update_fidelity:** 1 (safe tools)
- **Unique:** Domain is "content", target 0.75 (lowest). Content quality rules section.
- **Safe tools:** 10 tools — MISSING `LSP` and `python_check`

---

## Agent Files (5)

### 12. `agents/critic.md`
- **Lines:** 304 | **Bytes:** 11,741 (~2,935 tokens) | **Fidelity mentions:** 15 | **update_fidelity:** 1
- **Role:** Primary fidelity assessor. Two-pass validation protocol. Produces structured JSON fidelity scores.
- **Fidelity content:** Full fidelity assessment protocol, scoring guidance, JSON output format, priority gap routing.
- **update_fidelity instruction:** **EXPLICITLY SAYS NOT TO CALL IT.** Line 263: "You do NOT need to call `update_fidelity` yourself — the orchestrator handles this after your delegation returns."
- **Classification:** FIDELITY ASSESSMENT PRODUCER (does NOT update state)

### 13. `agents/builder.md`
- **Lines:** 196 | **Bytes:** 7,381 (~1,845 tokens) | **Fidelity mentions:** 8 | **update_fidelity:** 0
- **Role:** Implements artifacts from specification. Serves Implementation lens.
- **Fidelity content:** "Fidelity Context" section (lines 55-72) explains it serves the Implementation lens. No fidelity scoring or update instructions.
- **Classification:** FIDELITY-AWARE (knows its lens) but NOT a fidelity updater

### 14. `agents/shipper.md`
- **Lines:** 185 | **Bytes:** 7,393 (~1,848 tokens) | **Fidelity mentions:** 6 | **update_fidelity:** 0
- **Role:** Packages and delivers validated artifacts. Serves Ship-Readiness lens.
- **Fidelity content:** "Fidelity Context" section (lines 56-73) explains it serves the Ship-Readiness lens.
- **Classification:** FIDELITY-AWARE but NOT a fidelity updater

### 15. `agents/architect.md`
- **Lines:** 148 | **Bytes:** 5,108 (~1,277 tokens) | **Fidelity mentions:** 4 | **update_fidelity:** 0
- **Role:** Translates intent into specification. Serves Specification lens.
- **Fidelity content:** "Fidelity Context" section (lines 45-55) explains it serves the Specification lens.
- **Classification:** FIDELITY-AWARE but NOT a fidelity updater

### 16. `agents/intent-analyst.md`
- **Lines:** 157 | **Bytes:** 5,150 (~1,288 tokens) | **Fidelity mentions:** 4 | **update_fidelity:** 0
- **Role:** Decodes user intent. Serves Intent Clarity lens.
- **Fidelity content:** "Fidelity Context" section (lines 46-53) explains it serves the Intent Clarity lens.
- **Classification:** FIDELITY-AWARE but NOT a fidelity updater

---

## Behavior Files (2)

### 17. `behaviors/fidelity.yaml`
- **Lines:** 40 | **Bytes:** 1,244
- **Fidelity mentions:** 13 | **update_fidelity:** 1 (in description text only)
- **Declares:** hooks-fidelity-reporter, tool-fidelity-state, critic agent
- **Context includes:** using-zerovector.md, fidelity-framework.md
- **Role:** Extractable fidelity layer. Can be included by any Amplifier bundle.
- **Classification:** COMPOSITION MANIFEST for fidelity subsystem

### 18. `behaviors/zerovector-crew.yaml`
- **Lines:** 38 | **Bytes:** 1,111
- **Fidelity mentions:** 7 | **update_fidelity:** 0
- **Declares:** hooks-mode, hooks-fidelity-reporter (DUPLICATE), tool-mode, tool-fidelity-state (DUPLICATE), 4 agents
- **Includes:** `zerovector:behaviors/fidelity` (transitive)
- **Context includes:** using-zerovector.md, crew-instructions.md, domain-tuning.md, modes-instructions.md
- **Role:** Full crew composition. The top-level behavior included by bundle.md.
- **Note:** Duplicates hook and tool declarations from fidelity.yaml because "transitive include doesn't merge hooks" (commit `6a0999e`).
- **Classification:** COMPOSITION MANIFEST for full crew

---

## Bundle Root (1)

### 19. `bundle.md`
- **Lines:** 118 | **Bytes:** 4,884
- **Fidelity mentions:** 12 | **update_fidelity:** 0
- **Declares:** name=zerovector, version=0.3.0
- **Includes:** amplifier-foundation bundle, zerovector-crew behavior
- **Inline @includes:** zerovector-principles.md, crew-instructions.md, domain-tuning.md
- **Inline content:** `<STANDING-ORDER>` for pre-mode crew suggestion, philosophy overview, crew roles table, convergence loop description, recipes table.
- **Does NOT @include:** fidelity-framework.md, using-zerovector.md (these come via behaviors)
- **Classification:** ROOT COMPOSITION + INLINE CONTEXT

---

## Module Files (2, not in injection chain but relevant)

### `modules/tool-fidelity-state/__init__.py`
- **Lines:** 198 | **Bytes:** 6,607
- **Role:** Implements the `update_fidelity` tool that the LLM calls. Maintains FidelityState dataclass. Mounts as a tool on the coordinator.

### `modules/hooks-fidelity-reporter/__init__.py`
- **Lines:** 383 | **Bytes:** 13,566
- **Role:** Renders ANSI fidelity dashboard to stdout after tool:post and prompt:complete events. Returns ephemeral context injection with routing advice to the LLM.
