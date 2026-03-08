"""Shared fixtures for agent markdown file tests."""

import re
from pathlib import Path

import pytest
import yaml

AGENTS_DIR = Path(__file__).resolve().parents[2] / "agents"


def load_agent_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter from an agent markdown file (between --- delimiters)."""
    text = path.read_text()
    match = re.match(r"^---\n(.*?\n)---", text, re.DOTALL)
    assert match, f"{path.name} must have YAML frontmatter delimited by ---"
    return yaml.safe_load(match.group(1))


def load_agent_body(path: Path) -> str:
    """Return the markdown body after frontmatter."""
    text = path.read_text()
    match = re.match(r"^---\n.*?\n---\n?(.*)", text, re.DOTALL)
    assert match, f"{path.name} must have a body after frontmatter"
    return match.group(1)


@pytest.fixture(scope="module")
def intent_analyst_path() -> Path:
    return AGENTS_DIR / "intent-analyst.md"


@pytest.fixture(scope="module")
def intent_analyst_frontmatter(intent_analyst_path: Path) -> dict:
    return load_agent_frontmatter(intent_analyst_path)


@pytest.fixture(scope="module")
def intent_analyst_body(intent_analyst_path: Path) -> str:
    return load_agent_body(intent_analyst_path)


@pytest.fixture(scope="module")
def architect_path() -> Path:
    return AGENTS_DIR / "architect.md"


@pytest.fixture(scope="module")
def architect_frontmatter(architect_path: Path) -> dict:
    return load_agent_frontmatter(architect_path)


@pytest.fixture(scope="module")
def architect_body(architect_path: Path) -> str:
    return load_agent_body(architect_path)
