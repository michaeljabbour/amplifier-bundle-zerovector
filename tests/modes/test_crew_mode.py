"""Tests for modes/crew.md — fidelity convergence rewrite.

Validates that crew.md has been rewritten from the v0.2 linear pipeline
model (Stage 1-5) to the v0.3 fidelity convergence model, aligning with
the already-rewritten crew-instructions.md.
"""

from pathlib import Path

import pytest

CREW_MODE_PATH = Path(__file__).resolve().parents[2] / "modes" / "crew.md"


@pytest.fixture(scope="module")
def crew_mode_content() -> str:
    """Load modes/crew.md once for the entire test module."""
    assert CREW_MODE_PATH.exists(), f"crew.md not found: {CREW_MODE_PATH}"
    return CREW_MODE_PATH.read_text()


@pytest.fixture(scope="module")
def crew_mode_lower(crew_mode_content: str) -> str:
    """Lower-cased modes/crew.md for case-insensitive checks."""
    return crew_mode_content.lower()


# ---------------------------------------------------------------------------
# AC-1: YAML frontmatter preserved
# ---------------------------------------------------------------------------
class TestYamlFrontmatter:
    """YAML frontmatter must be preserved — mode name, tools, etc."""

    def test_has_yaml_frontmatter(self, crew_mode_content: str):
        assert crew_mode_content.startswith("---")

    def test_mode_name_is_crew(self, crew_mode_content: str):
        assert "name: crew" in crew_mode_content

    def test_delegate_tool_present(self, crew_mode_content: str):
        assert "delegate" in crew_mode_content

    def test_recipes_tool_present(self, crew_mode_content: str):
        assert "recipes" in crew_mode_content


# ---------------------------------------------------------------------------
# AC-2: Old pipeline terminology is REMOVED
# ---------------------------------------------------------------------------
class TestOldPipelineRemoved:
    """The rewrite must remove linear pipeline stage terminology."""

    @pytest.mark.parametrize("n", range(1, 6))
    def test_no_numbered_stages(self, crew_mode_content: str, n: int):
        """Should not have 'Stage 1:', 'Stage 2:', etc. as section headers."""
        assert f"Stage {n}" not in crew_mode_content

    def test_no_pipeline_keyword_in_critical(self, crew_mode_content: str):
        """The CRITICAL section should not describe a 'pipeline'."""
        # Extract the CRITICAL block
        if "<CRITICAL>" in crew_mode_content and "</CRITICAL>" in crew_mode_content:
            start = crew_mode_content.index("<CRITICAL>")
            end = crew_mode_content.index("</CRITICAL>") + len("</CRITICAL>")
            critical_block = crew_mode_content[start:end]
            assert "Pipeline:" not in critical_block
            assert "pipeline stage" not in critical_block.lower()

    def test_no_stage_numbered_arrows(self, crew_mode_content: str):
        """Should not have '1. zerovector:intent-analyst →' style pipeline."""
        assert "1. zerovector:" not in crew_mode_content

    def test_no_each_agent_receives_previous(self, crew_mode_content: str):
        """Old linear handoff language should be gone."""
        assert (
            "Each agent receives the output of the previous stage"
            not in crew_mode_content
        )

    def test_no_old_todo_pipeline_stages(self, crew_mode_content: str):
        """Old pipeline-style todo list should be gone."""
        assert "Decode intent (intent-analyst)" not in crew_mode_content
        assert "Ship it (shipper)" not in crew_mode_content


# ---------------------------------------------------------------------------
# AC-3: Fidelity convergence terminology is PRESENT
# ---------------------------------------------------------------------------
class TestFidelityConvergencePresent:
    """The rewrite must introduce fidelity convergence as the core model."""

    def test_mentions_fidelity(self, crew_mode_lower: str):
        assert "fidelity" in crew_mode_lower

    def test_mentions_convergence(self, crew_mode_lower: str):
        assert "convergence" in crew_mode_lower

    def test_mentions_lens(self, crew_mode_lower: str):
        assert "lens" in crew_mode_lower

    def test_mentions_translation_loss(self, crew_mode_lower: str):
        assert "translation loss" in crew_mode_lower


