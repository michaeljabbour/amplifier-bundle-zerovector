# Crew Agent Fidelity Awareness — Builder & Shipper Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

> **QUALITY WARNING:** This task (task-6) originated from an INCOMPLETE spec —
> the implementation plan had placeholder text for Part 2, Groups 2–3. The spec
> was reconstructed from the design document (`docs/plans/2026-03-08-zerovector-v03-design.md`,
> Section 7 "Modified Files"). The quality review loop on the dependency task
> (task-5: conftest refactoring) exhausted after 3 iterations before approval.
> **Human reviewer:** verify that the changes below match the v0.3 design intent
> during the approval gate.

**Goal:** Add fidelity framework awareness to the builder and shipper crew agents, completing the set of minor agent updates specified in the v0.3 design document.

**Architecture:** Mirror the pattern established in commit `b4d8511` (intent-analyst + architect updates): update frontmatter descriptions to reference the agent's fidelity lens, add a `## Fidelity Context` section to the markdown body, and add comprehensive tests validating structure, fidelity awareness, agent-specific features, and preserved content. Extend `tests/agents/conftest.py` with fixtures for builder and shipper.

**Tech Stack:** Markdown (agent definitions), Python 3.12+ / pytest (tests), YAML frontmatter

---

## Task 1: Add builder and shipper fixtures to conftest.py

**Files:**
- Modify: `tests/agents/conftest.py`

**Step 1: Read the current conftest.py**

Verify the file at `tests/agents/conftest.py` currently has fixtures for `intent_analyst` and `architect` only (lines 33–60). Confirm no builder/shipper fixtures exist.

**Step 2: Add builder fixtures after the architect fixtures**

Append the following after line 60 (after the `architect_body` fixture):

```python


@pytest.fixture(scope="module")
def builder_path() -> Path:
    return AGENTS_DIR / "builder.md"


@pytest.fixture(scope="module")
def builder_frontmatter(builder_path: Path) -> dict[str, Any]:
    return load_agent_frontmatter(builder_path)


@pytest.fixture(scope="module")
def builder_body(builder_path: Path) -> str:
    return load_agent_body(builder_path)


@pytest.fixture(scope="module")
def shipper_path() -> Path:
    return AGENTS_DIR / "shipper.md"


@pytest.fixture(scope="module")
def shipper_frontmatter(shipper_path: Path) -> dict[str, Any]:
    return load_agent_frontmatter(shipper_path)


@pytest.fixture(scope="module")
def shipper_body(shipper_path: Path) -> str:
    return load_agent_body(shipper_path)
```

**Step 3: Run existing tests to verify no regressions**

Run: `python -m pytest tests/agents/ -v --tb=short`

Expected: All 83 existing tests PASS. No new tests yet — this step only adds fixtures.

**Step 4: Commit**

```bash
git add tests/agents/conftest.py
git commit -m "refactor(tests/agents): add builder and shipper fixtures to conftest"
```

---

## Task 2: Write failing tests for builder fidelity awareness

**Files:**
- Create: `tests/agents/test_builder_agent.py`

**Step 1: Create the test file**

Create `tests/agents/test_builder_agent.py` with this exact content:

