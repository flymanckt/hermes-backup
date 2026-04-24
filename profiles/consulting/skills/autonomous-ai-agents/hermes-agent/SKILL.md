---
name: hermes-agent
description: Complete guide to using and extending Hermes Agent — CLI usage, setup, configuration, spawning additional agents, gateway platforms, skills, voice, tools, profiles, and a concise contributor reference. Load this skill when helping users configure Hermes, troubleshoot issues, spawn agent instances, or make code contributions.
version: 2.0.0
author: Hermes Agent + Teknium
license: MIT
metadata:
  hermes:
    tags: [hermes, setup, configuration, multi-agent, spawning, cli, gateway, development]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [claude-code, codex, opencode]
---

# Hermes Agent

Hermes Agent is an open-source AI agent framework by Nous Research that runs in your terminal, messaging platforms, and IDEs. It belongs to the same category as Claude Code (Anthropic), Codex (OpenAI), and OpenClaw — autonomous coding and task-execution agents that use tool calling to interact with your system. Hermes works with any LLM provider (OpenRouter, Anthropic, OpenAI, DeepSeek, local models, and 15+ others) and runs on Linux, macOS, and WSL.

What makes Hermes different:

- **Self-improving through skills** — Hermes learns from experience by saving reusable procedures as skills. When it solves a complex problem, discovers a workflow, or gets corrected, it can persist that knowledge as a skill document that loads into future sessions. Skills accumulate over time, making the agent better at your specific tasks and environment.
- **Persistent memory across sessions** — remembers who you are, your preferences, environment details, and lessons learned. Pluggable memory backends (built-in, Honcho, Mem0, and more) let you choose how memory works.
- **Multi-platform gateway** — the same agent runs on Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email, and 8+ other platforms with full tool access, not just chat.
- **Provider-agnostic** — swap models and providers mid-workflow without changing anything else. Credential pools rotate across multiple API keys automatically.
- **Profiles** — run multiple independent Hermes instances with isolated configs, sessions, skills, and memory.
- **Extensible** — plugins, MCP servers, custom tools, webhook triggers, cron scheduling, and the full Python ecosystem.

People use Hermes for software development, research, system administration, data analysis, content creation, home automation, and anything else that benefits from an AI agent with persistent context and full system access.

**This skill helps you work with Hermes Agent effectively** — setting it up, configuring features, spawning additional agent instances, troubleshooting issues, finding the right commands and settings, and understanding how the system works when you need to extend or contribute to it.

**Docs:** https://hermes-agent.nousresearch.com/docs/

## Quick Start

```bash
# Install
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Interactive chat (default)
hermes

# Single query
hermes chat -q "What is the capital of France?"

# Setup wizard
hermes setup

# Change model/provider
hermes model

# Check health
hermes doctor
```

---

## CLI Reference

### Global Flags

```
hermes [flags] [command]

  --version, -V             Show version
  --resume, -r SESSION      Resume session by ID or title
  --continue, -c [NAME]     Resume by name, or most recent session
  --worktree, -w            Isolated git worktree mode (parallel agents)
  --skills, -s SKILL        Preload skills (comma-separate or repeat)
  --profile, -p NAME        Use a named profile
  --yolo                    Skip dangerous command approval
  --pass-session-id         Include session ID in system prompt
```

No subcommand defaults to `chat`.

### Chat

```
hermes chat [flags]
  -q, --query TEXT          Single query, non-interactive
  -m, --model MODEL         Model (e.g. anthropic/claude-sonnet-4)
  -t, --toolsets LIST       Comma-separated toolsets
  --provider PROVIDER       Force provider (openrouter, anthropic, nous, etc.)
  -v, --verbose             Verbose output
  -Q, --quiet               Suppress banner, spinner, tool previews
  --checkpoints             Enable filesystem checkpoints (/rollback)
  --source TAG              Session source tag (default: cli)
```

### Configuration

```
hermes setup [section]      Interactive wizard (model|terminal|gateway|tools|agent)
hermes model                Interactive model/provider picker
hermes config               View current config
hermes config edit          Open config.yaml in $EDITOR
hermes config set KEY VAL   Set a config value
hermes config path          Print config.yaml path
hermes config env-path      Print .env path
hermes config check         Check for missing/outdated config
hermes config migrate       Update config with new options
hermes login [--provider P] OAuth login (nous, openai-codex)
hermes logout               Clear stored auth
hermes doctor [--fix]       Check dependencies and config
hermes status [--all]       Show component status
```

### Tools & Skills

