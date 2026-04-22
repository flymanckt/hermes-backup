"""Tests for parsing real search-page payloads into candidates."""

import json


def test_parse_search_page_normalizes_liepin_payload_and_auto_enqueues(tmp_path, monkeypatch):
    from tools.recruitment_tool import recruitment_workflow

    hermes_home = tmp_path / ".hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    resume = tmp_path / "resume.pdf"
    resume.write_text("resume", encoding="utf-8")

    created = json.loads(
        recruitment_workflow(
            action="create_batch_plan",
            site="liepin",
            resume_path=str(resume),
            keywords=["IT经理"],
            city="深圳",
        )
    )

    parsed = json.loads(
        recruitment_workflow(
            action="parse_search_page",
            batch_id=created["batch_id"],
            page_data=[
                {
                    "job_url": "https://www.liepin.com/job/1.shtml",
                    "company": "甲公司",
                    "title": "IT经理",
                    "salary": "25-35k",
                },
                {
                    "url": "https://www.liepin.com/job/2.shtml",
                    "company": "乙公司",
                    "job_title": "信息化负责人",
                    "salary": "30-45k",
                },
            ],
            auto_enqueue=True,
        )
    )
    status = json.loads(recruitment_workflow(action="batch_status", batch_id=created["batch_id"]))

    assert parsed["success"] is True
    assert parsed["count"] == 2
    assert parsed["jobs"][0]["salary"] == "25-35k"
    assert parsed["enqueued"]["added"] == 2
    assert status["summary"]["pending"] == 2


def test_parse_search_page_deduplicates_and_skips_items_without_url(tmp_path, monkeypatch):
    from tools.recruitment_tool import recruitment_workflow

    hermes_home = tmp_path / ".hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    resume = tmp_path / "resume.pdf"
    resume.write_text("resume", encoding="utf-8")

    created = json.loads(
        recruitment_workflow(
            action="create_batch_plan",
            site="boss",
            resume_path=str(resume),
            keywords=["IT经理"],
        )
    )

    parsed = json.loads(
        recruitment_workflow(
            action="parse_search_page",
            batch_id=created["batch_id"],
            page_data=[
                {"job_url": "https://www.zhipin.com/job_detail/1.html", "company": "甲公司", "title": "IT经理"},
                {"job_url": "https://www.zhipin.com/job_detail/1.html", "company": "甲公司", "title": "IT经理"},
                {"company": "缺链接公司", "title": "无效职位"},
            ],
            auto_enqueue=False,
        )
    )

    assert parsed["success"] is True
    assert parsed["count"] == 1
    assert parsed["skipped_missing_url"] == 1
