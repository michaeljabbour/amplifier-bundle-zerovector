# Code Tracer Findings — Context Injection Chain
**Agent:** agent-1-code-tracer (HOW)  
**Team:** team-beta-context-injection  
**Wave:** 1  
**Date:** 2026-03-09

---

## Executive Summary

Fidelity-tracking instructions reach the LLM through **two completely separate mechanisms**: static context injection (always present from session initialization) and dynamic hook-based injection (ephemeral, per-turn, conditional). The `fidelity-framework.md` file is **always** in the system prompt regardless of mode. What changes when `/crew-build` is activated is: (a) the mode file body is injected, (b) crew mode reminders stop firing, and (c) ephemeral fidelity state routing advice starts appearing after `update_fidelity` is called.

---

## 1. Bundle Composition: How Context Accumulates

### Entry point: `bundle.md`

`bundle.md` is the root bundle file. Its YAML frontmatter declares two `includes`:

```yaml
includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: zerovector:behaviors/zerovector-crew
```

**File:** `bundle.md:7-9`

The `zerovector:behaviors/zerovector-crew` reference resolves to `behaviors/zerovector-crew.yaml`, which itself includes:

```yaml
includes:
  - bundle: zerovector:behaviors/fidelity
```

**File:** `behaviors/zerovector-crew.yaml:9-10`

And `zerovector:behaviors/fidelity` resolves to `behaviors/fidelity.yaml`.

### The composition chain

```
bundle.md
  └── zerovector:behaviors/zerovector-crew  (behaviors/zerovector-crew.yaml)
        └── zerovector:behaviors/fidelity   (behaviors/fidelity.yaml)
```

Each of these bundles contributes **context files**, **hooks**, and **tools**. The `Bundle.compose()` method in `amplifier-foundation/amplifier_foundation/bundle.py:61-146` merges them:

- **context**: files are accumulated (never overwritten) with bundle-namespace prefixes  
- **hooks**: merged by module ID  
- **tools**: merged by module ID  

**File:** `amplifier-foundation/amplifier_foundation/bundle.py:128-136` — context accumulation

---

## 2. Static Context Files: What Is ALWAYS in the System Prompt

Context files enter the system prompt during `PreparedBundle.create_session()` or `PreparedBundle.spawn()`.

**Mechanism** (`bundle.py:515-594`):
1. Collects all context files from all composed bundles
2. Reads each file and builds `instruction_parts`
3. Resolves @mentions recursively via `load_mentions()`
4. Formats loaded files as XML `<context_file>` blocks
5. Injects as a single `{"role": "system", "content": final_instruction}` message

### Context files from `bundle.md` markdown body (@mentions, lines 29-31, 118)

These are **@mentions** in the bundle.md instruction body, resolved at session init:

| @mention | Resolved file |
|----------|--------------|
| `@zerovector:context/zerovector-principles.md` | `context/zerovector-principles.md` |
| `@zerovector:context/crew-instructions.md` | `context/crew-instructions.md` |
| `@zerovector:context/domain-tuning.md` | `context/domain-tuning.md` |
| `@foundation:context/shared/common-system-base.md` | foundation bundle context |

**File:** `bundle.md:29-31, 118`  
**Resolution:** `amplifier-foundation/amplifier_foundation/mentions/resolver.py:51-54` — namespace:name pattern routes to `bundle.resolve_context_path(name)`

### Context files from `behaviors/zerovector-crew.yaml` (context.include section)

```yaml
context:
  include:
    - zerovector:context/using-zerovector.md
    - zerovector:context/crew-instructions.md
    - zerovector:context/domain-tuning.md
    - modes:context/modes-instructions.md
```

**File:** `behaviors/zerovector-crew.yaml:33-38`

### Context files from `behaviors/fidelity.yaml` (context.include section)

```yaml
context:
  include:
    - zerovector:context/using-zerovector.md
    - zerovector:context/fidelity-framework.md
```

**File:** `behaviors/fidelity.yaml:37-40`

### The critical finding: `fidelity-framework.md` is ALWAYS injected

