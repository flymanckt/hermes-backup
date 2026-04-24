---
name: finance-reporting-cron-setup
description: Setup scheduled stock reports (pre-market/intraday/post-market) for Kent's finance profile
---

# Finance Reporting Cron Setup

## Context
When setting up scheduled stock reports (盘前/盘中/盘后) for Kent's finance profile, a specific delivery configuration is required.

## Key Lesson: deliver="origin" Fails in Cron Context

**⚠️ CRITICAL BUG (experienced 2026-04-21):** `deliver: "origin"` silently fails.
Cron jobs run in isolated sessions with no active chat context — `origin` cannot be resolved.
**Result:** Report is generated (saved to cron output) but user never sees it.

### Delivery Options
| deliver value | Behavior | Works for reports? |
|---|---|---|
| `local` | Saves to `/cron/output/<job_id>/<timestamp>.md` only | No — user看不到 |
| `origin` | Attempt to push to origin chat | ❌ **Fails** — no chat context in cron |

### ✅ Solution: Always Use Concrete Platform+ID

Find the correct ID from channel_directory:
```bash
cat /home/kent/.hermes/profiles/finance/channel_directory.json
```

Kent's finance profile uses Feishu. The correct deliver target format:
```
feishu:oc_83935f7867e9b9f6f2eccaacea92a0e5
```

Update all three cron jobs immediately:
```bash
#盘前报告
cronjob action=update job_id=857f7fc3fcd2 deliver=feishu:oc_83935f7867e9b9f6f2eccaacea92a0e5
#盘中报告 14:00
cronjob action=update job_id=a9ad30c447cb deliver=feishu:oc_83935f7867e9b9f6f2eccaacea92a0e5
#盘后复盘 15:05
cronjob action=update job_id=a980df4de8fd deliver=feishu:oc_83935f7867e9b9f6f2eccaacea92a0e5
```

## Recovery: Finding Reports When Delivery Fails

Cron output directory structure:
```
/home/kent/.hermes/profiles/finance/cron/output/<job_id>/
  └── YYYY-MM-DD_HH-MM-SS.md   ← the actual report
```

Job metadata (including prompt and last run status):
```
/home/kent/.hermes/profiles/finance/cron/jobs.json
```

When user asks "报告呢" (where's my report):
1. `cronjob list` → check `last_delivery_error` field
2. If error shows `no delivery target resolved` or similar:
   - Navigate to `/home/kent/.hermes/profiles/finance/cron/output/<job_id>/`
   - Read the `.md` file to get the report content
   - Present it directly to the user in the current chat
3. Then fix the deliver target so future reports work

## Cron Jobs for Kent's Stock Reports

Three jobs (updated 2026-04-21 with correct Feishu deliver target):

| Job ID | Name | Schedule | Deliver |
|--------|------|----------|---------|
| 857f7fc3fcd2 | 盘前报告 08:30 | 0 8 * * 1-5 | feishu:oc_83935f7867e9b9f6f2eccaacea92a0e5 |
| a9ad30c447cb | 盘中报告 14:00 | 0 14 * * 1-5 | feishu:oc_83935f7867e9b9f6f2eccaacea92a0e5 |
| a980df4de8fd | 盘后复盘 15:05 | 0 15 * * 1-5 | feishu:oc_83935f7867e9b9f6f2eccaacea92a0e5 |

## Positions File
`/home/kent/.hermes/profiles/finance/workspace/positions.md`

Contains: 603341 龙旗科技, 002969 嘉美包装, 603316 诚邦股份, 560390 电网E

## Setup Workflow

1. Read/update positions.md with current holdings (code, name, shares, cost, stop-loss)
2. Find correct Feishu target from `channel_directory.json` (use `oc_` prefixed ID, NOT `ou_`)
3. Create cron jobs with:
   - `schedule`: cron expression (UTC or local — confirm timezone)
   - `deliver`: **always use `feishu:<id>`** — never `origin` for user-facing reports
   - `skills`: `["finance"]`
   - Self-contained prompt with full position details (cron has no memory of prior turns)
4. Verify with `cronjob list` after creation
5. If jobs arrive with `deliver: "origin"`, update immediately with `cronjob action='update' job_id=X deliver='feishu:oc_83935f7867e9b9f6f2eccaacea92a0e5'`
