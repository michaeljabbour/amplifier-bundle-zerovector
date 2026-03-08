"""Tests for agents/architect.md — fidelity framework awareness updates."""

from pathlib import Path


# ---------------------------------------------------------------------------
# AC-1: File exists with valid structure
# ---------------------------------------------------------------------------
class TestFileStructure:
    """AC-1: File exists at agents/architect.md with valid frontmatter."""

    def test_file_exists(self, architect_path: Path):
        assert architect_path.exists(), "agents/architect.md must exist"

    def test_frontmatter_parses(self, architect_frontmatter: dict):
        assert isinstance(architect_frontmatter, dict), (
            "Frontmatter must parse to a dict"
        )

    def test_meta_has_name(self, architect_frontmatter: dict):
        assert architect_frontmatter["meta"]["name"] == "architect", (
            "meta.name must be 'architect'"
        )

    def test_meta_has_description(self, architect_frontmatter: dict):
        assert "description" in architect_frontmatter["meta"], (
            "meta must have 'description'"
        )
        assert len(architect_frontmatter["meta"]["description"].strip()) > 0, (
            "description must not be empty"
        )

    def test_frontmatter_has_tools(self, architect_frontmatter: dict):
        assert "tools" in architect_frontmatter, "Frontmatter must have 'tools' section"
        assert isinstance(architect_frontmatter["tools"], list), "tools must be a list"


# ---------------------------------------------------------------------------
# AC-2: Fidelity framework awareness — Specification lens
# ---------------------------------------------------------------------------
class TestFidelityAwareness:
    """AC-2: Architect is aware of the fidelity framework and its lens."""

    def test_mentions_fidelity(self, architect_body: str):
        body = architect_body.lower()
        assert "fidelity" in body, "Must mention fidelity framework"

    def test_mentions_specification_lens(self, architect_body: str):
        body = architect_body.lower()
        assert "specification lens" in body or (
            "specification" in body and "lens" in body
        ), "Must mention the Specification lens it serves"

    def test_mentions_translation_loss(self, architect_body: str):
        """Agent should understand its role in reducing translation loss."""
        body = architect_body.lower()
        assert "translation loss" in body or "translation-loss" in body, (
            "Must reference translation loss concept"
        )


# ---------------------------------------------------------------------------
# AC-3: Spec is a lens, not a gate
# ---------------------------------------------------------------------------
class TestSpecAsLens:
    """AC-3: Architect understands spec is a fidelity lens, not a pipeline gate."""

    def test_spec_not_a_gate(self, architect_body: str):
        body = architect_body.lower()
        assert (
            "not a gate" in body
            or "not a blocker" in body
            or ("lens" in body and "gate" in body)
        ), "Must convey that spec is a lens, not a gate"

    def test_partial_spec_acknowledged(self, architect_body: str):
        """Building can start before spec is 100% complete."""
        body = architect_body.lower()
        assert "partial" in body or "incomplete" in body or "evolve" in body, (
            "Must acknowledge that building can begin with partial spec"
        )

    def test_fidelity_routing_awareness(self, architect_body: str):
        """Architect can be re-invoked when specification is the priority gap."""
        body = architect_body.lower()
        assert (
            "priority gap" in body
            or "priority_gap" in body
            or ("weakest" in body and "lens" in body)
        ), "Must mention being routable via fidelity priority gap"


# ---------------------------------------------------------------------------
# AC-4: Preserved content — iron laws, process, output format
# ---------------------------------------------------------------------------
class TestPreservedContent:
    """AC-4: Original iron laws, process, and output format are preserved."""

    def test_iron_laws_section_exists(self, architect_body: str):
        assert "Iron Law" in architect_body or "iron law" in architect_body.lower(), (
            "Must preserve Iron Laws section"
        )

    def test_iron_law_no_implementation(self, architect_body: str):
        assert "No implementation" in architect_body, (
            "Must preserve 'No implementation' iron law"
        )

    def test_iron_law_acceptance_criteria(self, architect_body: str):
        body = architect_body.lower()
        assert "acceptance criteria" in body, (
            "Must preserve acceptance criteria iron law"
        )

    def test_iron_law_yagni(self, architect_body: str):
        assert "YAGNI" in architect_body, "Must preserve YAGNI iron law"

    def test_iron_law_flag_unresolvable(self, architect_body: str):
        body = architect_body.lower()
        assert "unresolvable" in body or "flag" in body, (
            "Must preserve 'Flag unresolvable architectural decisions' iron law"
        )

    def test_process_section_exists(self, architect_body: str):
        assert "Your Process" in architect_body, "Must preserve 'Your Process' section"

    def test_output_format_section_exists(self, architect_body: str):
        assert "Output Format" in architect_body, (
            "Must preserve 'Output Format' section"
        )

    def test_specification_document_template_preserved(self, architect_body: str):
        assert (
            "Specification Document" in architect_body
            or "Specification:" in architect_body
        ), "Must preserve Specification Document template"

    def test_verify_against_intent_preserved(self, architect_body: str):
        assert (
            "Verify Against Intent" in architect_body
            or "verify against intent" in architect_body.lower()
        ), "Must preserve 'Verify Against Intent' section"

    def test_handoff_to_builder(self, architect_body: str):
        body = architect_body.lower()
        assert "builder" in body, "Must preserve handoff to Builder"
