"""Tests for bundle.md — ZeroVector v0.3.0 integration validation.

Verifies that the bundle manifest:
- Declares version 0.3.0 in YAML frontmatter
- Includes zerovector:behaviors/zerovector-crew (not the old methodology behavior)
- References the fidelity-convergence recipe
- That behaviors/zerovector-methodology.yaml no longer exists (replaced by
  behaviors/fidelity.yaml + behaviors/zerovector-crew.yaml)
- That behaviors/zerovector-crew.yaml and behaviors/fidelity.yaml both exist
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_MD = REPO_ROOT / "bundle.md"
BEHAVIORS_DIR = REPO_ROOT / "behaviors"


# ---------------------------------------------------------------------------
# Helper — parse YAML frontmatter from bundle.md
# ---------------------------------------------------------------------------


def _parse_frontmatter(text: str) -> dict:
    """Extract and parse the YAML frontmatter block from a markdown file."""
    if not text.startswith("---"):
        raise ValueError(
            "bundle.md does not start with YAML frontmatter delimiter '---'"
        )
    # Strip the leading "---\n", find the closing "---"
    rest = text[3:].lstrip("\n")
    end = rest.find("\n---")
    if end == -1:
        raise ValueError("bundle.md frontmatter closing '---' not found")
    return yaml.safe_load(rest[:end])


@pytest.fixture(scope="module")
def bundle_text() -> str:
    assert BUNDLE_MD.exists(), f"bundle.md must exist at {BUNDLE_MD}"
    return BUNDLE_MD.read_text()


@pytest.fixture(scope="module")
def frontmatter(bundle_text: str) -> dict:
    return _parse_frontmatter(bundle_text)


# ---------------------------------------------------------------------------
# AC-1: bundle.md exists and frontmatter is valid YAML
# ---------------------------------------------------------------------------


class TestBundleMdExists:
    """AC-1: bundle.md is present and has parseable YAML frontmatter."""

    def test_file_exists(self):
        assert BUNDLE_MD.exists(), "bundle.md must exist at the repo root"

    def test_frontmatter_is_valid_yaml(self, frontmatter: dict):
        assert isinstance(frontmatter, dict), "frontmatter must parse to a dict"

    def test_frontmatter_has_bundle_key(self, frontmatter: dict):
        assert "bundle" in frontmatter, "frontmatter must have a 'bundle' key"

    def test_frontmatter_has_includes_key(self, frontmatter: dict):
        assert "includes" in frontmatter, "frontmatter must have an 'includes' key"


# ---------------------------------------------------------------------------
# AC-2: Version is 0.3.0
# ---------------------------------------------------------------------------


class TestBundleVersion:
    """AC-2: bundle.md declares version 0.3.0."""

    def test_version_is_0_3_0(self, frontmatter: dict):
        version = frontmatter["bundle"]["version"]
        assert version == "0.3.0", f"bundle.md version must be '0.3.0', got '{version}'"


# ---------------------------------------------------------------------------
# AC-3: Includes zerovector-crew, NOT zerovector-methodology
# ---------------------------------------------------------------------------


class TestBundleIncludes:
    """AC-3: includes section references zerovector-crew, not zerovector-methodology."""

    def test_includes_is_a_list(self, frontmatter: dict):
        assert isinstance(frontmatter["includes"], list), "'includes' must be a list"

    def test_includes_zerovector_crew(self, frontmatter: dict):
        bundles = [entry["bundle"] for entry in frontmatter["includes"]]
        assert any("zerovector-crew" in b for b in bundles), (
            "includes must contain an entry referencing 'zerovector-crew'"
        )

    def test_does_not_include_zerovector_methodology(self, frontmatter: dict):
        bundles = [entry["bundle"] for entry in frontmatter["includes"]]
        assert "zerovector:behaviors/zerovector-methodology" not in bundles, (
            "includes must NOT contain 'zerovector:behaviors/zerovector-methodology' "
            "(replaced by zerovector-crew)"
        )


# ---------------------------------------------------------------------------
# AC-4: Architecture description reflects fidelity convergence model (v0.3)
# ---------------------------------------------------------------------------


class TestBundleArchitectureDescription:
    """AC-4: bundle.md body describes the fidelity convergence architecture."""

    def test_mentions_fidelity(self, bundle_text: str):
        assert "fidelity" in bundle_text.lower(), (
            "bundle.md must mention 'fidelity' in its body (v0.3 convergence architecture)"
        )

    def test_mentions_convergence(self, bundle_text: str):
        assert "convergence" in bundle_text.lower(), (
            "bundle.md must mention 'convergence' in its body"
        )

    def test_mentions_fidelity_convergence_recipe(self, bundle_text: str):
        assert "fidelity-convergence" in bundle_text, (
            "bundle.md must reference 'fidelity-convergence.yaml' in the recipes section"
        )

    def test_no_linear_pipeline_diagram(self, bundle_text: str):
        """v0.2 linear pipeline diagram should be replaced."""
        assert "DECODE → (GATE 1" not in bundle_text, (
            "bundle.md must NOT contain the old v0.2 linear pipeline diagram "
            "'DECODE → (GATE 1: approve spec)…'"
        )


# ---------------------------------------------------------------------------
# AC-5: zerovector-methodology.yaml no longer exists
# ---------------------------------------------------------------------------


class TestMethodologyBehaviorRemoved:
    """AC-5: behaviors/zerovector-methodology.yaml has been deleted."""

    def test_methodology_file_does_not_exist(self):
        methodology_path = BEHAVIORS_DIR / "zerovector-methodology.yaml"
        assert not methodology_path.exists(), (
            "behaviors/zerovector-methodology.yaml must NOT exist — "
            "it is replaced by behaviors/fidelity.yaml + behaviors/zerovector-crew.yaml"
        )


# ---------------------------------------------------------------------------
# AC-6: Replacement behavior files exist
# ---------------------------------------------------------------------------


class TestReplacementBehaviorsExist:
    """AC-6: behaviors/zerovector-crew.yaml and behaviors/fidelity.yaml both exist."""

    def test_zerovector_crew_exists(self):
        path = BEHAVIORS_DIR / "zerovector-crew.yaml"
        assert path.exists(), "behaviors/zerovector-crew.yaml must exist"

    def test_fidelity_exists(self):
        path = BEHAVIORS_DIR / "fidelity.yaml"
        assert path.exists(), "behaviors/fidelity.yaml must exist"
