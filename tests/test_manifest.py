from __future__ import annotations

import json
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = REPO_ROOT / "custom_components" / "samsung_frame" / "manifest.json"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"

LIBRARY_NAME = "samsungtvws"


def _manifest_requirement() -> str:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return next(
        requirement
        for requirement in manifest["requirements"]
        if requirement.startswith(LIBRARY_NAME)
    )


def _dev_group_requirement() -> str:
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    return next(
        requirement
        for requirement in pyproject["dependency-groups"]["dev"]
        if requirement.startswith(LIBRARY_NAME)
    )


def test_manifest_requires_at_least_the_version_the_tests_run_against():
    tested_version = _dev_group_requirement().split("==", 1)[1]
    assert _manifest_requirement() == f"{LIBRARY_NAME}>={tested_version}"


def test_dev_group_pins_the_library_exactly():
    assert f"{LIBRARY_NAME}==" in _dev_group_requirement()
