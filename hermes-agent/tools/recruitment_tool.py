"""Recruitment workflow tool — browser-side job application helper.

This tool does not replace browser automation. It sits one level above it and
adds:
- site-specific application guidance
- resume/material preflight validation
- explicit final-submit confirmation guard
- local application result logging
- batch application queue planning for multi-job workflows
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote_plus, urlencode
from uuid import uuid4

from agent.safety_policy import get_sensitive_read_path_error
from hermes_constants import get_hermes_home
from tools.browser_tool import browser_console, browser_navigate
from tools.registry import registry, tool_error


SUPPORTED_SITES: dict[str, dict[str, Any]] = {
    "51job": {
        "display_name": "前程无忧",
        "login_methods": ["手机验证码", "密码登录"],
        "common_steps": [
            "打开职位详情页并确认岗位与地区",
            "检查是否已登录以及简历是否已上传",
            "如有附件上传框，使用 browser_upload 上传简历",
            "补全期望薪资、到岗时间、工作年限等必填项",
            "最终点击投递前，先调用 recruitment_workflow(action='confirm_submit', confirm=true, ...)",
        ],
        "common_blockers": ["短信验证码", "已投递提示", "必填项未补全", "隐私协议勾选"],
        "final_submit_keywords": ["投递", "立即投递", "确认投递", "提交申请"],
        "search_url_builder": lambda keyword, city, salary_min, salary_max: (
            "https://we.51job.com/pc/search?" + urlencode(
                {
                    "keyword": keyword,
                    **({"jobArea": city} if city else {}),
                    **({"providesalary": f"{salary_min}-{salary_max}"} if salary_min or salary_max else {}),
                }
            )
        ),
    },
    "liepin": {
        "display_name": "猎聘",
        "login_methods": ["手机验证码", "密码登录"],
        "common_steps": [
            "打开职位详情页并确认岗位名称、薪资和公司",
            "检查登录状态以及猎聘在线简历是否完整",
            "如页面要求附件简历，使用 browser_upload 上传 PDF/Word 简历",
            "处理弹窗、同意协议、补充附加问题",
            "最终点击投递前，先调用 recruitment_workflow(action='confirm_submit', confirm=true, ...)",
        ],
        "common_blockers": ["验证码", "简历完整度不足", "猎头沟通弹窗", "重复投递限制"],
        "final_submit_keywords": ["立即沟通", "立即投递", "申请职位", "确认申请"],
        "search_url_builder": lambda keyword, city, salary_min, salary_max: (
            "https://www.liepin.com/zhaopin/?" + urlencode(
                {
                    "key": keyword,
                    **({"city": city} if city else {}),
                    **({"salary": f"{salary_min}_{salary_max or salary_min}"} if salary_min or salary_max else {}),
                }
            )
        ),
    },
    "boss": {
        "display_name": "BOSS直聘",
        "login_methods": ["扫码登录", "手机验证码"],
        "common_steps": [
            "打开职位详情页并确认岗位与招聘者信息",
            "检查是否需要先发起沟通或打招呼",
            "如支持附件简历上传，使用 browser_upload 上传简历",
            "确认默认招呼语和附加问题是否合适",
            "最终点击发送/投递前，先调用 recruitment_workflow(action='confirm_submit', confirm=true, ...)",
        ],
        "common_blockers": ["滑块验证码", "需要先聊天", "账号风控", "附件格式限制"],
        "final_submit_keywords": ["发送简历", "立即沟通", "立即投递", "发送"],
        "search_url_builder": lambda keyword, city, salary_min, salary_max: (
            "https://www.zhipin.com/web/geek/job?" + urlencode(
                {
                    "query": keyword,
                    **({"city": city} if city else {}),
                    **({"salary": f"{salary_min}-{salary_max or salary_min}"} if salary_min or salary_max else {}),
                }
            )
        ),
    },
}

DEFAULT_STATUSES = {"prepared", "submitted", "skipped", "blocked", "failed"}
BATCH_JOB_STATUSES = {"pending", "submitted", "skipped", "blocked", "failed"}

SEARCH_EXTRACT_SCRIPTS: dict[str, str] = {
    "liepin": r"""
JSON.stringify(Array.from(document.querySelectorAll('a[href*="/job/"]')).map((link) => {
  const card = link.closest('div, li, article') || link;
  const textOf = (selectors) => {
    for (const selector of selectors) {
      const el = card.querySelector(selector);
      const text = (el?.textContent || '').trim();
      if (text) return text;
    }
    return '';
  };
  return {
    job_url: link.href,
    title: textOf(['.job-title', '.ellipsis-1', '[data-selector="job-title"]']) || link.textContent.trim(),
    company: textOf(['.company-name', '.company', '[data-selector="company-name"]']),
    salary: textOf(['.job-salary', '.salary', '[data-selector="job-salary"]'])
  };
}).filter(item => item.job_url))
""".strip(),
    "boss": r"""
JSON.stringify(Array.from(document.querySelectorAll('a[href*="job_detail"], a[href*="/job/"]')).map((link) => {
  const card = link.closest('li, div, article') || link;
  const textOf = (selectors) => {
    for (const selector of selectors) {
      const el = card.querySelector(selector);
      const text = (el?.textContent || '').trim();
      if (text) return text;
    }
    return '';
  };
  return {
    job_url: link.href,
    title: textOf(['.job-name', '.job-title', '[data-name="job-title"]']) || link.textContent.trim(),
    company: textOf(['.company-name', '.boss-name', '.company-text']),
    salary: textOf(['.salary', '.job-limit'])
  };
}).filter(item => item.job_url))
""".strip(),
    "51job": r"""
