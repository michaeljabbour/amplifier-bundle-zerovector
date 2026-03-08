"""Tests for agents/shipper.md — fidelity framework awareness updates."""

from pathlib import Path


# ---------------------------------------------------------------------------
# AC-1: File exists with valid structure
# ---------------------------------------------------------------------------
class TestFileStructure:
    """AC-1: File exists at agents/shipper.md with valid frontmatter."""

    def test_file_exists(self, shipper_path: Path):
        assert shipper_path.exists(), "agents/shipper.md must exist"

    def test_frontmatter_parses(self, shipper_frontmatter: dict):
        assert isinstance(shipper_frontmatter, dict), "Frontmatter must parse to a dict"

    def test_meta_has_name(self, shipper_frontmatter: dict):
        assert shipper_frontmatter["meta"]["name"] == "shipper", (
            "meta.name must be 'shipper'"
        )

    def test_meta_has_description(self, shipper_frontmatter: dict):
        assert "description" in shipper_frontmatter["meta"], (
            "meta must have 'description'"
        )
        assert len(shipper_frontmatter["meta"]["description"].strip()) > 0, (
            "description must not be empty"
        )

    def test_frontmatter_has_tools(self, shipper_frontmatter: dict):
        assert "tools" in shipper_frontmatter, "Frontmatter must have 'tools' section"
        assert isinstance(shipper_frontmatter["tools"], list), "tools must be a list"


# ---------------------------------------------------------------------------
# AC-2: Fidelity framework awareness — Ship-Readiness lens
# ---------------------------------------------------------------------------
class TestFidelityAwareness:
    """AC-2: Shipper is aware of the fidelity framework and its lens."""

    def test_mentions_fidelity(self, shipper_body: str):
        body = shipper_body.lower()
        assert "fidelity" in body, "Must mention fidelity framework"

    def test_mentions_ship_readiness_lens(self, shipper_body: str):
        body = shipper_body.lower()
        assert (
            "ship-readiness" in body or "ship_readiness" in body
        ) and "lens" in body, "Must mention the Ship-Readiness lens it serves"

    def test_mentions_translation_loss(self, shipper_body: str):
        """Agent should understand its role in reducing translation loss."""
        body = shipper_body.lower()
        assert "translation loss" in body or "translation-loss" in body, (
            "Must reference translation loss concept"
        )


# ---------------------------------------------------------------------------
# AC-3: Shipper-specific — early invocation
# ---------------------------------------------------------------------------
class TestEarlyInvocation:
    """AC-3: Shipper understands it can be invoked before the end of the pipeline."""

    def test_early_invocation_acknowledged(self, shipper_body: str):
        body = shipper_body.lower()
        assert "early" in body or "any point" in body or "not only" in body, (
            "Must acknowledge early invocation possibility"
        )

    def test_fidelity_routing_awareness(self, shipper_body: str):
        """Shipper can be re-invoked when Ship-Readiness is the priority gap."""
        body = shipper_body.lower()
        assert (
            "priority gap" in body
            or "priority_gap" in body
            or ("weakest" in body and "lens" in body)
        ), "Must mention being routable via fidelity priority gap"


# ---------------------------------------------------------------------------
# AC-4: Preserved content — iron laws, process, delivery report
# ---------------------------------------------------------------------------
class TestPreservedContent:
    """AC-4: Original iron laws, process, and delivery report are preserved."""

    def test_iron_laws_section_exists(self, shipper_body: str):
        assert "Iron Law" in shipper_body or "iron law" in shipper_body.lower(), (
            "Must preserve Iron Laws section"
        )

    def test_iron_law_no_fail_shipped(self, shipper_body: str):
        body = shipper_body.lower()
        assert "no fail gets shipped" in body or ("fail" in body and "stop" in body), (
            "Must preserve 'No FAIL gets shipped' iron law"
        )

    def test_iron_law_execute_action(self, shipper_body: str):
        body = shipper_body.lower()
        assert "execute the action" in body or "don't improvise" in body, (
            "Must preserve 'Execute the action, don't improvise' iron law"
        )

    def test_iron_law_fall_back_to_keep(self, shipper_body: str):
        body = shipper_body.lower()
        assert "fall back" in body and "keep" in body, (
            "Must preserve 'Fall back to keep' iron law"
        )

    def test_iron_law_delivery_report_mandatory(self, shipper_body: str):
        body = shipper_body.lower()
        assert "delivery report" in body and "mandatory" in body, (
            "Must preserve 'Delivery report is mandatory' iron law"
        )

    def test_process_section_exists(self, shipper_body: str):
        assert "Your Process" in shipper_body, "Must preserve 'Your Process' section"

    def test_finish_action_semantics_preserved(self, shipper_body: str):
        assert "Finish Action" in shipper_body, (
            "Must preserve 'Finish Action Semantics' section"
        )

    def test_delivery_report_template_preserved(self, shipper_body: str):
        assert "Delivery Report" in shipper_body, (
            "Must preserve Delivery Report template"
        )

    def test_four_finish_actions_preserved(self, shipper_body: str):
        body = shipper_body.lower()
        assert all(action in body for action in ["merge", "pr", "keep", "discard"]), (
            "Must preserve all four finish actions: merge, pr, keep, discard"
        )

    def test_handoff_close_pipeline(self, shipper_body: str):
        body = shipper_body.lower()
        assert "pipeline ends here" in body or "close the pipeline" in body, (
            "Must preserve pipeline closure"
        )
