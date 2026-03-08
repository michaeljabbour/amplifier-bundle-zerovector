"""Tests for context/domain-tuning.md — fidelity-per-lens restructure.

Validates that domain-tuning.md has been restructured from the v0.2
per-agent tuning model to the v0.3 domain-specific fidelity criteria
per lens model, per the design document.

The v0.3 model organizes tuning by fidelity lens within each domain,
not by crew agent. This aligns with the fidelity convergence engine
where the critic assesses all lenses simultaneously and routes to the
weakest one.
"""

from pathlib import Path

import pytest

DOMAIN_TUNING_PATH = (
    Path(__file__).resolve().parents[2] / "context" / "domain-tuning.md"
)

DOMAINS = ["build", "product", "platform", "research", "content"]

LENSES = [
    "intent clarity",
    "specification",
    "implementation",
    "quality",
    "ship-readiness",
]

LENS_KEYS = [
    "intent_clarity",
    "specification",
    "implementation",
    "quality",
    "ship_readiness",
]


def _extract_domain_section(content_lower: str, domain: str) -> str:
    """Extract the text of a single domain's H2 section (lower-cased).

    Returns the slice from the domain's ``## `` header up to the next ``## ``
    header (or end-of-file).  Returns an empty string if the domain header is
    not found.
    """
    import re

    h2_positions = [
        m.start() for m in re.finditer(r"^## ", content_lower, re.MULTILINE)
    ]
    domain_start = -1
    for pos in h2_positions:
        line_end = content_lower.find("\n", pos)
        header_line = (
            content_lower[pos:line_end] if line_end != -1 else content_lower[pos:]
        )
        if domain in header_line:
            domain_start = pos
            break
    if domain_start == -1:
        return ""
    next_h2 = len(content_lower)
    for pos in h2_positions:
        if pos > domain_start:
            next_h2 = pos
            break
    return content_lower[domain_start:next_h2]


@pytest.fixture(scope="module")
def tuning_content() -> str:
    """Load domain-tuning.md once for the entire test module."""
    assert DOMAIN_TUNING_PATH.exists(), (
        f"domain-tuning.md not found: {DOMAIN_TUNING_PATH}"
    )
    return DOMAIN_TUNING_PATH.read_text()


@pytest.fixture(scope="module")
def tuning_lower(tuning_content: str) -> str:
    """Lower-cased domain-tuning.md for case-insensitive checks."""
    return tuning_content.lower()


# ---------------------------------------------------------------------------
# AC-1: File exists and is non-empty
# ---------------------------------------------------------------------------
class TestFileExists:
    def test_file_exists(self):
        assert DOMAIN_TUNING_PATH.exists()

    def test_file_non_empty(self, tuning_content: str):
        assert len(tuning_content.strip()) > 200, "File must have substantial content"


# ---------------------------------------------------------------------------
# AC-2: Old per-agent-per-domain section headers REMOVED
# ---------------------------------------------------------------------------
class TestOldAgentHeadersRemoved:
    """The restructure must remove agent-per-domain section headers like
    '### Intent Analyst — build focus' in favor of lens-per-domain headers."""

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_no_intent_analyst_domain_header(self, tuning_content: str, domain: str):
        assert f"Intent Analyst \u2014 {domain} focus" not in tuning_content

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_no_architect_domain_header(self, tuning_content: str, domain: str):
        assert f"Architect \u2014 {domain} focus" not in tuning_content

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_no_builder_domain_header(self, tuning_content: str, domain: str):
        assert f"Builder \u2014 {domain} focus" not in tuning_content

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_no_critic_domain_header(self, tuning_content: str, domain: str):
        assert f"Critic \u2014 {domain} focus" not in tuning_content

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_no_shipper_domain_header(self, tuning_content: str, domain: str):
        assert f"Shipper \u2014 {domain} focus" not in tuning_content


# ---------------------------------------------------------------------------
# AC-3: All five domains present as sections
# ---------------------------------------------------------------------------
class TestAllDomainsPresent:
    """All five crew domains must have dedicated H2 sections."""

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_domain_section_present(self, tuning_lower: str, domain: str):
        section = _extract_domain_section(tuning_lower, domain)
        assert section, f"Domain '{domain}' not found as an H2 section"


# ---------------------------------------------------------------------------
# AC-4: All five lenses referenced in the document
# ---------------------------------------------------------------------------
class TestAllLensesReferenced:
    """All five fidelity lenses must appear in the document."""

    def test_intent_clarity_lens(self, tuning_lower: str):
        assert "intent clarity" in tuning_lower or "intent_clarity" in tuning_lower

    def test_specification_lens(self, tuning_lower: str):
        assert "specification" in tuning_lower

    def test_implementation_lens(self, tuning_lower: str):
        assert "implementation" in tuning_lower

    def test_quality_lens(self, tuning_lower: str):
        assert "quality" in tuning_lower

    def test_ship_readiness_lens(self, tuning_lower: str):
        assert "ship-readiness" in tuning_lower or "ship_readiness" in tuning_lower


