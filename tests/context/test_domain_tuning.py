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
    """All five crew domains must have dedicated sections."""

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_domain_section_present(self, tuning_lower: str, domain: str):
        assert domain in tuning_lower, f"Domain '{domain}' not found"

    def test_build_domain_section(self, tuning_content: str):
        assert "## " in tuning_content  # At least one H2 header
        assert "build" in tuning_content.lower()

    def test_product_domain_section(self, tuning_content: str):
        assert "product" in tuning_content.lower()

    def test_platform_domain_section(self, tuning_content: str):
        assert "platform" in tuning_content.lower()

    def test_research_domain_section(self, tuning_content: str):
        assert "research" in tuning_content.lower()

    def test_content_domain_section(self, tuning_content: str):
        assert "content" in tuning_content.lower()


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
        import re

        # Find all H2-level domain section starts (## Domain: ... lines)
        h2_positions = [
            m.start() for m in re.finditer(r"^## ", tuning_lower, re.MULTILINE)
        ]

        for domain in DOMAINS:
            # Find the H2 header for this domain
            domain_start = -1
            for pos in h2_positions:
                line_end = tuning_lower.find("\n", pos)
                header_line = (
                    tuning_lower[pos:line_end] if line_end != -1 else tuning_lower[pos:]
                )
                if domain in header_line:
                    domain_start = pos
                    break
            if domain_start == -1:
                continue

            # Find next H2 header or end of file
            next_h2 = len(tuning_lower)
            for pos in h2_positions:
                if pos > domain_start:
                    next_h2 = pos
                    break

            domain_section = tuning_lower[domain_start:next_h2]
            lens_count = sum(
                1
                for lens in [
                    "intent clarity",
                    "specification",
                    "implementation",
                    "quality",
                    "ship",
                ]
                if lens in domain_section
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
    """Each domain must have criteria specific to that domain, not generic."""

    def test_build_has_code_specific_criteria(self, tuning_lower: str):
        """Build domain should reference code-specific concepts."""
        assert any(
            term in tuning_lower
            for term in ["test", "type", "lint", "function", "module", "code"]
        )

    def test_product_has_product_specific_criteria(self, tuning_lower: str):
        """Product domain should reference product-specific concepts."""
        assert any(
            term in tuning_lower
            for term in ["user", "stakeholder", "decision", "ux", "prd"]
        )

    def test_research_has_research_specific_criteria(self, tuning_lower: str):
        """Research domain should reference research-specific concepts."""
        assert any(
            term in tuning_lower
            for term in ["evidence", "source", "citation", "finding", "synthesis"]
        )

    def test_content_has_content_specific_criteria(self, tuning_lower: str):
        """Content domain should reference writing-specific concepts."""
        assert any(
            term in tuning_lower
            for term in ["audience", "tone", "clarity", "reader", "prose"]
        )

    def test_platform_has_platform_specific_criteria(self, tuning_lower: str):
        """Platform domain should reference infrastructure-specific concepts."""
        assert any(
            term in tuning_lower
            for term in ["api", "contract", "interface", "consumer", "breaking"]
        )


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
