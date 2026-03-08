# Domain Tuning — Zero-Vector Crew Calibration

When a domain-specific mode is active, prime each crew agent with the relevant tuning below.
Pass domain context in every delegation so agents calibrate their focus and quality bar.

---

## How to Use This Document

When delegating, append the relevant domain tuning to each agent's instruction:

```
"Domain context for this pipeline run:
[paste the tuning block for the active domain]"
```

Or reference it by domain name and instruct agents to consult `domain-tuning.md`.

---

## Domain: `build` — Code Artifacts

Features, apps, tools, scripts, modules, configurations.
The artifact is working software.

### Intent Analyst — build focus
- Extract: functional requirements (what must the code DO), tech stack and constraints, success tests
- Ask: how will a developer know this works? What breaks if we get it wrong?
- Identify: existing patterns to follow, dependencies, test infrastructure available
- Anti-goals: be explicit about what is NOT being built (no scope creep for the Builder)

### Architect — build focus
- Produce: module/file structure with exact paths, public interfaces with type signatures
- TDD task breakdown: each task starts with "write failing test for X, then implement"
- Integration map: what does this connect to? Which contracts must be preserved?
- Acceptance criteria format: `[check: command to run] → [expected output]`

### Builder — build focus
- Test-first: for each task, write the failing test FIRST, then minimal implementation to pass
- Run full test suite after each task — report pass/fail counts, not "looks good"
- Commit atomically after each passing task
- Type hints on all public functions; docstrings on all public interfaces
- No debug code, print statements, or commented-out experiments in final commits

### Critic — build focus
**Pass 1 — Spec/Intent Compliance:**
- Every task's acceptance test: run it, report actual output
- Interface contracts match specification exactly (types, function signatures, return values)
- Scope: nothing missing from spec, nothing added beyond spec

**Pass 2 — Quality/Robustness:**
- Full test suite: run and report (N passed / N failed)
- Lint + type check: run and report actual output
- Error handling: edge cases covered (None/null, empty inputs, unexpected types)
- Code is readable: functions have clear names, logic is not opaque

### Shipper — build focus
- Clean commit history: squash "wip" commits, preserve atomic feature commits
- Commit message: `feat(scope): what was added` / `fix(scope): what was fixed`
- Update README or CHANGELOG if this adds a public interface or breaking change
- "How to use": show the import path, function signature, and a minimal usage example

---

## Domain: `product` — Product Artifacts

UX flows, PRDs, feature specs, validation frameworks, product strategy documents.
The artifact is a decision-enabling document.

### Intent Analyst — product focus
- Extract: jobs-to-be-done (what is the user hiring this for?), business outcome, customer constraints
- Ask: what decision does this artifact enable? Who reads it and what do they decide next?
- Identify: existing product context, prior decisions, stakeholders who need to align
- Anti-goals: what customer problem are we NOT solving here?

### Architect — product focus
- Produce: artifact type (PRD section / user flow / feature spec / research synthesis)
- Structure: sections with purpose statement for each
- Key decisions and trade-offs to address explicitly
- Acceptance criteria: what makes this spec "done" and actionable for a reader?
- Measurable outcomes: how will we know this product decision was right?

### Builder — product focus
- Write clearly and concisely — this is a human-readable artifact
- Ground every section in the user job from the Intent Document
- Include all sections specified — no omissions, no additions
- Decision points must be explicit: "we chose X over Y because Z"
- No padding: every sentence must carry information

### Critic — product focus
**Pass 1 — Spec/Intent Compliance:**
- Does it solve the user job in the Intent Document?
- Is the artifact type correct (PRD / flow / spec / etc.)?
- Are all specified sections present and purposeful?

**Pass 2 — Quality/Robustness:**
- Internal consistency: no contradictions between sections
- Measurability: acceptance criteria are concrete, not vague
- Stakeholder clarity: would a reader know what to build / decide?
- Anti-goals respected: nothing outside the stated scope

### Shipper — product focus
- Save to correct path (docs/, specs/, shared drive path if applicable)
- Add document header: artifact name, date, owner, what decision it enables
- Stakeholder summary: one paragraph — what this is, what decision it unblocks
- State explicitly what this artifact does NOT cover

---

## Domain: `platform` — Platform/Infrastructure Artifacts

Amplifier modules, bundle configurations, APIs, infrastructure configs, CLI tools, architectural changes.
The artifact is a system that other systems depend on.

### Intent Analyst — platform focus
- Extract: what system contract is being created or changed? Who are the consumers?
- Ask: is this additive (new capability) or mutating (changing existing behavior)?
- Identify: stability requirements, versioning constraints, backward-compat obligations
- Anti-goals: what architectural decisions are we explicitly NOT making here?
- Risk flags: what breaks for consumers if we get this wrong?

### Architect — platform focus
- Interface definition: exact function signatures, types, protocols — leave no room for ambiguity
- Protocol compliance: what kernel/module contracts must be implemented?
- Breaking change analysis: which consumers are affected and how?
- Migration path: if existing behavior changes, how do consumers migrate?
- Error contract: what errors, when, with what information, with what recovery?
- Task acceptance criteria: interface acceptance test for each task (not just "file exists")