```python
"""Tests for agents/builder.md — fidelity framework awareness updates."""

from pathlib import Path


# ---------------------------------------------------------------------------
# AC-1: File exists with valid structure
# ---------------------------------------------------------------------------
class TestFileStructure:
    """AC-1: File exists at agents/builder.md with valid frontmatter."""

    def test_file_exists(self, builder_path: Path):
        assert builder_path.exists(), "agents/builder.md must exist"

    def test_frontmatter_parses(self, builder_frontmatter: dict):
        assert isinstance(builder_frontmatter, dict), (
            "Frontmatter must parse to a dict"
        )

    def test_meta_has_name(self, builder_frontmatter: dict):
        assert builder_frontmatter["meta"]["name"] == "builder", (
            "meta.name must be 'builder'"
        )

    def test_meta_has_description(self, builder_frontmatter: dict):
        assert "description" in builder_frontmatter["meta"], (
            "meta must have 'description'"
        )
        assert len(builder_frontmatter["meta"]["description"].strip()) > 0, (
            "description must not be empty"
        )

    def test_frontmatter_has_tools(self, builder_frontmatter: dict):
        assert "tools" in builder_frontmatter, "Frontmatter must have 'tools' section"
        assert isinstance(builder_frontmatter["tools"], list), "tools must be a list"


# ---------------------------------------------------------------------------
# AC-2: Fidelity framework awareness — Implementation lens
# ---------------------------------------------------------------------------
class TestFidelityAwareness:
    """AC-2: Builder is aware of the fidelity framework and its lens."""

    def test_mentions_fidelity(self, builder_body: str):
        body = builder_body.lower()
        assert "fidelity" in body, "Must mention fidelity framework"

    def test_mentions_implementation_lens(self, builder_body: str):
        body = builder_body.lower()
        assert "implementation" in body and "lens" in body, (
            "Must mention the Implementation lens it serves"
        )

    def test_mentions_translation_loss(self, builder_body: str):
        """Agent should understand its role in reducing translation loss."""
        body = builder_body.lower()
        assert "translation loss" in body or "translation-loss" in body, (
            "Must reference translation loss concept"
        )


# ---------------------------------------------------------------------------
# AC-3: Can start with partial spec
# ---------------------------------------------------------------------------
class TestPartialSpecStart:
    """AC-3: Builder can start with partial spec if fidelity routing says so."""

    def test_partial_spec_acknowledged(self, builder_body: str):
        """Builder can begin with incomplete specification."""
        body = builder_body.lower()
        assert "partial" in body or "incomplete" in body, (
            "Must acknowledge starting with partial spec"
        )

    def test_fidelity_routing_awareness(self, builder_body: str):
        """Builder can be re-invoked when Implementation is the priority gap."""
        body = builder_body.lower()
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

    def test_iron_laws_section_exists(self, builder_body: str):
        assert "Iron Law" in builder_body or "iron law" in builder_body.lower(), (
            "Must preserve Iron Laws section"
        )

    def test_iron_law_build_exactly(self, builder_body: str):
        body = builder_body.lower()
        assert "build exactly" in body or "spec'd" in body, (
            "Must preserve 'Build exactly what's spec'd' iron law"
        )

    def test_iron_law_stop_at_boundary(self, builder_body: str):
        body = builder_body.lower()
        assert "stop at the boundary" in body or "acceptance criteria are met" in body, (
            "Must preserve 'Stop at the boundary' iron law"
        )

    def test_iron_law_no_silent_scope_expansion(self, builder_body: str):
        body = builder_body.lower()
        assert "scope expansion" in body or "scope creep" in body, (
            "Must preserve 'No silent scope expansion' iron law"
        )

    def test_iron_law_verify_before_reporting(self, builder_body: str):
        body = builder_body.lower()
        assert "verify before reporting" in body or "running checks" in body, (
            "Must preserve 'Verify before reporting done' iron law"
        )

    def test_process_section_exists(self, builder_body: str):
        assert "Your Process" in builder_body, "Must preserve 'Your Process' section"

    def test_output_contract_section_exists(self, builder_body: str):
        assert "Output Contract" in builder_body, (
            "Must preserve 'Output Contract' section"
        )

    def test_build_complete_template_preserved(self, builder_body: str):
        assert "Build Complete" in builder_body, (
            "Must preserve 'Build Complete' output template"
        )

    def test_refinement_loop_preserved(self, builder_body: str):
        assert (
            "Refinement Loop" in builder_body
            or "refinement loop" in builder_body.lower()
        ), "Must preserve refinement loop output contract"

    def test_domain_specific_standards_preserved(self, builder_body: str):
        body = builder_body.lower()
        assert "domain" in body and "standards" in body, (
            "Must preserve domain-specific build standards table"
        )

    def test_handoff_to_critic(self, builder_body: str):
        body = builder_body.lower()
        assert "critic" in body, "Must preserve handoff to Critic"
```

**Step 2: Run tests to verify they fail on fidelity-specific assertions**

Run: `python -m pytest tests/agents/test_builder_agent.py -v --tb=short`