```
hermes tools                Interactive tool enable/disable (curses UI)
hermes tools list           Show all tools and status
hermes tools enable NAME    Enable a toolset
hermes tools disable NAME   Disable a toolset

hermes skills list          List installed skills
hermes skills search QUERY  Search the skills hub
hermes skills install ID    Install a skill
hermes skills inspect ID    Preview without installing
hermes skills config        Enable/disable skills per platform
hermes skills check         Check for updates
hermes skills update        Update outdated skills
hermes skills uninstall N   Remove a hub skill
hermes skills publish PATH  Publish to registry
hermes skills browse        Browse all available skills
hermes skills tap add REPO  Add a GitHub repo as skill source
```

### MCP Servers

```
hermes mcp serve            Run Hermes as an MCP server
hermes mcp add NAME         Add an MCP server (--url or --command)
hermes mcp remove NAME      Remove an MCP server
hermes mcp list             List configured servers
hermes mcp test NAME        Test connection
hermes mcp configure NAME   Toggle tool selection
```

### Gateway (Messaging Platforms)

```
hermes gateway run          Start gateway foreground
hermes gateway install      Install as background service
hermes gateway start/stop   Control the service
hermes gateway restart      Restart the service
hermes gateway status       Check status
hermes gateway setup        Configure platforms
```

Supported platforms: Telegram, Discord, Slack, WhatsApp, Signal, Email, SMS, Matrix, Mattermost, Home Assistant, DingTalk, Feishu, WeCom, API Server, Webhooks, Open WebUI.

Platform docs: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/

### Sessions

```
hermes sessions list        List recent sessions
hermes sessions browse      Interactive picker
hermes sessions export OUT  Export to JSONL
hermes sessions rename ID T Rename a session
hermes sessions delete ID   Delete a session
hermes sessions prune       Clean up old sessions (--older-than N days)
hermes sessions stats       Session store statistics
```

### Cron Jobs

```
hermes cron list            List jobs (--all for disabled)
hermes cron create SCHED    Create: '30m', 'every 2h', '0 9 * * *'
hermes cron edit ID         Edit schedule, prompt, delivery
hermes cron pause/resume ID Control job state
hermes cron run ID          Trigger on next tick
hermes cron remove ID       Delete a job
hermes cron status          Scheduler status
```

### Webhooks

```
hermes webhook subscribe N  Create route at /webhooks/<name>
hermes webhook list         List subscriptions
hermes webhook remove NAME  Remove a subscription
hermes webhook test NAME    Send a test POST
```

### Profiles

```
hermes profile list         List all profiles
hermes profile create NAME  Create (--clone, --clone-all, --clone-from)
hermes profile use NAME     Set sticky default
hermes profile delete NAME  Delete a profile
hermes profile show NAME    Show details
hermes profile alias NAME   Manage wrapper scripts
hermes profile rename A B   Rename a profile
hermes profile export NAME  Export to tar.gz
hermes profile import FILE  Import from archive
```

### Credential Pools

```
hermes auth add             Interactive credential wizard
hermes auth list [PROVIDER] List pooled credentials
hermes auth remove P INDEX  Remove by provider + index
hermes auth reset PROVIDER  Clear exhaustion status
```

### Other

```
hermes insights [--days N]  Usage analytics
hermes update               Update to latest version
hermes pairing list/approve/revoke  DM authorization
hermes plugins list/install/remove  Plugin management
hermes honcho setup/status  Honcho memory integration
hermes memory setup/status/off  Memory provider config
hermes completion bash|zsh  Shell completions
hermes acp                  ACP server (IDE integration)
hermes claw migrate         Migrate from OpenClaw
hermes uninstall            Uninstall Hermes
```

---

## Slash Commands (In-Session)

Type these during an interactive chat session.

### Session Control
```
/new (/reset)        Fresh session
/clear               Clear screen + new session (CLI)
/retry               Resend last message
/undo                Remove last exchange
/title [name]        Name the session
/compress            Manually compress context
/stop                Kill background processes
/rollback [N]        Restore filesystem checkpoint
/background <prompt> Run prompt in background
/queue <prompt>      Queue for next turn
/resume [name]       Resume a named session
```

### Configuration
```
/config              Show config (CLI)
/model [name]        Show or change model
/provider            Show provider info
/personality [name]  Set personality
/reasoning [level]   Set reasoning (none|minimal|low|medium|high|xhigh|show|hide)
/verbose             Cycle: off → new → all → verbose
/voice [on|off|tts]  Voice mode
/yolo                Toggle approval bypass
/skin [name]         Change theme (CLI)
/statusbar           Toggle status bar (CLI)
```

### Tools & Skills
```
/tools               Manage tools (CLI)
/toolsets            List toolsets (CLI)
/skills              Search/install skills (CLI)
/skill <name>        Load a skill into session
/cron                Manage cron jobs (CLI)
/reload-mcp          Reload MCP servers
/plugins             List plugins (CLI)
```

### Info
```
/help                Show commands
/commands [page]     Browse all commands (gateway)
/usage               Token usage
/insights [days]     Usage analytics
/status              Session info (gateway)
/profile             Active profile info
```

