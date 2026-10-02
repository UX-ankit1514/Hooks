# Workflow Copilot – Claude Code Router

Workflow Copilot picks **one best model** for every prompt you type in Claude Code, asks you
**Use / Keep current**, and, if you accept, answers that prompt with the recommended model.
No copying prompts into a website, no modes.

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

## Quick start

```bash
cd <this folder>
bash scripts/install.sh          # sets everything up for this folder, safe to run again
claude                           # open a NEW Claude Code session in this folder
```

Want it in **every** Claude Code session instead? Use `bash scripts/install.sh --global`
(see "Use it in every session" below).

Type any prompt. A **Workflow Copilot** popup suggests a model:

- **Use …**: this prompt is answered by that model.
- **Keep current**, or no click within 30 s: your current model is used.

After each prompt Claude Code shows a one-line note, e.g.
`Workflow Copilot: using Claude Haiku 4.5 for this prompt. Short, simple request…`

Use it in one other project folder: `bash scripts/install.sh --project ~/path/to/project`

## Use it in every session (global)

```bash
bash scripts/install.sh --global      # add --no-routing for "suggest only, never switch"
```

This writes the two hooks (and the routing setting) into your **user-level** Claude Code settings,
`~/.claude/settings.json` (or `$CLAUDE_CONFIG_DIR/settings.json`), so every new session in any
folder, including the desktop app and IDE extensions, gets them. Open sessions are unchanged
until restarted.

What it does and doesn't do:
- Merges into your existing settings; nothing else in the file is touched, and a timestamped
  backup (`settings.json.bak-…`) is made first. A settings file it can't parse is left alone.
- Hooks point at *this* folder, so **keep it where it is**. If you move it, run the installer again.
- The hook command ends in `|| true`, so even a deleted/broken hook file can never block a prompt.
- If something already sets `ANTHROPIC_BASE_URL` (another gateway in your settings or in
  `~/.zshrc` etc.), routing is **not** switched on, so your gateway keeps working; you get
  suggestions only. To chain them, put that URL in `.env` as `WORKFLOW_COPILOT_UPSTREAM_URL`
  and re-run the installer.
- Installed both globally and per project? It still asks only once per prompt (a run-once guard).
- Scripted runs (`claude -p`, SDK) are skipped: no popup, no routing. Set
  `WORKFLOW_COPILOT_CONFIRM_UI=auto-accept` to opt a script in.
- Only works for Claude Code talking to Anthropic directly (subscription or API key). If you use
  Bedrock/Vertex/Foundry, `ANTHROPIC_BASE_URL` isn't used, so routing can't apply.
- With the built-in mock router you will get a popup on most prompts. Once the real router
  exists (below) this gets much quieter, since no popup shows when the suggestion equals your
  current model.

Undo: `bash scripts/uninstall.sh --global`.

## Share it with someone else

```bash
bash scripts/package.sh      # creates dist/workflow-copilot-claude-code-<version>.zip
```

The zip is built from an allow-list (code, scripts, tests, docs, `.env.example`) and the script
refuses to build if it finds a `.env`, logs, state, a `.venv`, a personal path or a key. Send the
zip by AirDrop, email, Slack or a shared drive. The recipient follows **START-HERE.md** (inside
the zip): unzip somewhere permanent, run `bash scripts/install.sh --global`, restart Claude Code.

Using GitHub instead? From this folder: `git init`, `git add .`, `git commit -m "Workflow Copilot for Claude Code"`,
create an empty repository on github.com, then run the two `git remote add origin …` /
`git push -u origin main` lines GitHub shows you. `.gitignore` already keeps `.env`, `.venv`,
logs, state, generated settings and `dist/` out. Recipients then `git clone` it instead of
unzipping. Prefer a **private** repository until `/api/route` is live.

What recipients need: a Mac, Claude Code signed in with their own account (their credentials pass
straight through the proxy; nothing of yours is in the zip), and Python 3.9+. Each person gets
their own local proxy, logs and settings. Nothing is shared between machines.

## Turning it off

| What you want | Command |
|---|---|
| Check that everything is OK | `bash scripts/doctor.sh` |
| Show recommendations, never switch models | `bash scripts/install.sh --no-routing` |
| Pause it without uninstalling | set `WORKFLOW_COPILOT_DISABLED=1` in `.env` |
| Remove it completely | `bash scripts/uninstall.sh` (add `--global` if you installed it globally, `--purge` to delete `.venv`, `logs`, `state`) |

Restart Claude Code after any of these.

## Settings (`.env`)

`install.sh` creates `.env` from `.env.example`. Never commit `.env`.

