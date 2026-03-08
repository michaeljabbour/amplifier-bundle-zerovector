"""Tests for agents/intent-analyst.md — fidelity framework awareness updates."""

from pathlib import Path


# ---------------------------------------------------------------------------
# AC-1: File exists with valid structure
# ---------------------------------------------------------------------------
class TestFileStructure:
    """AC-1: File exists at agents/intent-analyst.md with valid frontmatter."""

    def test_file_exists(self, intent_analyst_path: Path):
        assert intent_analyst_path.exists(), "agents/intent-analyst.md must exist"

    def test_frontmatter_parses(self, intent_analyst_frontmatter: dict):
        assert isinstance(intent_analyst_frontmatter, dict), (
            "Frontmatter must parse to a dict"
        )

    def test_meta_has_name(self, intent_analyst_frontmatter: dict):
        assert intent_analyst_frontmatter["meta"]["name"] == "intent-analyst", (
            "meta.name must be 'intent-analyst'"
        )

    def test_meta_has_description(self, intent_analyst_frontmatter: dict):
        assert "description" in intent_analyst_frontmatter["meta"], (
            "meta must have 'description'"
        )
        assert len(intent_analyst_frontmatter["meta"]["description"].strip()) > 0, (
            "description must not be empty"
        )

    def test_frontmatter_has_tools(self, intent_analyst_frontmatter: dict):
        assert "tools" in intent_analyst_frontmatter, (
            "Frontmatter must have 'tools' section"
        )
        assert isinstance(intent_analyst_frontmatter["tools"], list), (
            "tools must be a list"
        )


# ---------------------------------------------------------------------------
# AC-2: Fidelity framework awareness — Intent Clarity lens
# ---------------------------------------------------------------------------
class TestFidelityAwareness:
    """AC-2: Intent analyst is aware of the fidelity framework and its lens."""

    def test_mentions_fidelity(self, intent_analyst_body: str):
        body = intent_analyst_body.lower()
        assert "fidelity" in body, "Must mention fidelity framework"

    def test_mentions_intent_clarity_lens(self, intent_analyst_body: str):
        body = intent_analyst_body.lower()
        assert "intent clarity" in body, (
            "Must mention the Intent Clarity lens it serves"
        )

    def test_understands_lens_role(self, intent_analyst_body: str):
        """Agent must understand it serves the Intent Clarity lens."""
        body = intent_analyst_body.lower()
        # Should connect its work to the intent clarity lens specifically
        assert "intent clarity" in body and "lens" in body, (
            "Must connect its role to the Intent Clarity lens"
        )

    def test_mentions_translation_loss(self, intent_analyst_body: str):
        """Agent should understand its role in reducing translation loss."""
        body = intent_analyst_body.lower()
        assert "translation loss" in body or "translation-loss" in body, (
            "Must reference translation loss concept"
        )


# ---------------------------------------------------------------------------
# AC-3: Optional IDD input consumption
# ---------------------------------------------------------------------------
class TestIddInputConsumption:
    """AC-3: Intent analyst can optionally consume IDD decomposition output."""

    def test_mentions_idd(self, intent_analyst_body: str):
        body = intent_analyst_body.lower()
        assert "idd" in body, "Must mention IDD as an optional input source"

    def test_idd_is_optional(self, intent_analyst_body: str):
        body = intent_analyst_body.lower()
        # IDD input should be optional, not required
        assert "optional" in body, "IDD input must be described as optional"


# ---------------------------------------------------------------------------
# AC-4: Preserved content — iron laws, process, output format
# ---------------------------------------------------------------------------
class TestPreservedContent:
    """AC-4: Original iron laws, process, and output format are preserved."""

    def test_iron_laws_section_exists(self, intent_analyst_body: str):
        assert (
            "Iron Law" in intent_analyst_body
            or "iron law" in intent_analyst_body.lower()
        ), "Must preserve Iron Laws section"

    def test_iron_law_no_implementation(self, intent_analyst_body: str):
        assert "No implementation" in intent_analyst_body, (
            "Must preserve 'No implementation' iron law"
        )

    def test_iron_law_no_questions(self, intent_analyst_body: str):
        assert "No questions" in intent_analyst_body, (
            "Must preserve 'No questions' iron law"
        )

    def test_iron_law_explicit_assumptions(self, intent_analyst_body: str):
        body = intent_analyst_body.lower()
        assert "explicit about assumptions" in body, (
            "Must preserve 'Be explicit about assumptions' iron law"
        )

    def test_iron_law_compress_faithfully(self, intent_analyst_body: str):
        assert "Compress faithfully" in intent_analyst_body, (
            "Must preserve 'Compress faithfully' iron law"
        )

    def test_process_section_exists(self, intent_analyst_body: str):
        assert (
            "Your Process" in intent_analyst_body
            or "## Your Process" in intent_analyst_body
        ), "Must preserve 'Your Process' section"

    def test_output_format_section_exists(self, intent_analyst_body: str):
        assert "Output Format" in intent_analyst_body, (
            "Must preserve 'Output Format' section"
        )

    def test_intent_document_template_preserved(self, intent_analyst_body: str):
        assert "Intent Document" in intent_analyst_body, (
            "Must preserve Intent Document template"
        )

    def test_decode_dimensions_preserved(self, intent_analyst_body: str):
        assert (
            "Decode Dimensions" in intent_analyst_body
            or "decode dimensions" in intent_analyst_body.lower()
        ), "Must preserve 'Decode Dimensions' section"

    def test_handoff_to_architect(self, intent_analyst_body: str):
        assert (
            "Handoff to Architect" in intent_analyst_body
            or "architect" in intent_analyst_body.lower()
        ), "Must preserve handoff to Architect"