### Exit
```
/quit (/exit, /q)    Exit CLI
```

---

## Key Paths & Config

```
~/.hermes/config.yaml       Main configuration
~/.hermes/.env              API keys and secrets
~/.hermes/skills/           Installed skills
~/.hermes/sessions/         Session transcripts
~/.hermes/logs/             Gateway and error logs
~/.hermes/auth.json         OAuth tokens and credential pools
~/.hermes/hermes-agent/     Source code (if git-installed)
```

Profiles use `~/.hermes/profiles/<name>/` with the same layout.

### Config Sections

Edit with `hermes config edit` or `hermes config set section.key value`.

| Section | Key options |
|---------|-------------|
| `model` | `default`, `provider`, `base_url`, `api_key`, `context_length` |
| `agent` | `max_turns` (90), `tool_use_enforcement` |
| `terminal` | `backend` (local/docker/ssh/modal), `cwd`, `timeout` (180) |
| `compression` | `enabled`, `threshold` (0.50), `target_ratio` (0.20) |
| `display` | `skin`, `tool_progress`, `show_reasoning`, `show_cost` |
| `stt` | `enabled`, `provider` (local/groq/openai) |
| `tts` | `provider` (edge/elevenlabs/openai/kokoro/fish) |
| `memory` | `memory_enabled`, `user_profile_enabled`, `provider` |
| `security` | `tirith_enabled`, `website_blocklist` |
| `delegation` | `model`, `provider`, `max_iterations` (50) |
| `smart_model_routing` | `enabled`, `cheap_model` |
| `checkpoints` | `enabled`, `max_snapshots` (50) |

Full config reference: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

### Providers

18 providers supported. Set via `hermes model` or `hermes setup`.

| Provider | Auth | Key env var |
|----------|------|-------------|
| OpenRouter | API key | `OPENROUTER_API_KEY` |
| Anthropic | API key | `ANTHROPIC_API_KEY` |
| Nous Portal | OAuth | `hermes login --provider nous` |
| OpenAI Codex | OAuth | `hermes login --provider openai-codex` |
| GitHub Copilot | Token | `COPILOT_GITHUB_TOKEN` |
| DeepSeek | API key | `DEEPSEEK_API_KEY` |
| Hugging Face | Token | `HF_TOKEN` |
| Z.AI / GLM | API key | `GLM_API_KEY` |
| MiniMax | API key | `MINIMAX_API_KEY` |
| Kimi / Moonshot | API key | `KIMI_API_KEY` |
| Alibaba / DashScope | API key | `DASHSCOPE_API_KEY` |
| Kilo Code | API key | `KILOCODE_API_KEY` |
| Custom endpoint | Config | `model.base_url` + `model.api_key` in config.yaml |

Plus: AI Gateway, OpenCode Zen, OpenCode Go, MiniMax CN, GitHub Copilot ACP.

Full provider docs: https://hermes-agent.nousresearch.com/docs/integrations/providers

### Toolsets

Enable/disable via `hermes tools` (interactive) or `hermes tools enable/disable NAME`.

| Toolset | What it provides |
|---------|-----------------|
| `web` | Web search and content extraction |
| `browser` | Browser automation (Browserbase, Camofox, or local Chromium) |
| `terminal` | Shell commands and process management |
| `file` | File read/write/search/patch |
| `code_execution` | Sandboxed Python execution |
| `vision` | Image analysis |
| `image_gen` | AI image generation |
| `tts` | Text-to-speech |
| `skills` | Skill browsing and management |
| `memory` | Persistent cross-session memory |
| `session_search` | Search past conversations |
| `delegation` | Subagent task delegation |
| `cronjob` | Scheduled task management |
| `clarify` | Ask user clarifying questions |
| `moa` | Mixture of Agents (off by default) |
| `homeassistant` | Smart home control (off by default) |

Tool changes take effect on `/reset` (new session). They do NOT apply mid-conversation to preserve prompt caching.

---

## Voice & Transcription

### STT (Voice → Text)

Voice messages from messaging platforms are auto-transcribed.

Provider priority (auto-detected):
1. **Local faster-whisper** — free, no API key: `pip install faster-whisper`
2. **Groq Whisper** — free tier: set `GROQ_API_KEY`
3. **OpenAI Whisper** — paid: set `VOICE_TOOLS_OPENAI_KEY`

Config:
```yaml
stt:
  enabled: true
  provider: local        # local, groq, openai
  local:
    model: base          # tiny, base, small, medium, large-v3
```

### TTS (Text → Voice)

