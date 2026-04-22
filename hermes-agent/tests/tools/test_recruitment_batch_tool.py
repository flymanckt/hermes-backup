"""Tests for batch recruitment orchestration actions."""

import json


def test_create_batch_plan_returns_search_url_and_batch_id(tmp_path, monkeypatch):
    from tools.recruitment_tool import recruitment_workflow

    hermes_home = tmp_path / ".hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    resume = tmp_path / "resume.pdf"
    resume.write_text("resume", encoding="utf-8")

    result = json.loads(
        recruitment_workflow(
            action="create_batch_plan",
            site="liepin",
            resume_path=str(resume),
            keywords=["IT经理", "信息化负责人"],
            city="深圳",
            salary_min=25000,
        )
    )

    assert result["success"] is True
    assert result["batch_id"]
    assert result["search_url"].startswith("https://")
    assert result["queue_summary"]["pending"] == 0
    assert (hermes_home / "recruitment" / "batches" / f"{result['batch_id']}.json").exists()


def test_enqueue_next_and_mark_job_roundtrip(tmp_path, monkeypatch):
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
            city="上海",
        )
    )
    batch_id = created["batch_id"]

    enqueued = json.loads(
        recruitment_workflow(
            action="enqueue_jobs",
            batch_id=batch_id,
            jobs=[
                {
                    "job_url": "https://www.zhipin.com/job_detail/1.html",
                    "company": "甲公司",
                    "title": "IT经理",
                },
                {
                    "job_url": "https://www.zhipin.com/job_detail/2.html",
                    "company": "乙公司",
                    "title": "信息化负责人",
                },
            ],
        )
    )
    next_job = json.loads(recruitment_workflow(action="next_job", batch_id=batch_id))
    marked = json.loads(
        recruitment_workflow(
            action="mark_job",
            batch_id=batch_id,
            job_url="https://www.zhipin.com/job_detail/1.html",
            status="submitted",
            notes="已投递",
        )
    )
    status = json.loads(recruitment_workflow(action="batch_status", batch_id=batch_id))

    assert enqueued["success"] is True
    assert enqueued["added"] == 2
    assert next_job["success"] is True
    assert next_job["job"]["company"] == "甲公司"
    assert marked["success"] is True
    assert marked["job"]["status"] == "submitted"
    assert status["success"] is True
    assert status["summary"]["submitted"] == 1
    assert status["summary"]["pending"] == 1


def test_enqueue_jobs_deduplicates_by_url(tmp_path, monkeypatch):
    from tools.recruitment_tool import recruitment_workflow

    hermes_home = tmp_path / ".hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    resume = tmp_path / "resume.pdf"
    resume.write_text("resume", encoding="utf-8")

    created = json.loads(
        recruitment_workflow(
            action="create_batch_plan",
            site="51job",
            resume_path=str(resume),
            keywords=["IT经理"],
            city="广州",
        )
    )
    batch_id = created["batch_id"]

    first = json.loads(
        recruitment_workflow(
            action="enqueue_jobs",
            batch_id=batch_id,
            jobs=[{"job_url": "https://www.51job.com/job/1.html", "company": "甲公司", "title": "IT经理"}],
        )
    )
    second = json.loads(
        recruitment_workflow(
            action="enqueue_jobs",
            batch_id=batch_id,
            jobs=[{"job_url": "https://www.51job.com/job/1.html", "company": "甲公司", "title": "IT经理"}],
        )
    )

    assert first["added"] == 1
    assert second["added"] == 0
    assert second["skipped_duplicates"] == 1
