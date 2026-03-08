"""Fidelity reporter hook — live dashboard + ephemeral agent injection.

Fires on ``tool:post`` and ``prompt:complete``.  Reads the
``zerovector.fidelity_state`` capability and:

1. Writes an ANSI-formatted fidelity dashboard to ``sys.stdout``
   (visible in the terminal transcript — same technique as hooks-todo-display).

2. Returns a ``HookResult`` with:
   - ``user_message``: the dashboard text (for app-layer rendering)
   - ``context_injection`` + ``ephemeral=True``: plain-text routing advice
     that the agent sees but that does NOT accumulate in chat history.

Non-blocking observer: never modifies ``action`` away from ``continue``.
Priority 50 — runs after most other hooks have processed the event.
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Any, Callable

# Guard import — testable without amplifier-core installed.
try:
    from amplifier_core.models import HookResult  # pyright: ignore[reportAttributeAccessIssue]
except ImportError:  # pragma: no cover
    from dataclasses import dataclass

    @dataclass
    class HookResult:  # type: ignore[no-redef]
        """Minimal HookResult fallback for standalone/test environments."""

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

# Continue-only sentinel — avoids re-allocating on every no-op event.
_CONTINUE = HookResult(action="continue")

# ---------------------------------------------------------------------------
# ANSI codes — follows hooks-todo-display Colors class pattern
# ---------------------------------------------------------------------------


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    CYAN = "\033[36m"
    DIM_GRAY = "\033[2;37m"
    BOLD_RED = "\033[1;31m"
    BOLD_GREEN = "\033[1;32m"


# ---------------------------------------------------------------------------
# Progress bar and box drawing — follows hooks-todo-display Symbols pattern
# ---------------------------------------------------------------------------


class Symbols:
    FILL = "\u2588"  # █
    EMPTY = "\u2591"  # ░
    ARROW = "\u2190"  # ←
    TL = "\u250c"  # ┌
    TR = "\u2510"  # ┐
    BL = "\u2514"  # └
    BR = "\u2518"  # ┘
    H = "\u2500"  # ─
    V = "\u2502"  # │


# ---------------------------------------------------------------------------
# Display constants
# ---------------------------------------------------------------------------

_BAR_WIDTH = 10  # Characters in a per-lens progress bar
_BOX_WIDTH = 60  # Visible width inside the box borders

# Ordered lens labels — ljust'd at render time to the longest label width.
_LENS_LABELS: dict[str, str] = {
    "intent_clarity": "Intent Clarity",
    "specification": "Specification",
    "implementation": "Implementation",
    "quality": "Quality",
    "ship_readiness": "Ship-Readiness",
}
_LABEL_WIDTH = max(len(v) for v in _LENS_LABELS.values())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences to measure visible string length."""
    return re.sub(r"\033\[[0-9;]*m", "", text)


def _pad_to_width(line: str, width: int) -> str:
    """Pad *line* (which may contain ANSI codes) to *width* visible chars."""
    visible = len(_strip_ansi(line))
    return line + " " * max(0, width - visible)


def _score_color(score: float, is_priority: bool) -> str:
    """Return the ANSI color code appropriate for *score*."""
    if is_priority:
        return Colors.BOLD_RED
    if score >= 0.80:
        return Colors.GREEN
    if score >= 0.60:
        return Colors.CYAN
    if score >= 0.30:
        return Colors.YELLOW
    return Colors.RED


# ---------------------------------------------------------------------------
# FidelityReporter
# ---------------------------------------------------------------------------


