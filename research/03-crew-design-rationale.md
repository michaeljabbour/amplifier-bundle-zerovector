# 03 — Crew Design Rationale

> Why six crews, why five agents, and how the ~/dev workspace survey shaped both decisions

---

## 1. The Workspace Survey

Before designing the crew structure, we surveyed the entire `~/dev` directory (~130 git repos) to understand the operator's actual work domains. This was not a theoretical exercise — the crews needed to match real, recurring work patterns.

### Repository Classification

| Domain | Count | Key Repos | Evidence |
|--------|-------|-----------|----------|
| **Amplifier Core/Platform** | 5 | `amplifier-core`, `amplifier-foundation`, `amplifier`, `amplifier-dev` (monorepo), `amplifier-old` | Kernel development, module protocols, foundation bundle |
| **Modules (Userspace)** | 21 | `amplifier-module-provider-{anthropic,openai,azure,ollama,huggingface,xai}`, `amplifier-module-tool-{bash,filesystem,web,search,mcp,memory,deepresearch}`, `amplifier-module-hooks-{approval,logging,redaction,streaming-ui,ui-bridge,event-broadcast,insight-blocks,memory-capture}`, `amplifier-module-loop-{basic,streaming}`, `amplifier-module-context-{simple,persistent,memory}`, `amplifier-module-stories` | Each is a pip-installable module following kernel protocol contracts |
| **Bundles** | 7 | `amplifier-bundle-{pulse,superpowers,idd,centaur,errorcache,authorship-calibration,letsgo}` | `bundle.md` frontmatter in each; various methodologies and capabilities |
| **Apps / Products** | 8+ | Various web apps, CLI tools, product prototypes | Full-stack applications with deployment concerns |
| **Research / Academic** | 5+ | Papers, experiments, analysis repos | Academic writing, data analysis, experimental methodology |
| **Content / Writing** | 3+ | Documentation, curriculum, blog/publication repos | Long-form writing, technical documentation |

### Work Domain Identification

From this survey, five distinct work domains emerged — plus a "general" catch-all:

| Domain | What It Covers | Frequency | Complexity |
|--------|---------------|-----------|------------|
| **Build** | Features, apps, tools, scripts, modules | Daily | High (code + tests + integration) |
| **Product** | UX flows, specs, validation, strategy | Weekly | Medium-High (judgment + research) |
| **Platform** | Infrastructure, modules, APIs, architecture | Weekly | High (contracts + migration + stability) |
| **Research** | Investigation, analysis, synthesis, papers | Bi-weekly | Medium (evidence + structure) |
| **Content** | Documentation, writing, curriculum, posts | Weekly | Medium (audience + clarity) |
| **General** | Anything that doesn't fit the above | As needed | Varies |

---

## 2. Why Six Crews (Not Fewer, Not More)

### The Decision

Six crews: `/crew`, `/crew-build`, `/crew-product`, `/crew-platform`, `/crew-research`, `/crew-content`.

### Alternatives Considered

| Option | Crew Count | Rejected Because |
|--------|-----------|------------------|
| Single crew | 1 | No domain tuning; Intent Analyst and Critic can't specialize. "Build a module" and "write a paper" need fundamentally different quality bars. |
| Two crews (code / non-code) | 2 | Too coarse. Platform work (contracts, migration) differs from feature work (TDD, user-facing). Research (evidence standards) differs from content (audience-fit). |
| Three crews (build / think / write) | 3 | Better, but conflates platform (stability-focused) with build (feature-focused), and research (evidence-focused) with product (user-focused). |
| **Six crews** | **6** | **Matches the five real work domains + general fallback. Each domain has distinct quality criteria.** |
| Ten+ crews | 10+ | Over-fragmented. The marginal value of `/crew-devops` vs `/crew-platform` or `/crew-blog` vs `/crew-content` doesn't justify the cognitive load. |

### The Deciding Factor: Quality Criteria Divergence

The real reason for six crews is that **each domain has a different definition of "done"**:

| Domain | Intent Analyst Focuses On | Architect Focuses On | Critic Validates |
|--------|--------------------------|---------------------|-----------------|
| Build | Functional requirements + test criteria | Module structure + TDD tasks | Spec compliance + test results |
| Product | Jobs-to-be-done + business outcomes | Flow structure + decision points | User-centricity + consistency |
| Platform | Contracts + consumers + stability | Interfaces + migration paths | Breaking changes + edge cases |
| Research | Research question + evidence standard | Source strategy + synthesis framework | Evidence quality + actionability |
| Content | Audience + purpose + reading context | Structure + narrative arc | Clarity + audience-fit |

If the Critic doesn't know the domain, it can't apply the right quality bar. A Critic checking a research paper for "test coverage" is useless. A Critic checking a CLI tool for "narrative arc" is useless. Domain-specific tuning makes the pipeline meaningful.

