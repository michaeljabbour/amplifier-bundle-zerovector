"""Tests for agents/critic.md — multi-lens fidelity assessment protocol rewrite."""

import re
from pathlib import Path

import yaml

CRITIC_PATH = Path(__file__).resolve().parents[2] / "agents" / "critic.md"

# The 4 tool modules that must be referenced
REQUIRED_TOOL_MODULES = [
    "tool-filesystem",
    "tool-bash",
    "tool-search",
    "tool-python-check",
]

# The 5 fidelity lenses
FIDELITY_LENSES = [
    "intent_clarity",
    "specification",
    "implementation",
    "quality",
    "ship_readiness",
]


def _load_frontmatter() -> dict:
    """Parse YAML frontmatter from critic.md (between --- delimiters)."""
    text = CRITIC_PATH.read_text()
    # Match frontmatter between first pair of ---
    match = re.match(r"^---\n(.*?\n)---", text, re.DOTALL)
    assert match, "critic.md must have YAML frontmatter delimited by ---"
    return yaml.safe_load(match.group(1))


def _load_body() -> str:
    """Return the markdown body after frontmatter."""
    text = CRITIC_PATH.read_text()
    match = re.match(r"^---\n.*?\n---\n?(.*)", text, re.DOTALL)
    assert match, "critic.md must have a body after frontmatter"
    return match.group(1)


def _load_full() -> str:
    """Return the full file content."""
    return CRITIC_PATH.read_text()


# ---------------------------------------------------------------------------
# AC-1: File exists at agents/critic.md with updated content
# ---------------------------------------------------------------------------
class TestCriticFileExists:
    """AC-1: File exists at agents/critic.md."""

    def test_file_exists(self):
        assert CRITIC_PATH.exists(), "agents/critic.md must exist"

    def test_file_not_empty(self):
        assert CRITIC_PATH.stat().st_size > 0, "agents/critic.md must not be empty"


# ---------------------------------------------------------------------------
# AC-2: Frontmatter contains model_role: critique
# ---------------------------------------------------------------------------
class TestFrontmatterModelRole:
    """AC-2: Frontmatter contains model_role: critique."""

    def test_meta_has_model_role(self):
        fm = _load_frontmatter()
        assert "model_role" in fm.get("meta", {}), "meta block must contain model_role"

    def test_model_role_is_critique(self):
        fm = _load_frontmatter()
        assert fm["meta"]["model_role"] == "critique", "model_role must be 'critique'"


# ---------------------------------------------------------------------------
# AC-3: Fidelity Assessment Protocol section documents all 5 lenses
# ---------------------------------------------------------------------------
class TestFidelityAssessmentProtocol:
    """AC-3: Fidelity Assessment Protocol section documents all 5 lenses."""

    def test_fidelity_assessment_protocol_section_exists(self):
        body = _load_body()
        assert "fidelity assessment protocol" in body.lower(), (
            "Must have a Fidelity Assessment Protocol section"
        )

    def test_all_five_lenses_documented(self):
        body = _load_body().lower()
        for lens in FIDELITY_LENSES:
            # Accept both underscore and space/hyphen variants
            readable = lens.replace("_", " ")
            assert readable in body or lens in body, (
                f"Fidelity Assessment Protocol must document lens: {lens}"
            )

    def test_lenses_scored_simultaneously(self):
        body = _load_body().lower()
        assert "simultaneous" in body or "all" in body and "lenses" in body, (
            "Protocol must indicate all lenses are scored simultaneously"
        )


# ---------------------------------------------------------------------------
# AC-4: Structured JSON output format is specified
# ---------------------------------------------------------------------------
class TestStructuredJsonOutput:
    """AC-4: Structured JSON output format specified in agent description."""

    def test_json_block_present(self):
        body = _load_body()
        assert "```json" in body, "Must contain a JSON code block"

    def test_json_has_overall_field(self):
        body = _load_body()
        assert '"overall"' in body, "JSON output must include 'overall' field"

    def test_json_has_lenses_object(self):
        body = _load_body()
        assert '"lenses"' in body, "JSON output must include 'lenses' object"

    def test_json_has_all_lens_keys(self):
        body = _load_body()
        for lens in FIDELITY_LENSES:
            assert f'"{lens}"' in body, f"JSON output must include lens key: {lens}"

    def test_json_has_priority_gap(self):
        body = _load_body()
        assert '"priority_gap"' in body, (
            "JSON output must include 'priority_gap' object"
        )

    def test_priority_gap_has_lens_score_recommendation(self):
        body = _load_body()
        # priority_gap must contain lens, score, recommendation
        assert '"lens"' in body, "priority_gap must include 'lens'"
        assert '"score"' in body, "priority_gap must include 'score'"
        assert '"recommendation"' in body, "priority_gap must include 'recommendation'"


# ---------------------------------------------------------------------------
# AC-5: Two-pass protocol reframed
# ---------------------------------------------------------------------------
class TestTwoPassProtocol:
    """AC-5: Pass 1 = fidelity across all lenses; Pass 2 = domain-specific quality."""

    def test_pass_1_section_exists(self):
        body = _load_body()
        assert "pass 1" in body.lower(), "Must have Pass 1 section"

    def test_pass_1_is_fidelity(self):
        body = _load_body().lower()
        # Pass 1 should be about fidelity across lenses
        pass1_idx = body.find("pass 1")
        assert pass1_idx >= 0
        # Check that fidelity is mentioned near Pass 1
        pass1_context = body[pass1_idx : pass1_idx + 500]
        assert "fidelity" in pass1_context, "Pass 1 must be about fidelity assessment"

    def test_pass_2_section_exists(self):
        body = _load_body()
        assert "pass 2" in body.lower(), "Must have Pass 2 section"

    def test_pass_2_is_domain_quality(self):
        body = _load_body().lower()
        pass2_idx = body.find("pass 2")
        assert pass2_idx >= 0
        pass2_context = body[pass2_idx : pass2_idx + 500]
        assert "domain" in pass2_context or "quality" in pass2_context, (
            "Pass 2 must be about domain-specific quality"
        )


