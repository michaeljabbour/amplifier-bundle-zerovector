---
name: domain-tuning
description: "Domain-specific fidelity criteria for all 5 ZeroVector domains (build, product, platform, research, content). Load when a /crew* mode activates to calibrate assessment per domain."
version: 0.3.0
---

# Domain Tuning — Fidelity Criteria per Lens

Domain-specific fidelity criteria for the Zero-Vector crew. When a domain mode
is active, use these criteria to calibrate fidelity assessment and guide each
agent toward domain-appropriate standards.

For the universal lens model and scoring rubric, load the `fidelity-framework` skill.

---

## How to Use This Document

When assessing fidelity or delegating to a crew agent, consult the relevant
domain section below. Each domain defines what "high fidelity" looks like for
all five lenses, with specific indicators and evidence to look for.

---

## Domain: `build` — Code Artifacts (target: 0.85)

| Lens | High Fidelity (0.90+) | Low Fidelity (<0.50) | What to Assess |
|------|-----------------------|----------------------|----------------|
| **Intent Clarity** | Functional reqs, tech stack, test strategy, anti-goals, success criteria all explicit | Vague description, no testable criteria | Functional reqs explicit, constraints stated, success tests defined, anti-goals stated, failure modes identified |
| **Specification** | Every intent req has a spec task with acceptance test command; interfaces typed | No file paths, no signatures, no acceptance criteria | Module/file structure, public interfaces with types, TDD task breakdown, integration map, acceptance criteria |
| **Implementation** | All spec tasks done, all acceptance tests pass, no scope creep, clean commits | Major reqs unimplemented, tests failing/absent | Test-first per task, full suite passes after each task, atomic commits, type hints + docstrings, no debug code |
| **Quality** | Comprehensive tests pass, lint clean, types check, proper error handling | Tests failing, no type hints, no error handling | Run full test suite (N pass/fail), lint + type check, error handling, readability, interface contracts match spec |
| **Ship-Readiness** | Clean commits, docs complete, usage examples, deployment-ready | Messy history, no docs, no examples | Squash wip commits, conventional commit messages, README/CHANGELOG updated, usage docs, no delivery blockers |

## Domain: `product` — Product Artifacts (target: 0.80)

| Lens | High Fidelity (0.90+) | Low Fidelity (<0.50) | What to Assess |
|------|-----------------------|----------------------|----------------|
| **Intent Clarity** | User job, business outcome, target reader, decision to enable, anti-goals explicit | Vague direction, no user job identified | Jobs-to-be-done, business outcome, customer constraints, decision purpose, anti-goals |
| **Specification** | Every section has purpose, decisions explicit, acceptance criteria concrete | No structure, no decision framework | Artifact type, structure with section purposes, key decisions/trade-offs, measurable outcomes |
| **Implementation** | All sections present, grounded in intent, decisions explicit with rationale | Missing sections, decisions unjustified | All specified sections present, grounded in user job, decision points explicit, no padding |
| **Quality** | Internally consistent, measurable criteria, stakeholder-actionable | Contradictory sections, vague criteria | Internal consistency, measurability, stakeholder clarity, anti-goals respected, completeness |
| **Ship-Readiness** | Filed correctly, headers complete, stakeholder summary present | No location, no header, no summary | Correct path, document header, stakeholder summary, scope boundaries stated |

## Domain: `platform` — Platform/Infrastructure Artifacts (target: 0.88)

| Lens | High Fidelity (0.90+) | Low Fidelity (<0.50) | What to Assess |
|------|-----------------------|----------------------|----------------|
| **Intent Clarity** | Contract, consumers, change type, stability reqs, risk flags all explicit | No consumer analysis, no breaking change awareness | System contract, consumers named, change type, stability/versioning reqs, anti-goals, risk flags |
| **Specification** | Complete interface def with types, protocols, error contracts, migration paths | No signatures, no protocol compliance plan | Interface definition, protocol compliance, breaking change analysis, migration path, error contract |
| **Implementation** | Exact interface match, defensive error handling, fully typed/documented API | Interface deviates from spec, no error handling | Contract-first implementation, defensive code, typed + docstrings, linters after every task, conventional commits |
| **Quality** | Interface exact, protocol complete, error handling comprehensive, consumer-safe | Interface mismatch, missing protocol methods | Interface contract, protocol compliance, no unspec'd breaking changes, edge cases, consumer impact, type safety |
| **Ship-Readiness** | Changelog updated, README current, migration guide if needed | No changelog, no docs, consumers uninformed | Conventional commit, CHANGELOG.md, module README, MIGRATION.md if breaking, delivery report |

## Domain: `research` — Knowledge Artifacts (target: 0.80)

| Lens | High Fidelity (0.90+) | Low Fidelity (<0.50) | What to Assess |
|------|-----------------------|----------------------|----------------|
| **Intent Clarity** | Research question precise, decision it informs explicit, evidence standard stated | Vague topic, no specific question | Exact research question, decision it informs, evidence standard, time/depth constraint, confidence threshold |
| **Specification** | Sub-questions defined, source strategy explicit, synthesis structure clear | No breakdown, no source strategy | Sub-questions, source strategy, synthesis structure, output format, confidence framework |
| **Implementation** | All sub-questions addressed with cited sources, evidence levels clear, gaps noted | Sub-questions unanswered, sources uncited | Each sub-question investigated, sources cited specifically, evidence levels separated, structure followed |
| **Quality** | Claims grounded in cited evidence, logic sound, uncertainty acknowledged | Claims without evidence, logical gaps | Evidence quality, logical integrity, uncertainty honesty, actionability, scope |
| **Ship-Readiness** | Filed correctly, header complete, executive summary, unanswered questions noted | No location, no summary, no confidence level | Correct path, document header, executive summary (3 sentences max), unanswered questions noted |

## Domain: `content` — Written Artifacts (target: 0.75)

| Lens | High Fidelity (0.90+) | Low Fidelity (<0.50) | What to Assess |
|------|-----------------------|----------------------|----------------|
| **Intent Clarity** | Audience, purpose, tone, scope boundaries all explicit | No audience, no purpose stated | Primary audience, purpose (reader can DO what?), reading context, tone, length constraint, anti-goals |
| **Specification** | Detailed outline with section purposes, hook defined, arc planned | No outline, no section purposes | Outline with section titles + purposes, opening hook, narrative arc, voice/tone notes, acceptance criteria |
| **Implementation** | All sections present, audience calibrated, no padding, spec followed | Missing sections, wrong audience level | Structure followed, audience depth calibrated, active voice, every section fulfills its purpose, no extras |
| **Quality** | Purpose achieved, audience fit, clear prose, good structure, working examples | Purpose not achieved, unclear prose | Purpose achieved?, audience calibration, clarity, structure, opening hook, code examples correct, prose quality |
| **Ship-Readiness** | Proofread, correctly filed, examples verified, delivery summary | Typos, broken links, unfiled | Final proofread, correct location, code examples verified, delivery summary |