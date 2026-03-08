"""Structural validation tests for recipes/fidelity-convergence.yaml.

Verifies that the core convergence loop recipe is correctly structured:
- YAML parses without error
- Metadata fields are present and correct
- Context variables are defined
- Step IDs exist in the correct order
- Convergence loop is correctly configured
- While-steps contain the required sub-steps
- parse_json is set where required
- Agent references are correct
"""

from pathlib import Path

import pytest
import yaml

RECIPES_DIR = Path(__file__).resolve().parents[2] / "recipes"
RECIPE_PATH = RECIPES_DIR / "fidelity-convergence.yaml"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def recipe_path() -> Path:
    return RECIPE_PATH


@pytest.fixture(scope="module")
def recipe(recipe_path: Path) -> dict:
    """Load and parse the fidelity-convergence.yaml recipe."""
    assert recipe_path.exists(), (
        f"Recipe file must exist at {recipe_path}. "
        "Create recipes/fidelity-convergence.yaml to pass these tests."
    )
    return yaml.safe_load(recipe_path.read_text())


@pytest.fixture(scope="module")
def steps(recipe: dict) -> list:
    """Return the top-level steps list from the flat recipe."""
    assert "steps" in recipe, "Recipe must have a top-level 'steps' key (flat recipe)"
    return recipe["steps"]


@pytest.fixture(scope="module")
def steps_by_id(steps: list) -> dict:
    """Return a dict mapping step id -> step dict for easy lookup."""
    return {step["id"]: step for step in steps}


@pytest.fixture(scope="module")
def convergence_loop(steps_by_id: dict) -> dict:
    """Return the convergence-loop step."""
    assert "convergence-loop" in steps_by_id, (
        "Steps must include a step with id 'convergence-loop'"
    )
    return steps_by_id["convergence-loop"]


@pytest.fixture(scope="module")
def while_steps_by_id(convergence_loop: dict) -> dict:
    """Return a dict mapping while_step id -> step dict."""
    assert "while_steps" in convergence_loop, "convergence-loop must have 'while_steps'"
    return {step["id"]: step for step in convergence_loop["while_steps"]}


# ---------------------------------------------------------------------------
# AC-1: File parses correctly
# ---------------------------------------------------------------------------


class TestYamlParses:
    """AC-1: Recipe file exists and parses as valid YAML."""

    def test_file_exists(self, recipe_path: Path):
        assert recipe_path.exists(), "recipes/fidelity-convergence.yaml must exist"

    def test_yaml_parses_to_dict(self, recipe: dict):
        assert isinstance(recipe, dict), "Recipe YAML must parse to a dict"

    def test_recipe_is_not_empty(self, recipe: dict):
        assert len(recipe) > 0, "Recipe dict must not be empty"


# ---------------------------------------------------------------------------
# AC-2: Recipe metadata
# ---------------------------------------------------------------------------


class TestRecipeMetadata:
    """AC-2: Recipe has correct metadata fields."""

    def test_has_name(self, recipe: dict):
        assert "name" in recipe, "Recipe must have a 'name' field"

    def test_name_is_fidelity_convergence(self, recipe: dict):
        assert recipe["name"] == "fidelity-convergence", (
            "Recipe name must be 'fidelity-convergence'"
        )

    def test_has_version(self, recipe: dict):
        assert "version" in recipe, "Recipe must have a 'version' field"

    def test_version_is_0_3_0(self, recipe: dict):
        assert recipe["version"] == "0.3.0", "Recipe version must be '0.3.0'"

    def test_has_description(self, recipe: dict):
        assert "description" in recipe, "Recipe must have a 'description' field"

    def test_description_is_non_empty(self, recipe: dict):
        assert isinstance(recipe["description"], str), "description must be a string"
        assert len(recipe["description"].strip()) > 0, "description must not be empty"


# ---------------------------------------------------------------------------
# AC-3: Context variables
# ---------------------------------------------------------------------------


