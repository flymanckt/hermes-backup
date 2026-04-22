"""Tests for recruitment workflow tool."""

import json
from pathlib import Path


def test_prepare_accepts_existing_resume_and_returns_steps(tmp_path, monkeypatch):
    from tools.recruitment_tool import recruitment_workflow

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    resume = tmp_path / "resume.pdf"
    resume.write_text("resume", encoding="utf-8")

    result = json.loads(
        recruitment_workflow(
            action="prepare",
            site="51job",
            resume_path=str(resume),
            job_url="https://www.51job.com/job/123.html",
            company="测试公司",
            title="IT经理",
        )
    )

    assert result["success"] is True
    assert result["ready"] is True
    assert result["site"] == "51job"
    assert result["normalized_resume_path"] == str(resume.resolve())
    assert result["next_steps"]


def test_prepare_rejects_missing_resume(tmp_path, monkeypatch):
    from tools.recruitment_tool import recruitment_workflow

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    missing = tmp_path / "missing.pdf"

    result = json.loads(
        recruitment_workflow(action="prepare", site="liepin", resume_path=str(missing))
    )

    assert result["success"] is False
    assert "does not exist" in result["error"]


def test_prepare_blocks_sensitive_resume(tmp_path, monkeypatch):
    from tools.recruitment_tool import recruitment_workflow

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    secret = tmp_path / ".env"
    secret.write_text("SECRET=1", encoding="utf-8")

    result = json.loads(
        recruitment_workflow(action="prepare", site="boss", resume_path=str(secret))
    )

    assert result["success"] is False
    assert "Access denied" in result["error"]


def test_site_profile_returns_supported_site_metadata(tmp_path, monkeypatch):
    from tools.recruitment_tool import recruitment_workflow

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))

    result = json.loads(recruitment_workflow(action="site_profile", site="liepin"))

    assert result["success"] is True
    assert result["site"] == "liepin"
    assert result["profile"]["final_submit_keywords"]
    assert result["profile"]["common_blockers"]


def test_confirm_submit_requires_explicit_true(tmp_path, monkeypatch):
    from tools.recruitment_tool import recruitment_workflow

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))

    blocked = json.loads(
        recruitment_workflow(action="confirm_submit", site="51job", company="测试公司", title="IT经理")
    )
    allowed = json.loads(
        recruitment_workflow(
            action="confirm_submit",
            site="51job",
            company="测试公司",
            title="IT经理",
            confirm=True,
        )
    )

    assert blocked["success"] is False
    assert "confirm=true" in blocked["error"]
    assert allowed["success"] is True
    assert allowed["confirmed"] is True


def test_record_and_list_results_roundtrip(tmp_path, monkeypatch):
    from tools.recruitment_tool import recruitment_workflow

    hermes_home = tmp_path / ".hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    written = json.loads(
        recruitment_workflow(
            action="record_result",
            site="boss",
            company="测试公司",
            title="信息化经理",
            job_url="https://www.zhipin.com/job_detail/abc.html",
            status="submitted",
            notes="已人工确认后提交",
        )
    )
    listed = json.loads(recruitment_workflow(action="list_results", limit=10))

    assert written["success"] is True
    assert written["record"]["status"] == "submitted"
    assert listed["success"] is True
    assert listed["total"] == 1
    assert listed["results"][0]["company"] == "测试公司"
    assert (hermes_home / "recruitment" / "application_log.jsonl").exists()


def test_tool_is_wired_into_registry_and_toolsets():
    from model_tools import _LEGACY_TOOLSET_MAP
    from toolsets import TOOLSETS, _HERMES_CORE_TOOLS
    from tools.registry import registry
    from tools import recruitment_tool  # noqa: F401

    assert "recruitment_workflow" in _HERMES_CORE_TOOLS
    assert "recruitment_workflow" in TOOLSETS["browser"]["tools"]
    assert "recruitment_workflow" in _LEGACY_TOOLSET_MAP["browser_tools"]
    assert "recruitment_workflow" in registry._tools
