"""Structural validation tests for recipes/intent-to-artifact.yaml (v0.3.0).

Verifies that the master orchestrator recipe is correctly structured as a
fidelity convergence wrapper:
- YAML parses without error
- Metadata fields are present and correct (v0.3.0)
- Context variables include target_fidelity and fidelity_score
- Exactly 3 stages exist: decode-intent, fidelity-converge, finish-artifact
- Stage 2 (fidelity-converge) contains a convergence loop with while_condition
- Stages 1 and 2 each have an approval gate
- The convergence loop assessment steps have parse_json: true
"""

from pathlib import Path

import pytest
import yaml

RECIPES_DIR = Path(__file__).resolve().parents[2] / "recipes"
RECIPE_PATH = RECIPES_DIR / "intent-to-artifact.yaml"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def recipe_path() -> Path:
    return RECIPE_PATH


@pytest.fixture(scope="module")
def recipe(recipe_path: Path) -> dict:
    """Load and parse the intent-to-artifact.yaml recipe."""
    assert recipe_path.exists(), (
        f"Recipe file must exist at {recipe_path}. "
        "Rewrite recipes/intent-to-artifact.yaml to pass these tests."
    )
    return yaml.safe_load(recipe_path.read_text())


@pytest.fixture(scope="module")
def stages(recipe: dict) -> list:
    """Return the top-level stages list from the staged recipe."""
    assert "stages" in recipe, (
        "Recipe must have a top-level 'stages' key (staged recipe)"
    )
    return recipe["stages"]


@pytest.fixture(scope="module")
def stages_by_name(stages: list) -> dict:
    """Return a dict mapping stage name -> stage dict for easy lookup."""
    return {stage["name"]: stage for stage in stages}


@pytest.fixture(scope="module")
def stage_decode(stages_by_name: dict) -> dict:
    """Return the decode-intent stage."""
    assert "decode-intent" in stages_by_name, (
        "Stages must include a stage named 'decode-intent'"
    )
    return stages_by_name["decode-intent"]


@pytest.fixture(scope="module")
def stage_converge(stages_by_name: dict) -> dict:
    """Return the fidelity-converge stage."""
    assert "fidelity-converge" in stages_by_name, (
        "Stages must include a stage named 'fidelity-converge'"
    )
    return stages_by_name["fidelity-converge"]


@pytest.fixture(scope="module")
def stage_finish(stages_by_name: dict) -> dict:
    """Return the finish-artifact stage."""
    assert "finish-artifact" in stages_by_name, (
        "Stages must include a stage named 'finish-artifact'"
    )
    return stages_by_name["finish-artifact"]


@pytest.fixture(scope="module")
def converge_steps_by_id(stage_converge: dict) -> dict:
    """Return a dict mapping step id -> step dict for stage 2."""
    assert "steps" in stage_converge, "fidelity-converge stage must have 'steps'"
    return {step["id"]: step for step in stage_converge["steps"]}


@pytest.fixture(scope="module")
def convergence_loop(converge_steps_by_id: dict) -> dict:
    """Return the convergence-loop step from the fidelity-converge stage."""
    assert "convergence-loop" in converge_steps_by_id, (
        "fidelity-converge stage must have a step with id 'convergence-loop'"
    )
    return converge_steps_by_id["convergence-loop"]


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
        assert recipe_path.exists(), "recipes/intent-to-artifact.yaml must exist"

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

    def test_name_is_intent_to_artifact(self, recipe: dict):
        assert recipe["name"] == "intent-to-artifact", (
            "Recipe name must be 'intent-to-artifact'"
        )

    def test_has_version(self, recipe: dict):
        assert "version" in recipe, "Recipe must have a 'version' field"

    def test_version_is_0_3_0(self, recipe: dict):
        assert recipe["version"] == "0.3.0", "Recipe version must be '0.3.0'"

    def test_has_description(self, recipe: dict):
        assert "description" in recipe, "Recipe must have a 'description' field"

    def test_description_mentions_fidelity_convergence(self, recipe: dict):
        desc = recipe.get("description", "")
        assert "fidelity" in desc.lower(), (
            "description must mention 'fidelity' (convergence engine)"
        )

    def test_recipe_is_staged(self, recipe: dict):
        """Master recipe must be a staged recipe."""
        assert "stages" in recipe, (
            "intent-to-artifact must be a staged recipe (has 'stages' key)"
        )

    def test_recipe_has_no_top_level_steps(self, recipe: dict):
        """Staged recipe must NOT have a top-level 'steps' key."""
        assert "steps" not in recipe, (
            "intent-to-artifact must not have a top-level 'steps' key (it is staged)"
        )


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

    def test_context_has_project_path(self, recipe: dict):
        assert "project_path" in recipe["context"], "context must define 'project_path'"

    def test_context_has_approval_message(self, recipe: dict):
        assert "_approval_message" in recipe["context"], (
            "context must define '_approval_message'"
        )

    def test_context_has_target_fidelity(self, recipe: dict):
        assert "target_fidelity" in recipe["context"], (
            "context must define 'target_fidelity' (new in v0.3.0)"
        )

    def test_context_has_fidelity_score(self, recipe: dict):
        assert "fidelity_score" in recipe["context"], (
            "context must define 'fidelity_score' (new in v0.3.0)"
        )

    def test_target_fidelity_default_is_0_85(self, recipe: dict):
        assert str(recipe["context"]["target_fidelity"]) == "0.85", (
            "context.target_fidelity default must be '0.85'"
        )

    def test_fidelity_score_default_is_0(self, recipe: dict):
        assert str(recipe["context"]["fidelity_score"]) == "0", (
            "context.fidelity_score default must be '0'"
        )

    def test_domain_default_is_general(self, recipe: dict):
        assert recipe["context"]["domain"] == "general", (
            "context.domain default must be 'general'"
        )


