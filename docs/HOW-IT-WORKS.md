# How Workflow Copilot for Claude Code works

This is the technical guide. For installing and everyday use, see the [README](../README.md).

## Architecture

```
You type a prompt in Claude Code
        │
        ▼
UserPromptSubmit hook ──► local proxy (127.0.0.1:8787) ──► Workflow Copilot router (mock or cloud)
        │                        ◄── ONE model + short reason
        ▼
macOS popup:  "Recommended model: Claude Haiku 4.5 … Use this model for this prompt?"
        │  Use                                   │ Keep current / no answer / any error
        ▼                                        ▼
proxy swaps the model for this turn        nothing changes
        │                                        │
        └──────────────► Claude answers your prompt ◄─┘
```

- **SessionStart hook** makes sure the proxy is running (starts it if needed) and registers the
  session. It never routes.
- **UserPromptSubmit hook** sends the prompt to the proxy's `/recommend`, asks Use / Keep, and
  saves the answer via `/selection`. It always exits 0 and prints at most one
  `{"systemMessage": …}`, so Claude always continues.
- **Routing**: the installer sets `ANTHROPIC_BASE_URL=http://127.0.0.1:8787`. Claude Code's API
  requests pass through the proxy, which forwards them to Anthropic untouched, except during a
  turn where you accepted a recommendation. Then `POST /v1/messages` requests for that session
  use the recommended model, adjusted for what that model supports (e.g. Haiku 4.5 has no
  adaptive thinking, per-turn effort or mid-conversation system messages). Credentials are passed
  through as-is and never stored or logged.
- **Session matching**: requests are matched to sessions via the `x-claude-code-session-id`
  header (fallback: `metadata.user_id`). Claude Code's small background helpers (titles,
  summaries; they run on Haiku) are never rerouted.
- **Fail-open**: if the router, internet, popup or anything else fails, the current model is kept
  and the reason is logged. If Anthropic rejects a routed request (400/404/422), the proxy retries
  it once with the original model.
- **Providers**: recommendation and execution are separate (`proxy/provider.py`). Only the
  Anthropic adapter executes today. OpenAI/Codex, Gemini, OpenRouter… are registered as
  "not configured" placeholders, so they are shown but never faked. Retired Claude names
  (e.g. "Claude 3 Opus") map to the current model of the same family, and the note says so.

## Proxy endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | liveness + configuration summary |
| `POST /session/start` | register a session (SessionStart) |
| `GET /session/{id}` | inspect a session's state (debugging) |
| `POST /recommend` | one recommendation for a prompt (UserPromptSubmit) |
| `POST /selection` | record accept / reject |
| `POST /mock/api/route` | local mock of the planned cloud contract |
| everything else | transparent passthrough to `WORKFLOW_COPILOT_UPSTREAM_URL` |

## Install scopes

| Command | Hooks go to | Routing (`ANTHROPIC_BASE_URL`) goes to |
|---|---|---|
| `install.sh --global` | `~/.claude/settings.json` (or `$CLAUDE_CONFIG_DIR`) | same file |
| `install.sh` | `<this folder>/.claude/settings.json` | `<this folder>/.claude/settings.local.json` |
| `install.sh --project DIR` | `DIR/.claude/settings.json` | `DIR/.claude/settings.local.json` |

`scripts/settings_tool.py` does the merging:
- only entries whose command contains `workflow_copilot_hook.py` are added/removed;
- every changed file is backed up first (`*.bak-<timestamp>`); invalid JSON is never overwritten;
- the hook command ends in `|| true` (a missing script makes Python exit 2, which would *block*
  prompts);
- if `ANTHROPIC_BASE_URL` is already set to something else (settings, or `~/.zshrc` and friends
  for `--global`), routing is not enabled. Chain instead with `WORKFLOW_COPILOT_UPSTREAM_URL`;
- uninstall removes `ANTHROPIC_BASE_URL` only if it still points at this proxy.

Other safeguards in the hook: a run-once guard (global + project installs still ask once per
prompt), scripted runs (`CLAUDE_CODE_ENTRYPOINT=sdk-*`, e.g. `claude -p`) are skipped unless
`WORKFLOW_COPILOT_CONFIRM_UI=auto-accept`, and while paused it still keeps the proxy alive when
routing is on.

## Settings (`.env`)

The installer creates `.env` from `.env.example`. Never commit `.env`.