# ---------------------------------------------------------------------------
# AC-6: Step 6 (Update Fidelity State) instructs critic to call update_fidelity
# ---------------------------------------------------------------------------
class TestStep6UpdateFidelityState:
    """AC-6: Step 6 instructs critic to call update_fidelity tool."""

    def test_step_6_exists(self):
        body = _load_body()
        # Should have a step numbered 6
        assert re.search(r"#{1,4}\s*6[\.\s]", body) or "step 6" in body.lower(), (
            "Must have Step 6 in the process"
        )

    def test_step_6_mentions_update_fidelity(self):
        body = _load_body().lower()
        assert "update_fidelity" in body, (
            "Step 6 must reference the update_fidelity tool"
        )

    def test_step_6_mentions_fidelity_state(self):
        body = _load_body().lower()
        assert "fidelity state" in body or "fidelity" in body, (
            "Step 6 must reference updating fidelity state"
        )


# ---------------------------------------------------------------------------
# AC-7: Iron laws, tool list, VERDICT line, convergence loop preserved
# ---------------------------------------------------------------------------
class TestPreservedContent:
    """AC-7: Iron laws, tool list, VERDICT line, convergence loop preserved."""

    def test_iron_laws_section_exists(self):
        body = _load_body()
        assert "iron law" in body.lower(), "Must preserve Iron Laws section"

    def test_iron_law_be_honest(self):
        body = _load_body()
        assert "Be honest" in body, "Must preserve 'Be honest' iron law"

    def test_iron_law_cite_evidence(self):
        body = _load_body()
        assert "Cite evidence" in body or "cite evidence" in body.lower(), (
            "Must preserve 'Cite evidence' iron law"
        )

    def test_iron_law_run_checks(self):
        body = _load_body()
        assert "Run the checks" in body or "run the checks" in body.lower(), (
            "Must preserve 'Run the checks' iron law"
        )

    def test_iron_law_dont_fix(self):
        body = _load_body().lower()
        assert "don\u2019t fix" in body or "don't fix" in body, (
            "Must preserve 'Don't fix' iron law"
        )

    def test_iron_law_judge_against_intent(self):
        body = _load_body().lower()
        assert "judge against intent" in body, (
            "Must preserve 'Judge against intent' iron law"
        )

    def test_iron_law_always_end_with_verdict(self):
        body = _load_body().lower()
        assert "always end with verdict" in body, (
            "Must preserve 'Always end with VERDICT' iron law"
        )

    def test_verdict_pass(self):
        body = _load_body()
        assert "VERDICT: PASS" in body, "Must preserve VERDICT: PASS"

    def test_verdict_conditional_pass(self):
        body = _load_body()
        assert "VERDICT: CONDITIONAL_PASS" in body, (
            "Must preserve VERDICT: CONDITIONAL_PASS"
        )

    def test_verdict_fail(self):
        body = _load_body()
        assert "VERDICT: FAIL" in body, "Must preserve VERDICT: FAIL"

    def test_verdict_machine_readable(self):
        body = _load_body().lower()
        assert "machine-readable" in body or "machine readable" in body, (
            "Must state VERDICT line is machine-readable"
        )

    def test_convergence_loop_section(self):
        body = _load_body().lower()
        assert "convergence loop" in body, "Must preserve Convergence Loop section"

    def test_convergence_max_rounds(self):
        body = _load_body()
        assert "3" in body, "Must mention max 3 rounds in convergence loop"


# ---------------------------------------------------------------------------
# AC-8: Frontmatter parses without error
# ---------------------------------------------------------------------------
class TestFrontmatterValid:
    """AC-8: Frontmatter parses without error."""

    def test_frontmatter_parses(self):
        fm = _load_frontmatter()
        assert isinstance(fm, dict), "Frontmatter must parse to a dict"

    def test_frontmatter_has_meta(self):
        fm = _load_frontmatter()
        assert "meta" in fm, "Frontmatter must have 'meta' section"

    def test_frontmatter_has_tools(self):
        fm = _load_frontmatter()
        assert "tools" in fm, "Frontmatter must have 'tools' section"

    def test_meta_has_name(self):
        fm = _load_frontmatter()
        assert fm["meta"]["name"] == "critic", "meta.name must be 'critic'"

    def test_meta_has_description(self):
        fm = _load_frontmatter()
        assert "description" in fm["meta"], "meta must have 'description'"
        assert len(fm["meta"]["description"].strip()) > 0, (
            "description must not be empty"
        )


# ---------------------------------------------------------------------------
# AC-9: All 4 tool modules resolve in tool references
# ---------------------------------------------------------------------------
class TestToolModulesResolve:
    """AC-9: All 4 tool modules resolve in tool references."""

    def test_tools_is_list(self):
        fm = _load_frontmatter()
        assert isinstance(fm["tools"], list), "tools must be a list"

    def test_four_tool_modules_present(self):
        fm = _load_frontmatter()
        tool_modules = [t["module"] for t in fm["tools"]]
        for mod in REQUIRED_TOOL_MODULES:
            assert mod in tool_modules, (
                f"Tool module '{mod}' must be in tool references"
            )

    def test_each_tool_has_source(self):
        fm = _load_frontmatter()
        for tool in fm["tools"]:
            assert "source" in tool, (
                f"Tool '{tool.get('module', '?')}' must have a 'source'"
            )
            assert len(tool["source"].strip()) > 0, (
                f"Tool '{tool['module']}' source must not be empty"
            )
