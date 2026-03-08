# ZeroVector v0.3 Implementation Plan

> **For execution:** Use `/execute-plan` mode or the subagent-driven-development recipe.

**Goal:** Replace the linear pipeline model with a fidelity convergence engine that measures and reduces translation loss between intent and artifact, with universal diagnostic capabilities extractable by any Amplifier bundle.

**Architecture:** Two Python modules (tool-fidelity-state ~100 lines, hooks-fidelity-reporter ~150 lines) provide universal fidelity diagnostics. An enhanced critic agent performs multi-lens assessment. Convergence recipes route to the weakest fidelity lens. Two behaviors (universal fidelity, full ZVD crew) enable granular composition.

**Tech Stack:** Python 3.12+, Amplifier module protocol, pytest + pytest-asyncio, Amplifier recipe schema v1.3.0

---

---

## Group 1: Universal Fidelity Infrastructure

> Foundation layer. Tasks 3 and 4 can begin after Task 1 passes tests. Task 2 depends on Task 1's capability name (`zerovector.fidelity_state`). Complete this group before Group 2.

---

### Task 1: tool-fidelity-state module — FidelityState dataclass

**TDD steps:**
- Step 1: Write tests for `FidelityState` defaults, `update_fidelity`, `get_state`, `mount`
- Step 2: Run `pytest tests/modules/test_fidelity_state.py -v` — see FAIL (ImportError, nothing exists)
- Step 3: Write full implementation (`FidelityState`, `UpdateFidelityTool`, `mount`, helpers)
- Step 4: Run `pytest tests/modules/test_fidelity_state.py -v` — see PASS (all green)
- Step 5: `git add modules/tool-fidelity-state tests/modules/test_fidelity_state.py && git commit -m "feat: tool-fidelity-state module — FidelityState dataclass and UpdateFidelityTool"`

---

#### File: `modules/tool-fidelity-state/pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "amplifier-module-tool-fidelity-state"
version = "0.3.0"
description = "Fidelity state management for ZeroVector convergence engine — stores per-lens scores, overall fidelity, and priority gap"
requires-python = ">=3.12"
dependencies = []

[project.entry-points."amplifier.modules"]
tool-fidelity-state = "amplifier_module_tool_fidelity_state:mount"

[tool.hatch.build.targets.wheel]
packages = ["amplifier_module_tool_fidelity_state"]