---

## 3. Why Five Agents (Not Fewer, Not More)

### The Five Roles

| # | Role | Agent | Pipeline Position |
|---|------|-------|-------------------|
| 1 | Intent Analyst | `zerovector:intent-analyst` | Entry — decodes raw intent |
| 2 | Architect | `zerovector:architect` | Spec — translates intent into structure |
| 3 | Builder | `zerovector:builder` | Build — implements from spec |
| 4 | Critic | `zerovector:critic` | Validate — checks fidelity |
| 5 | Shipper | `zerovector:shipper` | Deliver — packages and ships |

### Why Not Fewer?

**Could we merge Intent Analyst + Architect?**
No. The Intent Analyst's job is to surface what the human actually wants (including what they didn't say). The Architect's job is to translate that into buildable structure. These are different cognitive modes — one is empathetic/investigative, the other is structural/technical. Merging them produces specs that assume too much about intent.

**Could we merge Builder + Shipper?**
No. The Builder's job is to create the artifact. The Shipper's job is to package, document, and deliver it. Builders who also ship tend to skip documentation and cleanup. The separation enforces delivery quality.

**Could we remove the Critic?**
Absolutely not. The Critic is the translation-fidelity guardian. Without an independent validation step, the Builder self-assesses (conflict of interest) and the Shipper ships unchecked work. The Critic is the whole point of ZVD's quality pipeline.

### Why Not More?

**Should we add a Researcher agent?**
Not as a pipeline stage. Research happens at the Intent Analyst stage (gathering context) and the Architect stage (feasibility checking). A dedicated researcher would add a stage without clear input/output contract.

**Should we add a Tester agent?**
No. Testing is part of the Builder's contract (test-first for code artifacts) and the Critic's contract (validation includes test results). A separate tester would fragment responsibility.

**Should we add a Designer agent?**
Not in v1. Design concerns are handled by domain-specific tuning of existing agents. If design-system-as-context is added (see `05-roadmap.md`), a dedicated design agent might become valuable.

### The Pipeline Invariant

The five agents map to five **irreducible functions** in any intent-to-artifact pipeline:

```
Capture -> Structure -> Build -> Validate -> Deliver
```

You can add sub-stages within each function (e.g., the Builder might internally iterate with the Critic), but you cannot remove any function without breaking the pipeline's fidelity guarantee.

---

## 4. Agent Design Principles

### Each Agent Has One Job

Following Amplifier's "single responsibility" principle, each agent does exactly one thing:

| Agent | Single Responsibility | Explicit Non-Responsibilities |
|-------|----------------------|-------------------------------|
| Intent Analyst | Decode intent into structured document | Does NOT design solutions or suggest architecture |
| Architect | Produce specification from intent | Does NOT implement or write code |
| Builder | Implement artifact from specification | Does NOT redesign the spec or skip tasks |
| Critic | Validate artifact against intent | Does NOT fix issues or suggest implementations |
| Shipper | Package and deliver | Does NOT re-validate or modify the artifact |

### Each Agent Has a Quality Bar

The quality bar is the **minimum standard** for the agent's output to be useful to the next stage:

| Agent | Quality Bar | Consequence of Failure |
|-------|------------|----------------------|
| Intent Analyst | "Could the Architect spec from this without asking questions?" | Architect produces spec based on assumptions, builds wrong artifact |
| Architect | "Could the Builder start immediately from this?" | Builder blocks on ambiguity, pipeline stalls |
| Builder | "Every task's acceptance criteria met" | Critic finds failures, rework loop |
| Critic | "Every claim backed by specific evidence" | False PASS ships broken artifact; False FAIL causes unnecessary rework |
| Shipper | "Artifact is immediately usable" | Delivery report missing, human can't use the artifact |

### Each Agent Has a Failure Mode