class TestContextVariables:
    """AC-3: Required context variables are defined."""

    def test_has_context(self, recipe: dict):
        assert "context" in recipe, "Recipe must have a 'context' section"

    def test_context_has_intent(self, recipe: dict):
        assert "intent" in recipe["context"], "context must define 'intent'"

    def test_context_has_domain(self, recipe: dict):
        assert "domain" in recipe["context"], "context must define 'domain'"

    def test_context_has_target_fidelity(self, recipe: dict):
        assert "target_fidelity" in recipe["context"], (
            "context must define 'target_fidelity'"
        )

    def test_context_has_fidelity_score(self, recipe: dict):
        assert "fidelity_score" in recipe["context"], (
            "context must define 'fidelity_score'"
        )

    def test_context_has_project_path(self, recipe: dict):
        assert "project_path" in recipe["context"], "context must define 'project_path'"

    def test_context_has_intent_document(self, recipe: dict):
        assert "intent_document" in recipe["context"], (
            "context must define 'intent_document'"
        )

    def test_context_has_specification(self, recipe: dict):
        assert "specification" in recipe["context"], (
            "context must define 'specification'"
        )

    def test_domain_default_is_general(self, recipe: dict):
        assert recipe["context"]["domain"] == "general", (
            "context.domain default must be 'general'"
        )

    def test_target_fidelity_default_is_0_85(self, recipe: dict):
        assert str(recipe["context"]["target_fidelity"]) == "0.85", (
            "context.target_fidelity default must be '0.85'"
        )

    def test_fidelity_score_default_is_0(self, recipe: dict):
        assert str(recipe["context"]["fidelity_score"]) == "0", (
            "context.fidelity_score default must be '0'"
        )


# ---------------------------------------------------------------------------
# AC-4: Step IDs exist in the correct order
# ---------------------------------------------------------------------------


class TestStepOrder:
    """AC-4: Step IDs exist in the correct order."""

    EXPECTED_STEP_IDS = [
        "establish-intent",
        "initial-assessment",
        "extract-score",
        "convergence-loop",
        "convergence-summary",
    ]

    def test_steps_key_exists(self, recipe: dict):
        assert "steps" in recipe, "Recipe must have a top-level 'steps' key"

    def test_steps_is_a_list(self, steps: list):
        assert isinstance(steps, list), "'steps' must be a list"

    def test_all_required_step_ids_present(self, steps_by_id: dict):
        for step_id in self.EXPECTED_STEP_IDS:
            assert step_id in steps_by_id, (
                f"Steps must include a step with id '{step_id}'"
            )

    def test_step_order_is_correct(self, steps: list):
        actual_ids = [step["id"] for step in steps]
        # Verify each expected ID appears in the correct relative order
        positions = []
        for step_id in self.EXPECTED_STEP_IDS:
            assert step_id in actual_ids, f"Step '{step_id}' must exist"
            positions.append(actual_ids.index(step_id))
        assert positions == sorted(positions), (
            f"Steps must appear in order {self.EXPECTED_STEP_IDS}, "
            f"but found at positions {positions}"
        )


# ---------------------------------------------------------------------------
# AC-5: Convergence loop configuration
# ---------------------------------------------------------------------------


class TestConvergenceLoop:
    """AC-5: convergence-loop step is correctly configured."""

    def test_has_while_condition(self, convergence_loop: dict):
        assert "while_condition" in convergence_loop, (
            "convergence-loop must have 'while_condition'"
        )

    def test_while_condition_references_fidelity_score(self, convergence_loop: dict):
        cond = convergence_loop["while_condition"]
        assert "fidelity_score" in cond, (
            "while_condition must reference '{{fidelity_score}}'"
        )

    def test_while_condition_references_target_fidelity(self, convergence_loop: dict):
        cond = convergence_loop["while_condition"]
        assert "target_fidelity" in cond, (
            "while_condition must reference '{{target_fidelity}}'"
        )

    def test_has_max_while_iterations(self, convergence_loop: dict):
        assert "max_while_iterations" in convergence_loop, (
            "convergence-loop must have 'max_while_iterations'"
        )

    def test_max_while_iterations_is_8(self, convergence_loop: dict):
        assert convergence_loop["max_while_iterations"] == 8, (
            "max_while_iterations must be 8"
        )

    def test_has_break_when(self, convergence_loop: dict):
        assert "break_when" in convergence_loop, (
            "convergence-loop must have 'break_when'"
        )

    def test_break_when_references_fidelity_score(self, convergence_loop: dict):
        bw = convergence_loop["break_when"]
        assert "fidelity_score" in bw, "break_when must reference '{{fidelity_score}}'"

    def test_has_update_context(self, convergence_loop: dict):
        assert "update_context" in convergence_loop, (
            "convergence-loop must have 'update_context'"
        )

    def test_update_context_has_fidelity_score(self, convergence_loop: dict):
        uc = convergence_loop["update_context"]
        assert "fidelity_score" in uc, "update_context must map 'fidelity_score'"

    def test_update_context_fidelity_score_references_assessment(
        self, convergence_loop: dict
    ):
        uc = convergence_loop["update_context"]
        assert "assessment" in uc["fidelity_score"], (
            "update_context.fidelity_score must reference '{{assessment.overall}}'"
        )


