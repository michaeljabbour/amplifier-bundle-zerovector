# Unknowns — What I Couldn't Determine
**Agent:** agent-1-code-tracer  
**Investigation:** Context injection chain for zerovector crew mode + fidelity

---

## 1. `hooks-mode` internals — exact mechanism for mode file injection

**What I couldn't determine:** The exact Python implementation of `hooks-mode`.

The module is declared in `behaviors/zerovector-crew.yaml:13-14`:
```yaml
hooks:
  - module: hooks-mode
    source: git+https://github.com/microsoft/amplifier-bundle-modes@main#subdirectory=modules/hooks-mode
```

This is an external git source. I could not read the source code. I can infer from `hooks-crew-gate/__init__.py` that it registers capabilities with names like `modes.active`, `modes.active_mode`, or `modes.state`. But the following are unknown:
- **Which event does hooks-mode listen to?** Likely `prompt:complete`, but could be `prompt:submit` or `session:start` or a combination.
- **Is the mode file content injected as ephemeral?** I infer yes (per `HookResult.ephemeral` docstring and the pattern of tool reminders), but cannot confirm.
- **At what priority does hooks-mode fire?** Affects ordering with hooks-fidelity-reporter (priority 50) and hooks-crew-gate (priority 10).
- **Does hooks-mode load the mode file from the bundle or from the coordinator's config?** It could read from the filesystem using a path registered via capability, or via the mention resolver.
- **What exactly is injected?** Just the markdown body, or does it include the frontmatter-parsed tool policy?

**Impact on findings:** Without this, I cannot fully trace the mode activation → fidelity instruction path in Step 8 of findings.md. The static context chain is complete and confirmed; the mode file injection step is inferred.

---

## 2. `tool-mode` internals — how mode state is set and surfaced

**What I couldn't determine:** The exact Python implementation of `tool-mode`.

The module is declared in `behaviors/zerovector-crew.yaml:19-22`:
```yaml
tools:
  - module: tool-mode
    source: git+https://github.com/microsoft/amplifier-bundle-modes@main#subdirectory=modules/tool-mode
    config:
      gate_policy: "warn"
```

Unknown:
- **What capability name does tool-mode register?** I know from `hooks-crew-gate` that it checks `modes.active`, `modes.active_mode`, and `modes.state`. Tool-mode must register one of these.
- **Does tool-mode fire any hook events when mode changes?** If it emits a custom event on mode activation, there might be additional context injection I missed.
- **Does tool-mode read mode files from the bundle or from a directory scan?** This determines which modes are "available" to the LLM.
- **How does `gate_policy: "warn"` affect tool invocation?** The config key is present but I don't know how tool-mode processes it.

---

## 3. The orchestrator — how it handles ephemeral HookResult from `HookRegistry.emit()`

**What I couldn't determine:** The exact code path from `HookRegistry.emit()` returning a `HookResult` with `ephemeral=True` and `context_injection` set, through to the orchestrator appending it to the current LLM call.

The orchestrator is declared via the session config and loaded dynamically. The orchestrator module (likely `loop-basic` or similar from amplifier-foundation) handles:
- Calling `coordinator.hooks.emit("prompt:complete", data)` 
- Receiving the merged HookResult
- Deciding how to forward the `context_injection` to the LLM provider call

I confirmed in `coordinator.py:411-413` that `ephemeral=True` skips `context.add_message()`. But the exact mechanism by which the orchestrator appends it to the **current turn's** message list before calling the LLM provider is not traceable without the orchestrator source.

**Specific open question:** Does the orchestrator pass `context_injection` as a message appended inline to `messages[]` for the current provider call? Or does it use a separate "ephemeral context" parameter? The `HookResult.ephemeral` docstring says "Orchestrator must append ephemeral injection to messages without storing in context" but the orchestrator implementation is in a separate module not read.

---

## 4. `modes:context/modes-instructions.md` — I couldn't resolve this reference