class FidelityReporter:
    """Renders fidelity state as an ANSI dashboard and ephemeral agent context.

    Designed as a stateless renderer — all state comes from the ``state``
    dict passed to each method.  This makes it straightforward to test
    without a running coordinator.
    """

    # ------------------------------------------------------------------
    # render_dashboard — human-visible ANSI box
    # ------------------------------------------------------------------

    def render_dashboard(self, state: dict[str, Any]) -> str:
        """Render a bordered ANSI fidelity dashboard.

        Returns a multi-line string with box borders, per-lens progress
        bars, score values, a priority-gap marker, and an overall bar.
        """
        lens_scores: dict[str, float] = state.get("lens_scores", {})
        overall: float = state.get("overall", 0.0)
        target: float = state.get("target", 0.85)
        domain: str = state.get("domain", "general")
        priority_lens: str = state.get("priority_gap", {}).get("lens", "")

        lines: list[str] = []

        # Top border
        title = " Fidelity "
        top = (
            f"{Colors.DIM_GRAY}{Symbols.TL}{Symbols.H}{title}"
            f"{Symbols.H * (_BOX_WIDTH - len(title) - 1)}{Symbols.TR}{Colors.RESET}"
        )
        lines.append(top)
        lines.append(
            f"{Colors.DIM_GRAY}{Symbols.V}{Colors.RESET}"
            f"{' ' * _BOX_WIDTH}"
            f"{Colors.DIM_GRAY}{Symbols.V}{Colors.RESET}"
        )

        # Per-lens rows
        for lens_key, label in _LENS_LABELS.items():
            score = lens_scores.get(lens_key, 0.0)
            is_priority = lens_key == priority_lens
            color = _score_color(score, is_priority)

            filled = round(score * _BAR_WIDTH)
            empty = _BAR_WIDTH - filled
            bar = (
                f"{color}{Symbols.FILL * filled}{Colors.RESET}"
                f"{Colors.DIM_GRAY}{Symbols.EMPTY * empty}{Colors.RESET}"
            )
            score_str = f"{color}{score:.2f}{Colors.RESET}"
            gap_marker = (
                f"  {Colors.BOLD_RED}\u2190 priority gap{Colors.RESET}"
                if is_priority
                else ""
            )

            padded_label = label.ljust(_LABEL_WIDTH)
            content = f" {padded_label} {bar}  {score_str}{gap_marker}"
            padded = _pad_to_width(content, _BOX_WIDTH)
            lines.append(
                f"{Colors.DIM_GRAY}{Symbols.V}{Colors.RESET}{padded}{Colors.DIM_GRAY}{Symbols.V}{Colors.RESET}"
            )

        lines.append(
            f"{Colors.DIM_GRAY}{Symbols.V}{Colors.RESET}"
            f"{' ' * _BOX_WIDTH}"
            f"{Colors.DIM_GRAY}{Symbols.V}{Colors.RESET}"
        )

        # Overall progress bar (uses 40% of box width)
        bar_total = round(_BOX_WIDTH * 0.40)
        overall_filled = round(overall * bar_total)
        overall_empty = bar_total - overall_filled
        overall_color = (
            Colors.BOLD_GREEN
            if overall >= target
            else (Colors.YELLOW if overall >= 0.60 else Colors.RED)
        )
        overall_bar = (
            f"{overall_color}{Symbols.FILL * overall_filled}{Colors.RESET}"
            f"{Colors.DIM_GRAY}{Symbols.EMPTY * overall_empty}{Colors.RESET}"
        )
        summary_content = (
            f" {overall_bar} "
            f"{overall_color}{overall:.2f}{Colors.RESET}"
            f" / {target:.2f} target ({domain})"
        )
        padded_summary = _pad_to_width(summary_content, _BOX_WIDTH)
        lines.append(
            f"{Colors.DIM_GRAY}{Symbols.V}{Colors.RESET}{padded_summary}{Colors.DIM_GRAY}{Symbols.V}{Colors.RESET}"
        )
        lines.append(
            f"{Colors.DIM_GRAY}{Symbols.V}{Colors.RESET}"
            f"{' ' * _BOX_WIDTH}"
            f"{Colors.DIM_GRAY}{Symbols.V}{Colors.RESET}"
        )

        # Bottom border
        lines.append(
            f"{Colors.DIM_GRAY}{Symbols.BL}{Symbols.H * _BOX_WIDTH}{Symbols.BR}{Colors.RESET}"
        )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # render_ephemeral — plain-text routing advice for the agent
    # ------------------------------------------------------------------

    def render_ephemeral(self, state: dict[str, Any]) -> str:
        """Render plain-text fidelity summary for ephemeral agent injection.

        No ANSI codes — this goes into ``context_injection`` which may be
        processed by the LLM tokeniser or logged.
        """
        overall: float = state.get("overall", 0.0)
        target: float = state.get("target", 0.85)
        domain: str = state.get("domain", "general")
        gap: dict[str, Any] = state.get("priority_gap", {})
        gap_lens: str = gap.get("lens", "none")
        gap_score: float = gap.get("score", 0.0)
        recommendation: str = gap.get("recommendation", "")

        converged = overall >= target
        status = "CONVERGED" if converged else "NEEDS_WORK"

        return (
            f"[FIDELITY STATE \u2014 ephemeral, auto-updates]\n"
            f"Status: {status}\n"
            f"Overall: {overall:.2f} | Target: {target:.2f} (domain: {domain})\n"
            f"Priority gap: {gap_lens} ({gap_score:.2f})\n"
            f"Recommendation: {recommendation}"
        )

    # ------------------------------------------------------------------
    # handle_event — called by both tool:post and prompt:complete
    # ------------------------------------------------------------------

    async def handle_event(
        self,
        event: str,
        data: dict[str, Any],
        coordinator: Any,
    ) -> HookResult:
        """Read fidelity state, write dashboard, return dual-channel HookResult.

        Returns ``_CONTINUE`` (no-op) if:
        - ``zerovector.fidelity_state`` capability is not yet registered, or
        - The state has no lens scores yet (update_fidelity not called yet).

        Otherwise, writes the dashboard to stdout (terminal visibility) and
        returns ``HookResult`` with ephemeral context injection + user_message.
        """
        try:
            fidelity_state = coordinator.get_capability("zerovector.fidelity_state")
            if fidelity_state is None:
                return _CONTINUE

            state = fidelity_state.get_state()
            if not state.get("lens_scores"):
                return _CONTINUE

            # Write dashboard to stdout — same pattern as hooks-todo-display.
            dashboard = self.render_dashboard(state)
            sys.stdout.write(f"\n{dashboard}\n")
            sys.stdout.flush()

            # Build ephemeral routing advice (no ANSI, won't pollute history).
            ephemeral_text = self.render_ephemeral(state)

            return HookResult(
                action="continue",
                context_injection=ephemeral_text,
                context_injection_role="system",
                ephemeral=True,
                user_message=dashboard,
                user_message_level="info",
            )
        except Exception:
            log.debug(
                "hooks-fidelity-reporter: error in handle_event (event=%s)",
                event,
                exc_info=True,
            )
            return _CONTINUE


