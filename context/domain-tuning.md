# Domain Tuning — Fidelity Criteria per Lens

Domain-specific fidelity criteria for the Zero-Vector crew. When a domain mode
is active, use these criteria to calibrate fidelity assessment and guide each
agent toward domain-appropriate standards.

For the universal lens model and scoring rubric, see `fidelity-framework.md`.
This document provides the **domain-specific interpretation** of what each
fidelity lens score means for each work domain.

---

## How to Use This Document

When assessing fidelity or delegating to a crew agent, consult the relevant
domain section below. Each domain defines what "high fidelity" looks like for
all five lenses, with specific indicators and evidence to look for.

The critic uses these criteria during multi-lens assessment. Agents routed by
the convergence loop use them to understand what fidelity standard they are
working toward.

---

## Domain: `build` — Code Artifacts

Features, apps, tools, scripts, modules, configurations.
The artifact is working software.

**Convergence target: 0.85**

### Intent Clarity

What to assess:
- Functional requirements are explicit (what must the code DO)
- Tech stack and constraints are stated
- Success tests are defined (how will a developer know this works?)
- Anti-goals are explicit (what is NOT being built — no scope creep)
- Failure modes are identified (what breaks if we get it wrong?)

High fidelity (0.90+): Intent specifies functional requirements, tech stack,
test strategy, anti-goals, and success criteria. Two builders would produce
equivalent implementations from it.

Low fidelity (below 0.50): Vague description with no testable criteria.
Building would require guessing at requirements.

### Specification

What to assess:
- Module/file structure with exact paths
- Public interfaces with type signatures
- TDD task breakdown (each task starts with "write failing test for X")
- Integration map (what does this connect to, which contracts are preserved?)
- Acceptance criteria format: `[check: command to run] → [expected output]`

High fidelity (0.90+): Every intent requirement has a spec task with an
acceptance test command. Interfaces are typed and unambiguous.

Low fidelity (below 0.50): No file paths, no signatures, no acceptance criteria.
Builder would have to invent the architecture.

### Implementation

What to assess:
- Test-first: for each task, failing test written FIRST, then minimal implementation
- Full test suite passes after each task (report pass/fail counts, not "looks good")
- Commits are atomic (one passing task per commit)
- Type hints on all public functions; docstrings on all public interfaces
- No debug code, print statements, or commented-out experiments

High fidelity (0.90+): All spec tasks implemented. All acceptance tests pass.
No scope creep. Clean atomic commits.

Low fidelity (below 0.50): Major spec requirements unimplemented. Tests failing
or absent. Significant deviation from specified interfaces.

### Quality

What to assess:
- Full test suite: run and report (N passed / N failed)
- Lint + type check: run and report actual output
- Error handling: edge cases covered (None/null, empty inputs, unexpected types)
- Code readability: functions have clear names, logic is not opaque
- Interface contracts match specification exactly (types, signatures, return values)

High fidelity (0.90+): Comprehensive tests pass, lint clean, types check,
proper error handling, readable code, typed interfaces.

Low fidelity (below 0.50): Tests failing, no type hints, no error handling,
unreadable or fragile code.

### Ship-Readiness

What to assess:
- Clean commit history: squash "wip" commits, preserve atomic feature commits
- Commit messages: `feat(scope): what was added` / `fix(scope): what was fixed`
- README or CHANGELOG updated if public interface or breaking change added
- Usage documentation: import path, function signature, minimal usage example
- No delivery blockers (broken CI, unresolved merge conflicts)

High fidelity (0.90+): Clean commits, documentation complete, usage examples
present, deployment-ready.

Low fidelity (below 0.50): Messy commit history, no documentation, no usage
examples, unresolved delivery blockers.

---

## Domain: `product` — Product Artifacts

UX flows, PRDs, feature specs, validation frameworks, product strategy documents.
The artifact is a decision-enabling document.

**Convergence target: 0.80**

### Intent Clarity

What to assess:
- Jobs-to-be-done identified (what is the user hiring this for?)
- Business outcome stated
- Customer constraints acknowledged
- Decision purpose explicit (what decision does this artifact enable? Who reads it?)
- Anti-goals stated (what customer problem are we NOT solving here?)

High fidelity (0.90+): Intent specifies user job, business outcome, target
reader, decision to enable, and anti-goals. Stakeholders could validate it.

Low fidelity (below 0.50): Vague product direction with no identified user
job or decision to enable.

### Specification

What to assess:
- Artifact type identified (PRD section / user flow / feature spec / research synthesis)
- Structure with sections and purpose statement for each
- Key decisions and trade-offs to address explicitly
- Acceptance criteria: what makes this spec "done" and actionable for a reader?
- Measurable outcomes: how will we know this product decision was right?

High fidelity (0.90+): Every section has a purpose, decisions are explicit,
acceptance criteria are concrete and measurable.

Low fidelity (below 0.50): No structure, no decision framework, no way to
tell when the document is "done."

### Implementation

What to assess:
- All specified sections present — no omissions, no additions
- Each section grounded in the user job from the intent document
- Decision points are explicit: "we chose X over Y because Z"
- Writing is clear and concise — every sentence carries information
- No padding or filler content