# ---------------------------------------------------------------------------
# AC-4: Exactly 3 stages with correct names
# ---------------------------------------------------------------------------


class TestStages:
    """AC-4: Exactly 3 stages exist with correct names."""

    EXPECTED_STAGE_NAMES = ["decode-intent", "fidelity-converge", "finish-artifact"]

    def test_stages_key_exists(self, recipe: dict):
        assert "stages" in recipe, "Recipe must have a top-level 'stages' key"

    def test_stages_is_a_list(self, stages: list):
        assert isinstance(stages, list), "'stages' must be a list"

    def test_exactly_3_stages(self, stages: list):
        assert len(stages) == 3, (
            f"Recipe must have exactly 3 stages (got {len(stages)}). "
            "v0.3.0 collapses build-and-review + verify-artifact into fidelity-converge."
        )

    def test_all_required_stage_names_present(self, stages_by_name: dict):
        for name in self.EXPECTED_STAGE_NAMES:
            assert name in stages_by_name, f"Stages must include a stage named '{name}'"

    def test_stage_order_is_correct(self, stages: list):
        actual_names = [stage["name"] for stage in stages]
        assert actual_names == self.EXPECTED_STAGE_NAMES, (
            f"Stages must appear in order {self.EXPECTED_STAGE_NAMES}, "
            f"but found {actual_names}"
        )


# ---------------------------------------------------------------------------
# AC-5: Stage 1 — decode-intent structure
# ---------------------------------------------------------------------------


class TestDecodeIntentStage:
    """AC-5: Stage 1 (decode-intent) retains the decode logic from v0.2."""

    EXPECTED_STEP_IDS = [
        "ensure-dirs",
        "decode-intent",
        "save-intent",
        "produce-spec",
        "save-spec",
        "decode-summary",
    ]

    def test_stage_has_steps(self, stage_decode: dict):
        assert "steps" in stage_decode, "decode-intent stage must have 'steps'"

    def test_all_decode_step_ids_present(self, stage_decode: dict):
        step_ids = {step["id"] for step in stage_decode["steps"]}
        for step_id in self.EXPECTED_STEP_IDS:
            assert step_id in step_ids, (
                f"decode-intent stage must have step '{step_id}'"
            )

    def test_decode_step_order(self, stage_decode: dict):
        actual_ids = [step["id"] for step in stage_decode["steps"]]
        positions = []
        for step_id in self.EXPECTED_STEP_IDS:
            assert step_id in actual_ids, f"Step '{step_id}' must exist"
            positions.append(actual_ids.index(step_id))
        assert positions == sorted(positions), (
            f"decode-intent steps must appear in order {self.EXPECTED_STEP_IDS}"
        )

    def test_stage_has_approval_gate(self, stage_decode: dict):
        assert "approval" in stage_decode, (
            "decode-intent stage must have an 'approval' gate"
        )

    def test_approval_gate_is_required(self, stage_decode: dict):
        approval = stage_decode.get("approval", {})
        assert approval.get("required") is True, (
            "decode-intent approval gate must have 'required: true'"
        )

    def test_approval_prompt_mentions_fidelity_convergence(self, stage_decode: dict):
        prompt = stage_decode.get("approval", {}).get("prompt", "")
        assert "fidelity" in prompt.lower(), (
            "decode-intent approval prompt must mention 'fidelity convergence' "
            "to guide the user about what comes next"
        )


