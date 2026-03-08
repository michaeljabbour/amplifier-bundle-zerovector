"""Tool-fidelity-state module -- session-level fidelity convergence tracking."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

_log = logging.getLogger(__name__)

# Guard import for ToolResult -- fall back to plain dict when amplifier_core
# is not installed (e.g. in isolated test environments).
try:
    from amplifier_core.models import ToolResult

    _HAS_TOOL_RESULT = True
except ImportError:
    _HAS_TOOL_RESULT = False

__amplifier_module_type__ = "tool"

# -- Constants ---------------------------------------------------------------

_DEFAULT_TARGET: float = 0.85
_DEFAULT_DOMAIN: str = "general"

DEFAULT_LENSES: list[str] = [
    "intent_clarity",
    "specification",
    "implementation",
    "quality",
    "ship_readiness",
]

_RECOMMENDATIONS: dict[str, str] = {
    "intent_clarity": "Route to intent-analyst to clarify goals and resolve ambiguity",
    "specification": "Route to architect to tighten spec and close open questions",
    "implementation": "Route to builder to address implementation gaps",
    "quality": "Route to critic for deeper quality assessment and fixes",
    "ship_readiness": "Route to shipper to finalize packaging and delivery",
}


# -- Helpers -----------------------------------------------------------------


def _tool_result(content: str, *, is_error: bool = False):
    """Return a ToolResult when available, otherwise a plain dict."""
    if _HAS_TOOL_RESULT:
        if is_error:
            return ToolResult(success=False, error={"message": content})  # type: ignore[possibly-undefined]
        return ToolResult(output=content)  # type: ignore[possibly-undefined]
    return {"content": content, "is_error": is_error}


# -- FidelityState -----------------------------------------------------------


@dataclass
class FidelityState:
    """Session-level fidelity scores across convergence lenses."""

    lens_scores: dict[str, float] = field(default_factory=dict)
    overall: float = 0.0
    target: float = _DEFAULT_TARGET
    domain: str = _DEFAULT_DOMAIN
    priority_gap: dict[str, Any] = field(default_factory=dict)

    def update_fidelity(
        self,
        lens_scores: dict[str, float],
        domain: str = _DEFAULT_DOMAIN,
        target: float = _DEFAULT_TARGET,
    ) -> None:
        """Push new scores into state after a multi-lens assessment."""
        self.lens_scores = {k: max(0.0, min(1.0, v)) for k, v in lens_scores.items()}
        self.domain = domain
        self.target = target

        if not self.lens_scores:
            self.overall = 0.0
            self.priority_gap = {}
            return

        self.overall = sum(self.lens_scores.values()) / len(self.lens_scores)

        lowest_lens = min(self.lens_scores, key=self.lens_scores.get)  # type: ignore[arg-type]
        self.priority_gap = {
            "lens": lowest_lens,
            "score": self.lens_scores[lowest_lens],
            "recommendation": _RECOMMENDATIONS.get(
                lowest_lens, "No routing recommendation available"
            ),
        }

    def get_state(self) -> dict[str, Any]:
        """Return a plain-dict snapshot (copies, not references)."""
        return {
            "lens_scores": dict(self.lens_scores),
            "overall": self.overall,
            "target": self.target,
            "domain": self.domain,
            "priority_gap": dict(self.priority_gap),
        }


# -- UpdateFidelityTool ------------------------------------------------------


class UpdateFidelityTool:
    """LLM-callable tool the critic uses to push fidelity scores."""

    def __init__(self, state: FidelityState) -> None:
        self.state = state
        self.name = "update_fidelity"
        self.description = (
            "Update fidelity scores after a multi-lens assessment. "
            "Accepts lens_scores mapping each lens to a 0-1 score."
        )
        self.input_schema: dict[str, Any] = {
            "type": "object",
            "required": ["lens_scores"],
            "properties": {
                "lens_scores": {
                    "type": "object",
                    "description": "Mapping of lens name to score (0.0-1.0)",
                },
                "domain": {
                    "type": "string",
                    "default": _DEFAULT_DOMAIN,
                    "description": "Domain context for the assessment",
                },
                "target": {
                    "type": "number",
                    "default": _DEFAULT_TARGET,
                    "description": "Convergence target threshold",
                },
            },
        }

    async def execute(self, input: dict[str, Any]):  # noqa: A002
        """Execute the tool with parsed LLM input."""
        lens_scores = input.get("lens_scores")
        if not lens_scores:
            return _tool_result("No lens_scores provided", is_error=True)

        domain = input.get("domain", _DEFAULT_DOMAIN)
        target = input.get("target", _DEFAULT_TARGET)

        self.state.update_fidelity(lens_scores, domain=domain, target=target)

        status = (
            "CONVERGED" if self.state.overall >= self.state.target else "NEEDS_WORK"
        )
        summary = (
            f"Fidelity {status}: overall={self.state.overall:.2f} "
            f"target={self.state.target}"
        )
        return _tool_result(summary)


# -- mount -------------------------------------------------------------------


async def mount(coordinator, config: dict | None = None) -> dict[str, str]:
    """Mount the fidelity-state tool and register capabilities."""
    config = config or {}
    target = config.get("target", _DEFAULT_TARGET)
    domain = config.get("domain", _DEFAULT_DOMAIN)

    state = FidelityState(target=target, domain=domain)
    tool = UpdateFidelityTool(state)

    try:
        await coordinator.mount("tools", tool, name=tool.name)
    except Exception:
        _log.debug("Failed to mount update_fidelity tool", exc_info=True)

    try:
        coordinator.register_capability("zerovector.fidelity_state", state)
    except Exception:
        _log.debug(
            "Failed to register zerovector.fidelity_state capability", exc_info=True
        )

    try:
        coordinator.register_capability(
            "zerovector.update_fidelity", state.update_fidelity
        )
    except Exception:
        _log.debug(
            "Failed to register zerovector.update_fidelity capability", exc_info=True
        )

    return {
        "name": "tool-fidelity-state",
        "version": "0.3.0",
    }