High fidelity (0.90+): All sections present, grounded in intent, decisions
explicit with rationale, no padding.

Low fidelity (below 0.50): Missing sections, decisions not justified,
content disconnected from stated user job.

### Quality

What to assess:
- Internal consistency: no contradictions between sections
- Measurability: acceptance criteria are concrete, not vague
- Stakeholder clarity: would a reader know what to build or decide?
- Anti-goals respected: nothing outside the stated scope
- Completeness: artifact solves the user job identified in intent

High fidelity (0.90+): Internally consistent, measurable criteria,
stakeholder-actionable, scope respected.

Low fidelity (below 0.50): Contradictory sections, vague criteria,
reader cannot determine next action.

### Ship-Readiness

What to assess:
- Saved to correct path (docs/, specs/, shared drive path if applicable)
- Document header: artifact name, date, owner, what decision it enables
- Stakeholder summary: one paragraph — what this is, what decision it unblocks
- Explicit statement of what the artifact does NOT cover
- Delivery report states what decision this enables for its audience

High fidelity (0.90+): Properly filed, headers complete, stakeholder
summary present, scope boundaries stated.

Low fidelity (below 0.50): No location, no header, no summary, reader
cannot tell what decision this enables.

---

## Domain: `platform` — Platform/Infrastructure Artifacts

Amplifier modules, bundle configurations, APIs, infrastructure configs, CLI tools,
architectural changes. The artifact is a system that other systems depend on.

**Convergence target: 0.88**

### Intent Clarity

What to assess:
- System contract being created or changed is identified
- Consumers are named (who depends on this?)
- Change type: additive (new capability) vs mutating (changing existing behavior)
- Stability requirements, versioning constraints, backward-compat obligations
- Anti-goals: what architectural decisions are we explicitly NOT making?
- Risk flags: what breaks for consumers if we get this wrong?

High fidelity (0.90+): Contract, consumers, change type, stability requirements,
and risk flags all explicit. Two teams would build the same interface from it.

Low fidelity (below 0.50): No consumer analysis, no breaking change awareness,
no stability requirements stated.

### Specification

What to assess:
- Interface definition: exact function signatures, types, protocols
- Protocol compliance: what kernel/module contracts must be implemented?
- Breaking change analysis: which consumers are affected and how?
- Migration path: if existing behavior changes, how do consumers migrate?
- Error contract: what errors, when, with what information, with what recovery?
- Task acceptance criteria: interface acceptance test for each task

High fidelity (0.90+): Complete interface definition with types, protocols,
error contracts, migration paths, and per-task acceptance tests.

Low fidelity (below 0.50): No signatures, no protocol compliance plan,
no consumer impact analysis.

### Implementation

What to assess:
- Contract-first: implemented exactly to the spec'd interface
- Defensive code: assumes consumer misuse; handles gracefully with informative errors
- All public interfaces: typed, docstrings, examples in docstrings
- Linters + type checkers run after EVERY task (not just at the end)
- Conventional commits: `feat(module-name): add X` / `fix(module-name): correct Y`

High fidelity (0.90+): Exact interface match, defensive error handling,
fully typed and documented public API, clean commits.

Low fidelity (below 0.50): Interface deviates from spec, no error handling,
missing types or documentation.

### Quality

What to assess:
- Interface contract: does implementation match spec signatures exactly?
- Protocol compliance: all required protocol methods implemented?
- No breaking changes beyond those explicitly spec'd
- Error handling: every error condition handled with appropriate information
- Edge cases: empty inputs, None/null, concurrent access, large payloads
- Consumer impact: would existing consumers break with this change?
- Type safety: all public interfaces typed and checked
- Documentation: all public interfaces documented with examples

High fidelity (0.90+): Interface exact, protocol complete, error handling
comprehensive, all edge cases covered, consumer-safe.

Low fidelity (below 0.50): Interface mismatch, missing protocol methods,
unhandled errors, consumer-breaking changes.

### Ship-Readiness

What to assess:
- Conventional commit: `feat(scope): what was added` (or fix/chore/docs)
- CHANGELOG.md: updated with version bump + what changed + who is affected
- Module README: updated if public interface changed
- If breaking change: MIGRATION.md with before/after usage examples
- Delivery report: what changed, what it's compatible with, how to use it

High fidelity (0.90+): Changelog updated, README current, migration guide
if needed, delivery report complete.

Low fidelity (below 0.50): No changelog, no documentation updates,
consumers have no way to learn about the change.

---

## Domain: `research` — Knowledge Artifacts

Literature reviews, technical investigations, competitive analyses, research
synthesis, academic writing. The artifact is knowledge made actionable.

**Convergence target: 0.80**

### Intent Clarity

What to assess:
- The exact research question (what are we trying to find out?)
- The decision this research informs
- Evidence standard required (primary sources / expert opinion / quantitative / qualitative)
- Time/depth constraint (quick scan vs. thorough review)
- Confidence threshold expected
- Anti-goals: what questions are we NOT answering?

High fidelity (0.90+): Research question precise, decision it informs explicit,
evidence standard and depth constraint stated.