Expected: `TestFileStructure` and `TestPreservedContent` PASS (content already exists). `TestFidelityAwareness` and `TestPartialSpecStart` FAIL (fidelity content not yet added).

**Step 3: Commit the failing tests**

```bash
git add tests/agents/test_builder_agent.py
git commit -m "test(builder): add fidelity awareness tests — RED phase"
```

---

## Task 3: Update builder.md with fidelity framework awareness

**Files:**
- Modify: `agents/builder.md`

**Step 1: Update the frontmatter description**

In `agents/builder.md`, replace the existing `description` block (lines 5–27) with:

```yaml
  description: |
    Use when implementing an artifact from a specification, or when the
    Implementation lens is the fidelity priority gap.
    Serves the Implementation fidelity lens — reducing translation loss
    between specification and built artifact.

    Examples:
    <example>
    Context: Specification document received from architect
    user: "Spec is ready — build it"
    assistant: "I'll delegate to zerovector:builder to implement the specification."
    <commentary>Builder takes the spec and produces the real artifact.</commentary>
    </example>

    <example>
    Context: Well-defined task needs execution
    user: "Implement Task 2: Create the auth middleware"
    assistant: "I'll delegate to zerovector:builder with the task specification."
    <commentary>Single well-specified tasks go directly to the builder.</commentary>
    </example>

    <example>
    Context: Convergence loop — critic returned FAIL or CONDITIONAL_PASS
    user: "Critic flagged issues — fix them"
    assistant: "I'll delegate to zerovector:builder with the critic's exact report."
    <commentary>Builder receives the full critic report and addresses each flagged issue.</commentary>
    </example>
```

**Step 2: Add the Fidelity Context section**

In `agents/builder.md`, insert the following new section immediately after the `## Your Role` block (after line 51: "You build exactly what was specified. Not more. Not less.") and before the existing `---` separator on line 52:

```markdown

## Fidelity Context

You serve the **Implementation** lens in the fidelity framework. Your work directly
determines the Implementation fidelity score — the measure of translation loss between
what was specified and what was actually built.

When the fidelity system identifies Implementation as the priority gap, you are the agent
routed to close that gap. Your goal: produce an artifact that faithfully implements the
specification, with no drift, no missing features, and no scope creep.

### Starting With Partial Spec

You do not need a complete specification to begin. If the fidelity system routes to you
with a partial spec (because the Specification lens has moderate fidelity but the
Implementation lens is the weakest), start building the high-confidence sections. The
spec can evolve as the fidelity system re-routes to the Architect when the Specification
lens becomes the priority gap again. Build what is clear; flag what is ambiguous in
Open Risks.
```

**Step 3: Run tests to verify they pass**

Run: `python -m pytest tests/agents/test_builder_agent.py -v --tb=short`

Expected: ALL tests PASS (including `TestFidelityAwareness` and `TestPartialSpecStart`).

**Step 4: Run full agent test suite to verify no regressions**

Run: `python -m pytest tests/agents/ -v --tb=short`

Expected: All tests PASS (83 existing + new builder tests).

**Step 5: Commit**

```bash
git add agents/builder.md
git commit -m "feat(builder): add fidelity framework awareness — Implementation lens"
```

---

## Task 4: Write failing tests for shipper fidelity awareness

**Files:**
- Create: `tests/agents/test_shipper_agent.py`

**Step 1: Create the test file**

Create `tests/agents/test_shipper_agent.py` with this exact content:

