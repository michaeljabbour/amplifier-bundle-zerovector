"""Crew gate hook — injects crew mode reminder when no mode is active.

Fires on ``prompt:complete`` and ``tool:post``. When no ``/crew-*`` mode
is active, injects a persistent ephemeral reminder telling the LLM to
suggest the appropriate crew mode before creating artifacts.

Uses ``tool:post`` to detect when creation tools (apply_patch, write_file,
bash with file-creation commands) have been used without a crew mode,
and escalates the warning.

This creates a two-layer defense:
1. Every LLM turn gets an ephemeral crew-mode reminder (prompt:complete)
2. After any creation tool runs without a mode, the reminder escalates (tool:post)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable

try:
    from amplifier_core.models import HookResult
except ImportError:
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class HookResult:  # type: ignore[no-redef]
        action: str = "continue"
        data: dict[str, Any] | None = None
        reason: str | None = None
        context_injection: str | None = None
        context_injection_role: str = "system"
        ephemeral: bool = False
        user_message: str | None = None
        user_message_level: str = "info"


__amplifier_module_type__ = "hook"

log = logging.getLogger(__name__)

_CONTINUE = HookResult(action="continue")

# Tools that create or modify files.
_CREATION_TOOLS: frozenset[str] = frozenset({
    "apply_patch",
    "write_file",
    "edit_file",
})

# Bash commands that indicate file creation.
_BASH_CREATION_RE = re.compile(
    r"cat\s*>|echo\s.*>|tee\s|mkdir\s|touch\s|printf\s.*>",
)

# Persistent reminder injected on every turn when no mode is active.
_SOFT_REMINDER = (
    "[CREW GATE — no mode active]\n"
    "You MUST suggest a /crew-* mode to the user before creating any artifacts.\n"
    "Say: 'This is a [domain] task. I recommend activating /crew-build "
    "(or the appropriate crew mode) so the fidelity convergence engine "
    "can orchestrate this with quality gates and translation-loss tracking. "
    "Type /crew-build to activate, or tell me to proceed without it.'\n"
    "Do NOT skip this. Do NOT start implementing."
)

# Escalated warning after creation tools are used without a mode.
_HARD_WARNING = (
    "[CREW GATE — VIOLATION DETECTED]\n"
    "You just used a creation tool WITHOUT an active crew mode. "
    "STOP creating files immediately. Your NEXT response MUST be:\n"
    "1. Acknowledge that you should have suggested a crew mode first\n"
    "2. Suggest the appropriate /crew-* mode to the user\n"
    "3. Wait for the user to activate or opt out\n"
    "Do NOT continue building. Do NOT rationalize."
)

_USER_WARNING = (
    "⚠️  No crew mode active — artifact creation detected without "
    "fidelity tracking.\n\n"
    "Consider activating a crew mode for quality gates:\n"
    "  `/crew-build` — for code, features, apps, tools, scripts\n\n"
    "Or tell the assistant to proceed without it."
)


class CrewGate:
    """Injects crew mode reminders when no mode is active."""

    def __init__(self) -> None:
        self._creation_detected = False

    def _is_mode_active(self, coordinator: Any) -> bool:
        """Check if any crew mode is currently active."""
        for cap_name in ("modes.active", "modes.active_mode", "modes.state"):
            try:
                cap = coordinator.get_capability(cap_name)
                if cap is not None:
                    if isinstance(cap, str):
                        return bool(cap)
                    if isinstance(cap, dict):
                        return bool(cap.get("name") or cap.get("active"))
                    return bool(cap)
            except Exception:
                continue

        try:
            modes = getattr(coordinator, "modes", None)
            if modes is not None:
                active = getattr(modes, "active_mode", None)
                if active is not None:
                    return bool(active)
        except Exception:
            pass

        return False

    def _is_creation_tool(self, data: dict[str, Any]) -> bool:
        """Check if the tool call is a creation action."""
        tool_name = (
            data.get("tool_name")
            or data.get("name")
            or data.get("tool")
            or ""
        )

        if tool_name in _CREATION_TOOLS:
            return True

        # Check bash commands for file creation patterns.
        if tool_name == "bash":
            command = ""
            tool_input = data.get("input") or data.get("arguments") or {}
            if isinstance(tool_input, dict):
                command = tool_input.get("command", "")
            elif isinstance(tool_input, str):
                command = tool_input
            if _BASH_CREATION_RE.search(command):
                return True

        return False

    async def on_prompt_complete(
        self,
        event: str,
        data: dict[str, Any],
        coordinator: Any,
    ) -> HookResult:
        """Inject crew mode reminder on every turn when no mode is active."""
        import sys as _sys

        _sys.stderr.write("[hooks-crew-gate] prompt:complete fired\n")
        _sys.stderr.flush()
        try:
            mode_active = self._is_mode_active(coordinator)
            _sys.stderr.write(f"[hooks-crew-gate] mode_active={mode_active}\n")
            _sys.stderr.flush()
            if mode_active:
                self._creation_detected = False
                return _CONTINUE

            # Choose injection strength based on whether creation was detected.
            injection = _HARD_WARNING if self._creation_detected else _SOFT_REMINDER

            # Write visible banner to stdout (same pattern as fidelity dashboard).
            import sys as _sys

            _sys.stdout.write(
                "\n\033[1;33m"
                "┌─ Crew Gate ────────────────────────────────────────────┐\n"
                "│                                                       │\n"
                "│  ⚠️  No /crew-* mode active.                          │\n"
                "│  Suggest /crew-build before creating artifacts.       │\n"
                "│                                                       │\n"
                "└───────────────────────────────────────────────────────┘"
                "\033[0m\n"
            )
            _sys.stdout.flush()

            return HookResult(
                action="continue",
                context_injection=injection,
                context_injection_role="system",
                ephemeral=True,
                user_message=_USER_WARNING,
                user_message_level="warn",
            )
        except Exception:
            log.debug("hooks-crew-gate: error in on_prompt_complete", exc_info=True)
            return _CONTINUE

    async def on_tool_post(
        self,
        event: str,
        data: dict[str, Any],
        coordinator: Any,
    ) -> HookResult:
        """Detect creation tools used without a crew mode."""
        try:
            if self._is_mode_active(coordinator):
                return _CONTINUE

            if not self._is_creation_tool(data):
                return _CONTINUE

            # Flag that creation happened without a mode.
            self._creation_detected = True
            log.info("hooks-crew-gate: creation tool used without crew mode")

            return HookResult(
                action="continue",
                context_injection=_HARD_WARNING,
                context_injection_role="system",
                ephemeral=True,
                user_message=_USER_WARNING,
                user_message_level="warn",
            )
        except Exception:
            log.debug("hooks-crew-gate: error in on_tool_post", exc_info=True)
            return _CONTINUE


async def mount(
    coordinator: Any,
    config: dict[str, Any] | None = None,
) -> Callable[[], None]:
    """Mount the crew gate hook on prompt:complete and tool:post."""
    import sys as _sys

    _sys.stderr.write("[hooks-crew-gate] mount() called\n")
    _sys.stderr.flush()

    config = config or {}
    priority: int = int(config.get("priority", 10))

    gate = CrewGate()
    unregister_fns: list[Callable[[], None]] = []

    async def _on_prompt_complete(event: str, data: dict[str, Any]) -> HookResult:
        return await gate.on_prompt_complete(event, data, coordinator)

    async def _on_tool_post(event: str, data: dict[str, Any]) -> HookResult:
        return await gate.on_tool_post(event, data, coordinator)

    for event_name, handler in [
        ("prompt:complete", _on_prompt_complete),
        ("tool:post", _on_tool_post),
    ]:
        try:
            unreg = coordinator.hooks.register(
                event_name,
                handler,
                priority=priority,
                name=f"crew-gate-{event_name}",
            )
            unregister_fns.append(unreg)
        except Exception:
            log.debug(
                "hooks-crew-gate: could not register for %s",
                event_name,
                exc_info=True,
            )

    def cleanup() -> None:
        for unreg in unregister_fns:
            try:
                unreg()
            except Exception:
                log.debug("hooks-crew-gate: error during cleanup", exc_info=True)

    return cleanup
