"""Tests for agents/builder.md — fidelity framework awareness updates."""

from pathlib import Path


# ---------------------------------------------------------------------------
# AC-1: File exists with valid structure
# ---------------------------------------------------------------------------
class TestFileStructure:
    """AC-1: File exists at agents/builder.md with valid frontmatter."""

    def test_file_exists(self, builder_path: Path):
        assert builder_path.exists(), "agents/builder.md must exist"

    def test_frontmatter_parses(self, builder_frontmatter: dict):
        assert isinstance(builder_frontmatter, dict), "Frontmatter must parse to a dict"

    def test_meta_has_name(self, builder_frontmatter: dict):
        assert builder_frontmatter["meta"]["name"] == "builder", (
            "meta.name must be 'builder'"
        )

    def test_meta_has_description(self, builder_frontmatter: dict):
        assert "description" in builder_frontmatter["meta"], (
            "meta must have 'description'"
        )
        assert len(builder_frontmatter["meta"]["description"].strip()) > 0, (
            "description must not be empty"
        )

    def test_frontmatter_has_tools(self, builder_frontmatter: dict):
        assert "tools" in builder_frontmatter, "Frontmatter must have 'tools' section"
        assert isinstance(builder_frontmatter["tools"], list), "tools must be a list"


# ---------------------------------------------------------------------------
# AC-2: Fidelity framework awareness — Implementation lens
# ---------------------------------------------------------------------------
class TestFidelityAwareness:
    """AC-2: Builder is aware of the fidelity framework and its lens."""

    def test_mentions_fidelity(self, builder_body: str):
        body = builder_body.lower()
        assert "fidelity" in body, "Must mention fidelity framework"

    def test_mentions_implementation_lens(self, builder_body: str):
        body = builder_body.lower()
        assert "implementation" in body and "lens" in body, (
            "Must mention the Implementation lens it serves"
        )

    def test_mentions_translation_loss(self, builder_body: str):
        """Agent should understand its role in reducing translation loss."""
        body = builder_body.lower()
        assert "translation loss" in body or "translation-loss" in body, (
            "Must reference translation loss concept"
        )


# ---------------------------------------------------------------------------
# AC-3: Builder-specific — partial spec handling
# ---------------------------------------------------------------------------
class TestPartialSpecHandling:
    """AC-3: Builder understands it can start with a partial spec."""

    def test_partial_spec_acknowledged(self, builder_body: str):
        body = builder_body.lower()
        assert "partial" in body or "incomplete" in body, (
            "Must acknowledge building can begin with partial spec"
        )

    def test_fidelity_routing_awareness(self, builder_body: str):
        """Builder can be re-invoked when Implementation is the priority gap."""
        body = builder_body.lower()
        assert (
            "priority gap" in body
            or "priority_gap" in body
            or ("weakest" in body and "lens" in body)
        ), "Must mention being routable via fidelity priority gap"


# ---------------------------------------------------------------------------
# AC-4: Preserved content — iron laws, process, output contract
# ---------------------------------------------------------------------------
class TestPreservedContent:
    """AC-4: Original iron laws, process, and output contract are preserved."""

    def test_iron_laws_section_exists(self, builder_body: str):
        assert "Iron Law" in builder_body or "iron law" in builder_body.lower(), (
            "Must preserve Iron Laws section"
        )

    def test_iron_law_build_exactly(self, builder_body: str):
        body = builder_body.lower()
        assert "build exactly" in body, (
            "Must preserve 'Build exactly what's spec'd' iron law"
        )

    def test_iron_law_stop_at_boundary(self, builder_body: str):
        body = builder_body.lower()
        assert (
            "stop at the boundary" in body or "acceptance criteria are met" in body
        ), "Must preserve 'Stop at the boundary' iron law"

    def test_iron_law_no_scope_expansion(self, builder_body: str):
        body = builder_body.lower()
        assert "scope" in body and "expansion" in body or "scope creep" in body, (
            "Must preserve 'No silent scope expansion' iron law"
        )

    def test_iron_law_verify_before_done(self, builder_body: str):
        body = builder_body.lower()
        assert "verify before" in body or "running checks" in body, (
            "Must preserve 'Verify before reporting done' iron law"
        )

    def test_process_section_exists(self, builder_body: str):
        assert "Your Process" in builder_body, "Must preserve 'Your Process' section"

    def test_output_contract_section_exists(self, builder_body: str):
        assert "Output Contract" in builder_body, (
            "Must preserve 'Output Contract' section"
        )

    def test_build_complete_template_preserved(self, builder_body: str):
        assert "Build Complete" in builder_body, (
            "Must preserve Build Complete report template"
        )

    def test_refinement_loop_preserved(self, builder_body: str):
        assert (
            "Refinement Loop" in builder_body or "refinement" in builder_body.lower()
        ), "Must preserve refinement loop output contract"

    def test_handoff_to_critic(self, builder_body: str):
        body = builder_body.lower()
        assert "critic" in body, "Must preserve handoff to Critic"