```python
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
        assert isinstance(shipper_frontmatter, dict), (
            "Frontmatter must parse to a dict"
        )

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
        assert ("ship-readiness" in body or "ship_readiness" in body) and "lens" in body, (
            "Must mention the Ship-Readiness lens it serves"
        )

    def test_mentions_translation_loss(self, shipper_body: str):
        """Agent should understand its role in reducing translation loss."""
        body = shipper_body.lower()
        assert "translation loss" in body or "translation-loss" in body, (
            "Must reference translation loss concept"
        )


# ---------------------------------------------------------------------------
# AC-3: Ship-readiness as a lens, can be invoked early
# ---------------------------------------------------------------------------
class TestEarlyInvocation:
    """AC-3: Shipper understands ship-readiness is a lens, can be invoked early."""

    def test_early_invocation_acknowledged(self, shipper_body: str):
        """Shipper can be invoked at any point, not just end of pipeline."""
        body = shipper_body.lower()
        assert (
            "early" in body
            or "any point" in body
            or "not only" in body
        ), "Must acknowledge being invocable before final validation"

    def test_fidelity_routing_awareness(self, shipper_body: str):
        """Shipper can be re-invoked when Ship-Readiness is the priority gap."""
        body = shipper_body.lower()
        assert (
            "priority gap" in body
            or "priority_gap" in body
            or ("weakest" in body and "lens" in body)
        ), "Must mention being routable via fidelity priority gap"


# ---------------------------------------------------------------------------
# AC-4: Preserved content — iron laws, process, output format
# ---------------------------------------------------------------------------
class TestPreservedContent:
    """AC-4: Original iron laws, process, finish actions, and output format are preserved."""

    def test_iron_laws_section_exists(self, shipper_body: str):
        assert "Iron Law" in shipper_body or "iron law" in shipper_body.lower(), (
            "Must preserve Iron Laws section"
        )

    def test_iron_law_no_fail_shipped(self, shipper_body: str):
        body = shipper_body.lower()
        assert "fail" in body and "ship" in body, (
            "Must preserve 'No FAIL gets shipped' iron law"
        )

    def test_iron_law_execute_dont_improvise(self, shipper_body: str):
        body = shipper_body.lower()
        assert "improvise" in body or "don't substitute" in body, (
            "Must preserve 'Execute the action, don't improvise' iron law"
        )

    def test_iron_law_fallback_to_keep(self, shipper_body: str):
        body = shipper_body.lower()
        assert "keep" in body and "fall back" in body, (
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

    def test_four_finish_actions_preserved(self, shipper_body: str):
        body = shipper_body.lower()
        for action in ("merge", "pr", "keep", "discard"):
            assert action in body, f"Must preserve '{action}' finish action"

    def test_delivery_report_template_preserved(self, shipper_body: str):
        assert "Delivery Report" in shipper_body, (
            "Must preserve Delivery Report template"
        )

    def test_close_the_pipeline_preserved(self, shipper_body: str):
        assert (
            "Close the Pipeline" in shipper_body
            or "close the pipeline" in shipper_body.lower()
        ), "Must preserve 'Close the Pipeline' section"
```

**Step 2: Run tests to verify they fail on fidelity-specific assertions**

Run: `python -m pytest tests/agents/test_shipper_agent.py -v --tb=short`

Expected: `TestFileStructure` and `TestPreservedContent` PASS (content already exists). `TestFidelityAwareness` and `TestEarlyInvocation` FAIL (fidelity content not yet added).

**Step 3: Commit the failing tests**

```bash
git add tests/agents/test_shipper_agent.py
git commit -m "test(shipper): add fidelity awareness tests — RED phase"
```

---

## Task 5: Update shipper.md with fidelity framework awareness

**Files:**
- Modify: `agents/shipper.md`

**Step 1: Update the frontmatter description**

In `agents/shipper.md`, replace the existing `description` block (lines 5–28) with:

```yaml
  description: |
    Use when packaging, committing, and delivering a validated artifact,
    or when the Ship-Readiness lens is the fidelity priority gap.
    Serves the Ship-Readiness fidelity lens — reducing translation loss
    between a validated artifact and a deliverable state.
    Supports four finish actions: merge / pr / keep / discard.

    Examples:
    <example>
    Context: Critic gave PASS verdict, finish action is "merge"
    user: "Critic approved — merge and ship"
    assistant: "I'll delegate to zerovector:shipper to merge and deliver the artifact."
    <commentary>Shipper takes a PASS verdict and executes the requested finish action.</commentary>
    </example>

    <example>
    Context: Artifact validated, open a PR for team review
    user: "Open a PR for this feature"
    assistant: "I'll delegate to zerovector:shipper with finish action 'pr'."
    <commentary>Shipper creates the PR with conventional commit message and description.</commentary>
    </example>

    <example>
    Context: Artifact complete but not ready to merge — keep on branch
    user: "Commit cleanly but don't merge yet"
    assistant: "I'll delegate to zerovector:shipper with finish action 'keep'."
    <commentary>Shipper commits cleanly and reports where to find the work without merging.</commentary>
    </example>
```