`behaviors/fidelity.yaml` is included transitively by `zerovector-crew.yaml` → included by `bundle.md`. This means **`context/fidelity-framework.md` is always in the system prompt**, regardless of which mode is active or whether any mode is active at all.

The `_parse_context()` function in `bundle.py:360-388` converts all `context.include` entries into `Path` objects. `Bundle.compose()` accumulates them all into the composed bundle's `context` dict. Then `create_session()` reads each one and adds it to the instruction.

---

## 3. The Mention Resolution Mechanism

When `bundle.md`'s markdown body contains `@zerovector:context/crew-instructions.md`, here is exactly how it resolves:

1. `bundle.py:569` calls `load_mentions(combined_instruction, resolver=resolver, deduplicator=deduplicator)`
2. `mentions/loader.py:98` calls `parse_mentions(text)` — regex extracts `@zerovector:context/crew-instructions.md`
3. `mentions/parser.py:32` — pattern: `@(?!...email...)([a-zA-Z0-9_:./\-]+)` matches it
4. `_resolve_mention()` in `loader.py:114` calls `resolver.resolve(mention)`
5. `resolver.py:51-54` splits `zerovector:context/crew-instructions.md` on `:` → namespace=`zerovector`, name=`context/crew-instructions.md`
6. `bundle.resolve_context_path("context/crew-instructions.md")` returns the path
7. File content is read and added to the `ContentDeduplicator`
8. Recursively loads any @mentions found in that file (max depth=3)

**File:** `amplifier-foundation/amplifier_foundation/mentions/loader.py:72-171`

The `format_context_block()` function wraps all loaded files in XML:
```xml
<context_file paths="@zerovector:context/crew-instructions.md → /path/to/file">
[file content]
</context_file>
```
**File:** `amplifier-foundation/amplifier_foundation/mentions/loader.py:15-68`

This XML block is prepended to the combined instruction, then added as a system message.

---

## 4. The Hook Registration Mechanism

When `AmplifierSession.initialize()` runs, it loads hooks in this order:

**File:** `amplifier-core/amplifier_core/session.py:193-208`

```python
for hook_config in self.config.get("hooks", []):
    hook_mount = await self.loader.load(module_id, ...)
    cleanup = await hook_mount(self.coordinator)
```

Each hook module has a `mount()` function. For `hooks-fidelity-reporter`:

**File:** `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:332-382`

```python
async def mount(coordinator, config=None):
    reporter = FidelityReporter()
    for event_name, handler in [("tool:post", _on_tool_post), ("prompt:complete", _on_prompt_complete)]:
        unreg = coordinator.hooks.register(event_name, handler, priority=priority, name=f"fidelity-reporter-{event_name}")
```

The hooks are registered into the `HookRegistry` at `coordinator.hooks`.

**Hooks declared in `behaviors/zerovector-crew.yaml`:**
- `hooks-mode` (from `amplifier-bundle-modes`, external) 
- `hooks-fidelity-reporter` (from `../modules/hooks-fidelity-reporter`, local)

**File:** `behaviors/zerovector-crew.yaml:12-16`

---

## 5. How `hooks-fidelity-reporter` Injects Fidelity Instructions

### Event trigger

The hook fires on two events:
- `tool:post` — after every tool call completes
- `prompt:complete` — after every LLM turn

**File:** `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py:355-357`

### Condition gate

Before injecting, it checks:
1. `coordinator.get_capability("zerovector.fidelity_state")` must return non-None
2. `fidelity_state.get_state()["lens_scores"]` must be non-empty (i.e., `update_fidelity` must have been called at least once)

**File:** `__init__.py:293-300`

```python
fidelity_state = coordinator.get_capability("zerovector.fidelity_state")
if fidelity_state is None:
    return _CONTINUE  # no-op

state = fidelity_state.get_state()
if not state.get("lens_scores"):
    return _CONTINUE  # no-op until scores are populated
```

### What gets injected

The hook returns a `HookResult` with two channels:

