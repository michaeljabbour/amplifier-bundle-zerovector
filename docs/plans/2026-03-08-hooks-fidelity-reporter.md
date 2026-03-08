# Hooks-Fidelity-Reporter Module Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

> **QUALITY REVIEW NOTE:** The automated quality review loop exhausted after
> 3 iterations without formal approval signal, despite the final verdict being
> **APPROVED** with 38/38 tests passing, clean ruff format/lint, and zero
> critical or important issues. The two Pyright errors are known false positives
> (guard-import pattern and dynamic sys.path in tests). Human reviewer: please
> verify the implementation meets acceptance criteria before merging. The final
> review verdict and all evidence are included at the bottom of this plan.

**Goal:** Create a Python hook module that fires on `tool:post` and `prompt:complete`, reads fidelity state, renders a live ANSI terminal dashboard, and injects ephemeral plain-text routing advice into agent context.

**Architecture:** Single-file Amplifier hook module (`__init__.py`) containing a stateless `FidelityReporter` class with three methods: `render_dashboard` (ANSI box), `render_ephemeral` (plain-text for LLM), and `handle_event` (async coordinator bridge). An async `mount()` entry point registers the handler on two events and returns a cleanup callable. Guard-imported `HookResult` with frozen-dataclass fallback allows the module to work with or without `amplifier_core` installed.

**Tech Stack:** Python 3.11+, dataclasses, ANSI escape codes, hatchling build, pytest + pytest-asyncio for testing.

**Dependency:** Requires task-1 (`tool-fidelity-state`) to be complete — reads the `zerovector.fidelity_state` capability registered by that module.

---

## File Map

| File | Action |
|------|--------|
| `modules/hooks-fidelity-reporter/pyproject.toml` | Create |
| `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py` | Create |
| `tests/modules/test_fidelity_reporter.py` | Create |

---

### Task 1: Scaffold the module directory and pyproject.toml

**Files:**
- Create: `modules/hooks-fidelity-reporter/pyproject.toml`
- Create: `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py` (empty placeholder)

**Step 1: Create pyproject.toml**

Create `modules/hooks-fidelity-reporter/pyproject.toml` with this exact content:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "amplifier-module-hooks-fidelity-reporter"
version = "0.3.0"
description = "Fidelity reporter hook — live ANSI dashboard + ephemeral agent routing injection"
requires-python = ">=3.11"
dependencies = []

[project.entry-points."amplifier.modules"]
hooks-fidelity-reporter = "amplifier_module_hooks_fidelity_reporter:mount"

[tool.hatch.build.targets.wheel]
packages = ["amplifier_module_hooks_fidelity_reporter"]

[tool.pytest.ini_options]
asyncio_mode = "auto"

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
]
```

**Step 2: Create empty __init__.py placeholder**

Create `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py` with:

```python
"""Fidelity reporter hook — live dashboard + ephemeral agent injection."""
```

**Step 3: Verify structure exists**

Run: `ls -la modules/hooks-fidelity-reporter/ && ls -la modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/`

Expected: Both directories exist with the files created above.

**Step 4: Commit scaffold**

```
git add modules/hooks-fidelity-reporter/
git commit -m "chore: scaffold hooks-fidelity-reporter module directory and pyproject.toml"
```

---

### Task 2: Write test infrastructure and test_strip_ansi tests (2 tests)

**Files:**
- Create: `tests/modules/test_fidelity_reporter.py`

**Step 1: Write the test file with imports, fixtures, and strip_ansi tests**

Create `tests/modules/test_fidelity_reporter.py` with:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m pytest tests/modules/test_fidelity_reporter.py -v`

Expected: FAIL — `ImportError` because `FidelityReporter`, `mount`, and `_strip_ansi` don't exist yet in the placeholder `__init__.py`.

**Step 3: Commit tests**

```
git add tests/modules/test_fidelity_reporter.py
git commit -m "test: add test infrastructure and strip_ansi tests for fidelity-reporter"
```

---

### Task 3: Implement Colors, Symbols, constants, and helper functions

**Files:**
- Modify: `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py`

**Step 1: Write the guard import, constants, and helpers**

Replace the entire content of `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py` with:

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
    from dataclasses import dataclass

    @dataclass(frozen=True)
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
```

**Step 2: Run the strip_ansi tests to verify they pass**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m pytest tests/modules/test_fidelity_reporter.py::test_strip_ansi_removes_escape_sequences tests/modules/test_fidelity_reporter.py::test_strip_ansi_leaves_plain_text -v`

Expected: 2 PASSED (the import now works, and the helper functions are correct). The other tests will still fail because `FidelityReporter` and `mount` are not yet defined.

