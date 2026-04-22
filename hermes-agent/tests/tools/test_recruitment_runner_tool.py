"""Tests for run_batch_once semi-automatic runner."""

import json


def test_run_batch_once_populates_queue_from_search_page_and_returns_next_job(tmp_path, monkeypatch):
    from tools import recruitment_tool as rt

    hermes_home = tmp_path / ".hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    resume = tmp_path / "resume.pdf"
    resume.write_text("resume", encoding="utf-8")

    created = json.loads(
        rt.recruitment_workflow(
            action="create_batch_plan",
            site="liepin",
            resume_path=str(resume),
            keywords=["IT经理"],
            city="深圳",
        )
    )

    nav_calls = []
    console_calls = []

    def fake_nav(url, task_id=None):
        nav_calls.append((url, task_id))
        return json.dumps({"success": True, "url": url})

    def fake_console(clear=False, expression=None, task_id=None):
        console_calls.append((expression, task_id))
        return json.dumps(
            {
                "success": True,
                "result": [
                    {
                        "job_url": "https://www.liepin.com/job/1.shtml",
                        "company": "甲公司",
                        "job_title": "IT经理",
                        "salary": "25-35k",
                    }
                ],
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr(rt, "browser_navigate", fake_nav)
    monkeypatch.setattr(rt, "browser_console", fake_console)

    result = json.loads(
        rt.recruitment_workflow(
            action="run_batch_once",
            batch_id=created["batch_id"],
            task_id="runner-task",
        )
    )

    assert result["success"] is True
    assert result["queue_refreshed"] is True
    assert result["next_job"]["company"] == "甲公司"
    assert result["prepared"]["ready"] is True
    assert nav_calls[0][0] == created["search_url"]
    assert nav_calls[1][0] == "https://www.liepin.com/job/1.shtml"
    assert console_calls[0][0]


def test_run_batch_once_uses_existing_pending_job_without_refresh(tmp_path, monkeypatch):
    from tools import recruitment_tool as rt

    hermes_home = tmp_path / ".hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    resume = tmp_path / "resume.pdf"
    resume.write_text("resume", encoding="utf-8")

    created = json.loads(
        rt.recruitment_workflow(
            action="create_batch_plan",
            site="boss",
            resume_path=str(resume),
            keywords=["IT经理"],
        )
    )
    batch_id = created["batch_id"]
    json.loads(
        rt.recruitment_workflow(
            action="enqueue_jobs",
            batch_id=batch_id,
            jobs=[{"job_url": "https://www.zhipin.com/job_detail/1.html", "company": "甲公司", "title": "IT经理"}],
        )
    )

    nav_calls = []
    console_calls = []

    monkeypatch.setattr(rt, "browser_navigate", lambda url, task_id=None: nav_calls.append((url, task_id)) or json.dumps({"success": True, "url": url}))
    monkeypatch.setattr(rt, "browser_console", lambda clear=False, expression=None, task_id=None: console_calls.append((expression, task_id)) or json.dumps([]))

    result = json.loads(rt.recruitment_workflow(action="run_batch_once", batch_id=batch_id, task_id="runner-task"))

    assert result["success"] is True
    assert result["queue_refreshed"] is False
    assert result["next_job"]["job_url"] == "https://www.zhipin.com/job_detail/1.html"
    assert len(nav_calls) == 1
    assert console_calls == []
