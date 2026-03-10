# Cross-Cutting Patterns and Anti-Patterns

Patterns observed across 27+ artifacts in 6 repositories, comparing the todo tool and fidelity tool ecosystems.

---

## Reliability Patterns (What Makes Todo Work)

### Pattern 1: Pre-LLM Injection (Proactive Closed Loop)

**Where observed**: `hooks-todo-reminder` fires on `provider:request` (before LLM call); documented in `todo_reminder.md` lines 36-42.

**Frequency**: Every LLM call in every session using the foundation bundle. 100% of foundation-based sessions.

**Description**: The todo reminder hook fires on the `provider:request` event — the moment before the orchestrator sends the next message to the LLM. This means the LLM's context always contains current todo state at every decision point. The LLM cannot "forget" its todos because the system puts them right in front of it before every response.

**Implications**: This is the single most important reliability pattern. By injecting state proactively, the system takes responsibility for the LLM's awareness rather than relying on the LLM to query state. This converts the LLM from an "active rememberer" to a "passive receiver" — a fundamentally more reliable arrangement.

**Contrast with fidelity**: The fidelity hook fires on `tool:post` and `prompt:complete` (after actions), making it reactive. The LLM sees fidelity state only after it has already acted.

---

### Pattern 2: Multi-Layer Prompt Saturation

**Where observed**: 5 locations across 3 files:
- `common-agent-base.md:57` — "Use the todo tool to plan the task if required"
- `common-agent-base.md:143` — "IMPORTANT: Always use the todo tool"
- `foundation/bundle.md:80` — "IMPORTANT: For anything more than trivial tasks, make sure to use the todo tool"
- `foundation/bundle.md:154` — "VERY IMPORTANT: Make sure to use the actual todo tool... there is code behind use of the todo tool that is invisible to you"
- `hooks-todo-reminder` — Adaptive "hasn't been used recently" nudge

**Frequency**: 5 of 5 prompt reinforcement layers active (agent base, bundle instructions, hook injection).

**Description**: The todo tool is mentioned in progressively stronger language across the system prompt chain. The escalation from "use the todo tool to plan" to "VERY IMPORTANT: Make sure to use the actual todo tool... there is code behind it" creates weight through repetition and urgency. The final layer (hook nudge) catches any LLM that ignores the static prompts.

**Implications**: Prompt saturation overcomes the natural tendency of LLMs to weight instructions by recency and salience. A single mention can be lost in long system prompts. Five mentions across multiple sections cannot.

---

### Pattern 3: Foundation-Level Deployment (Always-On)

**Where observed**: `amplifier-foundation/bundle.md:11` — `- bundle: foundation:behaviors/todo-reminder`

