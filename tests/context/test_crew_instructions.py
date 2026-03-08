"""Tests for context/crew-instructions.md — fidelity convergence rewrite.

Validates that crew-instructions.md has been rewritten from the v0.2
pipeline-stages-with-gates model to the v0.3 fidelity-convergence-with-
lens-routing model, per the design document.
"""

from pathlib import Path

import pytest

CREW_INSTRUCTIONS_PATH = (
    Path(__file__).resolve().parents[2] / "context" / "crew-instructions.md"
)


@pytest.fixture(scope="module")
def crew_content() -> str:
    """Load crew-instructions.md once for the entire test module."""
    assert CREW_INSTRUCTIONS_PATH.exists(), (
        f"crew-instructions.md not found: {CREW_INSTRUCTIONS_PATH}"
    )
    return CREW_INSTRUCTIONS_PATH.read_text()


@pytest.fixture(scope="module")
def crew_content_lower(crew_content: str) -> str:
    """Lower-cased crew-instructions.md for case-insensitive checks."""
    return crew_content.lower()


# ---------------------------------------------------------------------------
# AC-1: File exists and is non-empty
# ---------------------------------------------------------------------------
class TestFileExists:
    def test_file_exists(self):
        assert CREW_INSTRUCTIONS_PATH.exists()

    def test_file_non_empty(self, crew_content: str):
        assert len(crew_content.strip()) > 100, "File must have substantial content"


# ---------------------------------------------------------------------------
# AC-2: Old pipeline terminology is REMOVED
# ---------------------------------------------------------------------------
class TestOldTerminologyRemoved:
    """The rewrite must remove linear pipeline / gate terminology."""

    def test_no_stage_handoff_state_machine(self, crew_content: str):
        assert "Stage Handoff State Machine" not in crew_content

    def test_no_pipeline_stage_contracts(self, crew_content: str):
        assert "Pipeline Stage Contracts" not in crew_content

    def test_no_gate_contracts_section(self, crew_content: str):
        assert "Gate Contracts" not in crew_content

    def test_no_numbered_gates(self, crew_content: str):
        # Should not have GATE 1, GATE 2, GATE 3 as named concepts
        assert "GATE 1" not in crew_content
        assert "GATE 2" not in crew_content
        assert "GATE 3" not in crew_content

    def test_no_numbered_stages(self, crew_content: str):
        # Should not have "Stage 1 →", "Stage 2 →" etc as section headers
        assert "Stage 1" not in crew_content
        assert "Stage 2" not in crew_content
        assert "Stage 3" not in crew_content
        assert "Stage 4" not in crew_content
        assert "Stage 5" not in crew_content
        assert "Stage 6" not in crew_content

    def test_no_pipeline_depth_calibration(self, crew_content: str):
        assert "Pipeline Depth Calibration" not in crew_content

    def test_no_pipeline_telemetry(self, crew_content: str):
        assert "Pipeline Telemetry" not in crew_content


# ---------------------------------------------------------------------------
# AC-3: New fidelity convergence terminology is PRESENT
# ---------------------------------------------------------------------------
class TestFidelityConvergencePresent:
    """The rewrite must introduce fidelity convergence as the core model."""

    def test_mentions_fidelity(self, crew_content_lower: str):
        assert "fidelity" in crew_content_lower

    def test_mentions_convergence(self, crew_content_lower: str):
        assert "convergence" in crew_content_lower

    def test_mentions_translation_loss(self, crew_content_lower: str):
        assert "translation loss" in crew_content_lower

    def test_mentions_lenses(self, crew_content_lower: str):
        assert "lens" in crew_content_lower


# ---------------------------------------------------------------------------
# AC-4: All five fidelity lenses are referenced
# ---------------------------------------------------------------------------
class TestFiveLensesReferenced:
    """All five lenses from the fidelity framework must be present."""

    def test_intent_clarity_lens(self, crew_content_lower: str):
        assert (
            "intent clarity" in crew_content_lower
            or "intent_clarity" in crew_content_lower
        )

    def test_specification_lens(self, crew_content_lower: str):
        assert "specification" in crew_content_lower

    def test_implementation_lens(self, crew_content_lower: str):
        assert "implementation" in crew_content_lower

    def test_quality_lens(self, crew_content_lower: str):
        assert "quality" in crew_content_lower

    def test_ship_readiness_lens(self, crew_content_lower: str):
        assert (
            "ship-readiness" in crew_content_lower
            or "ship_readiness" in crew_content_lower
        )


