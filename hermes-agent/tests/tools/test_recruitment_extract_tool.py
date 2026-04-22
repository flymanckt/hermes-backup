"""Tests for extracting job candidates from browser search-result data."""

import json


def test_extract_search_results_parses_job_cards_and_optionally_enqueues(tmp_path, monkeypatch):
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
    batch_id = created["batch_id"]

    extraction = json.loads(
        recruitment_workflow(
            action="extract_search_results",
            batch_id=batch_id,
            candidates=[
                {
                    "job_url": "https://www.liepin.com/job/1.shtml",
                    "company": "甲公司",
                    "title": "IT经理",
                },
                {
                    "job_url": "https://www.liepin.com/job/2.shtml",
                    "company": "乙公司",
                    "title": "信息化负责人",
                },
            ],
            auto_enqueue=True,
        )
    )
    status = json.loads(recruitment_workflow(action="batch_status", batch_id=batch_id))

    assert extraction["success"] is True
    assert extraction["count"] == 2
    assert extraction["enqueued"]["added"] == 2
    assert status["summary"]["pending"] == 2


def test_extract_search_results_deduplicates_candidate_urls(tmp_path, monkeypatch):
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

    extraction = json.loads(
        recruitment_workflow(
            action="extract_search_results",
            batch_id=created["batch_id"],
            candidates=[
                {"job_url": "https://www.zhipin.com/job_detail/1.html", "company": "甲公司", "title": "IT经理"},
                {"job_url": "https://www.zhipin.com/job_detail/1.html", "company": "甲公司", "title": "IT经理"},
            ],
            auto_enqueue=False,
        )
    )

    assert extraction["success"] is True
    assert extraction["count"] == 1