**Frequency**: 100% of foundation-based sessions. The foundation bundle is included by every standard Amplifier deployment (confirmed in zerovector's `bundle.md:8`: `includes: - bundle: git+...amplifier-foundation@main`).

**Description**: The todo behavior is included at the foundation level, meaning every session gets both the tool and its reminder hook automatically. No opt-in required, no mode activation, no standing orders. It just works.

**Implications**: Foundation-level deployment eliminates the "forgot to enable" failure mode. The fidelity tool requires either the zerovector bundle or an explicit `includes: - bundle: zerovector:behaviors/fidelity` in a custom bundle. If the user doesn't use zerovector, they don't get fidelity tracking.

---

### Pattern 4: Behavioral Simplicity (3 Actions, Flat State)

**Where observed**: `todo.md` tool documentation; `todo-store.ts` StoreTodo interface.

**Frequency**: 3 actions (create/update/list), 3 statuses (pending/in_progress/completed), 2 key fields per item (content, activeForm).

**Description**: The todo tool's interface is minimal. `create` and `update` both take a full list replacement — no incremental mutations, no complex state transitions. The LLM sends the entire list every time, eliminating state synchronization bugs. The `list` action is a no-op that returns current state.

**Implications**: Low cognitive load for the LLM. The tool maps directly to natural task-tracking behavior. An LLM that can write a bulleted list can use this tool. Compare this to the fidelity tool's 5 lenses, 6 domains, and evidence requirements.

---

### Pattern 5: Adaptive Hook Behavior

**Where observed**: `todo_reminder.md` lines 38-42; hook behavior description.

**Frequency**: Every injection, with two modes:
- "Todo tool not used recently" → Gentle reminder + current state
- "Todo tool was used recently" → Just current state (no reminder)

**Description**: The hook adjusts its injection based on the `recent_tool_threshold` (default: 3 recent tool calls). If the LLM hasn't used the todo tool in the last 3 tool calls, the hook adds a nudge. If the LLM has been using it, the hook just shows state without nagging.

**Implications**: This prevents "reminder fatigue" while still catching cases where the LLM drifts away from using the tool. The fidelity hook has no adaptive behavior — it always renders the same dashboard regardless of recent usage.

---

### Pattern 6: Ephemeral + Append-to-Last-Tool-Result Placement

**Where observed**: `models.py` lines 145-220; `todo_reminder.md` lines 42, 100.

**Frequency**: Every injection is ephemeral (not stored in conversation history) and appended to the last tool result message.

**Description**: The todo hook uses `ephemeral=True` (not stored in history, preventing context bloat) and `append_to_last_tool_result=True` (contextually placed near the tool output the LLM is currently processing). This means the todo state appears "in flow" rather than as a disconnected system message.

**Implications**: Ephemeral injection prevents the conversation history from accumulating hundreds of todo state snapshots. Append-to-last-tool-result keeps the reminder contextually relevant. The fidelity hook also uses ephemeral injection but creates a new system message rather than appending.

---

## Anti-Patterns (What Makes Fidelity Less Reliable)

### Anti-Pattern 1: Open Feedback Loop (LLM Must Initiate Updates)

**Where observed**: `tool-fidelity-state/__init__.py` — `UpdateFidelityTool.execute()` requires explicit LLM call; `hooks-fidelity-reporter/__init__.py` — only reads state, never prompts for updates.

**Frequency**: 100% of fidelity sessions depend on LLM initiative to update state.

**Description**: The fidelity hook reads from `zerovector.fidelity_state` but nothing in the system prompts the LLM to call `update_fidelity`. The hook fires on `tool:post` and `prompt:complete` but only displays whatever was last written. If the LLM never calls `update_fidelity`, the dashboard stays at 0.0 forever.

**Implications**: This is the exact problem the todo tool was designed to solve — LLMs forgetting to maintain state during long turns. The fidelity system is vulnerable to the same drift that todo prevents.

---

### Anti-Pattern 2: Contradictory Ownership Instructions

**Where observed**: 
- `fidelity-framework.md:203` — "Always call update_fidelity after a fidelity assessment"
- `critic.md:263` — "You do NOT need to call update_fidelity yourself — the orchestrator handles this"

**Frequency**: The critic agent prompt (read by every critic delegation) contradicts the framework context (read by the coordinator).

**Description**: The critic agent is told the orchestrator handles `update_fidelity`. The framework tells whoever reads it to "always call update_fidelity." This creates ambiguity about who is responsible for pushing scores. If both think the other handles it, neither does.

**Implications**: Ownership ambiguity in distributed systems (even LLM agent systems) leads to missed updates. The todo tool has unambiguous ownership: the LLM writes, the hook reads, no delegation confusion.

---

### Anti-Pattern 3: High Cognitive Load per Update

**Where observed**: `fidelity-framework.md` scoring rubrics; `critic.md` two-pass protocol.

**Frequency**: Every fidelity update requires scoring 5 lenses (0-1 each) with per-lens evidence, identifying priority gap, selecting domain from 6 options, and optionally producing structured JSON.

**Description**: Updating fidelity state is expensive. The critic agent must perform a two-pass protocol (fidelity + domain quality), produce structured JSON, and provide evidence for every score. Compare this to `todo update` which just sends a list of items with statuses.

**Implications**: High update cost means fewer updates. The todo tool's low cost means updates happen naturally as part of the LLM's workflow. The fidelity tool's high cost means it only gets updated during formal assessment phases.

---

### Anti-Pattern 4: Post-Action Hook Timing

**Where observed**: `hooks-fidelity-reporter/__init__.py` — registers on `tool:post` and `prompt:complete`; priority 50.

**Frequency**: Hook fires after every tool call and prompt completion, but AFTER the action has already occurred.

**Description**: The fidelity hook's `prompt:complete` event fires after the LLM has already produced its response. The routing advice ("Route to builder to address implementation gaps") arrives after the LLM has already decided what to do. This is navigation advice that arrives after you've already turned.

**Implications**: Reactive feedback is less effective than proactive feedback. The todo hook's `provider:request` timing puts state in front of the LLM BEFORE it decides, which is when it matters most.

---

### Anti-Pattern 5: Single-Bundle Isolation

**Where observed**: `amplifier-bundle-zerovector/bundle.md` — fidelity only included via zerovector-crew behavior.

**Frequency**: 0% of non-zerovector sessions get fidelity tracking.

**Description**: The fidelity behavior is described as "universal" and "extractable" in the bundle description, but it is NOT included in the foundation bundle. Any session not using the zerovector bundle lacks fidelity tracking entirely. The `fidelity.yaml` behavior file says `includes: - bundle: zerovector:behaviors/fidelity` but this is a self-reference within the bundle.

**Implications**: A tool that only exists when you opt into a specific workflow can never achieve the reliability of a tool that exists everywhere. The fidelity tool's "universal" claim is aspirational, not actual.

---

### Anti-Pattern 6: No Adaptive Nudging

**Where observed**: `hooks-fidelity-reporter/__init__.py` handle_event method — no check for recent `update_fidelity` usage.

**Frequency**: Never. The hook never adjusts behavior based on how recently fidelity was updated.

**Description**: The fidelity hook always does the same thing: read state, render dashboard, inject ephemeral advice. It never says "Fidelity hasn't been assessed recently — consider running an assessment." Compare this to the todo hook's "The todo tool hasn't been used recently" nudge.

**Implications**: Without adaptive nudging, the fidelity tool relies entirely on static prompt instructions and LLM memory to trigger updates. Both are unreliable for long turns.

---

## Cross-Cutting Pattern: The Reliability Stack

Both tools use the same underlying Amplifier primitives (HookResult, ephemeral injection, capability registration). The difference is how many reliability layers they stack:

| Layer | Todo | Fidelity |
|-------|------|----------|
| 1. Foundation deployment | Yes | No |
| 2. Multiple prompt mentions | 5 | 1 (+1 contradictory) |
| 3. Pre-action hook timing | Yes (provider:request) | No (post-action) |
| 4. Closed feedback loop | Yes | No |
| 5. Adaptive nudging | Yes | No |
| 6. Low cognitive cost | Yes (flat list) | No (5 lenses + evidence) |
| 7. Multi-UI visibility | Yes (4 surfaces) | No (2 surfaces) |
| 8. State persistence | Yes (disk + localStorage) | No (memory only) |

**Todo activates 8 of 8 reliability layers. Fidelity activates 0 of 8.**

This isn't a matter of the fidelity tool being poorly built — its code is clean, well-tested (1,139 test lines), and well-documented. It's a matter of architectural decisions about where responsibility for maintaining tool engagement lies: with the system (todo) or with the LLM (fidelity).