JSON.stringify(Array.from(document.querySelectorAll('a[href*="/job/"]')).map((link) => {
  const card = link.closest('div, li, article') || link;
  const textOf = (selectors) => {
    for (const selector of selectors) {
      const el = card.querySelector(selector);
      const text = (el?.textContent || '').trim();
      if (text) return text;
    }
    return '';
  };
  return {
    job_url: link.href,
    title: textOf(['.jname', '.job-name', '.job-title']) || link.textContent.trim(),
    company: textOf(['.cname', '.company', '.company-name']),
    salary: textOf(['.sal', '.salary', '.job-salary'])
  };
}).filter(item => item.job_url))
""".strip(),
}

# Blocker detection scripts — return a JSON object: { "blocked": bool, "reason": string, "type": string }
# type: "captcha" | "login" | "frequency" | "cloudflare" | "empty" | "unknown"
BLOCKER_DETECTION_SCRIPTS: dict[str, str] = {
    "liepin": r"""
(function() {
  const html = document.body.innerHTML;
  const url = location.href;
  // 猎聘安全中心 / 验证码
  if (/verify|验证码|安全中心|异常登录/.test(html) || url.includes('captcha') || url.includes('verify')) {
    if (/请进行验证|安全验证|滑动/.test(html)) return JSON.stringify({blocked:true,reason:'滑块验证码',type:'captcha'});
    if (/登录异常|账号异常|安全中心/.test(html)) return JSON.stringify({blocked:true,reason:'账号异常/安全拦截',type:'frequency'});
  }
  // 登录墙
  if (document.querySelector('.login-container') || document.querySelector('[class*="login"]') && !document.querySelector('.job-title')) {
    return JSON.stringify({blocked:true,reason:'未登录',type:'login'});
  }
  // 空结果
  const jobCards = document.querySelectorAll('.job-card-box, .job-info, [class*="job-item"]');
  if (!jobCards || jobCards.length === 0) return JSON.stringify({blocked:true,reason:'页面无职位数据',type:'empty'});
  return JSON.stringify({blocked:false,reason:'',type:''});
})()
""".strip(),
    "boss": r"""
(function() {
  const html = document.body.innerHTML;
  const url = location.href;
  // BOSS 滑块
  if (/captcha|验证码|验证/.test(html) || url.includes('captcha')) {
    if (/滑动|拼图|验证/.test(html)) return JSON.stringify({blocked:true,reason:'滑块验证码',type:'captcha'});
  }
  // 登录
  if (url.includes('login') || document.querySelector('.login-container')) {
    return JSON.stringify({blocked:true,reason:'未登录',type:'login'});
  }
  // 空页面
  const content = document.querySelector('.job-list, .job-box, #job-list, main');
  if (!content || content.innerHTML.trim().length < 200) return JSON.stringify({blocked:true,reason:'页面内容为空',type:'empty'});
  return JSON.stringify({blocked:false,reason:'',type:''});
})()
""".strip(),
    "51job": r"""
