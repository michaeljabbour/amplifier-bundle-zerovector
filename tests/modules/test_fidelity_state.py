"""Tests for tool-fidelity-state module."""

import logging
import os
import sys

import pytest

# Ensure the module is importable without pip install -e
_mod_dir = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    os.pardir,
    "modules",
    "tool-fidelity-state",
)
if os.path.isdir(_mod_dir) and os.path.abspath(_mod_dir) not in sys.path:
    sys.path.insert(0, os.path.abspath(_mod_dir))

from amplifier_module_tool_fidelity_state import (  # noqa: E402
    FidelityState,
    UpdateFidelityTool,
    _RECOMMENDATIONS,
    mount,
)


# ── Helpers ─────────────────────────────────────────────────────


class MockCoordinator:
    """Records mount / register_capability calls."""

    def __init__(self):
        self.mounted: dict = {}
        self.capabilities: dict = {}

    def mount(self, namespace, obj, name=None):
        self.mounted[name or namespace] = obj

    def register_capability(self, name, value):
        self.capabilities[name] = value


class ErrorCoordinator:
    """Raises on every coordinator method."""

    def mount(self, *a, **kw):
        raise RuntimeError("boom")

    def register_capability(self, *a, **kw):
        raise RuntimeError("boom")


def _content(result):
    """Extract content string from ToolResult or plain dict."""
    if isinstance(result, dict):
        return result.get("content", "")
    # ToolResult.output may be None when no output was set; fall back to ""
    return getattr(result, "output", "") or ""


def _is_error(result):
    """Extract is_error flag from ToolResult or plain dict."""
    if isinstance(result, dict):
        return result.get("is_error", False)
    # Real ToolResult uses 'success' (inverted)
    return not getattr(result, "success", True)


# ── TestFidelityStateDefaults (5) ───────────────────────────────


class TestFidelityStateDefaults:
    def test_default_lens_scores(self):
        s = FidelityState()
        assert s.lens_scores == {}

    def test_default_overall(self):
        s = FidelityState()
        assert s.overall == 0.0

    def test_default_target(self):
        s = FidelityState()
        assert s.target == 0.85

    def test_default_domain(self):
        s = FidelityState()
        assert s.domain == "general"

    def test_default_priority_gap(self):
        s = FidelityState()
        assert s.priority_gap == {}


# ── TestUpdateFidelity (8) ──────────────────────────────────────


class TestUpdateFidelity:
    def test_sets_lens_scores(self):
        s = FidelityState()
        s.update_fidelity({"intent_clarity": 0.8, "specification": 0.7})
        assert s.lens_scores == {"intent_clarity": 0.8, "specification": 0.7}

    def test_overall_is_arithmetic_mean(self):
        s = FidelityState()
        s.update_fidelity({"intent_clarity": 0.8, "specification": 0.6})
        assert s.overall == pytest.approx(0.7)

    def test_clamps_above_one(self):
        s = FidelityState()
        s.update_fidelity({"intent_clarity": 1.5})
        assert s.lens_scores["intent_clarity"] == 1.0

    def test_clamps_below_zero(self):
        s = FidelityState()
        s.update_fidelity({"intent_clarity": -0.3})
        assert s.lens_scores["intent_clarity"] == 0.0

    def test_priority_gap_identifies_lowest(self):
        s = FidelityState()
        s.update_fidelity({"intent_clarity": 0.9, "specification": 0.3, "quality": 0.7})
        assert s.priority_gap["lens"] == "specification"
        assert s.priority_gap["score"] == 0.3

    def test_priority_gap_has_recommendation(self):
        s = FidelityState()
        s.update_fidelity({"intent_clarity": 0.5, "specification": 0.9})
        assert s.priority_gap["lens"] == "intent_clarity"
        assert s.priority_gap["recommendation"] == _RECOMMENDATIONS["intent_clarity"]

    def test_empty_scores_resets_overall(self):
        s = FidelityState()
        s.update_fidelity({"intent_clarity": 0.8})
        assert s.overall != 0.0
        s.update_fidelity({})
        assert s.overall == 0.0

    def test_empty_scores_resets_priority_gap(self):
        s = FidelityState()
        s.update_fidelity({"intent_clarity": 0.8})
        assert s.priority_gap != {}
        s.update_fidelity({})
        assert s.priority_gap == {}


# ── TestGetState (5) ────────────────────────────────────────────