Low fidelity (below 0.50): Vague topic area with no specific question or
decision to inform.

### Specification

What to assess:
- Research question broken into sub-questions
- Source strategy: where to look, in what order, what to prioritize
- Synthesis structure: how findings will be organized (theme / chronology / evidence strength)
- Output format: what the deliverable looks like
- Confidence framework: how certainty vs. uncertainty will be communicated

High fidelity (0.90+): Sub-questions defined, source strategy explicit,
synthesis structure clear, output format specified.

Low fidelity (below 0.50): No breakdown, no source strategy, no structure
for organizing findings.

### Implementation

What to assess:
- Each sub-question investigated using the source strategy
- Sources cited specifically (URL / author / date / title) — not vaguely
- Evidence levels separated: established fact / strong evidence / weak evidence / speculation
- Synthesis structure from spec followed exactly
- Gaps noted explicitly where evidence is thin, contradictory, or absent
- No padding with background the spec doesn't require

High fidelity (0.90+): All sub-questions addressed with cited sources,
evidence levels clear, structure followed, gaps noted.

Low fidelity (below 0.50): Sub-questions unanswered, sources uncited,
no evidence differentiation.

### Quality

What to assess:
- Evidence quality: claims supported by cited sources (not just asserted)
- Logical integrity: no gaps, unstated assumptions, non-sequiturs
- Uncertainty honest: thin or contradictory evidence labeled as such
- Actionability: does it enable the decision it was meant to inform?
- Scope: no out-of-scope content included

High fidelity (0.90+): Claims grounded in cited evidence, logic sound,
uncertainty acknowledged, research actionable.

Low fidelity (below 0.50): Claims without evidence, logical gaps,
uncertainty hidden, research not actionable.

### Ship-Readiness

What to assess:
- Saved to correct path (docs/research/, research/, etc.)
- Document header: research question, date, confidence level (high/medium/low)
- Executive summary: question + key finding + recommended action (3 sentences max)
- Explicit note of what questions remain unanswered
- Delivery report: what was found, what decision it enables, confidence level

High fidelity (0.90+): Filed correctly, header complete, executive summary
present, unanswered questions noted.

Low fidelity (below 0.50): No location, no summary, no confidence
indication, reader cannot assess reliability.

---

## Domain: `content` — Written Artifacts

Technical documentation, blog posts, essays, curriculum modules, README files,
release notes, API references. The artifact is words that work.

**Convergence target: 0.75**

### Intent Clarity

What to assess:
- Primary audience identified (who reads this, what do they already know?)
- Purpose stated (what should the reader be able to DO after reading?)
- Reading context acknowledged
- Tone specified (technical / conversational / instructional / persuasive)
- Length constraint stated
- Anti-goals: what are we explicitly NOT covering?

High fidelity (0.90+): Audience, purpose, tone, and scope boundaries all
explicit. Writer and reviewer would agree on what "done" looks like.

Low fidelity (below 0.50): No audience identified, no purpose stated,
writing would be guesswork.

### Specification

What to assess:
- Outline with section titles and one-sentence purpose for each section
- Opening hook: what grabs the audience on line 1?
- Narrative arc (if applicable): how does this piece flow?
- Voice and tone notes drawn from the intent
- Acceptance criteria: what makes each section "done"?
- Scope: what to explicitly NOT include

High fidelity (0.90+): Detailed outline with section purposes, hook defined,
arc planned, per-section acceptance criteria.

Low fidelity (below 0.50): No outline, no section purposes, no criteria
for "done."

### Implementation

What to assess:
- Structure spec followed exactly — sections, purpose, arc
- Written for the specified audience — technical depth calibrated
- Active voice, short sentences, no padding
- Every section fulfills its stated purpose from the spec
- Examples included where the spec calls for them
- No sections added beyond spec; no sections omitted from spec

High fidelity (0.90+): All sections present and purposeful, audience
calibrated, no padding, spec followed exactly.

Low fidelity (below 0.50): Missing sections, wrong audience level,
padded or off-topic content.

### Quality

What to assess:
- Purpose achieved: can the reader DO what was intended?
- Audience calibration: pitched at the right level?
- Clarity: no unclear, vague, or unexplained passages
- Structure: can a reader find what they need quickly?
- Opening: does it hook the intended audience?
- For technical docs: are all code examples correct and runnable?
- Prose quality: active voice, concise, no jargon without explanation

High fidelity (0.90+): Purpose achieved, audience fit, clear prose,
good structure, working examples where applicable.

Low fidelity (below 0.50): Purpose not achieved, wrong audience level,
unclear prose, broken examples.

### Ship-Readiness

What to assess:
- Final proofread: typos, inconsistent terminology, broken links
- Saved to correct location (docs/, README, posts/, etc.)
- For documentation: all code examples verified to actually run
- Delivery summary: what was written, where it lives, who it's for
- Delivery report: what action the content enables for its reader

High fidelity (0.90+): Proofread, correctly filed, examples verified,
delivery summary present.

Low fidelity (below 0.50): Typos, broken links, unfiled, no delivery
summary, reader cannot find or trust the content.
