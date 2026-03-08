"""Tests for domain crew modes — fidelity convergence rewrite.

Validates that crew-build.md and crew-product.md have been rewritten from
the v0.2 linear pipeline model (Stage 1-5) to the v0.3 fidelity convergence
model, aligning with the already-rewritten crew.md and crew-instructions.md.

Each domain mode must:
- Preserve YAML frontmatter and domain identity
- Remove old pipeline stage terminology
- Adopt fidelity convergence as the orchestration model
- Reference crew-instructions.md and fidelity-framework.md for protocol
- Preserve domain-specific agent tuning
- Update anti-rationalization for fidelity concepts
- Preserve transitions
"""

from pathlib import Path

import pytest

MODES_DIR = Path(__file__).resolve().parents[2] / "modes"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def crew_build_content() -> str:
    """Load modes/crew-build.md once for the entire test module."""
    path = MODES_DIR / "crew-build.md"
    assert path.exists(), f"crew-build.md not found: {path}"
    return path.read_text()


@pytest.fixture(scope="module")
def crew_build_lower(crew_build_content: str) -> str:
    return crew_build_content.lower()


@pytest.fixture(scope="module")
def crew_product_content() -> str:
    """Load modes/crew-product.md once for the entire test module."""
    path = MODES_DIR / "crew-product.md"
    assert path.exists(), f"crew-product.md not found: {path}"
    return path.read_text()


@pytest.fixture(scope="module")
def crew_product_lower(crew_product_content: str) -> str:
    return crew_product_content.lower()


# ===================================================================
# CREW-BUILD TESTS
# ===================================================================


class TestBuildYamlFrontmatter:
    """YAML frontmatter must be preserved — mode name, tools, etc."""

    def test_has_yaml_frontmatter(self, crew_build_content: str):
        assert crew_build_content.startswith("---")

    def test_mode_name_is_crew_build(self, crew_build_content: str):
        assert "name: crew-build" in crew_build_content

    def test_delegate_tool_present(self, crew_build_content: str):
        assert "delegate" in crew_build_content

    def test_recipes_tool_present(self, crew_build_content: str):
        assert "recipes" in crew_build_content


class TestBuildOldPipelineRemoved:
    """The rewrite must remove linear pipeline stage terminology."""

    @pytest.mark.parametrize("n", range(1, 6))
    def test_no_numbered_stages(self, crew_build_content: str, n: int):
        """Should not have 'Stage 1:', 'Stage 2:', etc. as section headers."""
        assert f"Stage {n}" not in crew_build_content

    def test_no_pipeline_keyword_in_critical(self, crew_build_content: str):
        """The CRITICAL section should not describe a 'pipeline'."""
        assert "<CRITICAL>" in crew_build_content
        assert "</CRITICAL>" in crew_build_content
        start = crew_build_content.index("<CRITICAL>")
        end = crew_build_content.index("</CRITICAL>") + len("</CRITICAL>")
        critical_block = crew_build_content[start:end]
        assert "pipeline" not in critical_block.lower()

    def test_no_old_todo_pipeline_stages(self, crew_build_content: str):
        """Old pipeline-style todo like 'Decode build intent (intent-analyst' should be gone."""
        assert "Decode build intent (intent-analyst" not in crew_build_content


class TestBuildFidelityConvergencePresent:
    """The rewrite must introduce fidelity convergence as the core model."""

    def test_mentions_fidelity(self, crew_build_lower: str):
        assert "fidelity" in crew_build_lower

    def test_mentions_convergence(self, crew_build_lower: str):
        assert "convergence" in crew_build_lower

    def test_mentions_lens(self, crew_build_lower: str):
        assert "lens" in crew_build_lower


class TestBuildConvergenceLoop:
    """The mode must describe or reference the convergence loop."""

    def test_assess_pattern(self, crew_build_lower: str):
        assert "assess" in crew_build_lower

    def test_route_or_weakest_lens(self, crew_build_lower: str):
        assert (
            "weakest lens" in crew_build_lower
            or "priority gap" in crew_build_lower
            or "route" in crew_build_lower
        )

    def test_convergence_target(self, crew_build_lower: str):
        assert "target" in crew_build_lower


class TestBuildLensesAndAgents:
    """All five agents must be referenced."""

    @pytest.mark.parametrize(
        "agent",
        ["intent-analyst", "architect", "builder", "critic", "shipper"],
    )
    def test_agent_referenced(self, crew_build_lower: str, agent: str):
        assert agent in crew_build_lower, f"Missing agent reference: {agent}"


