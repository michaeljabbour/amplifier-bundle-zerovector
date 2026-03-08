"""Tests for agents/intent-analyst.md — fidelity framework awareness updates."""

import re
from pathlib import Path

import yaml

AGENT_PATH = Path(__file__).resolve().parents[2] / "agents" / "intent-analyst.md"


def _load_frontmatter() -> dict:
    """Parse YAML frontmatter from intent-analyst.md (between --- delimiters)."""
    text = AGENT_PATH.read_text()
    match = re.match(r"^---\n(.*?\n)---", text, re.DOTALL)
    assert match, "intent-analyst.md must have YAML frontmatter delimited by ---"
    return yaml.safe_load(match.group(1))


def _load_body() -> str:
    """Return the markdown body after frontmatter."""
    text = AGENT_PATH.read_text()
    match = re.match(r"^---\n.*?\n---\n?(.*)", text, re.DOTALL)
    assert match, "intent-analyst.md must have a body after frontmatter"
    return match.group(1)


# ---------------------------------------------------------------------------
# AC-1: File exists with valid structure
# ---------------------------------------------------------------------------
class TestFileStructure:
    """AC-1: File exists at agents/intent-analyst.md with valid frontmatter."""

    def test_file_exists(self):
        assert AGENT_PATH.exists(), "agents/intent-analyst.md must exist"

    def test_frontmatter_parses(self):
        fm = _load_frontmatter()
        assert isinstance(fm, dict), "Frontmatter must parse to a dict"

    def test_meta_has_name(self):
        fm = _load_frontmatter()
        assert fm["meta"]["name"] == "intent-analyst", (
            "meta.name must be 'intent-analyst'"
        )

    def test_meta_has_description(self):
        fm = _load_frontmatter()
        assert "description" in fm["meta"], "meta must have 'description'"
        assert len(fm["meta"]["description"].strip()) > 0, (
            "description must not be empty"
        )

    def test_frontmatter_has_tools(self):
        fm = _load_frontmatter()
        assert "tools" in fm, "Frontmatter must have 'tools' section"
        assert isinstance(fm["tools"], list), "tools must be a list"


# ---------------------------------------------------------------------------
# AC-2: Fidelity framework awareness — Intent Clarity lens
# ---------------------------------------------------------------------------
class TestFidelityAwareness:
    """AC-2: Intent analyst is aware of the fidelity framework and its lens."""

    def test_mentions_fidelity(self):
        body = _load_body().lower()
        assert "fidelity" in body, "Must mention fidelity framework"

    def test_mentions_intent_clarity_lens(self):
        body = _load_body().lower()
        assert "intent clarity" in body, (
            "Must mention the Intent Clarity lens it serves"
        )

    def test_understands_lens_role(self):
        """Agent must understand it serves the Intent Clarity lens."""
        body = _load_body().lower()
        # Should connect its work to the intent clarity lens
        assert "lens" in body, "Must reference lenses in fidelity model"

    def test_mentions_translation_loss(self):
        """Agent should understand its role in reducing translation loss."""
        body = _load_body().lower()
        assert "translation loss" in body or "translation-loss" in body, (
            "Must reference translation loss concept"
        )


# ---------------------------------------------------------------------------
# AC-3: Optional IDD input consumption
# ---------------------------------------------------------------------------
class TestIddInputConsumption:
    """AC-3: Intent analyst can optionally consume IDD decomposition output."""

    def test_mentions_idd(self):
        body = _load_body().lower()
        assert "idd" in body, "Must mention IDD as an optional input source"

    def test_idd_is_optional(self):
        body = _load_body().lower()
        # IDD input should be optional, not required
        assert "optional" in body, "IDD input must be described as optional"


# ---------------------------------------------------------------------------
# AC-4: Preserved content — iron laws, process, output format
# ---------------------------------------------------------------------------
class TestPreservedContent:
    """AC-4: Original iron laws, process, and output format are preserved."""

    def test_iron_laws_section_exists(self):
        body = _load_body()
        assert "Iron Law" in body or "iron law" in body.lower(), (
            "Must preserve Iron Laws section"
        )

    def test_iron_law_no_implementation(self):
        body = _load_body()
        assert "No implementation" in body, "Must preserve 'No implementation' iron law"

    def test_iron_law_no_questions(self):
        body = _load_body()
        assert "No questions" in body, "Must preserve 'No questions' iron law"

    def test_iron_law_explicit_assumptions(self):
        body = _load_body().lower()
        assert "explicit about assumptions" in body, (
            "Must preserve 'Be explicit about assumptions' iron law"
        )

    def test_iron_law_compress_faithfully(self):
        body = _load_body()
        assert "Compress faithfully" in body, (
            "Must preserve 'Compress faithfully' iron law"
        )

    def test_process_section_exists(self):
        body = _load_body()
        assert "Your Process" in body or "## Your Process" in body, (
            "Must preserve 'Your Process' section"
        )

    def test_output_format_section_exists(self):
        body = _load_body()
        assert "Output Format" in body, "Must preserve 'Output Format' section"

    def test_intent_document_template_preserved(self):
        body = _load_body()
        assert "Intent Document" in body, "Must preserve Intent Document template"

    def test_decode_dimensions_preserved(self):
        body = _load_body()
        assert "Decode Dimensions" in body or "decode dimensions" in body.lower(), (
            "Must preserve 'Decode Dimensions' section"
        )

    def test_handoff_to_architect(self):
        body = _load_body()
        assert "Handoff to Architect" in body or "architect" in body.lower(), (
            "Must preserve handoff to Architect"
        )