| Provider | Env var | Free? |
|----------|---------|-------|
| Edge TTS | None | Yes (default) |
| ElevenLabs | `ELEVENLABS_API_KEY` | Free tier |
| OpenAI | `VOICE_TOOLS_OPENAI_KEY` | Paid |
| Kokoro (local) | None | Free |
| Fish Audio | `FISH_AUDIO_API_KEY` | Free tier |

Voice commands: `/voice on` (voice-to-voice), `/voice tts` (always voice), `/voice off`.

---

## Spawning Additional Hermes Instances

Run additional Hermes processes as fully independent subprocesses — separate sessions, tools, and environments.

### When to Use This vs delegate_task

| | `delegate_task` | Spawning `hermes` process |
|-|-----------------|--------------------------|
| Isolation | Separate conversation, shared process | Fully independent process |
| Duration | Minutes (bounded by parent loop) | Hours/days |
| Tool access | Subset of parent's tools | Full tool access |
| Interactive | No | Yes (PTY mode) |
| Use case | Quick parallel subtasks | Long autonomous missions |

### One-Shot Mode

```
terminal(command="hermes chat -q 'Research GRPO papers and write summary to ~/research/grpo.md'", timeout=300)

# Background for long tasks:
terminal(command="hermes chat -q 'Set up CI/CD for ~/myapp'", background=true)
```

### Interactive PTY Mode (via tmux)

Hermes uses prompt_toolkit, which requires a real terminal. Use tmux for interactive spawning:

```
# Start
terminal(command="tmux new-session -d -s agent1 -x 120 -y 40 'hermes'", timeout=10)

# Wait for startup, then send a message
terminal(command="sleep 8 && tmux send-keys -t agent1 'Build a FastAPI auth service' Enter", timeout=15)

# Read output
terminal(command="sleep 20 && tmux capture-pane -t agent1 -p", timeout=5)

# Send follow-up
terminal(command="tmux send-keys -t agent1 'Add rate limiting middleware' Enter", timeout=5)

# Exit
terminal(command="tmux send-keys -t agent1 '/exit' Enter && sleep 2 && tmux kill-session -t agent1", timeout=10)
```

### Multi-Agent Coordination

```
# Agent A: backend
terminal(command="tmux new-session -d -s backend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t backend 'Build REST API for user management' Enter", timeout=15)

# Agent B: frontend
terminal(command="tmux new-session -d -s frontend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t frontend 'Build React dashboard for user management' Enter", timeout=15)

# Check progress, relay context between them
terminal(command="tmux capture-pane -t backend -p | tail -30", timeout=5)
terminal(command="tmux send-keys -t frontend 'Here is the API schema from the backend agent: ...' Enter", timeout=5)
```

### Session Resume

```
# Resume most recent session
terminal(command="tmux new-session -d -s resumed 'hermes --continue'", timeout=10)

# Resume specific session
terminal(command="tmux new-session -d -s resumed 'hermes --resume 20260225_143052_a1b2c3'", timeout=10)
```

### Tips

- **Prefer `delegate_task` for quick subtasks** — less overhead than spawning a full process
- **Use `-w` (worktree mode)** when spawning agents that edit code — prevents git conflicts
- **Set timeouts** for one-shot mode — complex tasks can take 5-10 minutes
- **Use `hermes chat -q` for fire-and-forget** — no PTY needed
- **Use tmux for interactive sessions** — raw PTY mode has `\r` vs `\n` issues with prompt_toolkit
- **For scheduled tasks**, use the `cronjob` tool instead of spawning — handles delivery and retry

---

## Troubleshooting

### Voice not working
1. Check `stt.enabled: true` in config.yaml
2. Verify provider: `pip install faster-whisper` or set API key
3. Restart gateway: `/restart`

### Tool not available
1. `hermes tools` — check if toolset is enabled for your platform
2. Some tools need env vars (check `.env`)
3. `/reset` after enabling tools

### Model/provider issues
1. `hermes doctor` — check config and dependencies
2. `hermes login` — re-authenticate OAuth providers
3. Check `.env` has the right API key

### Changes not taking effect
- **Tools/skills:** `/reset` starts a new session with updated toolset
- **Config changes:** `/restart` reloads gateway config
- **Code changes:** Restart the CLI or gateway process

### Skills not showing
1. `hermes skills list` — verify installed
2. `hermes skills config` — check platform enablement
3. Load explicitly: `/skill name` or `hermes -s name`

### Gateway issues
Check logs first:
```bash
grep -i "failed to send\|error" ~/.hermes/logs/gateway.log | tail -20
```

If Feishu feels slow or sometimes does not reply, use this order:

1. Check whether multiple gateway services are running at the same time:
```bash
systemctl --user list-units --type=service --all | grep -i hermes
```
If you see `hermes-gateway.service` plus profile-specific services like `hermes-gateway-consulting.service`, `hermes-gateway-docs.service`, and `hermes-gateway-finance.service` all active, they may all be connecting to the same Feishu bot. That creates competing websocket sessions, reconnect churn, and harder-to-debug routing/replacement behavior. Prefer a single inbound Feishu gateway unless you intentionally separated bots.