**Step 3: Commit**

```
git add modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py
git commit -m "feat: add Colors, Symbols, constants, and helper functions for fidelity-reporter"
```

---

### Task 4: Write TestRenderDashboard tests (11 tests)

**Files:**
- Modify: `tests/modules/test_fidelity_reporter.py`

**Step 1: Append TestRenderDashboard class to the test file**

Add the following at the end of `tests/modules/test_fidelity_reporter.py`:

```python
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
        # overall ~0.538 -> f"{0.538:.2f}" deterministically produces "0.54"
        assert "0.54" in plain
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
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m pytest tests/modules/test_fidelity_reporter.py::TestRenderDashboard -v`

Expected: FAIL — `FidelityReporter` class does not exist yet.

**Step 3: Commit tests**

```
git add tests/modules/test_fidelity_reporter.py
git commit -m "test: add TestRenderDashboard tests (11 tests) for fidelity-reporter"
```

---

### Task 5: Implement FidelityReporter.render_dashboard

**Files:**
- Modify: `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py`

**Step 1: Add the FidelityReporter class with render_dashboard method**

Append the following to the end of `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py`:

```python
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
```

**Step 2: Run TestRenderDashboard to verify all 11 tests pass**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m pytest tests/modules/test_fidelity_reporter.py::TestRenderDashboard -v`

Expected: 11 PASSED.

**Step 3: Commit**

```
git add modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py
git commit -m "feat: implement FidelityReporter.render_dashboard with ANSI box rendering"
```

---

### Task 6: Write TestRenderEphemeral tests (9 tests)

**Files:**
- Modify: `tests/modules/test_fidelity_reporter.py`

**Step 1: Append TestRenderEphemeral class to the test file**

Add the following at the end of `tests/modules/test_fidelity_reporter.py`:

```python
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
        # 0.538 → f"{0.538:.2f}" deterministically produces "0.54"
        assert "0.54" in result

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
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m pytest tests/modules/test_fidelity_reporter.py::TestRenderEphemeral -v`

Expected: FAIL — `render_ephemeral` method does not exist yet.

**Step 3: Commit tests**

```
git add tests/modules/test_fidelity_reporter.py
git commit -m "test: add TestRenderEphemeral tests (9 tests) for fidelity-reporter"
```

---

### Task 7: Implement FidelityReporter.render_ephemeral

**Files:**
- Modify: `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py`

**Step 1: Add render_ephemeral method to FidelityReporter class**

Inside the `FidelityReporter` class, after the `render_dashboard` method, add:

```python
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
```

**Step 2: Run TestRenderEphemeral to verify all 9 tests pass**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m pytest tests/modules/test_fidelity_reporter.py::TestRenderEphemeral -v`

Expected: 9 PASSED.

**Step 3: Also verify dashboard tests still pass**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m pytest tests/modules/test_fidelity_reporter.py::TestRenderDashboard tests/modules/test_fidelity_reporter.py::TestRenderEphemeral -v`

Expected: 20 PASSED (11 + 9).

**Step 4: Commit**

```
git add modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py
git commit -m "feat: implement FidelityReporter.render_ephemeral with plain-text output"
```

---

### Task 8: Write TestHandleEvent tests (9 tests)

**Files:**
- Modify: `tests/modules/test_fidelity_reporter.py`

**Step 1: Append mock helper and TestHandleEvent class**

Add the following at the end of `tests/modules/test_fidelity_reporter.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m pytest tests/modules/test_fidelity_reporter.py::TestHandleEvent -v`

Expected: FAIL — `handle_event` method does not exist yet.

**Step 3: Commit tests**

```
git add tests/modules/test_fidelity_reporter.py
git commit -m "test: add TestHandleEvent tests (9 tests) for fidelity-reporter"
```

---

### Task 9: Implement FidelityReporter.handle_event

**Files:**
- Modify: `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py`

**Step 1: Add handle_event method to FidelityReporter class**

Inside the `FidelityReporter` class, after the `render_ephemeral` method, add:

```python
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
```

**Step 2: Run TestHandleEvent to verify all 9 tests pass**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m pytest tests/modules/test_fidelity_reporter.py::TestHandleEvent -v`

Expected: 9 PASSED.

**Step 3: Commit**

```
git add modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py
git commit -m "feat: implement FidelityReporter.handle_event with dual-channel output"
```

---

### Task 10: Write TestMount tests (6 tests)

**Files:**
- Modify: `tests/modules/test_fidelity_reporter.py`

**Step 1: Append mount mock helper and TestMount class**

Add the following at the end of `tests/modules/test_fidelity_reporter.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m pytest tests/modules/test_fidelity_reporter.py::TestMount -v`

