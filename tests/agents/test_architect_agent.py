"""Tests for agents/architect.md — fidelity framework awareness updates."""

import re
from pathlib import Path

import yaml

AGENT_PATH = Path(__file__).resolve().parents[2] / "agents" / "architect.md"


def _load_frontmatter() -> dict:
    """Parse YAML frontmatter from architect.md (between --- delimiters)."""
    text = AGENT_PATH.read_text()
    match = re.match(r"^---\n(.*?\n)---", text, re.DOTALL)
    assert match, "architect.md must have YAML frontmatter delimited by ---"
    return yaml.safe_load(match.group(1))


def _load_body() -> str:
    """Return the markdown body after frontmatter."""
    text = AGENT_PATH.read_text()
    match = re.match(r"^---\n.*?\n---\n?(.*)", text, re.DOTALL)
    assert match, "architect.md must have a body after frontmatter"
    return match.group(1)


# ---------------------------------------------------------------------------
# AC-1: File exists with valid structure
# ---------------------------------------------------------------------------
class TestFileStructure:
    """AC-1: File exists at agents/architect.md with valid frontmatter."""

    def test_file_exists(self):
        assert AGENT_PATH.exists(), "agents/architect.md must exist"

    def test_frontmatter_parses(self):
        fm = _load_frontmatter()
        assert isinstance(fm, dict), "Frontmatter must parse to a dict"

    def test_meta_has_name(self):
        fm = _load_frontmatter()
        assert fm["meta"]["name"] == "architect", "meta.name must be 'architect'"

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
# AC-2: Fidelity framework awareness — Specification lens
# ---------------------------------------------------------------------------
class TestFidelityAwareness:
    """AC-2: Architect is aware of the fidelity framework and its lens."""

    def test_mentions_fidelity(self):
        body = _load_body().lower()
        assert "fidelity" in body, "Must mention fidelity framework"

    def test_mentions_specification_lens(self):
        body = _load_body().lower()
        assert "specification lens" in body or (
            "specification" in body and "lens" in body
        ), "Must mention the Specification lens it serves"

    def test_mentions_translation_loss(self):
        """Agent should understand its role in reducing translation loss."""
        body = _load_body().lower()
        assert "translation loss" in body or "translation-loss" in body, (
            "Must reference translation loss concept"
        )


# ---------------------------------------------------------------------------
# AC-3: Spec is a lens, not a gate
# ---------------------------------------------------------------------------
class TestSpecAsLens:
    """AC-3: Architect understands spec is a fidelity lens, not a pipeline gate."""

    def test_spec_not_a_gate(self):
        body = _load_body().lower()
        assert (
            "not a gate" in body
            or "not a blocker" in body
            or ("lens" in body and "gate" in body)
        ), "Must convey that spec is a lens, not a gate"

    def test_partial_spec_acknowledged(self):
        """Building can start before spec is 100% complete."""
        body = _load_body().lower()
        assert "partial" in body or "incomplete" in body or "evolve" in body, (
            "Must acknowledge that building can begin with partial spec"
        )

    def test_fidelity_routing_awareness(self):
        """Architect can be re-invoked when specification is the priority gap."""
        body = _load_body().lower()
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

    def test_iron_laws_section_exists(self):
        body = _load_body()
        assert "Iron Law" in body or "iron law" in body.lower(), (
            "Must preserve Iron Laws section"
        )

    def test_iron_law_no_implementation(self):
        body = _load_body()
        assert "No implementation" in body, "Must preserve 'No implementation' iron law"

    def test_iron_law_acceptance_criteria(self):
        body = _load_body().lower()
        assert "acceptance criteria" in body, (
            "Must preserve acceptance criteria iron law"
        )

    def test_iron_law_yagni(self):
        body = _load_body()
        assert "YAGNI" in body, "Must preserve YAGNI iron law"

    def test_iron_law_flag_unresolvable(self):
        body = _load_body().lower()
        assert "unresolvable" in body or "flag" in body, (
            "Must preserve 'Flag unresolvable architectural decisions' iron law"
        )

    def test_process_section_exists(self):
        body = _load_body()
        assert "Your Process" in body, "Must preserve 'Your Process' section"

    def test_output_format_section_exists(self):
        body = _load_body()
        assert "Output Format" in body, "Must preserve 'Output Format' section"

    def test_specification_document_template_preserved(self):
        body = _load_body()
        assert "Specification Document" in body or "Specification:" in body, (
            "Must preserve Specification Document template"
        )

    def test_verify_against_intent_preserved(self):
        body = _load_body()
        assert (
            "Verify Against Intent" in body or "verify against intent" in body.lower()
        ), "Must preserve 'Verify Against Intent' section"

    def test_handoff_to_builder(self):
        body = _load_body().lower()
        assert "builder" in body, "Must preserve handoff to Builder"