2. Inspect the main gateway journal for timeout/restart patterns:
```bash
journalctl --user -u hermes-gateway.service -n 120 --no-pager
```
Look for repeated `APITimeoutError`, `Context: ... msgs, ~... tokens`, or stops/restarts while a reply is still being generated. In one real failure case, Feishu looked "stuck" because the request was running against `openai-codex/gpt-5.4` with a huge context (`175 msgs`, `~131540 tokens`), timed out repeatedly, and then the gateway was restarted before the answer finished.

3. Inspect `~/.hermes/logs/gateway.log` for end-to-end latency:
- `inbound message` timestamp
- `response ready ... time=...s`
This tells you whether Feishu delivery is slow or whether the model call is slow. Simple DM replies taking 8s–21s already indicate backend latency rather than websocket delivery failure.

4. Check for proxy/network issues separately:
- `ProxyError`
- Feishu message edit failures
- provider auth or connection errors (MiniMax/OpenAI/etc.)
These can amplify latency, but if the dominant symptom is large-context timeout, fix session size and gateway topology first.

Recommended stabilization steps:
- Keep only one Feishu inbound gateway active for the same bot
- Avoid very long DM threads for heavy tasks; start a fresh chat for large document/PPT jobs
- Use a faster default model for routine Feishu interactions, escalate only for complex work
- Do not restart gateway services while a long reply is still in progress unless you are intentionally aborting it

If you need a read-only topology audit before changing anything, map the 4 layers explicitly:

1. List running gateway units and their profile/root mapping:
```bash
systemctl --user show hermes-gateway.service hermes-gateway-consulting.service hermes-gateway-docs.service hermes-gateway-finance.service \
  -p Id -p FragmentPath -p UnitFileState -p ActiveState -p ExecStart -p Environment
```
Pay attention to `HERMES_HOME=`. A common source of confusion is that the default inbound service may use `/home/<user>/.hermes` directly, not `~/.hermes/profiles/hermes`.

2. Inspect config roots to see which model/provider each gateway really uses:
```bash
read_file ~/.hermes/config.yaml
read_file ~/.hermes/profiles/consulting/config.yaml
read_file ~/.hermes/profiles/docs/config.yaml
read_file ~/.hermes/profiles/finance/config.yaml
```
In one real case, the main Feishu DM was handled by root `~/.hermes` using `openai-codex/gpt-5.4`, while the profile gateways used `minimax-cn/MiniMax-M2.7-highspeed`.

3. Check which gateway actually owns the current Feishu DM target:
```bash
read_file ~/.hermes/channel_directory.json
read_file ~/.hermes/profiles/consulting/channel_directory.json
read_file ~/.hermes/profiles/docs/channel_directory.json
read_file ~/.hermes/profiles/finance/channel_directory.json
```
If the main root channel directory shows the DM `chat_id` but the profile directories show `feishu: []`, then only the root gateway currently holds the inbound target even though all profile gateways are connected.

4. Confirm connected-but-idle profile gateways via gateway state and startup logs:
```bash
read_file ~/.hermes/gateway_state.json
read_file ~/.hermes/profiles/consulting/gateway_state.json
read_file ~/.hermes/profiles/docs/gateway_state.json
read_file ~/.hermes/profiles/finance/gateway_state.json
```
Then inspect `.../logs/gateway.log` for each profile. A pattern like `Connected in websocket mode (feishu)` plus `Channel directory built: 0 target(s)` means the profile is online and consuming a Feishu connection, but is not currently routing that DM.

Interpretation rule:
- `connected + target(s)=1` on root gateway => this gateway is actually serving the current DM
- `connected + target(s)=0` on profile gateways => these are standby listeners, not current handlers
- multiple active listeners still increase complexity and reconnect surface even when only one owns the target

Important implementation details discovered during real Feishu incidents:

- `channel_directory.json` is not a live Feishu roster. It is built from each gateway's own `HERMES_HOME/sessions/sessions.json` history. So a profile can be fully connected to Feishu and still show `feishu: []` if that profile has never created a Feishu session locally.
- Session ownership is therefore per `HERMES_HOME`, not per visible bot connection. In one real case, only the root `~/.hermes` instance had the DM target because only that root home had prior Feishu session history.
- `build_session_key()` uses keys like `agent:main:feishu:dm:<chat_id>` even inside named profiles. Do not misread that `agent:main` prefix as meaning the root gateway owns all sessions. Actual isolation comes from separate `HERMES_HOME` directories and their independent session stores.
- `gateway run --replace` only replaces the gateway recorded in the current `HERMES_HOME/gateway.pid`. It does not kill gateways from other profiles. If `consulting`, `docs`, and `finance` each have their own `HERMES_HOME`, their `--replace` runs are isolated from the root gateway.
- If you observe a root gateway stop/start without a matching `Replacing existing gateway instance ... with --replace` log line, do not blame profile cross-replacement. Treat it as a separate systemd or external restart path and investigate the journal accordingly.

