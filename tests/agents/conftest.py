"""Shared fixtures for agent markdown file tests."""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

AGENTS_DIR = Path(__file__).resolve().parents[2] / "agents"


def _load_raw(path: Path) -> tuple[str, str]:
    """Read an agent markdown file once, returning (frontmatter_yaml, body)."""
    text = path.read_text()
    m = re.match(r"^---\n(.*?\n)---\n?(.*)", text, re.DOTALL)
    assert m, f"{path.name} must have YAML frontmatter delimited by ---"
    return m.group(1), m.group(2)


def load_agent_frontmatter(path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from an agent markdown file (between --- delimiters)."""
    raw_yaml, _ = _load_raw(path)
    return yaml.safe_load(raw_yaml)


def load_agent_body(path: Path) -> str:
    """Return the markdown body after frontmatter."""
    _, body = _load_raw(path)
    return body


@pytest.fixture(scope="module")
def intent_analyst_path() -> Path:
    return AGENTS_DIR / "intent-analyst.md"


@pytest.fixture(scope="module")
def intent_analyst_frontmatter(intent_analyst_path: Path) -> dict[str, Any]:
    return load_agent_frontmatter(intent_analyst_path)


@pytest.fixture(scope="module")
def intent_analyst_body(intent_analyst_path: Path) -> str:
    return load_agent_body(intent_analyst_path)


@pytest.fixture(scope="module")
def architect_path() -> Path:
    return AGENTS_DIR / "architect.md"


@pytest.fixture(scope="module")
def architect_frontmatter(architect_path: Path) -> dict[str, Any]:
    return load_agent_frontmatter(architect_path)


@pytest.fixture(scope="module")
def architect_body(architect_path: Path) -> str:
    return load_agent_body(architect_path)
