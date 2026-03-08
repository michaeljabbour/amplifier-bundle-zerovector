"""Tests for context/crew-instructions.md — fidelity convergence rewrite.

Validates that crew-instructions.md has been rewritten from the v0.2
pipeline-stages-with-gates model to the v0.3 fidelity-convergence-with-
lens-routing model, per the design document.
"""

from pathlib import Path

CREW_INSTRUCTIONS_PATH = (
    Path(__file__).resolve().parents[2] / "context" / "crew-instructions.md"
)


def _load_content() -> str:
    """Load crew-instructions.md as a string."""
    assert CREW_INSTRUCTIONS_PATH.exists(), (
        f"crew-instructions.md not found: {CREW_INSTRUCTIONS_PATH}"
    )
    return CREW_INSTRUCTIONS_PATH.read_text()


# ---------------------------------------------------------------------------
# AC-1: File exists and is non-empty
# ---------------------------------------------------------------------------
class TestFileExists:
    def test_file_exists(self):
        assert CREW_INSTRUCTIONS_PATH.exists()

    def test_file_non_empty(self):
        content = _load_content()
        assert len(content.strip()) > 100, "File must have substantial content"


# ---------------------------------------------------------------------------
# AC-2: Old pipeline terminology is REMOVED
# ---------------------------------------------------------------------------
class TestOldTerminologyRemoved:
    """The rewrite must remove linear pipeline / gate terminology."""

    def test_no_stage_handoff_state_machine(self):
        content = _load_content()
        assert "Stage Handoff State Machine" not in content

    def test_no_pipeline_stage_contracts(self):
        content = _load_content()
        assert "Pipeline Stage Contracts" not in content

    def test_no_gate_contracts_section(self):
        content = _load_content()
        assert "Gate Contracts" not in content

    def test_no_numbered_gates(self):
        content = _load_content()
        # Should not have GATE 1, GATE 2, GATE 3 as named concepts
        assert "GATE 1" not in content
        assert "GATE 2" not in content
        assert "GATE 3" not in content

    def test_no_numbered_stages(self):
        content = _load_content()
        # Should not have "Stage 1 →", "Stage 2 →" etc as section headers
        assert "Stage 1" not in content
        assert "Stage 2" not in content
        assert "Stage 3" not in content
        assert "Stage 4" not in content
        assert "Stage 5" not in content
        assert "Stage 6" not in content

    def test_no_pipeline_depth_calibration(self):
        content = _load_content()
        assert "Pipeline Depth Calibration" not in content

    def test_no_pipeline_telemetry(self):
        content = _load_content()
        assert "Pipeline Telemetry" not in content


# ---------------------------------------------------------------------------
# AC-3: New fidelity convergence terminology is PRESENT
# ---------------------------------------------------------------------------
class TestFidelityConvergencePresent:
    """The rewrite must introduce fidelity convergence as the core model."""

    def test_mentions_fidelity(self):
        content = _load_content().lower()
        assert "fidelity" in content

    def test_mentions_convergence(self):
        content = _load_content().lower()
        assert "convergence" in content

    def test_mentions_translation_loss(self):
        content = _load_content().lower()
        assert "translation loss" in content

    def test_mentions_lenses(self):
        content = _load_content().lower()
        assert "lens" in content


# ---------------------------------------------------------------------------
# AC-4: All five fidelity lenses are referenced
# ---------------------------------------------------------------------------
class TestFiveLensesReferenced:
    """All five lenses from the fidelity framework must be present."""

    def test_intent_clarity_lens(self):
        content = _load_content().lower()
        assert "intent clarity" in content or "intent_clarity" in content

    def test_specification_lens(self):
        content = _load_content().lower()
        assert "specification" in content

    def test_implementation_lens(self):
        content = _load_content().lower()
        assert "implementation" in content

    def test_quality_lens(self):
        content = _load_content().lower()
        assert "quality" in content

    def test_ship_readiness_lens(self):
        content = _load_content().lower()
        assert "ship-readiness" in content or "ship_readiness" in content


# ---------------------------------------------------------------------------
# AC-5: Lens routing is described (weakest lens gets attention)
# ---------------------------------------------------------------------------
class TestLensRouting:
    """The document must describe routing work to the weakest lens."""

    def test_priority_gap_concept(self):
        content = _load_content().lower()
        assert "priority gap" in content or "weakest lens" in content

    def test_routing_to_agents(self):
        """Each lens should map to an agent."""
        content = _load_content().lower()
        assert "intent-analyst" in content or "intent analyst" in content
        assert "architect" in content
        assert "builder" in content
        assert "critic" in content
        assert "shipper" in content