Additional findings from a later main-Feishu timeout investigation:

- Always compare **service state** vs **actual process state**. `hermes status` / `systemctl --user status hermes-gateway.service` can show `stopped` or `failed` while a manually started `hermes gateway` process is still actively serving Feishu DMs. Check both:
```bash
hermes status
systemctl --user --no-pager --full status hermes-gateway.service
ps -ef | grep -E 'hermes.*gateway' | grep -v grep
```
A mismatched state means the real inbound path may be a shell-started process rather than the systemd unit.

- For the “main” Feishu bot, do not assume `profiles/hermes` owns inbound traffic. Verify whether the active DM is actually handled by root `~/.hermes` (`default`) or by `~/.hermes/profiles/hermes`:
```bash
hermes profile list
HERMES_HOME=/home/<user>/.hermes/profiles/hermes hermes status
read_file ~/.hermes/config.yaml
read_file ~/.hermes/profiles/hermes/config.yaml
```
In one real case, the main Feishu DM was served by root `default` on `gpt-5.4`, while the named `hermes` profile was stopped and still configured for `MiniMax-M2.7-highspeed`.

- Measure real user-visible slowness from `~/.hermes/logs/gateway.log` instead of guessing. Search for paired lines:
  - `inbound message:`
  - `response ready: ... time=...s api_calls=...`
A few real samples were `33.4s`, `12.9s`, and `26.1s`; this distinguished genuine backend latency from mere user perception.

- Check proxy inheritance explicitly. A gateway may have `HTTP_PROXY` / `HTTPS_PROXY` in its environment even when basic network tests look healthy. That can break Feishu reply/edit calls intermittently and surface as “timeout” on the chat side. Verify both the shell and the live gateway PID environment:
```bash
env | grep -iE 'http_proxy|https_proxy|all_proxy|no_proxy'
tr '\0' '\n' < /proc/<gateway_pid>/environ | grep -iE 'http_proxy|https_proxy|all_proxy|no_proxy'
```
If `gateway.log` contains errors like below, treat proxy routing as a first-class suspect:
- `ProxyError('Unable to connect to proxy', RemoteDisconnected(...))`
- `Failed to edit message ... Remote end closed connection without response`

- Feishu shutdown problems can be a separate stability issue from slow inference. If you see journal lines like:
  - `State 'stop-sigterm' timed out. Killing.`
  - `Main process exited, code=killed, status=9/KILL`
  and gateway log lines like:
  - `[Feishu] Websocket thread did not exit within 10s - may be stuck`
  then the adapter is not stopping cleanly. That causes service flapping, stale state, and confusion about which gateway instance is live.

Practical interpretation for main Feishu timeout complaints:
- **slow `response ready` times** → model/tool latency problem
- **`ProxyError` / Feishu send-edit failures** → delivery-path/network problem
- **systemd failed + manual gateway still running** → topology/state-management problem
- **stop timeout + websocket thread stuck** → lifecycle/shutdown problem

Use those four buckets before proposing fixes.

---

## Where to Find Things