Expected: FAIL — `mount` function exists (imported) but is still the placeholder, not the real implementation.

**Step 3: Commit tests**

```
git add tests/modules/test_fidelity_reporter.py
git commit -m "test: add TestMount tests (6 tests) for fidelity-reporter"
```

---

### Task 11: Implement mount function

**Files:**
- Modify: `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py`

**Step 1: Add the mount function**

Append the following to the end of `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py`:

```python
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

**Step 2: Run TestMount to verify all 6 tests pass**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m pytest tests/modules/test_fidelity_reporter.py::TestMount -v`

Expected: 6 PASSED.

**Step 3: Commit**

```
git add modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py
git commit -m "feat: implement mount() with event registration and cleanup"
```

---

### Task 12: Full test suite, quality checks, and installability verification

**Files:**
- Verify: `modules/hooks-fidelity-reporter/amplifier_module_hooks_fidelity_reporter/__init__.py`
- Verify: `tests/modules/test_fidelity_reporter.py`
- Verify: `modules/hooks-fidelity-reporter/pyproject.toml`

**Step 1: Run the complete test suite**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m pytest tests/modules/test_fidelity_reporter.py -v`

Expected: 38 PASSED (2 strip_ansi + 11 dashboard + 9 ephemeral + 9 handle_event + 6 mount + 1 from test_contains_domain in ephemeral). Full output:

```
tests/modules/test_fidelity_reporter.py::test_strip_ansi_removes_escape_sequences PASSED
tests/modules/test_fidelity_reporter.py::test_strip_ansi_leaves_plain_text PASSED
tests/modules/test_fidelity_reporter.py::TestRenderDashboard::test_returns_string PASSED
tests/modules/test_fidelity_reporter.py::TestRenderDashboard::test_contains_top_border PASSED
tests/modules/test_fidelity_reporter.py::TestRenderDashboard::test_contains_bottom_border PASSED
tests/modules/test_fidelity_reporter.py::TestRenderDashboard::test_contains_title PASSED
tests/modules/test_fidelity_reporter.py::TestRenderDashboard::test_contains_all_lens_labels PASSED
tests/modules/test_fidelity_reporter.py::TestRenderDashboard::test_contains_priority_gap_marker PASSED
tests/modules/test_fidelity_reporter.py::TestRenderDashboard::test_contains_all_five_scores PASSED
tests/modules/test_fidelity_reporter.py::TestRenderDashboard::test_contains_overall_and_target PASSED
tests/modules/test_fidelity_reporter.py::TestRenderDashboard::test_contains_domain PASSED
tests/modules/test_fidelity_reporter.py::TestRenderDashboard::test_renders_without_error_for_empty_state PASSED
tests/modules/test_fidelity_reporter.py::TestRenderDashboard::test_multiline_output PASSED
tests/modules/test_fidelity_reporter.py::TestRenderEphemeral::test_returns_string PASSED
tests/modules/test_fidelity_reporter.py::TestRenderEphemeral::test_no_ansi_codes PASSED
tests/modules/test_fidelity_reporter.py::TestRenderEphemeral::test_contains_fidelity_state_header PASSED
tests/modules/test_fidelity_reporter.py::TestRenderEphemeral::test_contains_status PASSED
tests/modules/test_fidelity_reporter.py::TestRenderEphemeral::test_contains_converged_when_above_target PASSED
tests/modules/test_fidelity_reporter.py::TestRenderEphemeral::test_contains_overall_score PASSED
tests/modules/test_fidelity_reporter.py::TestRenderEphemeral::test_contains_target PASSED
tests/modules/test_fidelity_reporter.py::TestRenderEphemeral::test_contains_priority_gap_lens PASSED
tests/modules/test_fidelity_reporter.py::TestRenderEphemeral::test_contains_recommendation PASSED
tests/modules/test_fidelity_reporter.py::TestRenderEphemeral::test_contains_domain PASSED
tests/modules/test_fidelity_reporter.py::TestHandleEvent::test_returns_continue_when_no_capability PASSED
tests/modules/test_fidelity_reporter.py::TestHandleEvent::test_returns_continue_when_lens_scores_empty PASSED
tests/modules/test_fidelity_reporter.py::TestHandleEvent::test_writes_to_stdout_when_state_present PASSED
tests/modules/test_fidelity_reporter.py::TestHandleEvent::test_returns_hook_result_with_action_continue PASSED
tests/modules/test_fidelity_reporter.py::TestHandleEvent::test_context_injection_is_set PASSED
tests/modules/test_fidelity_reporter.py::TestHandleEvent::test_ephemeral_is_true PASSED
tests/modules/test_fidelity_reporter.py::TestHandleEvent::test_user_message_is_set PASSED
tests/modules/test_fidelity_reporter.py::TestHandleEvent::test_context_injection_has_no_ansi PASSED
tests/modules/test_fidelity_reporter.py::TestHandleEvent::test_returns_continue_on_coordinator_error PASSED
tests/modules/test_fidelity_reporter.py::TestMount::test_registers_tool_post_handler PASSED
tests/modules/test_fidelity_reporter.py::TestMount::test_registers_prompt_complete_handler PASSED
tests/modules/test_fidelity_reporter.py::TestMount::test_returns_callable_cleanup PASSED
tests/modules/test_fidelity_reporter.py::TestMount::test_cleanup_does_not_raise PASSED
tests/modules/test_fidelity_reporter.py::TestMount::test_respects_priority_config PASSED
tests/modules/test_fidelity_reporter.py::TestMount::test_tolerates_registration_failure PASSED
```

**Step 2: Run ruff format check**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m ruff format --check modules/hooks-fidelity-reporter/ tests/modules/test_fidelity_reporter.py`

