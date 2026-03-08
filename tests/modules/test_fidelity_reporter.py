"""Tests for amplifier_module_hooks_fidelity_reporter.

Run from repo root:
    cd modules/hooks-fidelity-reporter
    pip install -e ".[dev]"
    pytest ../../tests/modules/test_fidelity_reporter.py -v
"""

from __future__ import annotations

import os
import re
import sys

import pytest
from unittest.mock import MagicMock, patch

# Ensure the module is importable without pip install -e
_mod_dir = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    os.pardir,
    "modules",
    "hooks-fidelity-reporter",
)
if os.path.isdir(_mod_dir) and os.path.abspath(_mod_dir) not in sys.path:
    sys.path.insert(0, os.path.abspath(_mod_dir))

from amplifier_module_hooks_fidelity_reporter import (  # noqa: E402
    FidelityReporter,
    mount,
    _strip_ansi,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FULL_STATE: dict = {
    "lens_scores": {
        "intent_clarity": 0.87,
        "specification": 0.61,
        "implementation": 0.40,
        "quality": 0.58,
        "ship_readiness": 0.23,
    },
    "overall": 0.538,
    "target": 0.85,
    "domain": "build",
    "priority_gap": {
        "lens": "ship_readiness",
        "score": 0.23,
        "recommendation": "Route to shipper to resolve delivery blockers",
    },
}

EMPTY_STATE: dict = {
    "lens_scores": {},
    "overall": 0.0,
    "target": 0.85,
    "domain": "general",
    "priority_gap": {},
}


# ===========================================================================
# _strip_ansi helper
# ===========================================================================


def test_strip_ansi_removes_escape_sequences():
    text = "\033[1;32mHello\033[0m"
    assert _strip_ansi(text) == "Hello"


def test_strip_ansi_leaves_plain_text():
    assert _strip_ansi("plain text") == "plain text"


# ===========================================================================
# FidelityReporter.render_dashboard
# ===========================================================================


class TestRenderDashboard:
    def test_returns_string(self):
        reporter = FidelityReporter()
        result = reporter.render_dashboard(FULL_STATE)
        assert isinstance(result, str)

    def test_contains_top_border(self):
        reporter = FidelityReporter()
        result = reporter.render_dashboard(FULL_STATE)
        assert "\u250c" in result

    def test_contains_bottom_border(self):
        reporter = FidelityReporter()
        result = reporter.render_dashboard(FULL_STATE)
        assert "\u2514" in result

    def test_contains_title(self):
        reporter = FidelityReporter()
        result = reporter.render_dashboard(FULL_STATE)
        assert "Fidelity" in result

    def test_contains_all_lens_labels(self):
        reporter = FidelityReporter()
        plain = _strip_ansi(reporter.render_dashboard(FULL_STATE))
        for label in (
            "Intent Clarity",
            "Specification",
            "Implementation",
            "Quality",
            "Ship-Readiness",
        ):
            assert label in plain, f"Missing label: {label}"

    def test_contains_priority_gap_marker(self):
        reporter = FidelityReporter()
        plain = _strip_ansi(reporter.render_dashboard(FULL_STATE))
        assert "priority gap" in plain

    def test_contains_all_five_scores(self):
        reporter = FidelityReporter()
        plain = _strip_ansi(reporter.render_dashboard(FULL_STATE))
        assert "0.87" in plain
        assert "0.61" in plain
        assert "0.40" in plain
        assert "0.58" in plain
        assert "0.23" in plain

    def test_contains_overall_and_target(self):
        reporter = FidelityReporter()
        plain = _strip_ansi(reporter.render_dashboard(FULL_STATE))
        # overall ~0.538 should appear as 0.54
        assert "0.54" in plain or "0.53" in plain or "0.538" in plain
        assert "0.85" in plain

    def test_contains_domain(self):
        reporter = FidelityReporter()
        plain = _strip_ansi(reporter.render_dashboard(FULL_STATE))
        assert "build" in plain

    def test_renders_without_error_for_empty_state(self):
        reporter = FidelityReporter()
        result = reporter.render_dashboard(EMPTY_STATE)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_multiline_output(self):
        reporter = FidelityReporter()
        result = reporter.render_dashboard(FULL_STATE)
        lines = result.split("\n")
        # At minimum: top, empty, 5 lenses, empty, overall, empty, bottom = 11
        assert len(lines) >= 11


# ===========================================================================
# FidelityReporter.render_ephemeral
# ===========================================================================


class TestRenderEphemeral:
    def test_returns_string(self):
        reporter = FidelityReporter()
        result = reporter.render_ephemeral(FULL_STATE)
        assert isinstance(result, str)

    def test_no_ansi_codes(self):
        reporter = FidelityReporter()
        result = reporter.render_ephemeral(FULL_STATE)
        assert not re.search(r"\033\[", result), "Should contain no ANSI codes"

    def test_contains_fidelity_state_header(self):
        reporter = FidelityReporter()
        result = reporter.render_ephemeral(FULL_STATE)
        assert "[FIDELITY STATE" in result

    def test_contains_status(self):
        reporter = FidelityReporter()
        result = reporter.render_ephemeral(FULL_STATE)
        # overall 0.538 < target 0.85 → NEEDS_WORK
        assert "NEEDS_WORK" in result

    def test_contains_converged_when_above_target(self):
        reporter = FidelityReporter()
        converged_state = {**FULL_STATE, "overall": 0.90, "target": 0.85}
        result = reporter.render_ephemeral(converged_state)
        assert "CONVERGED" in result

    def test_contains_overall_score(self):
        reporter = FidelityReporter()
        result = reporter.render_ephemeral(FULL_STATE)
        # 0.538 → appears as 0.54 or 0.53
        assert "0.5" in result

    def test_contains_target(self):
        reporter = FidelityReporter()
        result = reporter.render_ephemeral(FULL_STATE)
        assert "0.85" in result

    def test_contains_priority_gap_lens(self):
        reporter = FidelityReporter()
        result = reporter.render_ephemeral(FULL_STATE)
        assert "ship_readiness" in result

    def test_contains_recommendation(self):
        reporter = FidelityReporter()
        result = reporter.render_ephemeral(FULL_STATE)
        assert "shipper" in result.lower() or "ship" in result.lower()

    def test_contains_domain(self):
        reporter = FidelityReporter()
        result = reporter.render_ephemeral(FULL_STATE)
        assert "build" in result


# ===========================================================================
# FidelityReporter.handle_event
# ===========================================================================


def _make_coordinator(state_dict: dict | None = None) -> MagicMock:
    """Build a mock coordinator with optional fidelity state."""
    coordinator = MagicMock()
    if state_dict is None:
        coordinator.get_capability.return_value = None
    else:
        mock_fs = MagicMock()
        mock_fs.get_state.return_value = state_dict
        coordinator.get_capability.return_value = mock_fs
    return coordinator


class TestHandleEvent:
    @pytest.mark.asyncio
    async def test_returns_continue_when_no_capability(self):
        reporter = FidelityReporter()
        coordinator = _make_coordinator(None)
        result = await reporter.handle_event("tool:post", {}, coordinator)
        assert result.action == "continue"

    @pytest.mark.asyncio
    async def test_returns_continue_when_lens_scores_empty(self):
        reporter = FidelityReporter()
        coordinator = _make_coordinator(EMPTY_STATE)
        result = await reporter.handle_event("tool:post", {}, coordinator)
        assert result.action == "continue"

    @pytest.mark.asyncio
    async def test_writes_to_stdout_when_state_present(self):
        reporter = FidelityReporter()
        coordinator = _make_coordinator(FULL_STATE)
        with patch.object(sys, "stdout") as mock_stdout:
            await reporter.handle_event("tool:post", {}, coordinator)
        assert mock_stdout.write.called

    @pytest.mark.asyncio
    async def test_returns_hook_result_with_action_continue(self):
        reporter = FidelityReporter()
        coordinator = _make_coordinator(FULL_STATE)
        with patch("sys.stdout"):
            result = await reporter.handle_event("tool:post", {}, coordinator)
        assert result.action == "continue"

    @pytest.mark.asyncio
    async def test_context_injection_is_set(self):
        reporter = FidelityReporter()
        coordinator = _make_coordinator(FULL_STATE)
        with patch("sys.stdout"):
            result = await reporter.handle_event("tool:post", {}, coordinator)
        assert result.context_injection is not None
        assert len(result.context_injection) > 0

    @pytest.mark.asyncio
    async def test_ephemeral_is_true(self):
        reporter = FidelityReporter()
        coordinator = _make_coordinator(FULL_STATE)
        with patch("sys.stdout"):
            result = await reporter.handle_event("prompt:complete", {}, coordinator)
        assert result.ephemeral is True

    @pytest.mark.asyncio
    async def test_user_message_is_set(self):
        reporter = FidelityReporter()
        coordinator = _make_coordinator(FULL_STATE)
        with patch("sys.stdout"):
            result = await reporter.handle_event("tool:post", {}, coordinator)
        assert result.user_message is not None

    @pytest.mark.asyncio
    async def test_context_injection_has_no_ansi(self):
        reporter = FidelityReporter()
        coordinator = _make_coordinator(FULL_STATE)
        with patch("sys.stdout"):
            result = await reporter.handle_event("tool:post", {}, coordinator)
        assert not re.search(r"\033\[", result.context_injection or "")

    @pytest.mark.asyncio
    async def test_returns_continue_on_coordinator_error(self):
        """handle_event never raises — returns _CONTINUE on any exception."""
        reporter = FidelityReporter()
        coordinator = MagicMock()
        coordinator.get_capability.side_effect = RuntimeError("boom")
        result = await reporter.handle_event("tool:post", {}, coordinator)
        assert result.action == "continue"


# ===========================================================================
# mount
# ===========================================================================


def _make_hooks_coordinator() -> MagicMock:
    coordinator = MagicMock()
    coordinator.hooks = MagicMock()
    coordinator.hooks.register = MagicMock(return_value=lambda: None)
    return coordinator


class TestMount:
    @pytest.mark.asyncio
    async def test_registers_tool_post_handler(self):
        coordinator = _make_hooks_coordinator()
        await mount(coordinator)
        events = [c[0][0] for c in coordinator.hooks.register.call_args_list]
        assert "tool:post" in events

    @pytest.mark.asyncio
    async def test_registers_prompt_complete_handler(self):
        coordinator = _make_hooks_coordinator()
        await mount(coordinator)
        events = [c[0][0] for c in coordinator.hooks.register.call_args_list]
        assert "prompt:complete" in events

    @pytest.mark.asyncio
    async def test_returns_callable_cleanup(self):
        coordinator = _make_hooks_coordinator()
        result = await mount(coordinator)
        assert callable(result)

    @pytest.mark.asyncio
    async def test_cleanup_does_not_raise(self):
        coordinator = _make_hooks_coordinator()
        cleanup = await mount(coordinator)
        cleanup()  # Must not raise

    @pytest.mark.asyncio
    async def test_respects_priority_config(self):
        coordinator = _make_hooks_coordinator()
        await mount(coordinator, config={"priority": 10})
        # Each call's kwargs should include priority=10
        for call_args in coordinator.hooks.register.call_args_list:
            assert call_args.kwargs["priority"] == 10

    @pytest.mark.asyncio
    async def test_tolerates_registration_failure(self):
        """mount does not raise if hooks.register fails."""
        coordinator = MagicMock()
        coordinator.hooks = MagicMock()
        coordinator.hooks.register = MagicMock(side_effect=Exception("test"))
        result = await mount(coordinator)
        assert callable(result)