| Looking for... | Location |
|----------------|----------|
| Config options | `hermes config edit` or [Configuration docs](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Available tools | `hermes tools list` or [Tools reference](https://hermes-agent.nousresearch.com/docs/reference/tools-reference) |
| Slash commands | `/help` in session or [Slash commands reference](https://hermes-agent.nousresearch.com/docs/reference/slash-commands) |
| Skills catalog | `hermes skills browse` or [Skills catalog](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) |
| Provider setup | `hermes model` or [Providers guide](https://hermes-agent.nousresearch.com/docs/integrations/providers) |
| Platform setup | `hermes gateway setup` or [Messaging docs](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/) |
| MCP servers | `hermes mcp list` or [MCP guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) |
| Profiles | `hermes profile list` or [Profiles docs](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) |
| Cron jobs | `hermes cron list` or [Cron docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) |
| Memory | `hermes memory status` or [Memory docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) |
| Env variables | `hermes config env-path` or [Env vars reference](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) |
| CLI commands | `hermes --help` or [CLI reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) |
| Gateway logs | `~/.hermes/logs/gateway.log` |
| Session files | `~/.hermes/sessions/` or `hermes sessions browse` |
| Source code | `~/.hermes/hermes-agent/` |

---

## Contributor Quick Reference

For occasional contributors and PR authors. Full developer docs: https://hermes-agent.nousresearch.com/docs/developer-guide/

### Project Layout

```
hermes-agent/
├── run_agent.py          # AIAgent — core conversation loop
├── model_tools.py        # Tool discovery and dispatch
├── toolsets.py           # Toolset definitions
├── cli.py                # Interactive CLI (HermesCLI)
├── hermes_state.py       # SQLite session store
├── agent/                # Prompt builder, compression, display, adapters
├── hermes_cli/           # CLI subcommands, config, setup, commands
│   ├── commands.py       # Slash command registry (CommandDef)
│   ├── config.py         # DEFAULT_CONFIG, env var definitions
│   └── main.py           # CLI entry point and argparse
├── tools/                # One file per tool
│   └── registry.py       # Central tool registry
├── gateway/              # Messaging gateway
│   └── platforms/        # Platform adapters (telegram, discord, etc.)
├── cron/                 # Job scheduler
├── tests/                # ~3000 pytest tests
└── website/              # Docusaurus docs site
```

Config: `~/.hermes/config.yaml` (settings), `~/.hermes/.env` (API keys).

### Adding a Tool (3 files)

**1. Create `tools/your_tool.py`:**
```python
import json, os
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": "..."})

registry.register(
    name="example_tool",
    toolset="example",
    schema={"name": "example_tool", "description": "...", "parameters": {...}},
    handler=lambda args, **kw: example_tool(
        param=args.get("param", ""), task_id=kw.get("task_id")),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

**2. Add import** in `model_tools.py` → `_discover_tools()` list.

**3. Add to `toolsets.py`** → `_HERMES_CORE_TOOLS` list.

All handlers must return JSON strings. Use `get_hermes_home()` for paths, never hardcode `~/.hermes`.

### Adding a Browser Subtool Inside `tools/browser_tool.py`

Browser capabilities are a special case. You do **not** create a new `tools/*.py` file for each browser action. Instead, add the subtool in the existing multiplexed browser module.

Required touchpoints:

1. Add the schema entry to `BROWSER_TOOL_SCHEMAS` in `tools/browser_tool.py`
2. Add the Python wrapper function (follow the existing `browser_type` / `browser_click` style)
3. Register it near the bottom with `registry.register(...)`
4. Add it to all relevant toolset lists in `toolsets.py`
   - `_HERMES_CORE_TOOLS`
   - `TOOLSETS["browser"]`
   - other browser-enabled bundles such as `hermes-acp` / `hermes-api-server` when appropriate
5. Add it to `_LEGACY_TOOLSET_MAP["browser_tools"]` in `model_tools.py`
6. Add focused pytest coverage under `tests/tools/`

Example discovered in practice: adding `browser_upload` for resume/job-site file uploads required exactly those 6 updates. If you only add the wrapper function, the tool will still be invisible to the model.

Recommended test pattern for browser subtools:
- write a targeted test file first, e.g. `tests/tools/test_browser_upload.py`
- mock `_run_browser_command()` instead of driving a real browser
- verify both behavior and wiring:
  - schema exists
  - registry entry exists
  - toolsets include it
  - legacy browser map includes it
- then run a narrow suite first:
```bash
source venv/bin/activate
pytest tests/tools/test_browser_upload.py -q
pytest tests/tools/test_browser_upload.py tests/tools/test_browser_console.py -q
```

For file-upload style browser actions, validate inputs before dispatch:
- normalize refs to `@eN`
- resolve paths with `Path(...).expanduser().resolve()`
- reject missing paths / directories
- block sensitive files with `agent.safety_policy.get_sensitive_read_path_error()`
- return uploaded file paths from the agent-browser response for easy downstream verification

### Adding a High-Level Workflow Tool

For domain workflows that orchestrate existing tools (rather than wrapping a new external API), prefer a dedicated `tools/<domain>_tool.py` with an `action` parameter instead of scattering logic across prompts.

A reusable pattern discovered in practice: build a workflow helper like `recruitment_workflow` that complements browser automation with:
- domain/site profiles
- preflight validation
- explicit confirmation gates before irreversible actions
- local result logging

Recommended implementation checklist:

1. Create `tools/<domain>_tool.py`
2. Define one schema with `action` enum (example actions: `site_profile`, `prepare`, `confirm_submit`, `record_result`, `list_results`)
3. Keep the tool pure orchestration — it should not duplicate low-level browser/file primitives when existing tools already cover them
4. For file inputs, validate with `agent.safety_policy.get_sensitive_read_path_error()` and `Path(...).expanduser().resolve()` before returning a normalized path
5. For side-effectful final steps, add an explicit boolean gate like `confirm=true` so the model cannot silently skip user confirmation semantics
6. Store durable workflow logs under `get_hermes_home() / <domain>/...` (for example JSONL append-only logs)
7. Register the tool with `registry.register(...)`
8. Wire it into:
   - `model_tools.py` → `_discover_tools()`
   - `toolsets.py` → `_HERMES_CORE_TOOLS`
   - any relevant scenario toolset (for browser-adjacent workflows, also `TOOLSETS["browser"]`)
   - `model_tools.py` → `_LEGACY_TOOLSET_MAP` when an existing legacy bucket applies
9. Write focused tests first, then verify both behavior and wiring

Recommended test coverage:
- supported-domain/site profile lookup
- prepare/preflight success and failure paths
- sensitive file blocking
- explicit confirmation refusal unless `confirm=true`
- result log write + readback roundtrip
- registry/toolset/legacy-map visibility

Suggested verification commands:
```bash
source venv/bin/activate
pytest tests/tools/test_<domain>_tool.py -q
pytest tests/tools/test_<domain>_tool.py tests/tools/test_browser_upload.py -q
python - <<'PY'
from model_tools import get_tool_definitions
print('recruitment_workflow' in [t['function']['name'] for t in get_tool_definitions(enabled_toolsets=['browser'], quiet_mode=True)])
PY
```

This pattern works well when you want the model to make fewer ad-hoc decisions and follow a stable operational sequence around browser automation or other existing primitives.

For batch browser workflows (like multi-job applications), extend the same tool with queue actions instead of creating a second tool prematurely. A reusable action set is:
- `create_batch_plan` — validate shared inputs (resume, site, filters), generate a stable `batch_id`, persist a batch JSON file, and return a site-specific search URL
- `enqueue_jobs` — append discovered targets into the queue, deduplicating by canonical URL
- `next_job` — return the first pending queue item so the model processes jobs deterministically
- `mark_job` — update the queue item to `submitted/skipped/blocked/failed` and mirror that result into the append-only log
- `batch_status` — return queue summary counters plus current job list
- `extract_search_results` — accept normalized candidates from a browser search-results page, deduplicate them by URL, and optionally auto-enqueue them into the batch queue
- `parse_search_page` — accept raw job-card payloads extracted from a real browser page (for example from `browser_console(expression=...)`), normalize field aliases like `url/href`, `title/job_title/position`, `company/company_name`, keep extra metadata such as salary text when useful, drop rows without URLs, and optionally auto-enqueue the parsed jobs

Recommended storage pattern for batch orchestration:
- append-only history: `get_hermes_home() / '<domain>' / 'application_log.jsonl'`
- mutable queue state: `get_hermes_home() / '<domain>' / 'batches' / '<batch_id>.json'`

Recommended implementation details discovered in practice:
- keep site metadata JSON-serializable; if a profile dict contains helper callables (like `search_url_builder`), strip them before returning tool output
- normalize keyword filters from either arrays or comma-separated strings
- treat queue item URL as the dedupe key unless you have a stronger canonical ID
- when `mark_job` updates queue state, also write the outcome to the append-only log so batch state and historical audit stay aligned
- for search-result extraction, keep the extraction action separate from enqueueing logic conceptually: normalize/dedupe candidate rows first, then optionally call the queue append path when `auto_enqueue=true`
- name the raw search-result input something distinct like `candidates` so it is clear they are pre-queue items, not already-accepted jobs

### Adding a Slash Command

1. Add `CommandDef` to `COMMAND_REGISTRY` in `hermes_cli/commands.py`
2. Add handler in `cli.py` → `process_command()`
3. (Optional) Add gateway handler in `gateway/run.py`

All consumers (help text, autocomplete, Telegram menu, Slack mapping) derive from the central registry automatically.

### Agent Loop (High Level)

```
run_conversation():
  1. Build system prompt
  2. Loop while iterations < max:
     a. Call LLM (OpenAI-format messages + tool schemas)
     b. If tool_calls → dispatch each via handle_function_call() → append results → continue
     c. If text response → return
  3. Context compression triggers automatically near token limit
```

### Testing

```bash
source venv/bin/activate  # or .venv/bin/activate
python -m pytest tests/ -o 'addopts=' -q   # Full suite
python -m pytest tests/tools/ -q            # Specific area
```

- Tests auto-redirect `HERMES_HOME` to temp dirs — never touch real `~/.hermes/`
- Run full suite before pushing any change
- Use `-o 'addopts='` to clear any baked-in pytest flags

### Commit Conventions

```
type: concise subject line

Optional body.
```

Types: `fix:`, `feat:`, `refactor:`, `docs:`, `chore:`

### Key Rules

- **Never break prompt caching** — don't change context, tools, or system prompt mid-conversation
- **Message role alternation** — never two assistant or two user messages in a row
- Use `get_hermes_home()` from `hermes_constants` for all paths (profile-safe)
- Config values go in `config.yaml`, secrets go in `.env`
- New tools need a `check_fn` so they only appear when requirements are met
