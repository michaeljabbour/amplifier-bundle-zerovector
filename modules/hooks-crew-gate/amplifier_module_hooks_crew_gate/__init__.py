"""Mode gate hook — warns when creation tools are used without an active mode.

Fires on ``tool:post`` to detect when creation tools (apply_patch, write_file,
edit_file, bash with file-creation commands) are used without an active mode,
and injects a warning suggesting the user activate one.

The warning only appears when you actually create files without a mode —
not on every response.
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

# Warning injected when creation tools fire without a mode.
_CREATION_WARNING = (
    "[MODE GATE — creation without active mode]\n"
    "You just used a creation tool without an active mode. "
    "Before continuing, suggest a mode to the user:\n"
    "  /build — code, features, apps, tools\n"
    "  /architect — modules, APIs, infrastructure\n"
    "  /design — UX, specs, strategy\n"
    "  /write — docs, posts, guides\n"
    "  /investigate — analysis, research\n"
    "  /make — not sure yet\n"
    "Wait for the user to activate or opt out before creating more files."
)

_USER_WARNING = (
    "No mode active — file creation detected without quality tracking.\n\n"
    "Consider activating a mode:\n"
    "  /build  /architect  /design  /write  /investigate  /make\n\n"
    "Or tell the assistant to proceed without it."
)


class ModeGate:
    """Warns when creation tools are used without an active mode."""

    def _is_mode_active(self, coordinator: Any) -> bool:
        """Check if any mode is currently active."""
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

    async def on_tool_post(
        self,
        event: str,
        data: dict[str, Any],
        coordinator: Any,
    ) -> HookResult:
        """Warn when creation tools are used without an active mode."""
        try:
            if self._is_mode_active(coordinator):
                return _CONTINUE

            if not self._is_creation_tool(data):
                return _CONTINUE

            log.info("hooks-crew-gate: creation tool used without active mode")

            return HookResult(
                action="continue",
                context_injection=_CREATION_WARNING,
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
    """Mount the mode gate hook on tool:post."""
    config = config or {}
    priority: int = int(config.get("priority", 10))

    gate = ModeGate()

    async def _on_tool_post(event: str, data: dict[str, Any]) -> HookResult:
        return await gate.on_tool_post(event, data, coordinator)

    unreg = None
    try:
        unreg = coordinator.hooks.register(
            "tool:post",
            _on_tool_post,
            priority=priority,
            name="mode-gate-tool-post",
        )
    except Exception:
        log.debug("hooks-crew-gate: could not register for tool:post", exc_info=True)

    def cleanup() -> None:
        if unreg is not None:
            try:
                unreg()
            except Exception:
                log.debug("hooks-crew-gate: error during cleanup", exc_info=True)

    return cleanup