class TestBuildOrchestratorRole:
    """The orchestrator role must be preserved."""

    def test_orchestrator_mentioned(self, crew_build_lower: str):
        assert "orchestrat" in crew_build_lower

    def test_does_not_implement(self, crew_build_lower: str):
        assert "do not" in crew_build_lower or "you do not" in crew_build_lower


class TestBuildReferencesProtocol:
    """Mode file should reference crew-instructions.md and fidelity-framework.md."""

    def test_references_crew_instructions(self, crew_build_content: str):
        assert "crew-instructions.md" in crew_build_content

    def test_references_fidelity_framework(self, crew_build_content: str):
        assert "fidelity-framework.md" in crew_build_content


class TestBuildAntiRationalization:
    """Anti-rationalization must be present and use fidelity concepts."""

    def test_anti_rationalization_section(self, crew_build_content: str):
        assert (
            "Anti-Rationalization" in crew_build_content
            or "anti-rationalization" in crew_build_content
        )

    def test_fidelity_aware_anti_patterns(self, crew_build_lower: str):
        """At least one anti-pattern should reference fidelity concepts."""
        assert "anti-rationalization" in crew_build_lower
        section_start = crew_build_lower.index("anti-rationalization")
        anti_rat_section = crew_build_lower[section_start:]
        assert "fidelity" in anti_rat_section


class TestBuildTransitions:
    """Mode transitions should still be documented."""

    def test_transitions_section(self, crew_build_content: str):
        assert "Transition" in crew_build_content or "transition" in crew_build_content

    def test_debug_transition(self, crew_build_lower: str):
        assert "debug" in crew_build_lower

    def test_mode_clear(self, crew_build_lower: str):
        assert "clear" in crew_build_lower


class TestBuildApprovalPoints:
    """Fidelity-based approval points should be mentioned."""

    def test_approval_mentioned(self, crew_build_lower: str):
        assert "approval" in crew_build_lower

    def test_no_old_numbered_gates(self, crew_build_content: str):
        assert "GATE 1" not in crew_build_content
        assert "GATE 2" not in crew_build_content
        assert "GATE 3" not in crew_build_content


class TestBuildDomainIdentity:
    """Build-specific domain tuning must be preserved."""

    def test_build_domain_mentioned(self, crew_build_lower: str):
        assert "build" in crew_build_lower

    def test_code_or_software_context(self, crew_build_lower: str):
        """Build crew should still reference code/software construction."""
        assert "code" in crew_build_lower or "software" in crew_build_lower

    def test_test_first_or_tdd_mentioned(self, crew_build_lower: str):
        """Build domain should reference test-first/TDD methodology."""
        assert "test" in crew_build_lower


class TestBuildDomainTuningReference:
    """Should reference domain-tuning.md for domain-specific criteria."""

    def test_domain_tuning_reference(self, crew_build_content: str):
        assert "domain-tuning.md" in crew_build_content


# ===================================================================
# CREW-PRODUCT TESTS
# ===================================================================


class TestProductYamlFrontmatter:
    """YAML frontmatter must be preserved — mode name, tools, etc."""

    def test_has_yaml_frontmatter(self, crew_product_content: str):
        assert crew_product_content.startswith("---")

    def test_mode_name_is_crew_product(self, crew_product_content: str):
        assert "name: crew-product" in crew_product_content

    def test_delegate_tool_present(self, crew_product_content: str):
        assert "delegate" in crew_product_content

    def test_recipes_tool_present(self, crew_product_content: str):
        assert "recipes" in crew_product_content


class TestProductOldPipelineRemoved:
    """The rewrite must remove linear pipeline stage terminology."""

    @pytest.mark.parametrize("n", range(1, 6))
    def test_no_numbered_stages(self, crew_product_content: str, n: int):
        assert f"Stage {n}" not in crew_product_content

    def test_no_pipeline_keyword_in_critical(self, crew_product_content: str):
        assert "<CRITICAL>" in crew_product_content
        assert "</CRITICAL>" in crew_product_content
        start = crew_product_content.index("<CRITICAL>")
        end = crew_product_content.index("</CRITICAL>") + len("</CRITICAL>")
        critical_block = crew_product_content[start:end]
        assert "pipeline" not in critical_block.lower()

    def test_no_old_todo_pipeline_stages(self, crew_product_content: str):
        assert "Decode product intent (jobs-to-be-done" not in crew_product_content


