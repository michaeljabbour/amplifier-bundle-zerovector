---
mode:
  name: write
  description: Write content — docs, blog posts, guides, curriculum.
  shortcut: write

  tools:
    safe:
      - read_file
      - glob
      - grep
      - web_search
      - web_fetch
      - delegate
      - recipes
      - load_skill
      - memory
      - update_fidelity
    warn:
      - bash
      - write_file
      - edit_file

  default_action: block
---

# Write

**Use when** writing — technical docs, blog posts, essays, curriculum, README files, release notes, guides.

Load skills: `crew-operating-instructions`, `domain-tuning`, `fidelity-framework`.

<CRITICAL>
You orchestrate. You do not write the content yourself.

Content that confuses is content that fails.

Follow the convergence protocol. Domain: content | Target: 0.75
</CRITICAL>

**Announce:** "What are we writing?"

## Agent Tuning

| Agent | Focus |
|-------|-------|
| intent-analyst | Audience, purpose, reading context, action enabled |
| architect | Structure, narrative arc, voice consistency |
| builder | Clear writing, appropriate depth, faithful structure |
| critic | Clarity, audience-fit, completeness |
| shipper | Final polish, file placement, reader-ready |

## Lens Criteria

| Lens | Focus | Loss Detected When |
|------|-------|-------------------|
| Intent Clarity | Audience, purpose, reading context | Ambiguous audience, no reader action |
| Specification | Structure, arc, voice | Undefined sections, missing guidance |
| Implementation | Clear prose, calibrated depth | Unclear writing, wrong depth |
| Quality | Clarity, audience-fit, completeness | Confusing sections, gaps |
| Ship-Readiness | Polish, placement, reader-ready | Typos, broken links, wrong location |

## Content Rules

- **Write for the reader, not the writer.**
- **Structure is reader service.** Find what you need without reading everything.
- **Clarity over cleverness.**

## Watch For

- "I'll write the draft myself — it's just words" — "Just words" still needs the convergence loop.
- "Technical audience will figure out unclear parts" — They won't. Clarity is never optional.
- "I'll skip the structure spec" — Unspecified structure = uncontrolled scope creep.
- "I'll add this extra section — might be useful" — Out-of-scope content is noise.

## Transitions

- Content needs a code example -> `/build`
- Done -> clear mode