# ---------------------------------------------------------------------------
# AC-6: Stage 2 — fidelity-converge structure
# ---------------------------------------------------------------------------


class TestFidelityConvergeStage:
    """AC-6: Stage 2 (fidelity-converge) contains the convergence loop."""

    EXPECTED_STEP_IDS = [
        "load-approved-spec",
        "initial-assessment",
        "extract-score",
        "convergence-loop",
        "converge-summary",
    ]

    def test_stage_has_steps(self, stage_converge: dict):
        assert "steps" in stage_converge, "fidelity-converge stage must have 'steps'"

    def test_all_converge_step_ids_present(self, converge_steps_by_id: dict):
        for step_id in self.EXPECTED_STEP_IDS:
            assert step_id in converge_steps_by_id, (
                f"fidelity-converge stage must have step '{step_id}'"
            )

    def test_converge_step_order(self, stage_converge: dict):
        actual_ids = [step["id"] for step in stage_converge["steps"]]
        positions = []
        for step_id in self.EXPECTED_STEP_IDS:
            assert step_id in actual_ids, f"Step '{step_id}' must exist"
            positions.append(actual_ids.index(step_id))
        assert positions == sorted(positions), (
            f"fidelity-converge steps must appear in order {self.EXPECTED_STEP_IDS}"
        )

    def test_load_approved_spec_is_bash(self, converge_steps_by_id: dict):
        step = converge_steps_by_id["load-approved-spec"]
        assert step.get("type") == "bash", (
            "load-approved-spec must be a bash step (type: bash)"
        )

    def test_initial_assessment_uses_critic(self, converge_steps_by_id: dict):
        step = converge_steps_by_id["initial-assessment"]
        assert step.get("agent") == "zerovector:critic", (
            "initial-assessment must use agent 'zerovector:critic'"
        )

    def test_initial_assessment_has_parse_json(self, converge_steps_by_id: dict):
        step = converge_steps_by_id["initial-assessment"]
        assert step.get("parse_json") is True, (
            "initial-assessment must have 'parse_json: true'"
        )

    def test_extract_score_is_bash(self, converge_steps_by_id: dict):
        step = converge_steps_by_id["extract-score"]
        assert step.get("type") == "bash", (
            "extract-score must be a bash step (type: bash)"
        )

    def test_converge_summary_is_bash(self, converge_steps_by_id: dict):
        step = converge_steps_by_id["converge-summary"]
        assert step.get("type") == "bash", (
            "converge-summary must be a bash step (type: bash)"
        )

    def test_stage_has_approval_gate(self, stage_converge: dict):
        assert "approval" in stage_converge, (
            "fidelity-converge stage must have an 'approval' gate"
        )

    def test_approval_gate_is_required(self, stage_converge: dict):
        approval = stage_converge.get("approval", {})
        assert approval.get("required") is True, (
            "fidelity-converge approval gate must have 'required: true'"
        )

    def test_approval_prompt_mentions_fidelity_score(self, stage_converge: dict):
        prompt = stage_converge.get("approval", {}).get("prompt", "")
        assert "fidelity_score" in prompt, (
            "fidelity-converge approval prompt must reference '{{fidelity_score}}' "
            "so the user can see the convergence result"
        )


# ---------------------------------------------------------------------------
# AC-7: Convergence loop configuration
# ---------------------------------------------------------------------------