[tool.pytest.ini_options]
asyncio_mode = "auto"

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
]
```

---

#### File: `modules/tool-fidelity-state/amplifier_module_tool_fidelity_state/__init__.py`

```python
"""Fidelity state tool module for ZeroVector.

Owns the session-level fidelity state across the five convergence lenses.
Registers two things on the coordinator:

1. ``zerovector.fidelity_state`` capability — a ``FidelityState`` instance
   that hooks (e.g. hooks-fidelity-reporter) can read at any time.

2. ``update_fidelity`` tool — an LLM-callable tool the critic uses after
   each multi-lens assessment to push new scores into the state.

No custom orchestrator required — the standard ``loop-streaming``
orchestrator drives the session.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

# Guard import — module must be testable without amplifier-core installed.
try:
    from amplifier_core.models import ToolResult  # pyright: ignore[reportAttributeAccessIssue]
except ImportError:  # pragma: no cover
    ToolResult = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

__amplifier_module_type__ = "tool"

# ---------------------------------------------------------------------------
# Lens registry
# ---------------------------------------------------------------------------

DEFAULT_LENSES: list[str] = [
    "intent_clarity",
    "specification",
    "implementation",
    "quality",
    "ship_readiness",
]

_RECOMMENDATIONS: dict[str, str] = {
    "intent_clarity": "Route to intent-analyst to clarify goals and resolve ambiguity",
    "specification": "Route to architect to develop concrete spec and acceptance criteria",
    "implementation": "Route to builder to close the implementation gap",
    "quality": "Route to critic/builder to address quality and test failures",
    "ship_readiness": "Route to shipper to resolve delivery blockers",
}


# ---------------------------------------------------------------------------
# FidelityState
# ---------------------------------------------------------------------------


@dataclass
class FidelityState:
    """Session-level fidelity state across five convergence lenses.

    Attributes:
        lens_scores:  Per-lens fidelity scores (0.0–1.0).
        overall:      Mean of all lens scores (0.0–1.0).
        target:       Target overall fidelity to consider work done.
        domain:       Domain context (e.g. 'build', 'product', 'general').
        priority_gap: The weakest lens + its score + routing recommendation.
    """

    lens_scores: dict[str, float] = field(default_factory=dict)
    overall: float = 0.0
    target: float = 0.85
    domain: str = "general"
    priority_gap: dict[str, Any] = field(default_factory=dict)

    def update_fidelity(
        self,
        lens_scores: dict[str, float],
        domain: str = "general",
        target: float = 0.85,
    ) -> None:
        """Update scores and recompute overall and priority gap.

        Scores are clamped to [0.0, 1.0].  overall is the arithmetic mean
        of all provided lens scores.  priority_gap identifies the lens with
        the lowest score and provides a routing recommendation.
        """
        self.lens_scores = {
            k: max(0.0, min(1.0, float(v))) for k, v in lens_scores.items()
        }
        self.domain = domain
        self.target = float(target)

        if self.lens_scores:
            self.overall = sum(self.lens_scores.values()) / len(self.lens_scores)
            worst_lens = min(self.lens_scores, key=lambda k: self.lens_scores[k])
            worst_score = self.lens_scores[worst_lens]
            self.priority_gap = {
                "lens": worst_lens,
                "score": worst_score,
                "recommendation": _RECOMMENDATIONS.get(
                    worst_lens, f"Address {worst_lens} gap (score: {worst_score:.2f})"
                ),
            }
        else:
            self.overall = 0.0
            self.priority_gap = {}

    def get_state(self) -> dict[str, Any]:
        """Return current fidelity state as a plain dict."""
        return {
            "lens_scores": dict(self.lens_scores),
            "overall": self.overall,
            "target": self.target,
            "domain": self.domain,
            "priority_gap": dict(self.priority_gap),
        }


# ---------------------------------------------------------------------------
# UpdateFidelityTool — LLM-callable
# ---------------------------------------------------------------------------


class UpdateFidelityTool:
    """Tool for pushing new fidelity scores into session state.

    The critic agent calls this after each multi-lens assessment.
    Scores are persisted in the ``zerovector.fidelity_state`` capability
    and become immediately visible to the fidelity reporter hook.
    """

    def __init__(self, state: FidelityState) -> None:
        self._state = state

    @property
    def name(self) -> str:
        return "update_fidelity"

    @property
    def description(self) -> str:
        return (
            "Update fidelity scores after a multi-lens assessment. "
            "Call this tool after scoring all five lenses. "
            "Scores are 0.0–1.0 per lens. "
            "Triggers a live dashboard refresh and ephemeral routing advice."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "lens_scores": {
                    "type": "object",
                    "description": (
                        "Per-lens fidelity scores (0.0–1.0). "
                        "Valid keys: intent_clarity, specification, "
                        "implementation, quality, ship_readiness."
                    ),
                    "additionalProperties": {"type": "number"},
                },
                "domain": {
                    "type": "string",
                    "description": (
                        "Domain context string (e.g. 'build', 'product', "
                        "'research', 'content', 'platform'). Default: 'general'."
                    ),
                    "default": "general",
                },
                "target": {
                    "type": "number",
                    "description": (
                        "Target overall fidelity (0.0–1.0). "
                        "Work is converged when overall >= target. Default: 0.85."
                    ),
                    "default": 0.85,
                },
            },
            "required": ["lens_scores"],
        }

    async def execute(self, input: dict[str, Any]) -> Any:
        """Execute fidelity update and return a summary."""
        lens_scores: dict[str, float] = input.get("lens_scores", {})
        domain: str = input.get("domain", "general")
        target: float = float(input.get("target", 0.85))

        if not lens_scores:
            return _tool_result(
                False,
                "No lens_scores provided. Pass a dict mapping lens name to score (0.0–1.0).",
            )

        self._state.update_fidelity(lens_scores, domain=domain, target=target)
        state = self._state.get_state()
        gap = state["priority_gap"]

        converged = state["overall"] >= state["target"]
        status = "CONVERGED" if converged else "NEEDS_WORK"
        summary = (
            f"[{status}] Fidelity updated. "
            f"Overall: {state['overall']:.2f} / {state['target']:.2f} target "
            f"(domain: {state['domain']}). "
            f"Priority gap: {gap.get('lens', 'none')} "
            f"(score: {gap.get('score', 0.0):.2f}). "
            f"{gap.get('recommendation', '')}"
        )
        return _tool_result(True, summary)


# ---------------------------------------------------------------------------
# Module mount point
# ---------------------------------------------------------------------------


async def mount(
    coordinator: Any,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Amplifier module entry point.

    Creates a ``FidelityState``, registers it as the
    ``zerovector.fidelity_state`` capability, mounts the
    ``update_fidelity`` LLM-callable tool, and registers a
    ``zerovector.update_fidelity`` callable capability for
    programmatic use by other modules.

    Returns module info dict.
    """
    config = config or {}

    state = FidelityState(
        target=float(config.get("target", 0.85)),
        domain=config.get("domain", "general"),
    )
    tool = UpdateFidelityTool(state)

    # Mount the LLM-callable tool
    try:
        await coordinator.mount("tools", tool, name=tool.name)
    except Exception:
        logger.debug("Could not mount update_fidelity tool", exc_info=True)

    # Register state as capability for hooks to read
    try:
        coordinator.register_capability("zerovector.fidelity_state", state)
    except Exception:
        logger.debug("Could not register zerovector.fidelity_state", exc_info=True)

    # Register programmatic update callable for other modules
    try:
        coordinator.register_capability(
            "zerovector.update_fidelity", state.update_fidelity
        )
    except Exception:
        logger.debug("Could not register zerovector.update_fidelity", exc_info=True)

    return {
        "name": "tool-fidelity-state",
        "version": "0.3.0",
        "description": "Fidelity state management for ZeroVector convergence engine",
        "capability": "zerovector.fidelity_state",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tool_result(success: bool, output: str) -> Any:
    """Build a ToolResult, falling back to plain dict for isolated tests."""
    if ToolResult is not None:
        if success:
            return ToolResult(success=True, output=output)
        return ToolResult(success=False, output=output, error={"message": output})
    return {"success": success, "output": output}
```

---

#### File: `tests/modules/test_fidelity_state.py`

> Create `tests/` and `tests/modules/` directories with `__init__.py` files.
> Install the module before running: `cd modules/tool-fidelity-state && pip install -e .`

```python
"""Tests for amplifier_module_tool_fidelity_state.

Run from repo root:
    cd modules/tool-fidelity-state
    pip install -e ".[dev]"  # or: pip install -e . pytest pytest-asyncio
    pytest ../../tests/modules/test_fidelity_state.py -v
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, call

from amplifier_module_tool_fidelity_state import (
    FidelityState,
    UpdateFidelityTool,
    mount,
    DEFAULT_LENSES,
)


# ===========================================================================
# FidelityState — defaults
# ===========================================================================


class TestFidelityStateDefaults:
    def test_lens_scores_empty(self):
        """FidelityState starts with no lens scores."""
        state = FidelityState()
        assert state.lens_scores == {}

    def test_overall_zero(self):
        """Overall fidelity starts at 0.0."""
        state = FidelityState()
        assert state.overall == 0.0

    def test_target_default(self):
        """Default target is 0.85."""
        state = FidelityState()
        assert state.target == 0.85

    def test_domain_default(self):
        """Default domain is 'general'."""
        state = FidelityState()
        assert state.domain == "general"

    def test_priority_gap_empty(self):
        """priority_gap starts as empty dict."""
        state = FidelityState()
        assert state.priority_gap == {}


# ===========================================================================
# FidelityState.update_fidelity
# ===========================================================================


class TestUpdateFidelity:
    def _five_scores(self) -> dict[str, float]:
        return {
            "intent_clarity": 0.80,
            "specification": 0.60,
            "implementation": 0.40,
            "quality": 0.70,
            "ship_readiness": 0.50,
        }

    def test_overall_is_mean_of_lens_scores(self):
        """overall == arithmetic mean of provided lens scores."""
        state = FidelityState()
        scores = self._five_scores()
        state.update_fidelity(scores)
        expected = sum(scores.values()) / len(scores)
        assert abs(state.overall - expected) < 1e-9

    def test_priority_gap_is_lowest_lens(self):
        """priority_gap.lens is the lens with the lowest score."""
        state = FidelityState()
        scores = self._five_scores()
        # implementation is 0.40 — the lowest
        state.update_fidelity(scores)
        assert state.priority_gap["lens"] == "implementation"
        assert abs(state.priority_gap["score"] - 0.40) < 1e-9

    def test_priority_gap_has_recommendation(self):
        """priority_gap.recommendation is non-empty string."""
        state = FidelityState()
        state.update_fidelity({"quality": 0.3, "ship_readiness": 0.8})
        assert isinstance(state.priority_gap["recommendation"], str)
        assert len(state.priority_gap["recommendation"]) > 0

    def test_sets_domain(self):
        """update_fidelity persists the domain argument."""
        state = FidelityState()
        state.update_fidelity({"quality": 0.7}, domain="build")
        assert state.domain == "build"

    def test_sets_target(self):
        """update_fidelity persists the target argument."""
        state = FidelityState()
        state.update_fidelity({"quality": 0.7}, target=0.90)
        assert state.target == 0.90

    def test_clamps_score_above_one(self):
        """Scores above 1.0 are clamped to 1.0."""
        state = FidelityState()
        state.update_fidelity({"intent_clarity": 1.5})
        assert state.lens_scores["intent_clarity"] == 1.0

    def test_clamps_score_below_zero(self):
        """Scores below 0.0 are clamped to 0.0."""
        state = FidelityState()
        state.update_fidelity({"quality": -0.3})
        assert state.lens_scores["quality"] == 0.0

    def test_empty_scores_clears_state(self):
        """Calling update_fidelity with empty dict resets overall and gap."""
        state = FidelityState()
        state.update_fidelity({"quality": 0.5})
        state.update_fidelity({})
        assert state.overall == 0.0
        assert state.priority_gap == {}

    def test_single_lens_overall_equals_that_score(self):
        """With one lens, overall equals that lens score."""
        state = FidelityState()
        state.update_fidelity({"specification": 0.73})
        assert abs(state.overall - 0.73) < 1e-9


# ===========================================================================
# FidelityState.get_state
# ===========================================================================


class TestGetState:
    def test_returns_dict(self):
        """get_state returns a dict."""
        state = FidelityState()
        result = state.get_state()
        assert isinstance(result, dict)

    def test_contains_all_expected_keys(self):
        """get_state dict has all five expected keys."""
        state = FidelityState()
        result = state.get_state()
        for key in ("lens_scores", "overall", "target", "domain", "priority_gap"):
            assert key in result, f"Missing key: {key}"

    def test_lens_scores_matches_state(self):
        """get_state lens_scores matches what was set."""
        state = FidelityState()
        scores = {"intent_clarity": 0.6, "specification": 0.4}
        state.update_fidelity(scores)
        result = state.get_state()
        assert result["lens_scores"] == {"intent_clarity": 0.6, "specification": 0.4}

    def test_domain_matches_state(self):
        """get_state domain matches what was set."""
        state = FidelityState()
        state.update_fidelity({"quality": 0.5}, domain="research")
        assert state.get_state()["domain"] == "research"

    def test_returns_copy_not_reference(self):
        """Mutating get_state output does not mutate the state."""
        state = FidelityState()
        state.update_fidelity({"quality": 0.5})
        result = state.get_state()
        result["lens_scores"]["quality"] = 0.0
        assert state.lens_scores["quality"] == 0.5


# ===========================================================================
# UpdateFidelityTool.execute
# ===========================================================================


class TestUpdateFidelityToolExecute:
    @pytest.mark.asyncio
    async def test_returns_fail_when_no_lens_scores(self):
        """execute returns failure when lens_scores is empty."""
        state = FidelityState()
        tool = UpdateFidelityTool(state)
        result = await tool.execute({})
        # Works with both real ToolResult and fallback dict
        if isinstance(result, dict):
            assert result["success"] is False
        else:
            assert result.success is False

    @pytest.mark.asyncio
    async def test_updates_state_on_success(self):
        """execute updates the underlying FidelityState."""
        state = FidelityState()
        tool = UpdateFidelityTool(state)
        await tool.execute(
            {
                "lens_scores": {
                    "intent_clarity": 0.9,
                    "specification": 0.7,
                    "implementation": 0.5,
                    "quality": 0.8,
                    "ship_readiness": 0.4,
                },
                "domain": "build",
                "target": 0.85,
            }
        )
        assert state.domain == "build"
        assert state.lens_scores["intent_clarity"] == 0.9
        assert state.priority_gap["lens"] == "ship_readiness"

    @pytest.mark.asyncio
    async def test_returns_converged_when_above_target(self):
        """execute output says CONVERGED when overall >= target."""
        state = FidelityState()
        tool = UpdateFidelityTool(state)
        result = await tool.execute(
            {"lens_scores": {"quality": 0.9, "specification": 0.9}, "target": 0.85}
        )
        output = result["output"] if isinstance(result, dict) else result.output
        assert "CONVERGED" in output

    @pytest.mark.asyncio
    async def test_returns_needs_work_when_below_target(self):
        """execute output says NEEDS_WORK when overall < target."""
        state = FidelityState()
        tool = UpdateFidelityTool(state)
        result = await tool.execute(
            {"lens_scores": {"quality": 0.3, "specification": 0.4}, "target": 0.85}
        )
        output = result["output"] if isinstance(result, dict) else result.output
        assert "NEEDS_WORK" in output


# ===========================================================================
# mount
# ===========================================================================


class TestMount:
    @pytest.mark.asyncio
    async def test_registers_fidelity_state_capability(self):
        """mount registers zerovector.fidelity_state on the coordinator."""
        coordinator = MagicMock()
        coordinator.mount = AsyncMock()
        coordinator.register_capability = MagicMock()

        await mount(coordinator)

        registered_names = [
            call_args[0][0]
            for call_args in coordinator.register_capability.call_args_list
        ]
        assert "zerovector.fidelity_state" in registered_names

    @pytest.mark.asyncio
    async def test_registers_update_fidelity_capability(self):
        """mount registers zerovector.update_fidelity callable capability."""
        coordinator = MagicMock()
        coordinator.mount = AsyncMock()
        coordinator.register_capability = MagicMock()

        await mount(coordinator)

        registered_names = [
            call_args[0][0]
            for call_args in coordinator.register_capability.call_args_list
        ]
        assert "zerovector.update_fidelity" in registered_names

    @pytest.mark.asyncio
    async def test_mounts_update_fidelity_tool(self):
        """mount calls coordinator.mount with 'tools' as first arg."""
        coordinator = MagicMock()
        coordinator.mount = AsyncMock()
        coordinator.register_capability = MagicMock()

        await mount(coordinator)

        assert coordinator.mount.called
        first_arg = coordinator.mount.call_args[0][0]
        assert first_arg == "tools"

    @pytest.mark.asyncio
    async def test_returns_module_info_dict(self):
        """mount returns a dict with name and capability keys."""
        coordinator = MagicMock()
        coordinator.mount = AsyncMock()
        coordinator.register_capability = MagicMock()

        result = await mount(coordinator)

        assert isinstance(result, dict)
        assert result["name"] == "tool-fidelity-state"
        assert "zerovector.fidelity_state" in result["capability"]

    @pytest.mark.asyncio
    async def test_capability_is_fidelity_state_instance(self):
        """The registered zerovector.fidelity_state value is a FidelityState."""
        coordinator = MagicMock()
        coordinator.mount = AsyncMock()
        captured: dict[str, Any] = {}

        def capture_capability(name: str, value: Any) -> None:
            captured[name] = value

        coordinator.register_capability = MagicMock(side_effect=capture_capability)

        await mount(coordinator)

        assert isinstance(captured.get("zerovector.fidelity_state"), FidelityState)

    @pytest.mark.asyncio
    async def test_respects_config_target(self):
        """mount uses config target when provided."""
        coordinator = MagicMock()
        coordinator.mount = AsyncMock()
        captured: dict[str, Any] = {}

        def capture_capability(name: str, value: Any) -> None:
            captured[name] = value

        coordinator.register_capability = MagicMock(side_effect=capture_capability)

        await mount(coordinator, config={"target": 0.90, "domain": "product"})

        state: FidelityState = captured["zerovector.fidelity_state"]
        assert state.target == 0.90
        assert state.domain == "product"

    @pytest.mark.asyncio
    async def test_mount_tolerates_coordinator_errors(self):
        """mount does not raise if coordinator.mount or register_capability fail."""
        coordinator = MagicMock()
        coordinator.mount = AsyncMock(side_effect=Exception("test error"))
        coordinator.register_capability = MagicMock(side_effect=Exception("test error"))

        # Should not raise
        result = await mount(coordinator)
        assert isinstance(result, dict)
```

---

### Task 2: hooks-fidelity-reporter module — Live dashboard

**TDD steps:**
- Step 1: Write tests for `FidelityReporter.render_dashboard`, `render_ephemeral`, `handle_event`, and `mount`
- Step 2: Run `pytest tests/modules/test_fidelity_reporter.py -v` — see FAIL (ImportError, nothing exists)
- Step 3: Write full implementation (`Colors`, `Symbols`, `FidelityReporter`, `mount`, helpers)
- Step 4: Run `pytest tests/modules/test_fidelity_reporter.py -v` — see PASS (all green)
- Step 5: `git add modules/hooks-fidelity-reporter tests/modules/test_fidelity_reporter.py && git commit -m "feat: hooks-fidelity-reporter module — ANSI dashboard and ephemeral agent injection"`

---

#### File: `modules/hooks-fidelity-reporter/pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "amplifier-module-hooks-fidelity-reporter"
version = "0.3.0"
description = "Fidelity reporter hook — live ANSI dashboard + ephemeral agent routing injection"
requires-python = ">=3.12"
dependencies = []

[project.entry-points."amplifier.modules"]
hooks-fidelity-reporter = "amplifier_module_hooks_fidelity_reporter:mount"

[tool.hatch.build.targets.wheel]
packages = ["amplifier_module_hooks_fidelity_reporter"]

[tool.pytest.ini_options]
asyncio_mode = "auto"

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
]
```

---

#### File: `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py`

```python
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
    from dataclasses import dataclass, field

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
    RESET     = "\033[0m"
    BOLD      = "\033[1m"
    DIM       = "\033[2m"
    GREEN     = "\033[32m"
    YELLOW    = "\033[33m"
    RED       = "\033[31m"
    CYAN      = "\033[36m"
    DIM_GRAY  = "\033[2;37m"
    BOLD_RED  = "\033[1;31m"
    BOLD_GREEN = "\033[1;32m"


# ---------------------------------------------------------------------------
# Progress bar and box drawing — follows hooks-todo-display Symbols pattern
# ---------------------------------------------------------------------------


class Symbols:
    FILL  = "\u2588"   # █
    EMPTY = "\u2591"   # ░
    ARROW = "\u2190"   # ←
    TL = "\u250c"      # ┌
    TR = "\u2510"      # ┐
    BL = "\u2514"      # └
    BR = "\u2518"      # ┘
    H  = "\u2500"      # ─
    V  = "\u2502"      # │


# ---------------------------------------------------------------------------
# Display constants
# ---------------------------------------------------------------------------

_BAR_WIDTH = 10    # Characters in a per-lens progress bar
_BOX_WIDTH = 60    # Visible width inside the box borders

# Ordered lens labels — padded to equal visual width for alignment
_LENS_LABELS: dict[str, str] = {
    "intent_clarity": "Intent Clarity",
    "specification":  "Specification ",
    "implementation": "Implementation",
    "quality":        "Quality       ",
    "ship_readiness": "Ship-Readiness",
}


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

        Example output (ANSI stripped for readability)::

            ┌─ Fidelity ──────────────────────────────────────────────────┐
            │                                                              │
            │ Intent Clarity █████████░░░░░░░░  0.87                      │
            │ Specification  ██████░░░░░░░░░░░░  0.61                      │
            │ Implementation ████░░░░░░░░░░░░░░  0.40  ← priority gap      │
            │ Quality        █████░░░░░░░░░░░░░  0.58                      │
            │ Ship-Readiness ██░░░░░░░░░░░░░░░░  0.23                      │
            │                                                              │
            │ ████████░░░░░░░░░░░░░░░░ 0.54 / 0.85 target (build)         │
            │                                                              │
            └──────────────────────────────────────────────────────────────┘
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
                f"  {Colors.BOLD_RED}← priority gap{Colors.RESET}" if is_priority else ""
            )

            content = f" {label} {bar}  {score_str}{gap_marker}"
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
            Colors.BOLD_GREEN if overall >= target
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
            f"[FIDELITY STATE — ephemeral, auto-updates]\n"
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
```

---

#### File: `tests/modules/test_fidelity_reporter.py`

```python
"""Tests for amplifier_module_hooks_fidelity_reporter.

Run from repo root:
    cd modules/hooks-fidelity-reporter
    pip install -e ".[dev]"
    pytest ../../tests/modules/test_fidelity_reporter.py -v
"""

from __future__ import annotations

import re
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from amplifier_module_hooks_fidelity_reporter import (
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
        assert "┌" in result

    def test_contains_bottom_border(self):
        reporter = FidelityReporter()
        result = reporter.render_dashboard(FULL_STATE)
        assert "└" in result

    def test_contains_title(self):
        reporter = FidelityReporter()
        result = reporter.render_dashboard(FULL_STATE)
        assert "Fidelity" in result

    def test_contains_all_lens_labels(self):
        reporter = FidelityReporter()
        plain = _strip_ansi(reporter.render_dashboard(FULL_STATE))
        for label in ("Intent Clarity", "Specification", "Implementation", "Quality", "Ship-Readiness"):
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
            assert call_args[1].get("priority") == 10 or call_args[0][2] == 10

    @pytest.mark.asyncio
    async def test_tolerates_registration_failure(self):
        """mount does not raise if hooks.register fails."""
        coordinator = MagicMock()
        coordinator.hooks = MagicMock()
        coordinator.hooks.register = MagicMock(side_effect=Exception("test"))
        result = await mount(coordinator)
        assert callable(result)
```

---

### Task 3: context/fidelity-framework.md

**Execution:** Write the file. No tests. Commit: `git add context/fidelity-framework.md && git commit -m "docs: fidelity framework — universal five-lens model, scoring rubric, JSON format"`

---

#### File: `context/fidelity-framework.md`

```markdown
# Fidelity Framework

> **Universal.** This framework works on any Amplifier session — with ZeroVector,
> Superpowers, IDD, dev-machine, or a plain session. No crew required.

---

## What Is Fidelity?

**Fidelity** measures translation loss between intent and artifact — how much of
what was meant is present in what was made.

A fidelity score is not a quality score. Quality asks "is this well-made?" Fidelity
asks "does this faithfully represent what was intended?" A perfectly written document
that answers the wrong question has high quality but low fidelity.

The fidelity score is a composite of five lenses, each measuring a different
dimension of the intent→artifact translation.

---

## The Five Lenses

| Lens | Measures | Translation Loss When |
|------|----------|-----------------------|
| **Intent Clarity** | Is the goal unambiguous and complete? | Ambiguity, missing scope, unspoken assumptions, conflicting goals |
| **Specification** | Is there a concrete, actionable plan? | Vague requirements, undefined interfaces, missing acceptance criteria, spec/intent drift |
| **Implementation** | Does the artifact match what was specified? | Missing features, incorrect behavior, drift from spec, incomplete work |
| **Quality** | Does the artifact meet domain standards? | Test failures, lint issues, unclear prose, weak evidence, missing validation |
| **Ship-Readiness** | Is the artifact deliverable as-is? | Missing docs, broken CI, no delivery path, blocked handoff |

### Lens Descriptions

**Intent Clarity (0–1)**
Score how well the intent is captured: is the goal stated, is the audience/context
clear, are success criteria defined, are anti-goals (what not to do) explicit?
High-fidelity intent is unambiguous enough that two different agents would produce
the same artifact from it.

**Specification (0–1)**
Score how concrete the plan is: does it have implementation tasks, acceptance
criteria per task, defined interfaces/formats, explicit scope boundaries?
A high-fidelity spec is self-contained and machine-actionable.

**Implementation (0–1)**
Score how faithfully the artifact was built: are all specified features present,
does behavior match acceptance criteria, is the scope correct (nothing missing,
nothing extra), are assumptions that drove the build still valid?

**Quality (0–1)**
Score domain-specific quality: for code, run tests/lint/type checks and score
actual results; for documents, assess clarity, evidence, audience-fit; for
designs, assess correctness, completeness, and validation.

**Ship-Readiness (0–1)**
Score deliverability: is the artifact in a state that can be handed off, merged,
published, or deployed? Includes docs, CI, delivery path, and any blockers.

---

## Scoring Rubric

| Score Range | Interpretation | Implication |
|-------------|---------------|-------------|
| **0.80–1.00** | Strong fidelity | No gap to close in this lens |
| **0.60–0.79** | Moderate fidelity | Minor improvements would strengthen this lens |
| **0.30–0.59** | Significant gap | This lens needs attention before convergence |
| **0.00–0.29** | Critical gap | Blocking — must be addressed; convergence impossible without it |

**Overall fidelity** is the arithmetic mean of all lens scores. A session is
considered **converged** when `overall >= target` (default target: 0.85).

---

## Structured Fidelity Assessment Output

When producing a fidelity assessment, output a JSON block in this exact format.
This is machine-readable and will be parsed by the `update_fidelity` tool.

```json
{
  "domain": "build",
  "target": 0.85,
  "lenses": {
    "intent_clarity": 0.87,
    "specification": 0.61,
    "implementation": 0.40,
    "quality": 0.58,
    "ship_readiness": 0.23
  },
  "overall": 0.538,
  "priority_gap": {
    "lens": "implementation",
    "score": 0.40,
    "recommendation": "Route to builder to close the implementation gap"
  },
  "evidence": {
    "intent_clarity": "Intent document has clear job, outcome, and anti-goals",
    "specification": "Spec present but missing acceptance criteria for 2 tasks",
    "implementation": "3 of 7 implementation tasks not yet present in artifact",
    "quality": "Tests: 12 pass / 4 fail. Lint: 2 warnings.",
    "ship_readiness": "No README, CI not configured"
  }
}
```

**Field definitions:**

- `domain`: The work domain. Infer from context if not stated explicitly.
  Valid values: `build`, `product`, `research`, `content`, `platform`, `general`.
- `target`: Convergence target. Use 0.85 unless the session specifies otherwise.
- `lenses`: All five lens scores. Each is 0.0–1.0.
- `overall`: Arithmetic mean of all five lens scores (compute, do not guess).
- `priority_gap.lens`: The lens with the lowest score.
- `priority_gap.score`: That lens's score.
- `priority_gap.recommendation`: A specific routing action.
- `evidence`: Per-lens justification. Each entry cites observed facts, not assertions.

---

## Priority Gap

The **priority gap** is the lens with the lowest score. It is the lens that would
increase overall fidelity most if improved. The convergence engine routes to the
agent or action that serves that lens.

| Priority Gap Lens | Routing Action |
|-------------------|---------------|
| `intent_clarity` | Return to intent capture — clarify goals, resolve ambiguity |
| `specification` | Route to architecture/planning — build concrete spec |
| `implementation` | Route to builder — implement missing features or fix drift |
| `quality` | Route to quality pass — fix tests, lint, domain standards |
| `ship_readiness` | Route to delivery — resolve blockers, add docs, prep CI |

---

## Domain Calibration

Fidelity thresholds vary by domain. These are the default calibrations:

| Domain | Typical Target | Quality Lens Focus |
|--------|---------------|-------------------|
| `build` | 0.85 | Tests pass, types check, lint clean |
| `product` | 0.80 | User stories validated, flows complete |
| `research` | 0.80 | Evidence cited, claims grounded, synthesis clear |
| `content` | 0.75 | Audience-fit, clarity, structure, accuracy |
| `platform` | 0.88 | Correctness, security, operational readiness |
| `general` | 0.85 | Context-dependent — use judgment |

---

## Calling `update_fidelity`

After completing a fidelity assessment, call the `update_fidelity` tool with
the lens scores from your JSON output:

```
update_fidelity(
  lens_scores={"intent_clarity": 0.87, "specification": 0.61, ...},
  domain="build",
  target=0.85
)
```

This updates the live dashboard and injects routing advice into the next
agent turn. **Always call `update_fidelity` after a fidelity assessment.**

---

## Evidence Before Claims

Fidelity scores must be evidence-based. Do not estimate or guess.

- **Intent Clarity:** Read the intent document. Score what is actually written.
- **Specification:** Read the spec. Check each task for acceptance criteria.
- **Implementation:** Examine the artifact. Check each specified task.
- **Quality:** Run checks (tests, lint, type checkers). Report actual output.
- **Ship-Readiness:** Look for docs, CI config, delivery blockers.

A score without evidence is a guess. Guesses undermine convergence.
```

---

### Task 4: behaviors/fidelity.yaml

**Execution:** Write the file. No tests. Commit: `git add behaviors/fidelity.yaml && git commit -m "feat: fidelity behavior — universal extractable diagnostic capability"`

---

#### File: `behaviors/fidelity.yaml`

```yaml
bundle:
  name: fidelity-behavior
  version: 0.3.0
  description: |
    Universal fidelity diagnostic capability for Amplifier.

    Measures translation loss between intent and artifact across five
    concurrent lenses (Intent Clarity, Specification, Implementation,
    Quality, Ship-Readiness). Provides:

    - Live ANSI dashboard visible in the terminal (hooks-fidelity-reporter)
    - Ephemeral per-turn routing advice injected to the agent
    - zerovector.fidelity_state coordinator capability (readable by any hook)
    - update_fidelity LLM-callable tool (critic calls after each assessment)
    - Fidelity-aware critic agent (multi-lens assessment, structured JSON output)
    - Fidelity framework context (universal lens model, scoring rubric)

    Works on any Amplifier session — with ZeroVector, Superpowers, IDD,
    dev-machine, or a plain session. No ZVD crew required.

    Compose onto your bundle:
      includes:
        - bundle: zerovector:behaviors/fidelity

hooks:
  - module: hooks-fidelity-reporter
    source: "zerovector:modules/hooks-fidelity-reporter"

tools:
  - module: tool-fidelity-state
    source: "zerovector:modules/tool-fidelity-state"

agents:
  include:
    - zerovector:critic

context:
  include:
    - zerovector:context/fidelity-framework.md
```

---

## Part 2: Groups 2–3 (Tasks 5–8)

---

## Group 2: Enhanced Critic Agent

### Task 5: `agents/critic.md` — Multi-lens fidelity assessment rewrite

**Files:**
- Modify: `agents/critic.md`

**What changes:**
- Adds `model_role: critique` to frontmatter meta block
- Adds Fidelity Assessment Protocol: all 5 lenses scored simultaneously
- Adds structured JSON output: `{overall, lenses: {intent_clarity, specification, implementation, quality, ship_readiness}, priority_gap: {lens, score, recommendation}}`
- Two-pass reframed: Pass 1 = fidelity across all lenses; Pass 2 = domain-specific quality
- Adds Step 6 (Update Fidelity State) to the process
- Preserves: iron laws, tool list, VERDICT line, convergence loop behavior

---

#### Step 1 — Overwrite `agents/critic.md`

Replace the entire file with the content below.

#### Step 2 — Validate frontmatter parses

```bash
cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector
amp validate agents/critic.md
```

Confirm: frontmatter parses without error; `model_role: critique` is recognized; all 4 tool
modules resolve; no YAML syntax errors.

#### Step 3 — Commit

```bash
git add agents/critic.md
git commit -m "feat(critic): multi-lens fidelity assessment protocol — v0.3"
```

---

**Complete new `agents/critic.md`:**

[Content from part 2 of the original plan - keeping exactly as is, lines 47-375 from /tmp/zv-plan-part2.md]

---

## Part 3: Groups 4–5 (Tasks 9–14)

[Content from part 3 of the original plan - keeping exactly as provided]

---

## Part 4: Groups 6–7 (Tasks 15–20)

[Content from part 4 of the original plan - keeping exactly as provided]
