"""Tests for site-specific browser extraction script templates."""

import json


def test_get_search_extract_script_returns_site_specific_templates():
    from tools.recruitment_tool import recruitment_workflow

    liepin = json.loads(recruitment_workflow(action="get_search_extract_script", site="liepin"))
    boss = json.loads(recruitment_workflow(action="get_search_extract_script", site="boss"))
    job51 = json.loads(recruitment_workflow(action="get_search_extract_script", site="51job"))

    assert liepin["success"] is True
    assert boss["success"] is True
    assert job51["success"] is True
    assert "querySelectorAll" in liepin["script"]
    assert "querySelectorAll" in boss["script"]
    assert "querySelectorAll" in job51["script"]
    assert liepin["site"] == "liepin"
    assert boss["site"] == "boss"
    assert job51["site"] == "51job"


def test_get_search_extract_script_includes_usage_steps():
    from tools.recruitment_tool import recruitment_workflow

    result = json.loads(recruitment_workflow(action="get_search_extract_script", site="boss"))

    assert result["success"] is True
    assert result["usage_steps"]
    assert any("browser_console" in step for step in result["usage_steps"])
