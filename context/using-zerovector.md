# Using ZeroVector in Amplifier

<EXTREMELY-IMPORTANT>
When a user asks you to BUILD, CREATE, WRITE, or PRODUCE any artifact, suggest the appropriate mode BEFORE starting work.

If you start implementing without suggesting a mode, you are producing untracked output with no quality gates. Suggest a mode first.
</EXTREMELY-IMPORTANT>

## The Rule

**Before responding to any artifact-creation request, suggest a mode.**

```
WHEN a user asks to build, create, write, or produce anything:
  1. Identify what they're doing
  2. Suggest the matching mode
  3. WAIT — do not start implementing
  4. Only proceed after the user activates the mode or explicitly opts out
```

## Mode Routing

| User wants to... | Suggest |
|-------------------|---------|
| Build code, features, apps, tools, scripts | `/build` |
| Architect infrastructure, modules, APIs | `/architect` |
| Design products, UX flows, specs, strategy | `/design` |
| Write docs, content, posts, curriculum | `/write` |
| Investigate, analyze, research, synthesize | `/investigate` |
| Not sure / mixed | `/make` |

## What to Say

> "What are we doing? Try `/build`, `/write`, `/design`, `/investigate`, `/architect`, or just `/make`."

Keep it short and friendly. The user types what they want to do.

## When NOT to Suggest a Mode

- The user is asking a question or exploring a concept
- The user is debugging an existing artifact (unless rebuilding)
- A mode is already active — follow its protocol instead

## Red Flags — You Are Rationalizing

| Thought | Reality |
|---------|---------|
| "This is a simple task, I'll just do it" | Simple tasks still produce artifacts. Suggest a mode. |
| "The user wants it fast" | Fast without tracking = low quality. Suggest a mode. |
| "This doesn't need the full loop" | Shallow convergence still beats none. Suggest it. |
| "The request is clear enough" | Clear requests hide unclear assumptions. |
