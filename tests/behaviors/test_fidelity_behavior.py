"""Tests for behaviors/fidelity.yaml — universal fidelity diagnostic behavior."""

from pathlib import Path

import yaml

BEHAVIOR_PATH = Path(__file__).resolve().parents[2] / "behaviors" / "fidelity.yaml"


def _load_behavior():
    """Load and parse the fidelity behavior YAML."""
    assert BEHAVIOR_PATH.exists(), f"Behavior file not found: {BEHAVIOR_PATH}"
    with BEHAVIOR_PATH.open() as f:
        return yaml.safe_load(f)


class TestFidelityBehaviorExists:
    """AC-1: File exists at behaviors/fidelity.yaml."""

    def test_file_exists(self):
        assert BEHAVIOR_PATH.exists(), "behaviors/fidelity.yaml must exist"


class TestFidelityBehaviorValidYAML:
    """AC-2: YAML is valid and parseable."""

    def test_yaml_parseable(self):
        data = _load_behavior()
        assert isinstance(data, dict), "YAML must parse to a dict"


class TestFidelityBehaviorBundle:
    """AC-3: bundle.name is 'fidelity-behavior', version '0.3.0'."""

    def test_bundle_name(self):
        data = _load_behavior()
        assert data["bundle"]["name"] == "fidelity-behavior"

    def test_bundle_version(self):
        data = _load_behavior()
        assert data["bundle"]["version"] == "0.3.0"


class TestFidelityBehaviorHooks:
    """AC-4: hooks section references hooks-fidelity-reporter with correct source."""

    def test_hooks_present(self):
        data = _load_behavior()
        assert "hooks" in data, "hooks section must exist"
        assert len(data["hooks"]) >= 1

    def test_hooks_fidelity_reporter_module(self):
        data = _load_behavior()
        hook = data["hooks"][0]
        assert hook["module"] == "hooks-fidelity-reporter"

    def test_hooks_fidelity_reporter_source(self):
        data = _load_behavior()
        hook = data["hooks"][0]
        assert hook["source"] == "zerovector:modules/hooks-fidelity-reporter"


class TestFidelityBehaviorTools:
    """AC-5: tools section references tool-fidelity-state with correct source."""

    def test_tools_present(self):
        data = _load_behavior()
        assert "tools" in data, "tools section must exist"
        assert len(data["tools"]) >= 1

    def test_tool_fidelity_state_module(self):
        data = _load_behavior()
        tool = data["tools"][0]
        assert tool["module"] == "tool-fidelity-state"

    def test_tool_fidelity_state_source(self):
        data = _load_behavior()
        tool = data["tools"][0]
        assert tool["source"] == "zerovector:modules/tool-fidelity-state"


class TestFidelityBehaviorAgents:
    """AC-6: agents.include references zerovector:critic."""

    def test_agents_include_critic(self):
        data = _load_behavior()
        assert "agents" in data
        assert "include" in data["agents"]
        assert "zerovector:critic" in data["agents"]["include"]


class TestFidelityBehaviorContext:
    """AC-7: context.include references zerovector:context/fidelity-framework.md."""

    def test_context_include_fidelity_framework(self):
        data = _load_behavior()
        assert "context" in data
        assert "include" in data["context"]
        assert "zerovector:context/fidelity-framework.md" in data["context"]["include"]


class TestFidelityBehaviorDescription:
    """AC-8: Description clearly states universal and works on any Amplifier session."""

    def test_description_mentions_universal(self):
        data = _load_behavior()
        desc = data["bundle"]["description"].lower()
        assert "universal" in desc, "Description must mention 'universal'"
        assert "any amplifier session" in desc, (
            "Description must state 'any Amplifier session'"
        )
