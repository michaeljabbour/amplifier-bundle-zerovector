# Using ZeroVector in Amplifier

<EXTREMELY-IMPORTANT>
When a user asks you to BUILD, CREATE, WRITE, or PRODUCE any artifact, you ABSOLUTELY MUST suggest the appropriate crew mode BEFORE starting work.

YOU DO NOT HAVE A CHOICE. YOU CANNOT RATIONALIZE YOUR WAY OUT OF THIS.

If you start implementing without suggesting a crew mode, you are producing untracked output with no fidelity convergence, no quality gates, and guaranteed translation loss. This is not acceptable.
</EXTREMELY-IMPORTANT>

## The Rule

**Before responding to any artifact-creation request, suggest the crew mode.**

```
WHEN a user asks to build, create, write, or produce anything:
  1. Identify the domain (build / product / platform / research / content)
  2. Suggest the matching crew mode
  3. WAIT — do not start implementing
  4. Only proceed after the user activates the mode or explicitly opts out
```

## Crew Mode Routing Table

| User Intent | Suggest |
|-------------|---------|
| Build code, features, apps, tools, scripts, CLIs | `/crew-build` |
| Design product, UX, user flows, specs, strategy | `/crew-product` |
| Build infrastructure, modules, APIs, architecture | `/crew-platform` |
| Research, analyze, investigate, synthesize | `/crew-research` |
| Write docs, content, posts, curriculum, copy | `/crew-content` |
| Not sure / mixed concerns | `/crew` |

## What to Say

> "This looks like a **[domain]** artifact. I recommend activating **`/crew-build`** (or whichever crew fits) so the ZeroVector fidelity convergence engine can orchestrate this with intent analysis, specification, quality gates, and translation-loss tracking.
>
> Type **`/crew-build`** to activate, or tell me to proceed without it."

## When NOT to Suggest a Crew Mode

- The user is asking a question or exploring a concept
- The user is debugging an existing artifact (unless rebuilding)
- A `/crew*` mode is already active — follow the convergence protocol instead

## Red Flags — You Are Rationalizing

| Thought | Reality |
|---------|---------|
| "This is a simple task, I'll just do it" | Simple tasks still produce artifacts. Suggest the crew. |
| "The user wants it fast" | Fast + fidelity-blind = low-quality output. Suggest the crew. |
| "They didn't say they want a crew" | Artifact-creation implies it. Your job is to surface it. |
| "I'll suggest the crew next time" | There is no next time if translation loss is already in flight. |
| "This doesn't need the full convergence loop" | Shallow convergence still beats no convergence. Suggest it. |
| "The request is clear enough" | Clear requests hide unclear assumptions. The intent-analyst exists for this reason. |