# ---------------------------------------------------------------------------
# AC-4: Core convergence loop pattern described
# ---------------------------------------------------------------------------
class TestConvergenceLoop:
    """The mode must describe the assess → route → act → re-assess loop."""

    def test_assess_pattern(self, crew_mode_lower: str):
        assert "assess" in crew_mode_lower

    def test_route_pattern(self, crew_mode_lower: str):
        assert "route" in crew_mode_lower

    def test_weakest_lens_or_priority_gap(self, crew_mode_lower: str):
        assert (
            "weakest lens" in crew_mode_lower
            or "priority gap" in crew_mode_lower
            or "weakest" in crew_mode_lower
        )

    def test_convergence_target(self, crew_mode_lower: str):
        assert "target" in crew_mode_lower


# ---------------------------------------------------------------------------
# AC-5: Five lenses referenced (agents mapped to lenses)
# ---------------------------------------------------------------------------
class TestLensesAndAgents:
    """All five lenses and their serving agents must be referenced."""

    def test_intent_clarity_lens(self, crew_mode_lower: str):
        assert "intent" in crew_mode_lower

    def test_specification_lens(self, crew_mode_lower: str):
        assert "specification" in crew_mode_lower

    def test_implementation_lens(self, crew_mode_lower: str):
        assert "implementation" in crew_mode_lower

    def test_quality_lens(self, crew_mode_lower: str):
        assert "quality" in crew_mode_lower

    def test_ship_readiness_lens(self, crew_mode_lower: str):
        assert (
            "ship-readiness" in crew_mode_lower or "ship readiness" in crew_mode_lower
        )

    def test_all_five_agents_referenced(self, crew_mode_lower: str):
        assert "intent-analyst" in crew_mode_lower
        assert "architect" in crew_mode_lower
        assert "builder" in crew_mode_lower
        assert "critic" in crew_mode_lower
        assert "shipper" in crew_mode_lower


# ---------------------------------------------------------------------------
# AC-6: Orchestrator role preserved
# ---------------------------------------------------------------------------
class TestOrchestratorRole:
    """The orchestrator role must be preserved — do not implement yourself."""

    def test_orchestrator_mentioned(self, crew_mode_lower: str):
        assert "orchestrat" in crew_mode_lower

    def test_does_not_implement(self, crew_mode_lower: str):
        assert "do not" in crew_mode_lower or "you do not" in crew_mode_lower


# ---------------------------------------------------------------------------
# AC-7: References crew-instructions.md for detailed protocol
# ---------------------------------------------------------------------------
class TestCrewInstructionsReference:
    """Mode file should reference crew-instructions.md for the full protocol."""

    def test_references_crew_instructions(self, crew_mode_content: str):
        assert "crew-instructions.md" in crew_mode_content


# ---------------------------------------------------------------------------
# AC-8: Anti-rationalization preserved and updated for fidelity
# ---------------------------------------------------------------------------
class TestAntiRationalization:
    """Anti-rationalization must be present and use fidelity concepts."""

    def test_anti_rationalization_section(self, crew_mode_content: str):
        assert (
            "Anti-Rationalization" in crew_mode_content
            or "anti-rationalization" in crew_mode_content
        )

    def test_fidelity_aware_anti_patterns(self, crew_mode_lower: str):
        """At least one anti-pattern should reference fidelity concepts."""
        # Should reference fidelity-related concepts in the anti-patterns
        assert "fidelity" in crew_mode_lower


# ---------------------------------------------------------------------------
# AC-9: Transitions preserved
# ---------------------------------------------------------------------------
class TestTransitions:
    """Mode transitions should still be documented."""

    def test_transitions_section(self, crew_mode_content: str):
        assert "Transition" in crew_mode_content or "transition" in crew_mode_content

    def test_debug_transition(self, crew_mode_lower: str):
        assert "debug" in crew_mode_lower

    def test_mode_clear(self, crew_mode_lower: str):
        assert "clear" in crew_mode_lower


# ---------------------------------------------------------------------------
# AC-10: Approval points mentioned
# ---------------------------------------------------------------------------
class TestApprovalPoints:
    """Fidelity-based approval points should replace fixed gates."""

    def test_approval_mentioned(self, crew_mode_lower: str):
        assert "approval" in crew_mode_lower

    def test_no_gate_1_2_3(self, crew_mode_content: str):
        """Old numbered gates should be gone."""
        assert "GATE 1" not in crew_mode_content
        assert "GATE 2" not in crew_mode_content
        assert "GATE 3" not in crew_mode_content