class TestConvergenceLoop:
    """AC-7: convergence-loop step is correctly configured."""

    def test_has_while_condition(self, convergence_loop: dict):
        assert "while_condition" in convergence_loop, (
            "convergence-loop must have 'while_condition'"
        )

    def test_while_condition_references_fidelity_score(self, convergence_loop: dict):
        cond = convergence_loop["while_condition"]
        assert "fidelity_score" in cond, (
            "while_condition must reference 'fidelity_score'"
        )

    def test_while_condition_references_target_fidelity(self, convergence_loop: dict):
        cond = convergence_loop["while_condition"]
        assert "target_fidelity" in cond, (
            "while_condition must reference 'target_fidelity'"
        )

    def test_has_max_while_iterations(self, convergence_loop: dict):
        assert "max_while_iterations" in convergence_loop, (
            "convergence-loop must have 'max_while_iterations'"
        )

    def test_max_while_iterations_is_8(self, convergence_loop: dict):
        assert convergence_loop["max_while_iterations"] == 8, (
            "max_while_iterations must be 8"
        )

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

    def test_has_while_steps(self, convergence_loop: dict):
        assert "while_steps" in convergence_loop, (
            "convergence-loop must have 'while_steps'"
        )

    def test_while_steps_is_a_list(self, convergence_loop: dict):
        assert isinstance(convergence_loop["while_steps"], list), (
            "'while_steps' must be a list"
        )


# ---------------------------------------------------------------------------
# AC-8: While-steps contain route-to-gap and re-assess
# ---------------------------------------------------------------------------


class TestWhileSteps:
    """AC-8: while_steps contain the required sub-steps."""

    def test_has_route_to_gap(self, while_steps_by_id: dict):
        assert "route-to-gap" in while_steps_by_id, (
            "while_steps must contain a step with id 'route-to-gap'"
        )

    def test_has_re_assess(self, while_steps_by_id: dict):
        assert "re-assess" in while_steps_by_id, (
            "while_steps must contain a step with id 're-assess'"
        )

    def test_route_to_gap_agent_is_self(self, while_steps_by_id: dict):
        route = while_steps_by_id["route-to-gap"]
        assert route.get("agent") == "self", "route-to-gap must use agent 'self'"

    def test_route_to_gap_has_on_error_continue(self, while_steps_by_id: dict):
        route = while_steps_by_id["route-to-gap"]
        assert route.get("on_error") == "continue", (
            "route-to-gap on_error must be 'continue'"
        )

    def test_re_assess_uses_critic(self, while_steps_by_id: dict):
        step = while_steps_by_id["re-assess"]
        assert step.get("agent") == "zerovector:critic", (
            "re-assess must use agent 'zerovector:critic'"
        )

    def test_re_assess_has_parse_json(self, while_steps_by_id: dict):
        step = while_steps_by_id["re-assess"]
        assert step.get("parse_json") is True, "re-assess must have 'parse_json: true'"

    def test_route_to_gap_before_re_assess(self, convergence_loop: dict):
        ids = [step["id"] for step in convergence_loop["while_steps"]]
        assert ids.index("route-to-gap") < ids.index("re-assess"), (
            "route-to-gap must appear before re-assess in while_steps"
        )


# ---------------------------------------------------------------------------
# AC-9: Stage 3 — finish-artifact structure
# ---------------------------------------------------------------------------


class TestFinishArtifactStage:
    """AC-9: Stage 3 (finish-artifact) has the finish logic."""

    EXPECTED_STEP_IDS = [
        "parse-finish-action",
        "execute-finish",
        "pipeline-summary",
    ]

    def test_stage_has_steps(self, stage_finish: dict):
        assert "steps" in stage_finish, "finish-artifact stage must have 'steps'"

    def test_all_finish_step_ids_present(self, stage_finish: dict):
        step_ids = {step["id"] for step in stage_finish["steps"]}
        for step_id in self.EXPECTED_STEP_IDS:
            assert step_id in step_ids, (
                f"finish-artifact stage must have step '{step_id}'"
            )

    def test_finish_step_order(self, stage_finish: dict):
        actual_ids = [step["id"] for step in stage_finish["steps"]]
        positions = []
        for step_id in self.EXPECTED_STEP_IDS:
            assert step_id in actual_ids, f"Step '{step_id}' must exist"
            positions.append(actual_ids.index(step_id))
        assert positions == sorted(positions), (
            f"finish-artifact steps must appear in order {self.EXPECTED_STEP_IDS}"
        )

    def test_execute_finish_uses_shipper(self, stage_finish: dict):
        steps_by_id = {step["id"]: step for step in stage_finish["steps"]}
        step = steps_by_id["execute-finish"]
        assert step.get("agent") == "zerovector:shipper", (
            "execute-finish must use agent 'zerovector:shipper'"
        )

    def test_stage_has_no_approval_gate(self, stage_finish: dict):
        """Stage 3 is a terminal action stage — no gate needed after gate 2."""
        assert "approval" not in stage_finish, (
            "finish-artifact stage must NOT have an approval gate "
            "(the gate is at end of fidelity-converge, not here)"
        )
