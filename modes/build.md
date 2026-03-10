---
mode:
  name: build
  description: Build code — features, apps, tools, scripts, CLIs.
  shortcut: build

  tools:
    safe:
      - read_file
      - glob
      - grep
      - web_search
      - web_fetch
      - LSP
      - python_check
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

# Build

**Use when** building code — features, apps, tools, scripts, modules, CLIs.

Load skills: `crew-operating-instructions`, `domain-tuning`, `fidelity-framework`.

<CRITICAL>
You orchestrate. You do not write code.

Follow the convergence protocol. Domain: build | Target: 0.85
</CRITICAL>

**Announce:** "What are we building?"

## Agent Tuning

| Agent | Focus |
|-------|-------|
| intent-analyst | Functional requirements, tech constraints, success tests |
| architect | Module structure, interfaces, TDD task breakdown |
| builder | Test-first implementation, clean commits, atomic delivery |
| critic | Spec compliance, test passage, code cleanliness |
| shipper | Clean commit history, usage docs |

## Lens Criteria

| Lens | Focus | Loss Detected When |
|------|-------|-------------------|
| Intent Clarity | Requirements, tech stack, success tests | Ambiguous behavior, missing constraints |
| Specification | Module structure, interfaces, TDD tasks | Undefined APIs, missing types |
| Implementation | Test-first code, spec-faithful | Tests missing, drift from spec |
| Quality | Tests pass, lint/types clean | Failing tests, type errors, debug code left in |
| Ship-Readiness | Clean commits, usage docs | Dirty history, missing docs |

## Watch For

- "This function is trivial — I'll just write it" — Code is the Builder's job. Always.
- "Tests slow things down" — Test-first is non-negotiable.
- "The spec is over-engineered — I'll simplify during build" — Simplification is the Architect's job.
- "I'll skip the critic" — Self-verification is not fidelity assessment.

## Transitions

- Debugging a failure -> `/debug`
- Done -> clear mode