### Builder — platform focus
- Contract-first: implement exactly to the spec'd interface — not your preferred style
- Defensive code: assume consumer misuse; handle gracefully with informative errors
- All public interfaces: typed, docstrings, examples in docstrings
- Run linters + type checkers after EVERY task — not just at the end
- Conventional commits: `feat(module-name): add X` / `fix(module-name): correct Y`

### Critic — platform focus
**Pass 1 — Spec/Intent Compliance:**
- Interface contract: does the implementation match spec signatures exactly?
- Protocol compliance: all required protocol methods implemented?
- No breaking changes beyond those explicitly spec'd

**Pass 2 — Quality/Robustness:**
- Error handling: every error condition handled with appropriate information
- Edge cases: empty inputs, None/null, concurrent access, large payloads
- Consumer impact: would existing consumers break with this change?
- Type safety: all public interfaces typed and checked
- Documentation: all public interfaces documented with examples

### Shipper — platform focus
- Conventional commit: `feat(scope): what was added` (or fix/chore/docs)
- CHANGELOG.md: update (or create) with version bump + what changed + who is affected
- Module README: update if public interface changed
- If breaking change: add or update MIGRATION.md with before/after usage examples
- Delivery report must state: what changed, what it's compatible with, how to use it

---

## Domain: `research` — Knowledge Artifacts

Literature reviews, technical investigations, competitive analyses, research synthesis, academic writing.
The artifact is knowledge made actionable.

### Intent Analyst — research focus
- Extract: the exact research question (what are we trying to find out?), the decision it informs
- Ask: what evidence standard is required? (primary sources / expert opinion / quantitative / qualitative)
- Identify: time/depth constraint (quick scan vs. thorough review), confidence threshold
- Anti-goals: what questions are we NOT answering here?

### Architect — research focus
- Research question breakdown: what sub-questions must be answered?
- Source strategy: where to look, in what order, what to prioritize
- Synthesis structure: how will findings be organized? (by theme / chronology / strength of evidence)
- Output format: what does the deliverable look like?
- Confidence framework: how will we communicate certainty vs. uncertainty?

### Builder — research focus
- Investigate each sub-question using the source strategy
- Cite sources specifically (URL / author / date / title) — not vaguely
- Separate: established fact / strong evidence / weak evidence / speculation
- Follow the synthesis structure from the spec exactly
- Note explicitly where evidence is thin, contradictory, or absent
- Do not pad with background the spec doesn't require

### Critic — research focus
**Pass 1 — Spec/Intent Compliance:**
- Does it answer the original research question?
- Are all sub-questions addressed?
- Is the synthesis structure followed?

**Pass 2 — Quality/Robustness:**
- Evidence quality: claims supported by cited sources (not just asserted)
- Logical integrity: no gaps, unstated assumptions, non-sequiturs
- Uncertainty honest: thin or contradictory evidence labeled as such
- Actionability: does it enable the decision it was meant to inform?
- Scope: no out-of-scope content included

### Shipper — research focus
- Save to correct path (docs/research/, research/, etc.)
- Add document header: research question, date, confidence level (high/medium/low)
- Executive summary: question + key finding + recommended action (3 sentences max)
- Note explicitly what questions remain unanswered
- Delivery report: what was found, what decision it enables, confidence level

---

## Domain: `content` — Written Artifacts

Technical documentation, blog posts, essays, curriculum modules, README files, release notes, API references.
The artifact is words that work.

### Intent Analyst — content focus
- Extract: primary audience (who reads this, what do they already know?), purpose, reading context
- Ask: what should the reader be able to DO after reading this?
- Identify: tone (technical / conversational / instructional / persuasive), length constraint
- Anti-goals: what are we explicitly NOT covering here?

### Architect — content focus
- Outline with section titles and one-sentence purpose for each section
- Opening hook: what grabs the audience on line 1?
- Narrative arc (if applicable): how does this piece flow?
- Voice and tone notes (drawn from the intent)
- Acceptance criteria: what makes each section "done"?
- Scope: what to explicitly NOT include

### Builder — content focus
- Follow the structure spec exactly — sections, purpose, arc
- Write for the specified audience — calibrate technical depth accordingly
- Active voice. Short sentences. No padding.
- Every section must fulfill its stated purpose from the spec
- Include examples where the spec calls for them
- Do not add sections not in the spec; do not omit sections that are

### Critic — content focus
**Pass 1 — Spec/Intent Compliance:**
- Does it achieve its stated purpose? (Can the reader DO what was intended?)
- Is the structure present and followed?
- Is scope respected? (No out-of-scope material)

**Pass 2 — Quality/Robustness:**
- Audience calibration: pitched at the right level?
- Clarity: no unclear, vague, or unexplained passages
- Structure: can a reader find what they need quickly?
- Opening: does it hook the intended audience?
- For technical docs: are all code examples correct and runnable?

### Shipper — content focus
- Final proofread: typos, inconsistent terminology, broken links
- Save to correct location (docs/, README, posts/, etc.)
- For documentation: verify all code examples actually run
- Delivery summary: what was written, where it lives, who it's for
- Delivery report must state: what action the content enables for its reader