(function() {
  const html = document.body.innerHTML;
  const url = location.href;
  // 51job 滑块
  if (/verify|验证码|滑动/.test(html) || url.includes('verify')) {
    if (/滑动|验证/.test(html)) return JSON.stringify({blocked:true,reason:'滑块验证码',type:'captcha'});
  }
  // 登录
  if (url.includes('login') || document.querySelector('.login-container')) {
    return JSON.stringify({blocked:true,reason:'未登录',type:'login'});
  }
  // 空搜索结果
  const items = document.querySelectorAll('.j_joblist li, .job_item, [class*="job-item"]');
  if (!items || items.length === 0) return JSON.stringify({blocked:true,reason:'无搜索结果',type:'empty'});
  return JSON.stringify({blocked:false,reason:'',type:''});
})()
""".strip(),
}


def _normalize_site(site: Optional[str]) -> str:
    value = (site or "").strip().lower()
    aliases = {
        "前程无忧": "51job",
        "51job": "51job",
        "liepin": "liepin",
        "猎聘": "liepin",
        "boss": "boss",
        "boss直聘": "boss",
        "zhipin": "boss",
    }
    return aliases.get(value, value)


def _recruitment_dir() -> Path:
    return get_hermes_home() / "recruitment"


def _log_path() -> Path:
    return _recruitment_dir() / "application_log.jsonl"


def _batch_dir() -> Path:
    return _recruitment_dir() / "batches"


def _batch_path(batch_id: str) -> Path:
    return _batch_dir() / f"{batch_id}.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_supported_site(site: Optional[str]) -> tuple[Optional[str], Optional[dict[str, Any]], Optional[str]]:
    normalized = _normalize_site(site)
    profile = SUPPORTED_SITES.get(normalized)
    if not profile:
        supported = ", ".join(sorted(SUPPORTED_SITES.keys()))
        return None, None, f"Unsupported site: {site}. Supported sites: {supported}"
    return normalized, profile, None


def _validate_resume_path(resume_path: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    candidate = str(resume_path or "").strip()
    if not candidate:
        return None, "resume_path is required for this action."

    path_error = get_sensitive_read_path_error(candidate)
    if path_error:
        return None, path_error

    resolved = Path(candidate).expanduser().resolve()
    if not resolved.exists():
        return None, f"Resume file does not exist: {candidate}"
    if not resolved.is_file():
        return None, f"Resume path must be a file, not a directory: {candidate}"
    return str(resolved), None


def _coerce_keywords(keywords: Any) -> list[str]:
    if keywords is None:
        return []
    if isinstance(keywords, str):
        items = [part.strip() for part in keywords.replace("，", ",").split(",")]
        return [item for item in items if item]
    if isinstance(keywords, list):
        result = []
        for item in keywords:
            value = str(item or "").strip()
            if value:
                result.append(value)
        return result
    return []


def _build_keyword_text(keywords: list[str]) -> str:
    if not keywords:
        return ""
    if len(keywords) == 1:
        return keywords[0]
    return " OR ".join(keywords)


def _batch_summary(jobs: list[dict[str, Any]]) -> dict[str, int]:
    summary = {status: 0 for status in BATCH_JOB_STATUSES}
    for job in jobs:
        status = str(job.get("status") or "pending").strip().lower()
        if status not in summary:
            summary[status] = 0
        summary[status] += 1
    return summary


def _read_batch(batch_id: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    path = _batch_path(batch_id)
    if not path.exists():
        return None, f"Batch not found: {batch_id}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"Batch file is corrupted: {exc}"


def _write_batch(batch: dict[str, Any]) -> None:
    batch_dir = _batch_dir()
    batch_dir.mkdir(parents=True, exist_ok=True)
    _batch_path(batch["batch_id"]).write_text(
        json.dumps(batch, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _search_url(site: str, profile: dict[str, Any], keywords: list[str], city: str, salary_min: Optional[int], salary_max: Optional[int]) -> str:
    keyword = _build_keyword_text(keywords)
    builder = profile["search_url_builder"]
    return builder(keyword, city, salary_min, salary_max)


def _public_site_profile(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in profile.items()
        if key != "search_url_builder"
    }


def _get_search_extract_script(site: str) -> dict[str, Any]:
    script = SEARCH_EXTRACT_SCRIPTS.get(site)
    if not script:
        return {"success": False, "error": f"No search extract script template for site: {site}"}
    return {
        "success": True,
        "site": site,
        "script": script,
        "usage_steps": [
            "在搜索结果页执行 browser_console(expression=<script>) 抓取职位卡片原始数据",
            "把返回结果作为 page_data 传给 recruitment_workflow(action='parse_search_page', ...)",
            "如果希望直接入队，把 auto_enqueue 设为 true",
        ],
    }


def _detect_blocker(site: str, raw_console_result: str) -> dict[str, Any]:
    """Parse blocker detection result from browser console. Returns {blocked, reason, type}."""
    script = BLOCKER_DETECTION_SCRIPTS.get(site)
    if not script:
        return {"blocked": False, "reason": "", "type": ""}

    try:
        parsed = json.loads(raw_console_result)
    except json.JSONDecodeError:
        return {"blocked": False, "reason": "", "type": ""}

    # Handle nested "result" wrapper from browser_console
    if isinstance(parsed, dict):
        if parsed.get("success") is False:
            return {"blocked": True, "reason": "浏览器执行失败", "type": "unknown"}
        if "result" in parsed:
            inner = parsed["result"]
            if isinstance(inner, str):
                try:
                    inner = json.loads(inner)
                except json.JSONDecodeError:
                    return {"blocked": False, "reason": "", "type": ""}
            parsed = inner

    blocked = bool(parsed.get("blocked", False))
    reason = str(parsed.get("reason", "") or "")
    blocker_type = str(parsed.get("type", "") or "")
    return {"blocked": blocked, "reason": reason, "type": blocker_type}


def _coerce_browser_eval_payload(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"success": False, "error": "Browser console returned non-JSON content."}

    if isinstance(payload, list):
        return {"success": True, "page_data": payload}
    if isinstance(payload, dict) and payload.get("success") and isinstance(payload.get("result"), list):
        return {"success": True, "page_data": payload["result"]}
    if isinstance(payload, dict) and payload.get("success") is False:
        return {"success": False, "error": payload.get("error", "Browser eval failed")}
    return {"success": False, "error": "Browser console did not return a candidate list."}


def _build_prepare_response(site: str, profile: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    normalized_resume_path, error = _validate_resume_path(args.get("resume_path"))
    if error:
        return {"success": False, "error": error}

    company = str(args.get("company") or "").strip()
    title = str(args.get("title") or "").strip()
    job_url = str(args.get("job_url") or "").strip()

    next_steps = [
        f"先用 browser_navigate 打开目标页面：{job_url or '职位详情页 URL 未提供，需要先定位职位页'}",
        "用 browser_snapshot 查找上传控件、必填输入框和最终提交按钮",
        "如有文件上传控件，调用 browser_upload 上传简历附件",
        *profile["common_steps"],
    ]

    return {
        "success": True,
        "ready": True,
        "site": site,
        "site_display_name": profile["display_name"],
        "normalized_resume_path": normalized_resume_path,
        "company": company,
        "title": title,
        "job_url": job_url,
        "common_blockers": profile["common_blockers"],
        "final_submit_keywords": profile["final_submit_keywords"],
        "next_steps": next_steps,
    }


def _build_confirm_response(site: str, profile: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    company = str(args.get("company") or "").strip()
    title = str(args.get("title") or "").strip()
    confirmed = bool(args.get("confirm", False))

    if not confirmed:
        return {
            "success": False,
            "error": (
                "Final application submission is blocked until you pass confirm=true. "
                "Use this only after you have verified the target job, company, resume, and form fields."
            ),
            "site": site,
            "company": company,
            "title": title,
            "final_submit_keywords": profile["final_submit_keywords"],
        }

    return {
        "success": True,
        "confirmed": True,
        "site": site,
        "company": company,
        "title": title,
        "message": "Explicit submit confirmation recorded. You may now click the final submit/apply button in the browser.",
        "final_submit_keywords": profile["final_submit_keywords"],
    }


def _record_result(args: dict[str, Any]) -> dict[str, Any]:
    site, profile, error = _ensure_supported_site(args.get("site"))
    if error:
        return {"success": False, "error": error}

    status = str(args.get("status") or "").strip().lower()
    if status not in DEFAULT_STATUSES:
        allowed = ", ".join(sorted(DEFAULT_STATUSES))
        return {"success": False, "error": f"Invalid status: {status}. Allowed: {allowed}"}

    record = {
        "timestamp": _utc_now(),
        "site": site,
        "site_display_name": profile["display_name"],
        "company": str(args.get("company") or "").strip(),
        "title": str(args.get("title") or "").strip(),
        "url": str(args.get("job_url") or args.get("url") or "").strip(),
        "status": status,
        "notes": str(args.get("notes") or "").strip(),
        **({"batch_id": str(args.get("batch_id"))} if args.get("batch_id") else {}),
    }

    log_path = _log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {"success": True, "record": record, "log_path": str(log_path)}


def _list_results(args: dict[str, Any]) -> dict[str, Any]:
    limit = args.get("limit", 20)
    try:
        limit = max(1, int(limit))
    except (TypeError, ValueError):
        limit = 20

    log_path = _log_path()
    if not log_path.exists():
        return {"success": True, "total": 0, "results": [], "log_path": str(log_path)}

    results: list[dict[str, Any]] = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    sliced = list(reversed(results))[:limit]
    return {
        "success": True,
        "total": len(results),
        "results": sliced,
        "log_path": str(log_path),
    }


def _create_batch_plan(args: dict[str, Any]) -> dict[str, Any]:
    site, profile, error = _ensure_supported_site(args.get("site"))
    if error:
        return {"success": False, "error": error}

    normalized_resume_path, resume_error = _validate_resume_path(args.get("resume_path"))
    if resume_error:
        return {"success": False, "error": resume_error}

    keywords = _coerce_keywords(args.get("keywords"))
    if not keywords:
        return {"success": False, "error": "keywords is required for create_batch_plan."}

    city = str(args.get("city") or "").strip()
    salary_min = args.get("salary_min")
    salary_max = args.get("salary_max")
    try:
        salary_min = int(salary_min) if salary_min is not None else None
    except (TypeError, ValueError):
        return {"success": False, "error": "salary_min must be an integer when provided."}
    try:
        salary_max = int(salary_max) if salary_max is not None else None
    except (TypeError, ValueError):
        return {"success": False, "error": "salary_max must be an integer when provided."}

    batch_id = f"batch_{uuid4().hex[:12]}"
    batch = {
        "batch_id": batch_id,
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "site": site,
        "site_display_name": profile["display_name"],
        "resume_path": normalized_resume_path,
        "filters": {
            "keywords": keywords,
            "city": city,
            "salary_min": salary_min,
            "salary_max": salary_max,
        },
        "search_url": _search_url(site, profile, keywords, city, salary_min, salary_max),
        "jobs": [],
    }
    _write_batch(batch)

    return {
        "success": True,
        "batch_id": batch_id,
        "site": site,
        "resume_path": normalized_resume_path,
        "filters": batch["filters"],
        "search_url": batch["search_url"],
        "queue_summary": _batch_summary(batch["jobs"]),
        "next_steps": [
            f"先用 browser_navigate 打开搜索结果页：{batch['search_url']}",
            "浏览搜索结果后，把候选岗位 URL/公司/标题整理给 recruitment_workflow(action='enqueue_jobs', ...)",
            "每次处理前用 recruitment_workflow(action='next_job', batch_id=...) 取下一个待投岗位",
        ],
        "batch_path": str(_batch_path(batch_id)),
    }


def _normalize_jobs(raw_jobs: Any, *, field_name: str = "jobs") -> tuple[list[dict[str, Any]], Optional[str]]:
    if not isinstance(raw_jobs, list) or not raw_jobs:
        return [], f"{field_name} must be a non-empty array."
    normalized: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for job in raw_jobs:
        if not isinstance(job, dict):
            return [], f"Each item in {field_name} must be an object with at least job_url."
        job_url = str(job.get("job_url") or job.get("url") or "").strip()
        if not job_url:
            return [], f"Each item in {field_name} must include job_url."
        if job_url in seen_urls:
            continue
        seen_urls.add(job_url)
        normalized.append(
            {
                "job_url": job_url,
                "company": str(job.get("company") or "").strip(),
                "title": str(job.get("title") or "").strip(),
                "salary": str(job.get("salary") or "").strip(),
                "status": "pending",
                "notes": str(job.get("notes") or "").strip(),
                "added_at": _utc_now(),
            }
        )
    return normalized, None


def _parse_page_jobs(page_data: Any) -> dict[str, Any]:
    if not isinstance(page_data, list) or not page_data:
        return {"success": False, "error": "page_data must be a non-empty array."}

    jobs: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    skipped_missing_url = 0

    for item in page_data:
        if not isinstance(item, dict):
            continue
        job_url = str(item.get("job_url") or item.get("url") or item.get("href") or "").strip()
        if not job_url:
            skipped_missing_url += 1
            continue
        if job_url in seen_urls:
            continue
        seen_urls.add(job_url)
        jobs.append(
            {
                "job_url": job_url,
                "company": str(item.get("company") or item.get("company_name") or "").strip(),
                "title": str(item.get("title") or item.get("job_title") or item.get("position") or "").strip(),
                "salary": str(item.get("salary") or item.get("salary_text") or "").strip(),
                "notes": str(item.get("notes") or "").strip(),
                "status": "pending",
                "added_at": _utc_now(),
            }
        )

    return {
        "success": True,
        "jobs": jobs,
        "count": len(jobs),
        "skipped_missing_url": skipped_missing_url,
    }


def _enqueue_jobs(args: dict[str, Any]) -> dict[str, Any]:
    batch_id = str(args.get("batch_id") or "").strip()
    if not batch_id:
        return {"success": False, "error": "batch_id is required for enqueue_jobs."}
    batch, error = _read_batch(batch_id)
    if error:
        return {"success": False, "error": error}

    normalized_jobs, jobs_error = _normalize_jobs(args.get("jobs"))
    if jobs_error:
        return {"success": False, "error": jobs_error}

    existing_urls = {str(job.get("job_url") or "") for job in batch["jobs"]}
    added = 0
    skipped_duplicates = 0
    for job in normalized_jobs:
        if job["job_url"] in existing_urls:
            skipped_duplicates += 1
            continue
        batch["jobs"].append(job)
        existing_urls.add(job["job_url"])
        added += 1

    batch["updated_at"] = _utc_now()
    _write_batch(batch)
    return {
        "success": True,
        "batch_id": batch_id,
        "added": added,
        "skipped_duplicates": skipped_duplicates,
        "summary": _batch_summary(batch["jobs"]),
    }


def _next_job(args: dict[str, Any]) -> dict[str, Any]:
    batch_id = str(args.get("batch_id") or "").strip()
    if not batch_id:
        return {"success": False, "error": "batch_id is required for next_job."}
    batch, error = _read_batch(batch_id)
    if error:
        return {"success": False, "error": error}

    for job in batch["jobs"]:
        if str(job.get("status") or "pending") == "pending":
            return {
                "success": True,
                "batch_id": batch_id,
                "job": job,
                "summary": _batch_summary(batch["jobs"]),
            }

    return {
        "success": True,
        "batch_id": batch_id,
        "job": None,
        "summary": _batch_summary(batch["jobs"]),
        "message": "No pending jobs remain in this batch.",
    }


def _mark_job(args: dict[str, Any]) -> dict[str, Any]:
    batch_id = str(args.get("batch_id") or "").strip()
    if not batch_id:
        return {"success": False, "error": "batch_id is required for mark_job."}
    batch, error = _read_batch(batch_id)
    if error:
        return {"success": False, "error": error}

    job_url = str(args.get("job_url") or args.get("url") or "").strip()
    if not job_url:
        return {"success": False, "error": "job_url is required for mark_job."}

    status = str(args.get("status") or "").strip().lower()
    if status not in BATCH_JOB_STATUSES - {"pending"}:
        allowed = ", ".join(sorted(BATCH_JOB_STATUSES - {"pending"}))
        return {"success": False, "error": f"Invalid mark_job status: {status}. Allowed: {allowed}"}

    notes = str(args.get("notes") or "").strip()
    matched_job = None
    for job in batch["jobs"]:
        if str(job.get("job_url") or "") == job_url:
            job["status"] = status
            job["notes"] = notes
            job["updated_at"] = _utc_now()
            matched_job = job
            break

    if matched_job is None:
        return {"success": False, "error": f"Job not found in batch: {job_url}"}

    batch["updated_at"] = _utc_now()
    _write_batch(batch)
    _record_result(
        {
            "site": batch["site"],
            "job_url": matched_job["job_url"],
            "company": matched_job.get("company"),
            "title": matched_job.get("title"),
            "status": status,
            "notes": notes,
            "batch_id": batch_id,
        }
    )
    return {
        "success": True,
        "batch_id": batch_id,
        "job": matched_job,
        "summary": _batch_summary(batch["jobs"]),
    }


def _batch_status(args: dict[str, Any]) -> dict[str, Any]:
    batch_id = str(args.get("batch_id") or "").strip()
    if not batch_id:
        return {"success": False, "error": "batch_id is required for batch_status."}
    batch, error = _read_batch(batch_id)
    if error:
        return {"success": False, "error": error}
    return {
        "success": True,
        "batch_id": batch_id,
        "site": batch["site"],
        "filters": batch["filters"],
        "search_url": batch["search_url"],
        "summary": _batch_summary(batch["jobs"]),
        "jobs": batch["jobs"],
    }


def _extract_search_results(args: dict[str, Any]) -> dict[str, Any]:
    batch_id = str(args.get("batch_id") or "").strip()
    if not batch_id:
        return {"success": False, "error": "batch_id is required for extract_search_results."}
    batch, error = _read_batch(batch_id)
    if error:
        return {"success": False, "error": error}

    normalized_candidates, candidates_error = _normalize_jobs(args.get("candidates"), field_name="candidates")
    if candidates_error:
        return {"success": False, "error": candidates_error}

    response = {
        "success": True,
        "batch_id": batch_id,
        "count": len(normalized_candidates),
        "jobs": normalized_candidates,
    }

    if bool(args.get("auto_enqueue", False)):
        enqueued = _enqueue_jobs({"batch_id": batch_id, "jobs": normalized_candidates})
        response["enqueued"] = enqueued
    else:
        response["enqueued"] = {"success": True, "added": 0, "skipped_duplicates": 0}

    return response


def _parse_search_page(args: dict[str, Any]) -> dict[str, Any]:
    batch_id = str(args.get("batch_id") or "").strip()
    if not batch_id:
        return {"success": False, "error": "batch_id is required for parse_search_page."}
    batch, error = _read_batch(batch_id)
    if error:
        return {"success": False, "error": error}

    parsed = _parse_page_jobs(args.get("page_data"))
    if not parsed.get("success"):
        return parsed

    response = {
        "success": True,
        "batch_id": batch_id,
        "count": parsed["count"],
        "jobs": parsed["jobs"],
        "skipped_missing_url": parsed["skipped_missing_url"],
    }

    if bool(args.get("auto_enqueue", False)):
        enqueued = _enqueue_jobs({"batch_id": batch_id, "jobs": parsed["jobs"]})
        response["enqueued"] = enqueued
    else:
        response["enqueued"] = {"success": True, "added": 0, "skipped_duplicates": 0}

    return response


def _run_batch_once(args: dict[str, Any]) -> dict[str, Any]:
    batch_id = str(args.get("batch_id") or "").strip()
    if not batch_id:
        return {"success": False, "error": "batch_id is required for run_batch_once."}
    task_id = str(args.get("task_id") or "default").strip() or "default"

    batch, error = _read_batch(batch_id)
    if error:
        return {"success": False, "error": error}

    summary = _batch_summary(batch["jobs"])
    queue_refreshed = False
    extracted_count = 0

    if summary.get("pending", 0) == 0:
        nav_result = json.loads(browser_navigate(batch["search_url"], task_id=task_id))
        if not nav_result.get("success"):
            return {"success": False, "error": nav_result.get("error", "Failed to navigate search page")}

        # Blocker detection on search page
        search_blocker_script = BLOCKER_DETECTION_SCRIPTS.get(batch["site"], "")
        if search_blocker_script:
            raw_result = browser_console(expression=search_blocker_script, task_id=task_id)
            search_blocker = _detect_blocker(batch["site"], raw_result)
            if search_blocker["blocked"]:
                return {
                    "success": False,
                    "error": f"Search page blocked: {search_blocker['reason']} ({search_blocker['type']})",
                    "blocker": search_blocker,
                }

        script_payload = _get_search_extract_script(batch["site"])
        if not script_payload.get("success"):
            return script_payload

        raw_console = browser_console(expression=script_payload["script"], task_id=task_id)
        eval_payload = _coerce_browser_eval_payload(raw_console)
        if not eval_payload.get("success"):
            return eval_payload

        parsed = _parse_search_page(
            {
                "batch_id": batch_id,
                "page_data": eval_payload["page_data"],
                "auto_enqueue": True,
            }
        )
        if not parsed.get("success"):
            return parsed
        queue_refreshed = True
        extracted_count = int(parsed.get("count", 0))
        batch, error = _read_batch(batch_id)
        if error:
            return {"success": False, "error": error}

    next_payload = _next_job({"batch_id": batch_id})
    if not next_payload.get("success"):
        return next_payload
    next_job = next_payload.get("job")
    if not next_job:
        return {
            "success": True,
            "batch_id": batch_id,
            "queue_refreshed": queue_refreshed,
            "extracted_count": extracted_count,
            "next_job": None,
            "message": "No pending jobs available after this runner pass.",
        }

    job_nav = json.loads(browser_navigate(next_job["job_url"], task_id=task_id))
    if not job_nav.get("success"):
        return {"success": False, "error": job_nav.get("error", "Failed to navigate job detail page")}

    # ── Blocker detection on job detail page ──────────────────────────────────
    site = batch["site"]
    blocker_script = BLOCKER_DETECTION_SCRIPTS.get(site, "")
    blocker_result = {"blocked": False, "reason": "", "type": ""}
    if blocker_script:
        raw_result = browser_console(expression=blocker_script, task_id=task_id)
        blocker_result = _detect_blocker(site, raw_result)

    if blocker_result["blocked"]:
        # Auto-mark as blocked and return blocker info so caller can decide next action
        _mark_job({
            "batch_id": batch_id,
            "job_url": next_job["job_url"],
            "status": "blocked",
            "notes": f"[blocker] {blocker_result['reason']} ({blocker_result['type']})",
        })
        return {
            "success": True,
            "batch_id": batch_id,
            "job": next_job,
            "blocker": {
                "type": blocker_result["type"],
                "reason": blocker_result["reason"],
            },
            "summary": _batch_summary(_read_batch(batch_id)[0]["jobs"]),
            "runner_steps": [
                f"检测到 blocker: {blocker_result['reason']}（{blocker_result['type']}）",
                "该职位已自动标记为 blocked，可调用 next_job 取下一个",
                "如需换平台或等待冷却后重试，可调整批次后继续",
            ],
        }
    # ── End blocker detection ────────────────────────────────────────────────

    prepared = _build_prepare_response(
        batch["site"],
        SUPPORTED_SITES[batch["site"]],
        {
            "resume_path": batch["resume_path"],
            "job_url": next_job.get("job_url"),
            "company": next_job.get("company"),
            "title": next_job.get("title"),
        },
    )
    if not prepared.get("success"):
        return prepared

    return {
        "success": True,
        "batch_id": batch_id,
        "queue_refreshed": queue_refreshed,
        "extracted_count": extracted_count,
        "next_job": next_job,
        "prepared": prepared,
        "summary": _batch_summary(batch["jobs"]),
        "runner_steps": [
            "如页面有文件上传控件，下一步调用 browser_upload 上传简历",
            "补充必填项后调用 recruitment_workflow(action='confirm_submit', confirm=true, ...)",
            "最终点击提交后用 recruitment_workflow(action='mark_job', status='submitted', ... ) 记录结果",
        ],
    }


def recruitment_workflow(
    action: str,
    site: Optional[str] = None,
    resume_path: Optional[str] = None,
    job_url: Optional[str] = None,
    company: Optional[str] = None,
    title: Optional[str] = None,
    confirm: bool = False,
    status: Optional[str] = None,
    notes: Optional[str] = None,
    limit: int = 20,
    batch_id: Optional[str] = None,
    keywords: Any = None,
    city: Optional[str] = None,
    salary_min: Optional[int] = None,
    salary_max: Optional[int] = None,
    jobs: Any = None,
    candidates: Any = None,
    auto_enqueue: bool = False,
    page_data: Any = None,
    task_id: Optional[str] = None,
) -> str:
    """High-level helper for browser-based job application workflows."""
    normalized_action = str(action or "").strip().lower()

    if normalized_action == "list_results":
        return json.dumps(_list_results({"limit": limit}), ensure_ascii=False)

    if normalized_action == "record_result":
        return json.dumps(
            _record_result(
                {
                    "site": site,
                    "job_url": job_url,
                    "company": company,
                    "title": title,
                    "status": status,
                    "notes": notes,
                    "batch_id": batch_id,
                }
            ),
            ensure_ascii=False,
        )

    if normalized_action == "create_batch_plan":
        return json.dumps(
            _create_batch_plan(
                {
                    "site": site,
                    "resume_path": resume_path,
                    "keywords": keywords,
                    "city": city,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                }
            ),
            ensure_ascii=False,
        )

    if normalized_action == "enqueue_jobs":
        return json.dumps(_enqueue_jobs({"batch_id": batch_id, "jobs": jobs}), ensure_ascii=False)

    if normalized_action == "next_job":
        return json.dumps(_next_job({"batch_id": batch_id}), ensure_ascii=False)

    if normalized_action == "mark_job":
        return json.dumps(
            _mark_job(
                {
                    "batch_id": batch_id,
                    "job_url": job_url,
                    "status": status,
                    "notes": notes,
                }
            ),
            ensure_ascii=False,
        )

    if normalized_action == "batch_status":
        return json.dumps(_batch_status({"batch_id": batch_id}), ensure_ascii=False)

    if normalized_action == "extract_search_results":
        return json.dumps(
            _extract_search_results(
                {
                    "batch_id": batch_id,
                    "candidates": candidates,
                    "auto_enqueue": auto_enqueue,
                }
            ),
            ensure_ascii=False,
        )

    if normalized_action == "parse_search_page":
        return json.dumps(
            _parse_search_page(
                {
                    "batch_id": batch_id,
                    "page_data": page_data,
                    "auto_enqueue": auto_enqueue,
                }
            ),
            ensure_ascii=False,
        )

    if normalized_action == "get_search_extract_script":
        normalized_site, _, error = _ensure_supported_site(site)
        if error:
            return json.dumps({"success": False, "error": error}, ensure_ascii=False)
        return json.dumps(_get_search_extract_script(normalized_site), ensure_ascii=False)

    if normalized_action == "run_batch_once":
        return json.dumps(_run_batch_once({"batch_id": batch_id, "task_id": task_id}), ensure_ascii=False)

    normalized_site, profile, error = _ensure_supported_site(site)
    if error:
        return json.dumps({"success": False, "error": error}, ensure_ascii=False)

    if normalized_action == "site_profile":
        return json.dumps(
            {
                "success": True,
                "site": normalized_site,
                "profile": _public_site_profile(profile),
            },
            ensure_ascii=False,
        )

    if normalized_action == "prepare":
        return json.dumps(
            _build_prepare_response(
                normalized_site,
                profile,
                {
                    "resume_path": resume_path,
                    "job_url": job_url,
                    "company": company,
                    "title": title,
                },
            ),
            ensure_ascii=False,
        )

    if normalized_action == "confirm_submit":
        return json.dumps(
            _build_confirm_response(
                normalized_site,
                profile,
                {
                    "company": company,
                    "title": title,
                    "confirm": confirm,
                },
            ),
            ensure_ascii=False,
        )

    return tool_error(
        "Invalid action. Use one of: site_profile, prepare, confirm_submit, record_result, list_results, create_batch_plan, enqueue_jobs, next_job, mark_job, batch_status, extract_search_results, parse_search_page, get_search_extract_script, run_batch_once."
    )


RECRUITMENT_WORKFLOW_SCHEMA = {
    "name": "recruitment_workflow",
    "description": (
        "Recruitment application helper for browser-based job sites such as 51job, Liepin, and BOSS. "
        "Use it to validate resume files before upload, inspect site-specific application rules, require an explicit final-submit confirmation, record application outcomes locally, and manage batch application queues. "
        "This tool complements browser automation; it does not click buttons by itself."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "site_profile",
                    "prepare",
                    "confirm_submit",
                    "record_result",
                    "list_results",
                    "create_batch_plan",
                    "enqueue_jobs",
                    "next_job",
                    "mark_job",
                    "batch_status",
                    "extract_search_results",
                    "parse_search_page",
                    "get_search_extract_script",
                    "run_batch_once",
                ],
                "description": "Workflow action to perform."
            },
            "site": {
                "type": "string",
                "description": "Target recruitment site. Supported: 51job, liepin, boss. Chinese aliases like 前程无忧/猎聘/BOSS直聘 also work."
            },
            "resume_path": {
                "type": "string",
                "description": "Local resume file path for preflight validation before browser_upload."
            },
            "job_url": {
                "type": "string",
                "description": "Optional target job URL for prepare/record_result/mark_job."
            },
            "company": {
                "type": "string",
                "description": "Optional company name for submit confirmation or logging."
            },
            "title": {
                "type": "string",
                "description": "Optional job title for submit confirmation or logging."
            },
            "confirm": {
                "type": "boolean",
                "description": "Must be true for action=confirm_submit to explicitly allow the final browser click.",
                "default": False
            },
            "status": {
                "type": "string",
                "description": "Result status for action=record_result or mark_job."
            },
            "notes": {
                "type": "string",
                "description": "Optional free-form notes for record_result or mark_job."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum records to return for action=list_results.",
                "default": 20
            },
            "batch_id": {
                "type": "string",
                "description": "Batch application queue ID for enqueue_jobs/next_job/mark_job/batch_status."
            },
            "keywords": {
                "oneOf": [
                    {"type": "array", "items": {"type": "string"}},
                    {"type": "string"}
                ],
                "description": "Keywords for create_batch_plan. Can be an array like ['IT经理', '信息化负责人'] or a comma-separated string."
            },
            "city": {
                "type": "string",
                "description": "Optional city filter for create_batch_plan."
            },
            "salary_min": {
                "type": "integer",
                "description": "Optional minimum monthly salary for create_batch_plan."
            },
            "salary_max": {
                "type": "integer",
                "description": "Optional maximum monthly salary for create_batch_plan."
            },
            "jobs": {
                "type": "array",
                "description": "Jobs to add into a batch queue. Each item should include job_url and can include company/title/notes.",
                "items": {
                    "type": "object",
                    "properties": {
                        "job_url": {"type": "string"},
                        "company": {"type": "string"},
                        "title": {"type": "string"},
                        "notes": {"type": "string"},
                    },
                    "required": ["job_url"],
                },
            },
            "candidates": {
                "type": "array",
                "description": "Search-result candidates extracted from a page. Each item should include job_url and may include company/title/notes. Used by action=extract_search_results.",
                "items": {
                    "type": "object",
                    "properties": {
                        "job_url": {"type": "string"},
                        "company": {"type": "string"},
                        "title": {"type": "string"},
                        "notes": {"type": "string"},
                    },
                    "required": ["job_url"],
                },
            },
            "auto_enqueue": {
                "type": "boolean",
                "description": "When true, action=extract_search_results or parse_search_page also pushes extracted candidates into the batch queue.",
                "default": False
            },
            "page_data": {
                "type": "array",
                "description": "Raw job-card data extracted from the current search-results page, typically from browser_console(expression=...). Used by action=parse_search_page.",
                "items": {
                    "type": "object"
                }
            },
            "task_id": {
                "type": "string",
                "description": "Optional browser session task_id for action=run_batch_once so search-page extraction and job-page navigation stay in one browser session."
            },
        },
        "required": ["action"],
    },
}


registry.register(
    name="recruitment_workflow",
    toolset="browser",
    schema=RECRUITMENT_WORKFLOW_SCHEMA,
    handler=lambda args, **kw: recruitment_workflow(
        action=args.get("action", ""),
        site=args.get("site"),
        resume_path=args.get("resume_path"),
        job_url=args.get("job_url"),
        company=args.get("company"),
        title=args.get("title"),
        confirm=args.get("confirm", False),
        status=args.get("status"),
        notes=args.get("notes"),
        limit=args.get("limit", 20),
        batch_id=args.get("batch_id"),
        keywords=args.get("keywords"),
        city=args.get("city"),
        salary_min=args.get("salary_min"),
        salary_max=args.get("salary_max"),
        jobs=args.get("jobs"),
        candidates=args.get("candidates"),
        auto_enqueue=args.get("auto_enqueue", False),
        page_data=args.get("page_data"),
        task_id=args.get("task_id"),
    ),
    check_fn=lambda: True,
    emoji="🧾",
)
