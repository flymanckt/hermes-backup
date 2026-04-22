"""Tests for browser_upload tool wiring and path validation."""

import json
from pathlib import Path
from unittest.mock import patch


def test_browser_upload_calls_agent_browser_upload_with_resolved_paths(tmp_path):
    from tools.browser_tool import browser_upload

    resume = tmp_path / "resume.pdf"
    cover = tmp_path / "cover-letter.docx"
    resume.write_text("resume", encoding="utf-8")
    cover.write_text("cover", encoding="utf-8")

    with patch("tools.browser_tool._run_browser_command") as mock_cmd:
        mock_cmd.return_value = {
            "success": True,
            "data": {"uploaded": [str(resume.resolve()), str(cover.resolve())]},
        }
        result = json.loads(browser_upload("e12", [str(resume), str(cover)], task_id="job-task"))

    assert result["success"] is True
    assert result["element"] == "@e12"
    assert result["uploaded_files"] == [str(resume.resolve()), str(cover.resolve())]
    mock_cmd.assert_called_once_with(
        "job-task",
        "upload",
        ["@e12", str(resume.resolve()), str(cover.resolve())],
    )


def test_browser_upload_requires_existing_files(tmp_path):
    from tools.browser_tool import browser_upload

    missing = tmp_path / "missing.pdf"
    result = json.loads(browser_upload("@e3", [str(missing)], task_id="job-task"))

    assert result["success"] is False
    assert "does not exist" in result["error"]


def test_browser_upload_blocks_sensitive_files(tmp_path):
    from tools.browser_tool import browser_upload

    secret_file = tmp_path / ".env"
    secret_file.write_text("SECRET=1", encoding="utf-8")

    result = json.loads(browser_upload("@e5", [str(secret_file)], task_id="job-task"))

    assert result["success"] is False
    assert "Access denied" in result["error"]


def test_browser_upload_schema_registered():
    from tools.browser_tool import BROWSER_TOOL_SCHEMAS

    schema = next(s for s in BROWSER_TOOL_SCHEMAS if s["name"] == "browser_upload")
    props = schema["parameters"]["properties"]

    assert "ref" in props
    assert "paths" in props
    assert props["paths"]["type"] == "array"


def test_browser_upload_is_wired_into_toolsets_and_registry():
    from model_tools import _LEGACY_TOOLSET_MAP
    from toolsets import TOOLSETS, _HERMES_CORE_TOOLS
    from tools.registry import registry
    from tools import browser_tool  # noqa: F401

    assert "browser_upload" in TOOLSETS["browser"]["tools"]
    assert "browser_upload" in _HERMES_CORE_TOOLS
    assert "browser_upload" in _LEGACY_TOOLSET_MAP["browser_tools"]
    assert "browser_upload" in registry._tools