# ---------------------------------------------------------------------------
# AC-5: Lens-based structure within domains (not agent-based)
# ---------------------------------------------------------------------------
class TestLensBasedStructure:
    """Each domain should have lens-organized subsections, not agent-organized."""

    def test_lens_headers_present(self, tuning_content: str):
        """Document should have subsection headers referencing lenses."""
        lens_header_count = 0
        for lens in LENSES:
            if (
                f"### {lens.title()}" in tuning_content
                or f"### {lens}" in tuning_content.lower()
            ):
                lens_header_count += 1
        # We expect at least some lens headers across the document
        # (each domain has 5 lenses, but we just need to confirm the pattern)
        assert lens_header_count >= 3, (
            f"Expected lens-based headers (### Intent Clarity, ### Quality, etc.), "
            f"found {lens_header_count}"
        )

    def test_multiple_lens_references_per_domain(self, tuning_lower: str):
        """Each domain section should reference multiple lenses."""
        for domain in DOMAINS:
            section = _extract_domain_section(tuning_lower, domain)
            if not section:
                continue
            lens_count = sum(
                1
                for lens in [
                    "intent clarity",
                    "specification",
                    "implementation",
                    "quality",
                    "ship",
                ]
                if lens in section
            )
            assert lens_count >= 4, (
                f"Domain '{domain}' should reference at least 4 lenses, found {lens_count}"
            )


# ---------------------------------------------------------------------------
# AC-6: Fidelity terminology present
# ---------------------------------------------------------------------------
class TestFidelityTerminology:
    """The restructured document must use fidelity convergence terminology."""

    def test_mentions_fidelity(self, tuning_lower: str):
        assert "fidelity" in tuning_lower

    def test_mentions_lens_or_lenses(self, tuning_lower: str):
        assert "lens" in tuning_lower

    def test_mentions_scoring_or_criteria(self, tuning_lower: str):
        assert "scor" in tuning_lower or "criteria" in tuning_lower


# ---------------------------------------------------------------------------
# AC-7: References fidelity-framework.md
# ---------------------------------------------------------------------------
class TestFidelityFrameworkReference:
    """Should reference the universal fidelity framework document."""

    def test_fidelity_framework_reference(self, tuning_content: str):
        assert "fidelity-framework.md" in tuning_content


# ---------------------------------------------------------------------------
# AC-8: Domain-specific criteria (not just generic restatements)
# ---------------------------------------------------------------------------
class TestDomainSpecificCriteria:
    """Each domain section must contain criteria specific to that domain."""

    def test_build_has_code_specific_criteria(self, tuning_lower: str):
        """Build domain section should reference code-specific concepts."""
        section = _extract_domain_section(tuning_lower, "build")
        assert section, "build domain section not found"
        assert any(
            term in section
            for term in ["test", "type", "lint", "function", "module", "code"]
        ), "build section missing code-specific criteria"

    def test_product_has_product_specific_criteria(self, tuning_lower: str):
        """Product domain section should reference product-specific concepts."""
        section = _extract_domain_section(tuning_lower, "product")
        assert section, "product domain section not found"
        assert any(
            term in section for term in ["user", "stakeholder", "decision", "ux", "prd"]
        ), "product section missing product-specific criteria"

    def test_research_has_research_specific_criteria(self, tuning_lower: str):
        """Research domain section should reference research-specific concepts."""
        section = _extract_domain_section(tuning_lower, "research")
        assert section, "research domain section not found"
        assert any(
            term in section
            for term in ["evidence", "source", "citation", "finding", "synthesis"]
        ), "research section missing research-specific criteria"

    def test_content_has_content_specific_criteria(self, tuning_lower: str):
        """Content domain section should reference writing-specific concepts."""
        section = _extract_domain_section(tuning_lower, "content")
        assert section, "content domain section not found"
        assert any(
            term in section
            for term in ["audience", "tone", "clarity", "reader", "prose"]
        ), "content section missing writing-specific criteria"

    def test_platform_has_platform_specific_criteria(self, tuning_lower: str):
        """Platform domain section should reference infrastructure-specific concepts."""
        section = _extract_domain_section(tuning_lower, "platform")
        assert section, "platform domain section not found"
        assert any(
            term in section
            for term in ["api", "contract", "interface", "consumer", "breaking"]
        ), "platform section missing infrastructure-specific criteria"


# ---------------------------------------------------------------------------
# AC-9: Evidence guidance present
# ---------------------------------------------------------------------------
class TestEvidenceGuidance:
    """Document should provide guidance on what evidence to look for per lens."""

    def test_evidence_or_indicators_mentioned(self, tuning_lower: str):
        """Should mention evidence, indicators, or signals for assessment."""
        assert any(
            term in tuning_lower
            for term in ["evidence", "indicator", "signal", "look for", "assess"]
        )