Expected: All files already formatted, exit code 0.

**Step 3: Run ruff lint check**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector && python -m ruff check modules/hooks-fidelity-reporter/ tests/modules/test_fidelity_reporter.py`

Expected: Clean, no errors.

**Step 4: Verify installability**

Run: `cd /Users/michaeljabbour/dev/amplifier-bundle-zerovector/modules/hooks-fidelity-reporter && pip install -e . && pip show amplifier-module-hooks-fidelity-reporter`

Expected: Package installs successfully, shows version 0.3.0.

**Step 5: Final commit if any formatting was auto-fixed**

Only if Steps 2-3 required fixes:
```
git add -A
git commit -m "style: format and lint fixes"
```

---

## Acceptance Criteria Checklist

| # | Criterion | Verified By |
|---|-----------|-------------|
| 1 | 38 tests pass across 6 test groups | Task 12, Step 1 |
| 2 | render_dashboard returns multi-line (>=11 lines) with borders, title, lenses, scores, priority gap, overall/target, domain | TestRenderDashboard (Task 5) |
| 3 | render_ephemeral returns string with NO ANSI codes, FIDELITY STATE header, CONVERGED/NEEDS_WORK, overall/target/domain, priority gap, recommendation | TestRenderEphemeral (Task 7) |
| 4 | handle_event returns _CONTINUE when no capability or empty lens_scores | TestHandleEvent tests 1-2 (Task 9) |
| 5 | handle_event writes to stdout and returns HookResult with ephemeral=True, context_injection (no ANSI), user_message | TestHandleEvent tests 3-8 (Task 9) |
| 6 | handle_event never raises — returns _CONTINUE on any exception | TestHandleEvent test 9 (Task 9) |
| 7 | mount registers handlers on tool:post and prompt:complete, returns callable cleanup | TestMount tests 1-4 (Task 11) |
| 8 | mount respects priority config and tolerates registration failures | TestMount tests 5-6 (Task 11) |
| 9 | pip install -e . works from modules/hooks-fidelity-reporter/ | Task 12, Step 4 |

---

## Quality Review Status

> **WARNING: Quality review loop exhausted after 3 iterations without formal
> approval signal.** The final (3rd) review verdict was **APPROVED** with the
> following evidence:
>
> - **38/38 tests pass** (0.04s)
> - **ruff format**: clean
> - **ruff lint**: clean
> - **pyright**: 2 false-positives:
>   1. `reportAssignmentType` (line 27): Guard-import pattern where `HookResult`
>      is redefined in the `except` branch — `# pyright: ignore` already present.
>      Standard Amplifier module pattern.
>   2. `reportMissingImports` (line 29, test file): Dynamic `sys.path` insertion
>      for the module — works at runtime, Pyright can't resolve statically.
>      Expected for test files targeting editable-install modules.
> - **Stub-check**: 4 warnings — all false positives (section header comments
>   reference "hooks-todo-display" pattern name, stub checker flags substring)
> - **Zero critical or important issues**
> - **3 nice-to-have suggestions**:
>   1. `_CONTINUE` sentinel is shared mutable instance (theoretical concern only —
>      fallback dataclass is `frozen=True` since refactor commit `64456fc`)
>   2. Test helpers could be `@pytest.fixture`s (current factory-function style
>      is equally valid and more explicit)
>   3. `test_contains_overall_score` uses loose `"0.5"` assertion (cosmetic —
>      could match `"0.54"` precisely for consistency with dashboard test)
>
> Human reviewer: please verify the implementation independently before merging.
> The loop exhaustion was a process issue, not a code quality issue.