# ---------------------------------------------------------------------------
# AC-6: Convergence loop replaces the old build-only loop
# ---------------------------------------------------------------------------
class TestConvergenceLoop:
    """The convergence loop should be the CORE pattern, not a build sub-loop."""

    def test_convergence_loop_section(self):
        content = _load_content()
        assert "Convergence" in content

    def test_fidelity_target(self):
        """Should reference convergence toward a fidelity target."""
        content = _load_content().lower()
        assert "target" in content

    def test_assess_route_act_pattern(self):
        """The core loop should be: assess → route → act → re-assess."""
        content = _load_content().lower()
        assert "assess" in content
        assert "route" in content


# ---------------------------------------------------------------------------
# AC-7: Orchestrator role preserved but reframed
# ---------------------------------------------------------------------------
class TestOrchestratorRole:
    """The orchestrator role is preserved but reframed for convergence."""

    def test_orchestrator_mentioned(self):
        content = _load_content().lower()
        assert "orchestrat" in content  # orchestrator or orchestration

    def test_orchestrator_does_not_implement(self):
        """Orchestrator should NOT implement — this is preserved from v0.2."""
        content = _load_content()
        # Should still contain a statement about not implementing
        lower = content.lower()
        assert "do not" in lower or "you do not" in lower or "don't" in lower


# ---------------------------------------------------------------------------
# AC-8: Delegation contract preserved
# ---------------------------------------------------------------------------
class TestDelegationContract:
    """Context must flow losslessly between delegations."""

    def test_delegation_section_exists(self):
        content = _load_content()
        assert "Delegation" in content or "delegation" in content

    def test_context_passing_mentioned(self):
        content = _load_content().lower()
        assert "context" in content


# ---------------------------------------------------------------------------
# AC-9: Anti-rationalization preserved (updated for fidelity model)
# ---------------------------------------------------------------------------
class TestAntiRationalization:
    """Anti-rationalization patterns must be preserved, updated for v0.3."""

    def test_anti_rationalization_section(self):
        content = _load_content()
        assert "Anti-Rationalization" in content or "anti-rationalization" in content

    def test_fidelity_aware_anti_patterns(self):
        """Anti-patterns should reference fidelity concepts, not pipeline gates."""
        content = _load_content().lower()
        # At least one anti-pattern should mention fidelity-related concepts
        assert "fidelity" in content


# ---------------------------------------------------------------------------
# AC-10: Domain-specific tuning reference preserved
# ---------------------------------------------------------------------------
class TestDomainTuning:
    """Should still reference domain-tuning.md."""

    def test_domain_tuning_reference(self):
        content = _load_content()
        assert "domain-tuning.md" in content


# ---------------------------------------------------------------------------
# AC-11: Crew selection reference preserved
# ---------------------------------------------------------------------------
class TestCrewSelection:
    """Crew commands (/crew, /crew-build, etc.) should still be listed."""

    def test_crew_commands_present(self):
        content = _load_content()
        assert "/crew" in content

    def test_multiple_crew_domains(self):
        content = _load_content()
        domain_count = sum(
            1
            for cmd in [
                "/crew-build",
                "/crew-product",
                "/crew-platform",
                "/crew-research",
                "/crew-content",
            ]
            if cmd in content
        )
        assert domain_count >= 4, (
            f"Expected at least 4 domain crew commands, found {domain_count}"
        )


# ---------------------------------------------------------------------------
# AC-12: Version bump in title
# ---------------------------------------------------------------------------
class TestVersionBump:
    """Document should reflect v0.3."""

    def test_version_03(self):
        content = _load_content()
        assert "0.3" in content, "Document should reference v0.3"


# ---------------------------------------------------------------------------
# AC-13: References fidelity-framework.md
# ---------------------------------------------------------------------------
class TestFidelityFrameworkReference:
    """Should reference the universal fidelity framework document."""

    def test_fidelity_framework_reference(self):
        content = _load_content()
        assert "fidelity-framework.md" in content


# ---------------------------------------------------------------------------
# AC-14: update_fidelity tool mentioned
# ---------------------------------------------------------------------------
class TestUpdateFidelityTool:
    """The orchestrator should know about the update_fidelity tool."""

    def test_update_fidelity_mentioned(self):
        content = _load_content()
        assert "update_fidelity" in content