# ---------------------------------------------------------------------------
# Module mount point
# ---------------------------------------------------------------------------


async def mount(
    coordinator: Any,
    config: dict[str, Any] | None = None,
) -> Callable[[], None]:
    """Mount the fidelity reporter hook.

    Registers ``handle_event`` on ``tool:post`` and ``prompt:complete``
    at ``priority`` (default 50).

    Returns a cleanup callable that unregisters all handlers.
    """
    config = config or {}
    priority: int = int(config.get("priority", 50))

    reporter = FidelityReporter()
    unregister_fns: list[Callable[[], None]] = []

    async def _on_tool_post(event: str, data: dict[str, Any]) -> HookResult:
        return await reporter.handle_event(event, data, coordinator)

    async def _on_prompt_complete(event: str, data: dict[str, Any]) -> HookResult:
        return await reporter.handle_event(event, data, coordinator)

    for event_name, handler in [
        ("tool:post", _on_tool_post),
        ("prompt:complete", _on_prompt_complete),
    ]:
        try:
            unreg = coordinator.hooks.register(
                event_name,
                handler,
                priority=priority,
                name=f"fidelity-reporter-{event_name}",
            )
            unregister_fns.append(unreg)
        except Exception:
            log.debug(
                "hooks-fidelity-reporter: could not register for %s",
                event_name,
                exc_info=True,
            )

    def cleanup() -> None:
        for unreg in unregister_fns:
            try:
                unreg()
            except Exception:
                log.debug(
                    "hooks-fidelity-reporter: error during cleanup", exc_info=True
                )

    return cleanup