| Setting | Default | Meaning |
|---|---|---|
| `WORKFLOW_COPILOT_API_URL` | *(empty = mock)* | Where recommendations come from |
| `WORKFLOW_COPILOT_API_STYLE` | auto | `route` (planned contract) or `analyze` (today's site); auto-detected from the URL |
| `WORKFLOW_COPILOT_API_KEY` | | Optional bearer token for the cloud router |
| `WORKFLOW_COPILOT_API_TIMEOUT` | `25` | Seconds to wait for the router |
| `WORKFLOW_COPILOT_CONFIRM_UI` | `auto` | `auto` (terminal, then popup), `dialog`, `tty`, `auto-accept`, `never` |
| `WORKFLOW_COPILOT_CONFIRM_TIMEOUT` | `30` | Seconds before "no answer" keeps the current model |
| `WORKFLOW_COPILOT_UPSTREAM_URL` | `https://api.anthropic.com` | Where Claude Code's requests are forwarded |
| `WORKFLOW_COPILOT_MAX_PROMPT_CHARS` | `8000` | Only this much of a prompt is sent for routing |
| `WORKFLOW_COPILOT_LOG_PROMPTS` | `0` | `1` adds an 80-character prompt preview to logs |
| `WORKFLOW_COPILOT_DISABLED` | `0` | `1` pauses it (`scripts/pause.sh` / `resume.sh`) |
| `WORKFLOW_COPILOT_PORT` | `8787` | Local proxy port |

The hook reads `.env` on every run; the proxy reads it at start. After changing router settings,
restart the proxy: `python3 hooks/workflow_copilot_hook.py --stop-proxy` (it restarts by itself).

## Connecting the real Workflow Copilot router

Status of the live site (checked 2026-10-02):

| Endpoint | Status |
|---|---|
| `POST /api/route` | does not exist yet (404); needs to be added to the website |
| `POST /api/analyze` | exists; returns a long free-text analysis from an LLM |

**Stopgap:** `WORKFLOW_COPILOT_API_URL=https://workflow-copilot-ten.vercel.app/api/analyze`. The
proxy reads the "SECTION 1: RECOMMENDED MODEL" line and drops the tier (low/max…). It works
(≈4 s per prompt) but knows an old model list (most picks are Gemini/GPT, which are shown, never
applied), costs one LLM call per prompt, and the endpoint has no auth.

**Planned contract:**

```http
POST /api/route
Content-Type: application/json
Authorization: Bearer <WORKFLOW_COPILOT_API_KEY>

{ "prompt": "…", "client": "claude-code" }
```
```json
{ "recommended_model": "claude-sonnet-5-5", "reason": "Coding task; strong and fast.", "confidence": 0.82 }
```

- For `client: "claude-code"`, choose among models Claude Code can run and return API ids
  (`claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-4-5`, `claude-fable-5-1`); display
  names like "Claude Sonnet 5.5" also work.
- One-sentence `reason`; no tiers or modes. Respond in under ~3 s; require an API key.

Rehearse locally with `WORKFLOW_COPILOT_API_URL=http://127.0.0.1:8787/mock/api/route`.

## Known limits

- **No terminal `[Y/n]` inside Claude Code**: hooks run without a controlling terminal, so the
  macOS popup is used. The terminal prompt works where a terminal exists, and is tried first.
- Claude Code's status bar keeps showing the configured model; the note under the prompt and
  `logs/proxy.log` show what answered.
- If your own main model is Haiku, recommendations can't be applied (Haiku requests are treated
  as background helpers).
- Routing needs Claude Code talking to Anthropic directly (subscription or API key), not
  Bedrock / Vertex / Foundry.
- The popup needs macOS; elsewhere the current model is kept.

## Logs

`logs/hook.log` and `logs/proxy.log` record sessions, recommendations, accept/reject, routing and
fallbacks. Prompts appear only as length + fingerprint; keys and auth headers are never logged.

## Project layout

```
hooks/workflow_copilot_hook.py   SessionStart + UserPromptSubmit hook (standard library only)
proxy/app.py                     FastAPI proxy: endpoints above + passthrough
proxy/router_client.py           mock, /api/route and /api/analyze clients
proxy/provider.py                model catalog + provider adapters
proxy/session_store.py           per-session state (state/sessions.json)
proxy/config.py                  settings from env/.env
scripts/install.sh  uninstall.sh  doctor.sh  pause.sh  resume.sh  package.sh
scripts/settings_tool.py         safe settings merge (project or --global)
scripts/set_env.py               edit one .env value
tests/                           pytest suite
```

## Development

```bash
.venv/bin/python -m pytest        # 84 tests, ~25 s, no network or popups needed
bash scripts/doctor.sh --tests    # health check + tests
bash scripts/package.sh           # shareable zip in dist/ (refuses to include anything private)
```

Mock router trick: a prompt containing `wc-test: GPT-4o` (or any model name) makes the mock
recommend that model, which is handy for trying unsupported-model behaviour.