# ---------------------------------------------------------------------------
# AC-5: Lens routing is described (weakest lens gets attention)
# ---------------------------------------------------------------------------
class TestLensRouting:
    """The document must describe routing work to the weakest lens."""

    def test_priority_gap_concept(self, crew_content_lower: str):
        assert (
            "priority gap" in crew_content_lower or "weakest lens" in crew_content_lower
        )

    def test_routing_to_agents(self, crew_content_lower: str):
        """Each lens should map to an agent."""
        assert (
            "intent-analyst" in crew_content_lower
            or "intent analyst" in crew_content_lower
        )
        assert "architect" in crew_content_lower
        assert "builder" in crew_content_lower
        assert "critic" in crew_content_lower
        assert "shipper" in crew_content_lower


# ---------------------------------------------------------------------------
# AC-6: Convergence loop replaces the old build-only loop
# ---------------------------------------------------------------------------
class TestConvergenceLoop:
    """The convergence loop should be the CORE pattern, not a build sub-loop."""

    def test_convergence_loop_section(self, crew_content: str):
        assert "Convergence" in crew_content

    def test_fidelity_target(self, crew_content_lower: str):
        """Should reference convergence toward a fidelity target."""
        assert "target" in crew_content_lower

    def test_assess_route_act_pattern(self, crew_content_lower: str):
        """The core loop should be: assess → route → act → re-assess."""
        assert "assess" in crew_content_lower
        assert "route" in crew_content_lower


# ---------------------------------------------------------------------------
# AC-7: Orchestrator role preserved but reframed
# ---------------------------------------------------------------------------
class TestOrchestratorRole:
    """The orchestrator role is preserved but reframed for convergence."""

    def test_orchestrator_mentioned(self, crew_content_lower: str):
        assert "orchestrat" in crew_content_lower  # orchestrator or orchestration

    def test_orchestrator_does_not_implement(self, crew_content_lower: str):
        """Orchestrator should NOT implement — this is preserved from v0.2."""
        assert (
            "do not" in crew_content_lower
            or "you do not" in crew_content_lower
            or "don't" in crew_content_lower
        )


# ---------------------------------------------------------------------------
# AC-8: Delegation contract preserved
# ---------------------------------------------------------------------------
class TestDelegationContract:
    """Context must flow losslessly between delegations."""

    def test_delegation_section_exists(self, crew_content: str):
        assert "Delegation" in crew_content or "delegation" in crew_content

    def test_context_passing_mentioned(self, crew_content_lower: str):
        assert "context" in crew_content_lower


# ---------------------------------------------------------------------------
# AC-9: Anti-rationalization preserved (updated for fidelity model)
# ---------------------------------------------------------------------------
class TestAntiRationalization:
    """Anti-rationalization patterns must be preserved, updated for v0.3."""

    def test_anti_rationalization_section(self, crew_content: str):
        assert (
            "Anti-Rationalization" in crew_content
            or "anti-rationalization" in crew_content
        )

    def test_fidelity_aware_anti_patterns(self, crew_content_lower: str):
        """Anti-patterns should reference fidelity concepts, not pipeline gates."""
        # At least one anti-pattern should mention fidelity-related concepts
        assert "fidelity" in crew_content_lower


# ---------------------------------------------------------------------------
# AC-10: Domain-specific tuning reference preserved
# ---------------------------------------------------------------------------
class TestDomainTuning:
    """Should still reference domain-tuning.md."""

    def test_domain_tuning_reference(self, crew_content: str):
        assert "domain-tuning.md" in crew_content


# ---------------------------------------------------------------------------
# AC-11: Crew selection reference preserved
# ---------------------------------------------------------------------------
class TestCrewSelection:
    """Crew commands (/crew, /crew-build, etc.) should still be listed."""

    def test_crew_commands_present(self, crew_content: str):
        assert "/crew" in crew_content

    def test_multiple_crew_domains(self, crew_content: str):
        domain_count = sum(
            1
            for cmd in [
                "/crew-build",
                "/crew-product",
                "/crew-platform",
                "/crew-research",
                "/crew-content",
            ]
            if cmd in crew_content
        )
        assert domain_count >= 4, (
            f"Expected at least 4 domain crew commands, found {domain_count}"
        )


# ---------------------------------------------------------------------------
# AC-12: Version bump in title
# ---------------------------------------------------------------------------
class TestVersionBump:
    """Document should reflect v0.3."""

    def test_version_03(self, crew_content: str):
        assert "0.3" in crew_content, "Document should reference v0.3"


# ---------------------------------------------------------------------------
# AC-13: References fidelity-framework.md
# ---------------------------------------------------------------------------
class TestFidelityFrameworkReference:
    """Should reference the universal fidelity framework document."""

    def test_fidelity_framework_reference(self, crew_content: str):
        assert "fidelity-framework.md" in crew_content


# ---------------------------------------------------------------------------
# AC-14: update_fidelity tool mentioned
# ---------------------------------------------------------------------------
class TestUpdateFidelityTool:
    """The orchestrator should know about the update_fidelity tool."""

    def test_update_fidelity_mentioned(self, crew_content: str):
        assert "update_fidelity" in crew_content
