# 00 — Source Material

> Research date: 2026-03-06
> Source domain: `zerovector.design`
> Creator: **Erika Flowers** — ~31-year UX/Service Design veteran; former NASA AI Innovation Lead; published science fiction author
> Extraction method: Headless Chromium browser (the site is a fully client-side JS-rendered SPA; non-JS fetchers get an empty shell)

---

## 1. Pages Visited

Eight pages were loaded in a live headless browser. All text was extracted from the **rendered DOM**, not from source HTML.

| # | URL | Page Title |
|---|-----|------------|
| 1 | `https://zerovector.design/` | Zero-Vector Design (Homepage / Manifesto) |
| 2 | `https://zerovector.design/philosophy` | Philosophy — Zero-Vector Design |
| 3 | `https://zerovector.design/for-builders` | For Builders — Zero-Vector Design |
| 4 | `https://zerovector.design/for-leaders` | For Leaders — Transform Your Organization |
| 5 | `https://zerovector.design/name` | Zero Vector — The Name |
| 6 | `https://zerovector.design/start` | Get Started — Zero-Vector Design |
| 7 | `https://zerovector.design/open` | The Open Vector — Zero-Vector Design |
| 8 | `https://zerovector.design/investiture` | Investiture — Zero-Vector Design |

Additional sources consulted:
- Erika Flowers' foundational Substack manifesto ("You Will Move Planets")
- "The 20 Rules for AI-First Design" essay
- LinkedIn company page for Zero-Vector Design
- Author's personal site and conference bios
- GitHub organization (`github.com/zerovector-design`)

---

## 2. Page-by-Page Content Summary

### 2A. Homepage (`/`) — The Manifesto

The homepage is the canonical long-form piece — numbered sections 001 through 007, approximately 4,000+ words of rendered prose. It functions as a manifesto, not a landing page with teasers.

**Section 001 — "What Is Zero Vector?"**
Opens with a geographic coordinate (44.8024 N / 68.7853 W — coastal Maine) and the label "A New Discipline." Defines the movement:

> "A growing network of practitioners who believe the person with the vision should build the artifact directly, using AI agents as crew."

Branches to three audience paths: "Learn the philosophy" → `/philosophy`, "Start building" → `/for-builders`, "Transform your org" → `/for-leaders`.

**Section 003 — "The Pipeline, Reimagined"**
Subtitled "Every phase of concept-to-customer. Transformed." Contains a seven-phase before/after comparison:

| Phase | Before (Traditional) | Zero-Vector |
|-------|---------------------|-------------|
| 01 Market Research | Weeks of desk research, PDF reports nobody reads | AI agents continuously scanning, synthesizing, surfacing patterns in real time |
| 02 Customer Research | Scheduled interviews, transcription backlogs, insight decks | Continuous signal capture across channels; agents surface patterns as they emerge |
| 03 Jobs-to-be-Done | Workshop-dependent; captured in static frameworks | Living JTBD models continuously refined by agent observation |
| 04 Ideation | Brainstorm sessions, post-it walls, convergence theater | Rapid concept generation grounded in real signals; instant feasibility checking |
| 05 Prototyping | Static mockups, clickable prototypes, design-to-dev handoff | Working artifacts from the start — not pictures of the thing, the thing |
| 06 Validation | Usability labs, A/B tests after build | Continuous validation woven into every build cycle |
| 07 Build & Ship | Handoff-heavy, ticket-driven, multi-sprint | Direct intent-to-artifact; crew builds what you specified |

**Section 004 — "The Seven Principles"**
The philosophical core of ZVD, each with substantial prose explanation:

> **1. Work in the Medium** — "Build real artifacts, not representations of artifacts. Not a picture of the thing. Not a prototype of the thing. The thing."

> **2. Boundaryless by Nature** — "The old disciplinary walls — design, engineering, research, content — were constraints of a model where each discipline required years of specialized training."

> **3. The Medium Shapes Thought** — "The tool you use changes how you think. Working directly in the real artifact changes what you see, what you ask, and what you build."

> **4. Intentional Impermanence** — "Artifacts are regeneratable from specification. Don't patch — regenerate."

> **5. POSIWID** — "The Purpose of a System Is What It Does. Judge systems by their outputs, not their intentions."

> **6. Compound Your Leverage** — "Each pipeline stage amplifies the last. A precise intent produces a sharper spec."

