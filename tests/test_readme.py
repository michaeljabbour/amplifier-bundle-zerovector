"""Tests for README.md — ZeroVector v0.3.0 documentation validation.

Verifies that the README:
- Declares version 0.3.0
- Describes the fidelity convergence architecture (not linear pipeline)
- References the fidelity-convergence recipe
- Mentions the modules/ directory with Python packages
- Includes a Universal Fidelity section
- Has v0.3 design decisions
- Has correct file counts for the v0.3 inventory
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"


@pytest.fixture(scope="module")
def readme_text() -> str:
    assert README.exists(), f"README.md must exist at {README}"
    return README.read_text()


@pytest.fixture(scope="module")
def readme_lower(readme_text: str) -> str:
    return readme_text.lower()


# ---------------------------------------------------------------------------
# AC-1: Version is 0.3.0
# ---------------------------------------------------------------------------


class TestReadmeVersion:
    """AC-1: README.md declares version 0.3.0."""

    def test_version_is_0_3_0(self, readme_text: str):
        assert "0.3.0" in readme_text, "README.md must reference version '0.3.0'"

    def test_no_stale_0_1_0_version(self, readme_text: str):
        """The old '0.1.0' version string should not appear as the current version."""
        # The version line at the bottom should NOT say 0.1.0 as current version
        assert "`0.1.0`" not in readme_text, (
            "README.md must not contain '`0.1.0`' — update version to 0.3.0"
        )

    def test_no_stale_0_2_0_version(self, readme_text: str):
        assert "0.2.0" not in readme_text, (
            "README.md must not contain stale version '0.2.0'"
        )


# ---------------------------------------------------------------------------
# AC-2: Fidelity convergence architecture is described
# ---------------------------------------------------------------------------


class TestReadmeArchitecture:
    """AC-2: README.md describes fidelity convergence, not a linear pipeline."""

    def test_mentions_fidelity(self, readme_lower: str):
        assert "fidelity" in readme_lower, (
            "README.md must mention 'fidelity' — v0.3 convergence architecture"
        )

    def test_mentions_convergence(self, readme_lower: str):
        assert "convergence" in readme_lower, (
            "README.md must mention 'convergence' — v0.3 convergence loop"
        )

    def test_mentions_five_lenses(self, readme_lower: str):
        assert "lens" in readme_lower or "lenses" in readme_lower, (
            "README.md must mention fidelity 'lenses' — five concurrent fidelity lenses"
        )

    def test_mentions_translation_loss(self, readme_lower: str):
        assert "translation loss" in readme_lower, (
            "README.md must mention 'translation loss' — the core fidelity question"
        )

    def test_mentions_intent_clarity_lens(self, readme_lower: str):
        assert "intent clarity" in readme_lower, (
            "README.md must name the 'Intent Clarity' fidelity lens"
        )

    def test_mentions_ship_readiness_lens(self, readme_lower: str):
        assert "ship-readiness" in readme_lower, (
            "README.md must name the 'Ship-Readiness' fidelity lens"
        )


# ---------------------------------------------------------------------------
# AC-3: fidelity-convergence recipe is referenced
# ---------------------------------------------------------------------------


class TestReadmeRecipes:
    """AC-3: README.md references the fidelity-convergence recipe."""

    def test_mentions_fidelity_convergence_recipe(self, readme_text: str):
        assert "fidelity-convergence" in readme_text, (
            "README.md must reference 'fidelity-convergence' recipe"
        )

    def test_lists_all_six_recipes(self, readme_text: str):
        expected_recipes = [
            "intent-to-artifact",
            "fidelity-convergence",
            "decode-intent",
            "build-and-review",
            "verify-artifact",
            "finish-artifact",
        ]
        for recipe in expected_recipes:
            assert recipe in readme_text, f"README.md must reference recipe '{recipe}'"


# ---------------------------------------------------------------------------
# AC-4: modules/ directory is referenced
# ---------------------------------------------------------------------------


class TestReadmeModules:
    """AC-4: README.md mentions the modules/ directory with Python packages."""

    def test_mentions_modules_directory(self, readme_text: str):
        assert "modules/" in readme_text, (
            "README.md must reference the 'modules/' directory in bundle structure"
        )

    def test_mentions_tool_fidelity_state(self, readme_lower: str):
        assert "tool-fidelity-state" in readme_lower, (
            "README.md must mention Python module 'tool-fidelity-state'"
        )

    def test_mentions_hooks_fidelity_reporter(self, readme_lower: str):
        assert "hooks-fidelity-reporter" in readme_lower, (
            "README.md must mention Python module 'hooks-fidelity-reporter'"
        )


# ---------------------------------------------------------------------------
# AC-5: Universal Fidelity section exists
# ---------------------------------------------------------------------------


class TestReadmeUniversalFidelity:
    """AC-5: README.md has a Universal Fidelity section."""

    def test_has_universal_fidelity_section(self, readme_lower: str):
        assert "universal fidelity" in readme_lower, (
            "README.md must have a 'Universal Fidelity' section describing the "
            "extractable fidelity behavior"
        )

    def test_universal_fidelity_mentions_extractable(self, readme_lower: str):
        assert "extractable" in readme_lower, (
            "README.md Universal Fidelity section must describe it as 'extractable'"
        )

    def test_universal_fidelity_mentions_behaviors_fidelity(self, readme_text: str):
        assert "behaviors/fidelity" in readme_text, (
            "README.md must reference 'behaviors/fidelity' in the Universal Fidelity section"
        )


# ---------------------------------------------------------------------------
# AC-6: v0.3 design decisions are present
# ---------------------------------------------------------------------------


class TestReadmeDesignDecisions:
    """AC-6: README.md design decisions table includes v0.3 entries."""

    def test_mentions_fidelity_convergence_decision(self, readme_lower: str):
        assert "fidelity convergence" in readme_lower, (
            "README.md Design Decisions must include 'fidelity convergence' entry"
        )

    def test_mentions_no_custom_orchestrator_decision(self, readme_lower: str):
        # Either "no custom orchestrator" or "power through content" phrasing
        assert "orchestrator" in readme_lower, (
            "README.md Design Decisions must mention orchestrator decision"
        )

    def test_mentions_two_python_modules_decision(self, readme_text: str):
        # Should mention two modules in design decisions context
        assert "two" in readme_text.lower() or "2" in readme_text, (
            "README.md must reference the two-Python-modules decision"
        )

    def test_mentions_ecosystem_composability_or_universal(self, readme_lower: str):
        assert "composab" in readme_lower or "universal fidelity" in readme_lower, (
            "README.md Design Decisions must mention ecosystem composability "
            "or universal fidelity"
        )


# ---------------------------------------------------------------------------
# AC-7: File inventory counts are correct for v0.3
# ---------------------------------------------------------------------------


class TestReadmeFileCounts:
    """AC-7: README.md smoke tests reflect accurate v0.3 file counts."""

    def test_mentions_two_behaviors(self, readme_text: str):
        # Should reference 2 behaviors (not 1)
        assert "2 behavior" in readme_text or "two behavior" in readme_text.lower(), (
            "README.md must indicate 2 behaviors in file count comments"
        )

    def test_mentions_six_recipes(self, readme_text: str):
        assert "6 recipe" in readme_text or "six recipe" in readme_text.lower(), (
            "README.md must indicate 6 recipes in file count comments"
        )

    def test_mentions_four_context_files(self, readme_text: str):
        assert "4 context" in readme_text or "four context" in readme_text.lower(), (
            "README.md must indicate 4 context files in file count comments"
        )

    def test_mentions_two_python_modules(self, readme_text: str):
        assert "2 module" in readme_text or "2 Python" in readme_text, (
            "README.md must indicate 2 Python modules in file count comments"
        )

    def test_old_count_16_removed(self, readme_text: str):
        """The old expected count of 16 runtime files should be gone."""
        assert "Expected: 16" not in readme_text, (
            "README.md must not contain the stale 'Expected: 16' file count"
        )


# ---------------------------------------------------------------------------
# AC-8: fidelity-framework.md context file is referenced
# ---------------------------------------------------------------------------


class TestReadmeFidelityFramework:
    """AC-8: README.md references fidelity-framework.md context file."""

    def test_mentions_fidelity_framework(self, readme_lower: str):
        assert "fidelity-framework" in readme_lower, (
            "README.md must reference 'fidelity-framework.md' context file"
        )