```python
return HookResult(
    action="continue",
    context_injection=ephemeral_text,   # plain-text routing advice for LLM
    context_injection_role="system",
    ephemeral=True,                      # NOT stored in conversation history
    user_message=dashboard,              # ANSI box for terminal display
    user_message_level="info",
)
```

**File:** `__init__.py:310-317`

The `ephemeral_text` format:
```
[FIDELITY STATE — ephemeral, auto-updates]
Status: NEEDS_WORK
Overall: 0.53 | Target: 0.85 (domain: build)
Priority gap: implementation (0.40)
Recommendation: Route to builder to address implementation gaps
```

**File:** `__init__.py:249-272` (`render_ephemeral()`)

### The ephemeral flag — what it means for context storage

When `ephemeral=True`, `coordinator._handle_context_injection()` does **NOT** add it to the context store:

**File:** `amplifier-core/amplifier_core/coordinator.py:411-426`

```python
# 3. Add to context with provenance (ONLY if not ephemeral)
if not result.ephemeral:
    context = self.mount_points["context"]
    if context and hasattr(context, "add_message"):
        await context.add_message(message)
```

Ephemeral injections are handled by the **orchestrator** — it appends the content to the current LLM call's messages without storing it in the conversation history. This means the fidelity routing advice is present for the **current turn only** and does not accumulate.

---

## 6. How `tool-fidelity-state` Connects to `hooks-fidelity-reporter`

The `tool-fidelity-state` module:
1. Creates a `FidelityState` dataclass instance
2. Creates an `UpdateFidelityTool` wrapping that state
3. Mounts the tool at `coordinator.tools["update_fidelity"]`
4. Registers two capabilities: `zerovector.fidelity_state` and `zerovector.update_fidelity`

**File:** `modules/tool-fidelity-state/amplifier_module_tool_fidelity_state/__init__.py:165-193`

When the LLM calls `update_fidelity({lens_scores: {...}, domain: "build", target: 0.85})`:
1. `UpdateFidelityTool.execute()` is called
2. It calls `self.state.update_fidelity(lens_scores, domain, target)`
3. `FidelityState.update_fidelity()` clamps scores, computes overall mean, finds priority gap
4. Updates the shared `FidelityState` object in-place

**File:** `__init__.py:141-159` and `__init__.py:69-94`

On the very next `tool:post` event (after `update_fidelity` returns), `hooks-fidelity-reporter` fires, reads the now-populated state via `coordinator.get_capability("zerovector.fidelity_state")`, and injects the routing advice ephemerally.

---

## 7. The `hooks-crew-gate` Mechanism (No-Mode Defense)

`hooks-crew-gate` registers on `prompt:complete` (priority 10) and `tool:post` (priority 10).

**File:** `modules/hooks-crew-gate/amplifier_module_hooks_crew_gate/__init__.py:246-256`

When no mode is active, it injects a crew-mode reminder:

```python
_SOFT_REMINDER = "[CREW GATE — no mode active]\nYou MUST suggest a /crew-* mode..."
_HARD_WARNING = "[CREW GATE — VIOLATION DETECTED]\nYou just used a creation tool WITHOUT..."
```

**File:** `__init__.py:58-77`

It detects mode state by probing three capability names:
- `coordinator.get_capability("modes.active")`
- `coordinator.get_capability("modes.active_mode")`
- `coordinator.get_capability("modes.state")`

**File:** `__init__.py:96-117`

**Key difference:** When crew-build is active, `_is_mode_active()` returns True → the crew gate returns `_CONTINUE` (no injection). When NO mode is active, the LLM receives the crew-gate reminder on every turn.

---

## 8. Mode File Injection: What Changes When `/crew-build` is Activated

The `hooks-mode` and `tool-mode` modules are external (from `amplifier-bundle-modes`, source: `git+https://github.com/microsoft/amplifier-bundle-modes@main`). They are declared in `behaviors/zerovector-crew.yaml:12-20`.

The mode activation flow (inferred from the tools/hooks pattern):
1. User types `/crew-build` — the LLM calls `tool-mode` with `operation='set', name='crew-build'`
2. `tool-mode` reads `modes/crew-build.md` from the bundle
3. `tool-mode` sets the active mode capability (e.g., `modes.active_mode = "crew-build"`)
4. `hooks-mode` fires on subsequent `prompt:complete` events, reads active mode file content
5. Returns a `HookResult` with `context_injection` = mode file markdown body (ephemeral)