class TestGetState:
    def test_returns_dict(self):
        s = FidelityState()
        assert isinstance(s.get_state(), dict)

    def test_has_all_keys(self):
        s = FidelityState()
        keys = set(s.get_state().keys())
        assert keys == {"lens_scores", "overall", "target", "domain", "priority_gap"}

    def test_lens_scores_is_copy(self):
        s = FidelityState()
        s.update_fidelity({"intent_clarity": 0.8})
        out = s.get_state()
        out["lens_scores"]["intent_clarity"] = 999.0
        assert s.lens_scores["intent_clarity"] == 0.8

    def test_priority_gap_is_copy(self):
        s = FidelityState()
        s.update_fidelity({"intent_clarity": 0.8})
        out = s.get_state()
        out["priority_gap"]["lens"] = "hacked"
        assert s.priority_gap["lens"] == "intent_clarity"

    def test_reflects_current_state(self):
        s = FidelityState()
        s.update_fidelity({"intent_clarity": 0.9, "specification": 0.7})
        out = s.get_state()
        assert out["overall"] == pytest.approx(0.8)
        assert out["lens_scores"] == {"intent_clarity": 0.9, "specification": 0.7}


# ── TestUpdateFidelityToolExecute (4) ───────────────────────────


class TestUpdateFidelityToolExecute:
    @pytest.fixture()
    def tool(self):
        return UpdateFidelityTool(FidelityState())

    @pytest.mark.asyncio
    async def test_failure_no_lens_scores(self, tool):
        result = await tool.execute({})
        assert _is_error(result) is True

    @pytest.mark.asyncio
    async def test_converged_status(self, tool):
        result = await tool.execute({"lens_scores": {"a": 0.9, "b": 0.9}})
        assert "CONVERGED" in _content(result)

    @pytest.mark.asyncio
    async def test_needs_work_status(self, tool):
        result = await tool.execute({"lens_scores": {"a": 0.4, "b": 0.3}})
        assert "NEEDS_WORK" in _content(result)

    def test_tool_name_and_schema(self, tool):
        assert tool.name == "update_fidelity"
        assert (
            "Update fidelity scores after a multi-lens assessment" in tool.description
        )
        assert "lens_scores" in tool.input_schema["properties"]
        assert "lens_scores" in tool.input_schema["required"]


# ── TestMount (9 — includes tolerates-errors) ──────────────────


class TestMount:
    @pytest.mark.asyncio
    async def test_returns_info_dict(self):
        info = await mount(MockCoordinator())
        assert isinstance(info, dict)

    @pytest.mark.asyncio
    async def test_info_name(self):
        info = await mount(MockCoordinator())
        assert info["name"] == "tool-fidelity-state"

    @pytest.mark.asyncio
    async def test_info_version(self):
        info = await mount(MockCoordinator())
        assert info["version"] == "0.3.0"

    @pytest.mark.asyncio
    async def test_config_target(self):
        coord = MockCoordinator()
        await mount(coord, config={"target": 0.9})
        state = coord.capabilities["zerovector.fidelity_state"]
        assert state.target == 0.9

    @pytest.mark.asyncio
    async def test_config_domain(self):
        coord = MockCoordinator()
        await mount(coord, config={"domain": "platform"})
        state = coord.capabilities["zerovector.fidelity_state"]
        assert state.domain == "platform"

    @pytest.mark.asyncio
    async def test_mounts_tool(self):
        coord = MockCoordinator()
        await mount(coord)
        assert "update_fidelity" in coord.mounted
        assert isinstance(coord.mounted["update_fidelity"], UpdateFidelityTool)

    @pytest.mark.asyncio
    async def test_registers_fidelity_state_capability(self):
        coord = MockCoordinator()
        await mount(coord)
        assert "zerovector.fidelity_state" in coord.capabilities
        assert isinstance(
            coord.capabilities["zerovector.fidelity_state"], FidelityState
        )

    @pytest.mark.asyncio
    async def test_registers_update_fidelity_callable(self):
        coord = MockCoordinator()
        await mount(coord)
        assert "zerovector.update_fidelity" in coord.capabilities
        assert callable(coord.capabilities["zerovector.update_fidelity"])

    @pytest.mark.asyncio
    async def test_mount_tolerates_coordinator_errors(self):
        info = await mount(ErrorCoordinator())
        assert info["name"] == "tool-fidelity-state"

    @pytest.mark.asyncio
    async def test_mount_logs_coordinator_errors(self, caplog):
        with caplog.at_level(logging.DEBUG):
            await mount(ErrorCoordinator())
        assert len(caplog.records) == 3
        assert all(r.levelno == logging.DEBUG for r in caplog.records)
