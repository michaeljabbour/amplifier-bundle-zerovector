"""Tests for behaviors/zerovector-crew.yaml — full ZVD crew behavior."""

from pathlib import Path

import yaml

BEHAVIOR_PATH = (
    Path(__file__).resolve().parents[2] / "behaviors" / "zerovector-crew.yaml"
)


def _load_behavior():
    """Load and parse the zerovector-crew behavior YAML."""
    assert BEHAVIOR_PATH.exists(), f"Behavior file not found: {BEHAVIOR_PATH}"
    with BEHAVIOR_PATH.open() as f:
        return yaml.safe_load(f)


class TestZerovectorCrewBehaviorExists:
    """AC-1: File exists at behaviors/zerovector-crew.yaml."""

    def test_file_exists(self):
        assert BEHAVIOR_PATH.exists(), "behaviors/zerovector-crew.yaml must exist"


class TestZerovectorCrewBehaviorValidYAML:
    """AC-2: YAML is valid and parseable."""

    def test_yaml_parseable(self):
        data = _load_behavior()
        assert isinstance(data, dict), "YAML must parse to a dict"


class TestZerovectorCrewBehaviorBundle:
    """AC-3: bundle.name is 'zerovector-crew', version '0.3.0'."""

    def test_bundle_name(self):
        data = _load_behavior()
        assert data["bundle"]["name"] == "zerovector-crew"

    def test_bundle_version(self):
        data = _load_behavior()
        assert data["bundle"]["version"] == "0.3.0"


class TestZerovectorCrewBehaviorIncludes:
    """AC-4: includes the fidelity behavior transitively."""

    def test_includes_section_present(self):
        data = _load_behavior()
        assert "includes" in data, "includes section must exist"
        assert len(data["includes"]) >= 1

    def test_includes_fidelity_behavior(self):
        data = _load_behavior()
        included_bundles = [entry["bundle"] for entry in data["includes"]]
        assert "zerovector:behaviors/fidelity" in included_bundles, (
            "Must include zerovector:behaviors/fidelity"
        )


class TestZerovectorCrewBehaviorAgents:
    """AC-5: agents.include lists exactly 4 agents (critic comes from fidelity)."""

    def test_agents_include_present(self):
        data = _load_behavior()
        assert "agents" in data
        assert "include" in data["agents"]

    def test_agents_include_intent_analyst(self):
        data = _load_behavior()
        assert "zerovector:intent-analyst" in data["agents"]["include"]

    def test_agents_include_architect(self):
        data = _load_behavior()
        assert "zerovector:architect" in data["agents"]["include"]

    def test_agents_include_builder(self):
        data = _load_behavior()
        assert "zerovector:builder" in data["agents"]["include"]

    def test_agents_include_shipper(self):
        data = _load_behavior()
        assert "zerovector:shipper" in data["agents"]["include"]

    def test_agents_include_exactly_four(self):
        data = _load_behavior()
        agents = data["agents"]["include"]
        assert len(agents) == 4, (
            f"Expected exactly 4 agents (critic comes from fidelity), got {len(agents)}: {agents}"
        )

    def test_agents_does_not_include_critic(self):
        data = _load_behavior()
        agents = data["agents"]["include"]
        assert "zerovector:critic" not in agents, (
            "critic must NOT be listed here — it comes transitively from the fidelity behavior"
        )


class TestZerovectorCrewBehaviorContext:
    """AC-6: context.include references crew and modes context files."""

    def test_context_include_present(self):
        data = _load_behavior()
        assert "context" in data
        assert "include" in data["context"]

    def test_context_includes_crew_instructions(self):
        data = _load_behavior()
        assert "zerovector:context/crew-instructions.md" in data["context"]["include"]

    def test_context_includes_domain_tuning(self):
        data = _load_behavior()
        assert "zerovector:context/domain-tuning.md" in data["context"]["include"]

    def test_context_includes_modes_instructions(self):
        data = _load_behavior()
        assert "modes:context/modes-instructions.md" in data["context"]["include"]


class TestZerovectorCrewBehaviorHooks:
    """AC-7: hooks include hooks-mode with correct source and search_paths config."""

    def test_hooks_present(self):
        data = _load_behavior()
        assert "hooks" in data, "hooks section must exist"
        assert len(data["hooks"]) >= 1

    def test_hooks_mode_module(self):
        data = _load_behavior()
        hook_modules = [h["module"] for h in data["hooks"]]
        assert "hooks-mode" in hook_modules

    def test_hooks_mode_source(self):
        data = _load_behavior()
        hooks_mode = next(h for h in data["hooks"] if h["module"] == "hooks-mode")
        assert hooks_mode["source"] == "modes:modules/hooks-mode"

    def test_hooks_mode_search_paths(self):
        data = _load_behavior()
        hooks_mode = next(h for h in data["hooks"] if h["module"] == "hooks-mode")
        assert "config" in hooks_mode
        assert hooks_mode["config"]["search_paths"] == ["@zerovector:modes"]


class TestZerovectorCrewBehaviorTools:
    """AC-8: tools include tool-mode with gate_policy 'warn'."""

    def test_tools_present(self):
        data = _load_behavior()
        assert "tools" in data, "tools section must exist"
        assert len(data["tools"]) >= 1

    def test_tool_mode_module(self):
        data = _load_behavior()
        tool_modules = [t["module"] for t in data["tools"]]
        assert "tool-mode" in tool_modules

    def test_tool_mode_source(self):
        data = _load_behavior()
        tool_mode = next(t for t in data["tools"] if t["module"] == "tool-mode")
        assert tool_mode["source"] == "modes:modules/tool-mode"

    def test_tool_mode_gate_policy_warn(self):
        data = _load_behavior()
        tool_mode = next(t for t in data["tools"] if t["module"] == "tool-mode")
        assert "config" in tool_mode
        assert tool_mode["config"]["gate_policy"] == "warn"