The crew-build.md markdown body (lines 29-156) becomes the per-turn ephemeral system context. This body contains:
- `Read crew-instructions.md for the full orchestration protocol`
- `Read fidelity-framework.md for the universal lens model and scoring rubric`
- `Read domain-tuning.md for build-specific fidelity criteria`

These are LLM directives pointing to content already in the static system prompt.

---

## 9. Complete Execution Path: From `/crew-build` to Fidelity Instructions in Prompt

```
USER: /crew-build
  │
  ▼
LLM calls tool-mode(operation='set', name='crew-build')
  │
  ├── tool-mode reads modes/crew-build.md
  ├── Sets capability: modes.active_mode = "crew-build"
  └── Returns: "Build crew ready. What are we building?"
  │
  ▼ [IMMEDIATE STATIC - already in prompt from session init]
  │
  System prompt contains:
  ├── bundle.md markdown body (STANDING-ORDER + crew table)
  ├── <context_file> zerovector-principles.md
  ├── <context_file> crew-instructions.md          ← always present
  ├── <context_file> domain-tuning.md              ← always present
  ├── <context_file> fidelity-framework.md         ← ALWAYS PRESENT (from fidelity.yaml)
  ├── <context_file> using-zerovector.md           ← always present
  ├── <context_file> modes-instructions.md         ← always present
  └── <context_file> common-system-base.md         ← always present
  │
  ▼ [DYNAMIC - per turn, via hooks]
  │
  On every prompt:complete event:
  ├── hooks-mode (priority unknown):
  │     IF mode active: inject crew-build.md body as ephemeral system msg
  ├── hooks-crew-gate (priority 10):
  │     IF mode active: SKIP (returns _CONTINUE)
  └── hooks-fidelity-reporter (priority 50):
        IF fidelity_state has lens_scores: inject routing advice as ephemeral system msg
        ELSE: SKIP (returns _CONTINUE, no injection)
  │
  ▼
  After /crew-build active, LLM does initial assessment:
    delegates to zerovector:critic → critic calls update_fidelity(lens_scores={...})
  │
  ▼ tool:post event fires for update_fidelity call
  │
  hooks-fidelity-reporter fires:
  ├── reads coordinator.get_capability("zerovector.fidelity_state") → populated state
  ├── renders ANSI dashboard → stdout
  └── returns HookResult(context_injection="[FIDELITY STATE...]", ephemeral=True)
  │
  ▼
  Orchestrator appends ephemeral injection to CURRENT LLM call messages
  LLM receives: "[FIDELITY STATE — ephemeral, auto-updates]\nStatus: NEEDS_WORK\n..."
```

---

## 10. What's Different: No Mode vs crew-build Active

| Aspect | No mode active | crew-build active |
|--------|---------------|-------------------|
| `fidelity-framework.md` in prompt | ✅ Always (static) | ✅ Always (static) |
| `crew-instructions.md` in prompt | ✅ Always (static) | ✅ Always (static) |
| `using-zerovector.md` in prompt | ✅ Always (static) | ✅ Always (static) |
| hooks-crew-gate injection | ✅ YES — soft reminder | ❌ NO — mode active, gate passes |
| hooks-mode injection | ❌ Nothing | ✅ crew-build.md body injected |
| hooks-fidelity-reporter injection | ⚠️ Only if scores populated | ⚠️ Only if scores populated |
| `update_fidelity` tool available | ✅ Always mounted | ✅ Always mounted |
| `zerovector.fidelity_state` capability | ✅ Always registered | ✅ Always registered |

The core finding: **fidelity tracking instructions are ALWAYS present in the static system prompt** (via `fidelity-framework.md` from `fidelity.yaml`). The mode system adds **behavioral framing** (crew-build.md says "you are an orchestrator") and the hooks add **live state** (current scores, priority gap, routing recommendation).