**What I couldn't determine:** The actual content of `modes:context/modes-instructions.md`, referenced in `behaviors/zerovector-crew.yaml:38`.

The namespace `modes:` refers to the `amplifier-bundle-modes` bundle (from `git+https://github.com/microsoft/amplifier-bundle-modes@main`). I could not access this file. Its content may contain additional instructions about how modes work that affect what the LLM sees. It could reinforce or contradict the mode file injection mechanism.

---

## 5. Whether `HookResult(action="continue", context_injection=...)` vs `HookResult(action="inject_context", ...)` are handled differently by the orchestrator

**What I noticed:** `hooks-fidelity-reporter` returns `action="continue"` with `context_injection` set (not `action="inject_context"`). The `HookRegistry.emit()` logic in `hooks.py:162-165` only collects results for the inject_context merge pathway when `result.action == "inject_context"`. 

With `action="continue"`, the registry returns the result directly from the loop. But the `coordinator.process_hook_result()` method at `coordinator.py:361` checks: `if result.action == "inject_context" and result.context_injection`.

**Open question:** If `hooks-fidelity-reporter` uses `action="continue"` (not `"inject_context"`), does `coordinator.process_hook_result()` actually handle the `context_injection` field? Looking at `coordinator.py:361-362`, it only handles injection when `action == "inject_context"`. Yet the `HookResult` dataclass does allow `context_injection` with `action="continue"`.

This is a potential gap: either (a) the orchestrator has its own separate pathway for handling `context_injection` on `continue`-action results, or (b) `hooks-fidelity-reporter` relies on the orchestrator — not the coordinator — to read `context_injection` directly from the returned `HookResult`. I cannot confirm which without the orchestrator source.

---

## 6. The `foundation:context/shared/common-system-base.md` content

**What I couldn't determine:** The actual content of `@foundation:context/shared/common-system-base.md`. This file is referenced in `bundle.md:118` and is loaded from the amplifier-foundation bundle. It presumably contains base system instructions shared across all foundation bundles, and may include additional context about tool usage, behaviors, or other capabilities.

---

## 7. Whether `Bundle.compose()` is actually called for included bundles during `load_bundle()`

**What I couldn't determine:** The discovery module implementation (`amplifier-foundation/amplifier_foundation/discovery/__init__.py` — only directory listing available). 

The bundle loading mechanism (how `includes:` entries in bundle.md are processed) was not directly traced. I inferred from `Bundle.compose()` and the `_parse_context()` function that composed bundles accumulate their context files. But the `load_bundle()` function and how it triggers `compose()` for included bundles is not confirmed.

**Suspicion:** The `includes` entries in the YAML frontmatter are processed by the bundle loader, which fetches each included bundle and calls `compose()` to merge them. The result is a single composed `Bundle` object with all context files. This is what I assumed in my trace, but I didn't read the `load_bundle()` implementation.

---

## 8. Behavior of `_merge_inject_context_results` when fidelity reporter uses `action="continue"`

If the ephemeral routing advice from `hooks-fidelity-reporter` and the mode body from `hooks-mode` both fire on the same `prompt:complete` event, the merge logic in `hooks.py:188-219` only applies to `inject_context` actions, not `continue` actions. The ordering and combination of these two injections in the final message the orchestrator receives is unknown without orchestrator source.

---

## Summary of Risk to Findings

| Unknown | Risk to core findings |
|---------|----------------------|
| hooks-mode internals | Medium — static chain fully confirmed; mode injection inferred |
| tool-mode internals | Low — mode state detection confirmed via hooks-crew-gate probe logic |
| Orchestrator ephemeral handling | Medium — coordinator.py confirms non-storage; exact orchestrator path unknown |
| modes:context/modes-instructions.md content | Low — doesn't affect the injection mechanism |
| action="continue" vs action="inject_context" handling | High — may affect whether fidelity routing advice actually reaches the LLM |
| common-system-base.md content | Low — doesn't affect mechanism |
| load_bundle() implementation | Low — composition behavior inferred from bundle.py |