# ---------------------------------------------------------------------------
# AC-6: While-steps contain route-to-gap and re-assess
# ---------------------------------------------------------------------------


class TestWhileSteps:
    """AC-6: while_steps contain the required sub-steps."""

    def test_has_while_steps(self, convergence_loop: dict):
        assert "while_steps" in convergence_loop, (
            "convergence-loop must have 'while_steps'"
        )

    def test_while_steps_is_a_list(self, convergence_loop: dict):
        assert isinstance(convergence_loop["while_steps"], list), (
            "'while_steps' must be a list"
        )

    def test_while_steps_has_route_to_gap(self, while_steps_by_id: dict):
        assert "route-to-gap" in while_steps_by_id, (
            "while_steps must contain a step with id 'route-to-gap'"
        )

    def test_while_steps_has_re_assess(self, while_steps_by_id: dict):
        assert "re-assess" in while_steps_by_id, (
            "while_steps must contain a step with id 're-assess'"
        )

    def test_route_to_gap_has_on_error_continue(self, while_steps_by_id: dict):
        route = while_steps_by_id["route-to-gap"]
        assert "on_error" in route, "route-to-gap must have 'on_error'"
        assert route["on_error"] == "continue", (
            "route-to-gap on_error must be 'continue'"
        )

    def test_route_to_gap_order_before_re_assess(self, convergence_loop: dict):
        ids = [step["id"] for step in convergence_loop["while_steps"]]
        assert "route-to-gap" in ids, "route-to-gap must exist in while_steps"
        assert "re-assess" in ids, "re-assess must exist in while_steps"
        assert ids.index("route-to-gap") < ids.index("re-assess"), (
            "route-to-gap must appear before re-assess in while_steps"
        )


# ---------------------------------------------------------------------------
# AC-7: parse_json on assessment steps
# ---------------------------------------------------------------------------


class TestParseJson:
    """AC-7: initial-assessment and re-assess have parse_json: true."""

    def test_initial_assessment_has_parse_json(self, steps_by_id: dict):
        step = steps_by_id["initial-assessment"]
        assert step.get("parse_json") is True, (
            "initial-assessment must have 'parse_json: true'"
        )

    def test_re_assess_has_parse_json(self, while_steps_by_id: dict):
        step = while_steps_by_id["re-assess"]
        assert step.get("parse_json") is True, "re-assess must have 'parse_json: true'"


# ---------------------------------------------------------------------------
# AC-8: Agent references
# ---------------------------------------------------------------------------


class TestAgentReferences:
    """AC-8: Agent references use correct zerovector namespaced names."""

    def test_establish_intent_uses_intent_analyst(self, steps_by_id: dict):
        step = steps_by_id["establish-intent"]
        assert step.get("agent") == "zerovector:intent-analyst", (
            "establish-intent must use agent 'zerovector:intent-analyst'"
        )

    def test_initial_assessment_uses_critic(self, steps_by_id: dict):
        step = steps_by_id["initial-assessment"]
        assert step.get("agent") == "zerovector:critic", (
            "initial-assessment must use agent 'zerovector:critic'"
        )

    def test_re_assess_uses_critic(self, while_steps_by_id: dict):
        step = while_steps_by_id["re-assess"]
        assert step.get("agent") == "zerovector:critic", (
            "re-assess must use agent 'zerovector:critic'"
        )

    def test_recipe_is_not_staged(self, recipe: dict):
        """Flat recipe: must NOT use 'stages' key."""
        assert "stages" not in recipe, (
            "fidelity-convergence must be a flat recipe (no 'stages' key)"
        )

    def test_extract_score_is_bash(self, steps_by_id: dict):
        step = steps_by_id["extract-score"]
        assert step.get("type") == "bash", (
            "extract-score must be a bash step (type: bash)"
        )

    def test_convergence_summary_is_bash(self, steps_by_id: dict):
        step = steps_by_id["convergence-summary"]
        assert step.get("type") == "bash", (
            "convergence-summary must be a bash step (type: bash)"
        )