> **7. Venture Beyond 'Possible'** — "The old ceiling was set by the translation chain. When translation is eliminated, the ceiling rises."

**Section 005 — "What This Is / Is Not"**
A defensive clarification section. Key declarations:

> "This is NOT vibe coding. This is NOT anti-craft. This is NOT anti-process. This is NOT 'AI replaces designers.'"

> "This IS rigorous, intentional work. This IS high-fidelity artifact production. This IS systems thinking about your workflow."

**Section 006 — "The Crew Model"**
Distinguishes between assistants and crew:

> "An assistant waits for instructions and executes them literally. A crew member has a role, a standard, and a contract — and executes with judgment."

**Section 007 — "Join the Movement"**
Call to action with links to community channels, the Open Vector curriculum, and the Investiture scaffold.

---

### 2B. Philosophy Page (`/philosophy`)

Expands on the seven principles with deeper argumentation. Each principle gets 300-500 words of elaboration with examples and counter-examples.

Key addition beyond the homepage: explicit grounding in **systems thinking** and **cybernetics** (Stafford Beer's POSIWID concept). The philosophy page positions ZVD as a descendant of service design and systems theory, not of UI/UX tooling trends.

> "Zero-Vector is not a tool choice. It is a systems intervention. You are redesigning the production system itself."

---

### 2C. For Builders (`/for-builders`)

Practical orientation for individual practitioners. Structured as a progression:

1. **Start with intent clarity** — before touching any tool, articulate what you're building and why
2. **Assemble your crew** — name your agents, give them roles, hold them to standards
3. **Work in the medium** — build real artifacts from day one
4. **Validate against intent** — not "does it work?" but "does it preserve the original vision?"
5. **Ship and regenerate** — delivery is not the end; the spec is the source of truth

Includes references to "Fictioneer" — a complex full-stack application Erika built solo using named AI agents as proof-of-concept for the methodology.

> "Fictioneer is not a demo. It is a production application built by one person with a crew of AI agents. Every feature, every test, every deployment — crew-directed."

---

### 2D. For Leaders (`/for-leaders`)

Organizational positioning. Argues that ZVD changes team topology:

- Traditional: large cross-functional teams with handoff protocols
- Zero-Vector: smaller crews with broader individual scope
- The "10x" is not individual speed — it's elimination of translation loss at organizational boundaries

Key quote on organizational implications:

> "The question is not 'how do we use AI tools?' The question is 'what does our production system look like when translation is no longer a constraint?'"

---

### 2E. The Name (`/name`)

Explains the "zero vector" metaphor:

> "In mathematics, the zero vector is the vector with no magnitude and no direction — the identity element of vector addition. In our context: the zero vector is the state where the distance between intent and artifact is zero. No translation. No loss. No direction change."

This is the origin of the name: the goal is to reduce the "vector" between what you envision and what gets built to zero magnitude.

---

### 2F. Get Started (`/start`)

Onboarding page with three tracks:
1. **Read the manifesto** (links back to `/`)
2. **Try the Investiture scaffold** (links to `/investiture`)
3. **Join the community** (links to Discord and GitHub)

---

### 2G. The Open Vector (`/open`)

Describes a growing curriculum for practitioners. Positioned as "the education arm" of ZVD:

- Open-source learning materials
- Community-contributed case studies
- Progressive skill-building from "first crew" to "production pipeline"

> "The Open Vector is not a course. It is a living curriculum maintained by practitioners for practitioners."

---

### 2H. Investiture (`/investiture`)

A starter scaffold / boilerplate for beginning Zero-Vector practice:

- Pre-configured agent roles (the five-role crew)
- Starter prompts for each pipeline stage
- Example intent documents and specifications
- Instructions for adapting to your own toolchain

The name "Investiture" comes from the formal ceremony of conferring authority — here, the act of investing your AI agents with crew authority and standards.

---

## 3. Core Thesis (Synthesized)

**"Eliminate translation loss between vision and product."**

Everything on the site revolves around this single thesis:

1. **The problem**: Traditional product creation is a chain of lossy compressions. Every handoff (designer to developer, researcher to designer, spec to ticket) loses information. The shipped artifact is a degraded version of the original intent.

2. **The enabler**: AI agents, when directed with architecture and discipline, can compress the boundaries between disciplines. The creator can work in the actual medium (working product), not in representation (wireframes, prototypes, specification documents).

3. **The method**: Treat AI agents as a directed crew — not assistants who wait for literal instructions, but crew members who have roles, standards, and contracts. The human provides vision and judgment; the crew provides execution and craft.

4. **The proof**: Fictioneer — a complex, production full-stack application built by one person directing a crew of named AI agents.

---

## 4. Key Distinctions the Site Makes

### Zero-Vector vs. Vibe Coding

The site is emphatic that ZVD is not "vibe coding" (casual, unstructured prompting):

> "Vibe coding has no intent, no crew, no quality bar. Zero-Vector has all three."

| Dimension | Vibe Coding | Zero-Vector |
|-----------|-------------|-------------|
| Intent | Vague or absent | Explicit, documented, structured |
| Process | Ad hoc prompting | Staged pipeline with quality gates |
| Agents | Generic assistant | Named crew with contracts |
| Quality | "Does it run?" | "Does it preserve original intent?" |
| Artifacts | Disposable experiments | Production-grade, regeneratable |

### Crew vs. Assistant

| Dimension | Assistant | Crew Member |
|-----------|-----------|-------------|
| Agency | Waits for literal instructions | Has a role and exercises judgment |
| Standard | Does what you say | Does what the role demands |
| Contract | None — output varies | Defined inputs, outputs, quality bar |
| Failure mode | Silent degradation | Explicit failure with evidence |

---

## 5. About the Creator

**Erika Flowers** — biographical details gathered from the site, LinkedIn, personal site, and conference bios:

- ~31 years in UX and service design
- Former Principal Service Designer and AI Innovation Lead at NASA
- Published science fiction author
- Based in coastal Maine (coordinates on the site: 44.8024 N / 68.7853 W)
- Built "Fictioneer" as the ZVD proof-of-concept
- Founded the Zero-Vector Design movement in early 2026
- Active on Substack with foundational essays

The background matters: ZVD comes from a **design-led** perspective, not an engineering-led one. The author's framing is consistently about preserving human intent and vision, using AI as amplification — not about coding productivity or developer experience.

---

## 6. External References

| Source | URL | Content |
|--------|-----|---------|
| ZVD Homepage | `https://zerovector.design/` | Full manifesto (sections 001-007) |
| ZVD Philosophy | `https://zerovector.design/philosophy` | Expanded seven principles |
| For Builders | `https://zerovector.design/for-builders` | Practitioner onboarding |
| For Leaders | `https://zerovector.design/for-leaders` | Organizational transformation |
| The Name | `https://zerovector.design/name` | Zero vector metaphor explained |
| Get Started | `https://zerovector.design/start` | Three onboarding tracks |
| Open Vector | `https://zerovector.design/open` | Community curriculum |
| Investiture | `https://zerovector.design/investiture` | Starter scaffold |
| Substack | Erika Flowers' Substack | "You Will Move Planets" + supporting essays |
| GitHub Org | `github.com/zerovector-design` | Open-source components |
| LinkedIn | Zero-Vector Design company page | Professional positioning |

---

## 7. Research Methodology

### Why browser extraction was necessary

The site at `zerovector.design` is a fully **client-side JavaScript-rendered SPA**. All routes (`/`, `/philosophy`, `/for-builders`, `/for-leaders`, `/name`, `/start`, `/open`, `/investiture`) return only a shell HTML document with the title "Zero-Vector Design" and zero body text to a non-JS fetcher. The site explicitly states: "This site requires JavaScript to run correctly."

### Extraction approach

1. **Primary**: Headless Chromium browser visited all 8 pages, waited for JS rendering, extracted full text from rendered DOM
2. **Supplementary**: Google's indexed snippets for cross-validation
3. **Supplementary**: Substack essays, LinkedIn company page, GitHub org, author's personal site for biographical and contextual detail
4. **Cross-validation**: Compared browser-extracted content against indexed snippets to confirm completeness

### Confidence assessment

- Homepage/manifesto content: **High** — full text extracted, cross-validated
- Philosophy page: **High** — full text extracted
- Builder/Leader pages: **High** — full text extracted
- Name/Start/Open/Investiture: **High** — full text extracted
- Substack essays: **Medium-High** — fetched via standard HTTP (not JS-rendered)
- Biographical details: **Medium** — synthesized from multiple secondary sources

---

*This document preserves the primary source research. It should be read before any analysis documents that follow.*