**Step 2: Add the Fidelity Context section**

In `agents/shipper.md`, insert the following new section immediately after the `## Your Role` block (after line 51: "finished work lands cleanly, safely, and with the human knowing exactly what they have.") and before the existing `---` separator on line 52:

```markdown

## Fidelity Context

You serve the **Ship-Readiness** lens in the fidelity framework. Your work directly
determines the Ship-Readiness fidelity score — the measure of translation loss between
a validated artifact and a state that can actually be delivered, merged, published, or
deployed.

When the fidelity system identifies Ship-Readiness as the priority gap, you are the agent
routed to close that gap. Your goal: resolve delivery blockers — missing docs, broken CI,
no delivery path, incomplete cleanup.

### Early Invocation

You are not only invoked at the end of the pipeline. The fidelity system may route to you
at any point when Ship-Readiness is the weakest lens — even before the artifact is fully
built. Early invocation means assessing and improving deliverability incrementally: setting
up CI, writing deployment notes, or preparing the delivery path while the Builder is still
working. You close the Ship-Readiness gap whenever it is the priority, not only after a
Critic PASS.
```

**Step 3: Run tests to verify they pass**

Run: `python -m pytest tests/agents/test_shipper_agent.py -v --tb=short`

Expected: ALL tests PASS (including `TestFidelityAwareness` and `TestEarlyInvocation`).

**Step 4: Run full agent test suite to verify no regressions**

Run: `python -m pytest tests/agents/ -v --tb=short`

Expected: All tests PASS (83 existing + builder tests + shipper tests).

**Step 5: Commit**

```bash
git add agents/shipper.md
git commit -m "feat(shipper): add fidelity framework awareness — Ship-Readiness lens"
```

---

## Task 6: Final validation

**Files:**
- None (verification only)

**Step 1: Run the complete test suite**

Run: `python -m pytest tests/ -v --tb=short`

Expected: ALL tests pass — agent tests + module tests.

**Step 2: Run python_check on test files**

Run: `python_check` on `tests/agents/`

Expected: All checks pass (ruff-format, ruff-lint, pyright, stubs).

**Step 3: Verify git status is clean**

Run: `git status`

Expected: Working tree clean, all changes committed.

---

## Summary of Changes

| File | Change Type | What Changes |
|------|------------|-------------|
| `tests/agents/conftest.py` | Modify | Add 6 fixtures (builder_path, builder_frontmatter, builder_body, shipper_path, shipper_frontmatter, shipper_body) |
| `tests/agents/test_builder_agent.py` | Create | 18 tests: file structure (5), fidelity awareness (3), partial spec (2), preserved content (8) |
| `agents/builder.md` | Modify | Update description to reference Implementation lens; add Fidelity Context section with partial-spec guidance |
| `tests/agents/test_shipper_agent.py` | Create | 18 tests: file structure (5), fidelity awareness (3), early invocation (2), preserved content (8) |
| `agents/shipper.md` | Modify | Update description to reference Ship-Readiness lens; add Fidelity Context section with early-invocation guidance |

## Design Traceability

Each change traces to the design document (`docs/plans/2026-03-08-zerovector-v03-design.md`):

| Design Doc Reference | Implementation |
|---------------------|---------------|
| Section 7, "agents/builder.md — Minor: can start with partial spec if fidelity routing says so" | Task 3: Fidelity Context section + "Starting With Partial Spec" subsection |
| Section 7, "agents/shipper.md — Minor: ship-readiness as a lens, can be invoked early" | Task 5: Fidelity Context section + "Early Invocation" subsection |
| Section 2, "Five Lenses" table: Implementation lens served by builder | Task 3: Description + Fidelity Context reference Implementation lens |
| Section 2, "Five Lenses" table: Ship-Readiness lens served by shipper | Task 5: Description + Fidelity Context reference Ship-Readiness lens |