class TestProductFidelityConvergencePresent:
    """The rewrite must introduce fidelity convergence as the core model."""

    def test_mentions_fidelity(self, crew_product_lower: str):
        assert "fidelity" in crew_product_lower

    def test_mentions_convergence(self, crew_product_lower: str):
        assert "convergence" in crew_product_lower

    def test_mentions_lens(self, crew_product_lower: str):
        assert "lens" in crew_product_lower


class TestProductConvergenceLoop:
    """The mode must describe or reference the convergence loop."""

    def test_assess_pattern(self, crew_product_lower: str):
        assert "assess" in crew_product_lower

    def test_route_or_weakest_lens(self, crew_product_lower: str):
        assert (
            "weakest lens" in crew_product_lower
            or "priority gap" in crew_product_lower
            or "route" in crew_product_lower
        )

    def test_convergence_target(self, crew_product_lower: str):
        assert "target" in crew_product_lower


class TestProductLensesAndAgents:
    """All five agents must be referenced."""

    @pytest.mark.parametrize(
        "agent",
        ["intent-analyst", "architect", "builder", "critic", "shipper"],
    )
    def test_agent_referenced(self, crew_product_lower: str, agent: str):
        assert agent in crew_product_lower, f"Missing agent reference: {agent}"


class TestProductOrchestratorRole:
    """The orchestrator role must be preserved."""

    def test_orchestrator_mentioned(self, crew_product_lower: str):
        assert "orchestrat" in crew_product_lower

    def test_does_not_implement(self, crew_product_lower: str):
        assert "do not" in crew_product_lower or "you do not" in crew_product_lower


class TestProductReferencesProtocol:
    """Mode file should reference crew-instructions.md and fidelity-framework.md."""

    def test_references_crew_instructions(self, crew_product_content: str):
        assert "crew-instructions.md" in crew_product_content

    def test_references_fidelity_framework(self, crew_product_content: str):
        assert "fidelity-framework.md" in crew_product_content


class TestProductAntiRationalization:
    """Anti-rationalization must be present and use fidelity concepts."""

    def test_anti_rationalization_section(self, crew_product_content: str):
        assert (
            "Anti-Rationalization" in crew_product_content
            or "anti-rationalization" in crew_product_content
        )

    def test_fidelity_aware_anti_patterns(self, crew_product_lower: str):
        assert "anti-rationalization" in crew_product_lower
        section_start = crew_product_lower.index("anti-rationalization")
        anti_rat_section = crew_product_lower[section_start:]
        assert "fidelity" in anti_rat_section


class TestProductTransitions:
    """Mode transitions should still be documented."""

    def test_transitions_section(self, crew_product_content: str):
        assert (
            "Transition" in crew_product_content or "transition" in crew_product_content
        )

    def test_debug_or_brainstorm_transition(self, crew_product_lower: str):
        assert "brainstorm" in crew_product_lower or "debug" in crew_product_lower

    def test_mode_clear(self, crew_product_lower: str):
        assert "clear" in crew_product_lower


class TestProductApprovalPoints:
    """Fidelity-based approval points should be mentioned."""

    def test_approval_mentioned(self, crew_product_lower: str):
        assert "approval" in crew_product_lower

    def test_no_old_numbered_gates(self, crew_product_content: str):
        assert "GATE 1" not in crew_product_content
        assert "GATE 2" not in crew_product_content
        assert "GATE 3" not in crew_product_content


class TestProductDomainIdentity:
    """Product-specific domain tuning must be preserved."""

    def test_product_domain_mentioned(self, crew_product_lower: str):
        assert "product" in crew_product_lower

    def test_ux_or_user_context(self, crew_product_lower: str):
        """Product crew should still reference UX/user concepts."""
        assert "user" in crew_product_lower or "ux" in crew_product_lower

    def test_jobs_to_be_done_or_jtbd(self, crew_product_lower: str):
        """Product domain should reference jobs-to-be-done or similar."""
        assert (
            "jobs-to-be-done" in crew_product_lower
            or "job" in crew_product_lower
            or "jtbd" in crew_product_lower
        )


class TestProductDomainTuningReference:
    """Should reference domain-tuning.md for domain-specific criteria."""

    def test_domain_tuning_reference(self, crew_product_content: str):
        assert "domain-tuning.md" in crew_product_content