Documenting failure modes (from ZVD's crew model) makes the pipeline self-correcting:

| Agent | Primary Failure Mode | Mitigation |
|-------|---------------------|------------|
| Intent Analyst | Under-specified, builds wrong thing | Quality bar check before proceeding |
| Architect | Over-specified, builds too much | Scope alignment with intent document |
| Builder | Scope creep, loses fidelity | Strict adherence to spec tasks only |
| Critic | Too lenient, ships translation loss | Evidence requirement for every claim |
| Shipper | Messy delivery, artifact is unusable | Delivery checklist in agent prompt |

---

## 5. Crew-Agent Interaction Model

### Same Agents, Different Context

A critical design decision: **all six crews use the same five agents**. The crews differ only in the **domain context** injected into each agent's prompt.

```
/crew-build    -> Intent Analyst (with build-domain priming) -> Architect (with build-domain priming) -> ...
/crew-research -> Intent Analyst (with research-domain priming) -> Architect (with research-domain priming) -> ...
```

### Why Not Crew-Specific Agents?

| Option | Agent Count | Rejected Because |
|--------|-----------|------------------|
| 5 shared agents + domain context injection | 5 | Chosen — manageable, composable, maintainable |
| 5 agents x 6 crews = 30 agents | 30 | Explosion of agent files; most would be 90% identical |
| 5 core + specialist overlay agents | 10-15 | Complexity without proportional value in v1 |

The domain tuning is in the **mode files** (which inject domain context) and the **crew-instructions** (which define domain-specific focus areas). The agents themselves are domain-agnostic, making them reusable and maintainable.

### Context Flow

```
Human Intent
    |
[Mode activates -> injects domain context]
    |
Orchestrator receives intent + domain
    |
delegate(zerovector:intent-analyst, intent + domain)
    | Intent Document
delegate(zerovector:architect, intent_doc + domain)
    | Specification
delegate(zerovector:builder, spec + intent_doc + domain)
    | Artifact + Self-Verification
delegate(zerovector:critic, artifact + spec + intent_doc)
    | Validation Report
[If PASS] -> delegate(zerovector:shipper, artifact + validation + intent_doc)
[If FAIL] -> delegate(zerovector:builder, critic_findings) -> re-critic
    |
Delivered Artifact + Delivery Report
```

---

## 6. Comparison with Existing Amplifier Agents

### Foundation Bundle Agents (9 agents)

The Foundation bundle ships agents for general-purpose work. The zerovector agents are specialized pipeline stages:

| Foundation Agent | Overlap with ZVD? | Relationship |
|-----------------|-------------------|--------------|
| `foundation:explorer` | Partial — does investigation | Intent Analyst is more structured (produces Intent Document) |
| `foundation:zen-architect` | Partial — does architecture | ZVD Architect produces spec in pipeline format, not free-form |
| `foundation:modular-builder` | Strong — implements code | ZVD Builder follows spec + acceptance criteria strictly |
| `foundation:file-ops` | None — utility agent | Used as tool by ZVD Builder, not a pipeline stage |
| `foundation:git-ops` | Partial — handles git | ZVD Shipper uses git-ops patterns but adds delivery report |
| `foundation:post-task-cleanup` | Partial — cleanup | ZVD Shipper includes cleanup but also packages/documents |

### Superpowers Bundle (5 modes, different model)

Superpowers uses modes (not agents) with human sequencing. ZVD automates the sequencing:

| Superpowers Mode | ZVD Agent | Key Difference |
|-----------------|-----------|----------------|
| `/brainstorm` | Intent Analyst | ZVD produces structured Intent Document; brainstorm is open-ended |
| `/write-plan` | Architect | ZVD produces spec from intent document; write-plan takes direct human input |
| `/execute-plan` | Builder | Similar — both follow a spec. ZVD Builder is scoped to one pipeline run |
| `/verify` | Critic | ZVD Critic checks intent-fidelity, not just completion |
| `/finish` | Shipper | Similar — both handle delivery. ZVD Shipper produces structured delivery report |

---

## 7. Naming Decisions

### Crew Commands

| Name | Alternative Considered | Why Chosen |
|------|----------------------|------------|
| `/crew` | `/zv`, `/zero-vector` | "Crew" is the ZVD term; shorter; self-explanatory |
| `/crew-build` | `/crew-code`, `/crew-dev` | "Build" is broader than "code" — includes configs, scripts, non-code artifacts |
| `/crew-product` | `/crew-ux`, `/crew-design` | "Product" encompasses UX + strategy + validation; not just visual design |
| `/crew-platform` | `/crew-infra`, `/crew-ops` | "Platform" covers modules + APIs + architecture; broader than "infra" |
| `/crew-research` | `/crew-investigate`, `/crew-analyze` | "Research" is the established term for the domain |
| `/crew-content` | `/crew-write`, `/crew-docs` | "Content" is broader — docs + curriculum + posts + writing |

### Agent Names

| Name | Alternative Considered | Why Chosen |
|------|----------------------|------------|
| `intent-analyst` | `decoder`, `listener`, `intake` | "Analyst" implies active investigation, not passive reception |
| `architect` | `planner`, `designer`, `specifier` | "Architect" is the standard term for structure-from-requirements |
| `builder` | `implementer`, `developer`, `coder` | "Builder" is medium-agnostic — builds code, docs, configs, anything |
| `critic` | `validator`, `reviewer`, `checker` | "Critic" implies judgment, not just verification. Checking fidelity requires judgment |
| `shipper` | `deliverer`, `packager`, `closer` | "Shipper" echoes "real artists ship" — implies completion and delivery, not just packaging |

---

*This document should be read after `02-amplifier-alignment.md` and before `04-implementation-decisions.md`.*