| Setting | Default | Meaning |
|---|---|---|
| `WORKFLOW_COPILOT_API_URL` | *(empty = mock)* | Where recommendations come from (see below) |
| `WORKFLOW_COPILOT_API_STYLE` | auto | `route` (planned contract) or `analyze` (today's site); auto-detected from the URL |
| `WORKFLOW_COPILOT_API_KEY` | | Optional bearer token for the cloud router |
| `WORKFLOW_COPILOT_API_TIMEOUT` | `25` | Seconds to wait for the router |
| `WORKFLOW_COPILOT_CONFIRM_UI` | `auto` | `auto` (terminal, then popup), `dialog`, `tty`, `auto-accept`, `never` |
| `WORKFLOW_COPILOT_CONFIRM_TIMEOUT` | `30` | Seconds before "no answer" keeps your current model |
| `WORKFLOW_COPILOT_UPSTREAM_URL` | `https://api.anthropic.com` | Where Claude Code's requests are forwarded |
| `WORKFLOW_COPILOT_MAX_PROMPT_CHARS` | `8000` | Only this much of a prompt is sent for routing |
| `WORKFLOW_COPILOT_LOG_PROMPTS` | `0` | `1` adds an 80-character prompt preview to logs |
| `WORKFLOW_COPILOT_PORT` | `8787` | Local proxy port |

The proxy reads `.env` when it starts. After editing it, restart the proxy with
`python3 hooks/workflow_copilot_hook.py --stop-proxy` (it starts again automatically).

## Connecting the real Workflow Copilot

What the live site exposes today (checked 2026-10-02):

| Endpoint | Status |
|---|---|
| `POST /api/route` | **does not exist (404)**. This needs to be added to the website. |
| `POST /api/analyze` | exists; returns a long free-text analysis from an LLM |

**Today:** set
`WORKFLOW_COPILOT_API_URL=https://workflow-copilot-ten.vercel.app/api/analyze` to use the
existing analyzer. The proxy reads its "SECTION 1: RECOMMENDED MODEL" line and drops the tier
(low/max…). This works (≈4 s per prompt) but has limits:

- it only knows an old model list (GPT-4o, Gemini 1.5/2.5, *Claude 3/4*), so most of its picks
  are Gemini/GPT, which Claude Code can't run (shown, never applied);
- retired Claude names (e.g. "Claude 3 Opus") are mapped to the current model of the same
  family, and the note says so;
- every prompt costs one LLM call on the site's Curvet account, and the endpoint has no auth.

**Next step (website change):** add `POST /api/route` with this contract:

```http
POST /api/route
Content-Type: application/json
Authorization: Bearer <WORKFLOW_COPILOT_API_KEY>   (recommended)

{ "prompt": "…", "client": "claude-code" }
```
```json
{ "recommended_model": "claude-sonnet-5-5", "reason": "Coding task; strong and fast.", "confidence": 0.82 }
```

Recommendations for that endpoint:
- When `client` is `claude-code`, choose only among models Claude Code can run (current Claude
  models), and return API ids (`claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-4-5`,
  `claude-fable-5-1`). Display names like "Claude Sonnet 5.5" also work.
- Keep `reason` to one sentence; no tiers or modes.
- Respond in under ~3 s (it runs before every prompt) and require an API key.

Then set `WORKFLOW_COPILOT_API_URL=https://workflow-copilot-ten.vercel.app/api/route`.
To rehearse the contract locally: `WORKFLOW_COPILOT_API_URL=http://127.0.0.1:8787/mock/api/route`.

## How it works

- **SessionStart hook** makes sure the proxy is running (starts it if needed) and registers
  the session. It never routes.
- **UserPromptSubmit hook** sends the prompt to the proxy's `/recommend`, asks Use/Keep, and
  saves the answer via `/selection`. It always exits successfully, so Claude always continues.
- **Routing**: `install.sh` sets `ANTHROPIC_BASE_URL=http://127.0.0.1:8787` for this project
  only (`.claude/settings.local.json`, git-ignored). Claude Code's API requests then pass
  through the proxy, which forwards them to Anthropic untouched, except during a turn where you
  accepted a recommendation. Then the main requests use the recommended model, adjusted
  for what that model supports (e.g. Haiku has no adaptive thinking). Your login is passed
  through as-is; the proxy never stores or logs credentials.
- **Fail-open**: if the router, internet, popup or anything else fails, your current model is
  kept and the reason is logged. If Anthropic rejects a routed request, the proxy retries it
  once with your original model.
- **Providers**: recommendation and execution are separate (`proxy/provider.py`). Only the
  Anthropic adapter executes today; OpenAI/Codex, Gemini, OpenRouter… are registered as
  "not configured" placeholders, so they are shown but never faked.

### Known limits (V1)

- **No terminal `[Y/n]`.** Claude Code runs hooks without a terminal (`/dev/tty` is not
  available), so the macOS popup is used instead. The terminal prompt still works where a
  terminal exists, and is tried first.
- Claude Code's status bar keeps showing your configured model; the note under your prompt
  (and `logs/proxy.log`) shows what actually answered.
- Claude Code's small background helpers (titles, summaries; they run on Haiku) are never
  rerouted. If your own main model is Haiku, recommendations can't be applied.
- With routing on, Claude Code reaches the API *through* the proxy. The hooks restart it
  automatically at session start and before every prompt; if it can't start, `doctor.sh` tells
  you, or turn routing off with `install.sh --no-routing`.

## Logs

`logs/hook.log` (hook) and `logs/proxy.log` (proxy). They record sessions, recommendations,
accept/reject, routing and fallbacks. Prompts are logged only as length + fingerprint; API
keys and auth headers are never logged.

## Project layout

```
.claude/settings.json            project hooks (created/merged by install.sh; git-ignored)
.claude/settings.local.json      ANTHROPIC_BASE_URL for routing (personal, git-ignored)
~/.claude/settings.json          the same, for every session, when installed with --global
hooks/workflow_copilot_hook.py   SessionStart + UserPromptSubmit hook (standard library only)
proxy/app.py                     FastAPI proxy: /health /session/start /recommend /selection + passthrough
proxy/router_client.py           mock, /api/route and /api/analyze clients
proxy/provider.py                model catalog + provider adapters
proxy/session_store.py           per-session state (state/sessions.json)
proxy/config.py                  settings from env/.env
scripts/install.sh | uninstall.sh | doctor.sh | settings_tool.py | package.sh
START-HERE.md                    plain-English install guide for people you share it with
tests/                           pytest suite (`.venv/bin/python -m pytest`)
```

## Testing

```bash
.venv/bin/python -m pytest        # 82 tests, ~25 s, no network or popups needed
bash scripts/doctor.sh --tests    # health check + tests
```

Mock router test hook: a prompt containing `wc-test: GPT-4o` (or any model name) makes the
mock recommend that model, which is handy for trying unsupported-model behaviour.
