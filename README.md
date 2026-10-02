# Workflow Copilot for Claude Code

**Get the right Claude model for every prompt, suggested automatically, accepted with one click.**

Every time you type a prompt in Claude Code, Workflow Copilot looks at it and suggests the one
model that fits best: a fast model for quick questions, a stronger one for hard problems. You
decide with one click. If you do nothing, nothing changes.

**Contents:** [What you'll see](#what-youll-see) · [Before you start](#before-you-start) ·
[Install](#install-in-3-steps) · [Everyday use](#everyday-use) · [Pause, update, remove](#pause-update-or-remove-it) ·
[Troubleshooting](#troubleshooting) · [Privacy](#privacy-and-safety) · [How it works](#how-it-works)

---

## What you'll see

1. You type a prompt in Claude Code, exactly as you do today.
2. A small **Workflow Copilot** window pops up on your Mac:

   ```
   ┌─────────────────────────────────────────────────────┐
   │  Workflow Copilot                                   │
   │                                                     │
   │  Recommended model: Claude Haiku 4.5                │
   │  Reason: Short, simple request: a fast,             │
   │  lightweight model is enough.                       │
   │                                                     │
   │  Use this model for this prompt?                    │
   │                                                     │
   │       [ Keep current ]   [ Use Claude Haiku 4.5 ]   │
   └─────────────────────────────────────────────────────┘
   ```

3. You click a button:
   - **Use Claude Haiku 4.5**: this prompt is answered by the recommended model.
   - **Keep current**: your usual model answers, as always.
   - **Do nothing**: after 30 seconds it keeps your usual model.
4. Claude answers. A short line under your prompt confirms what happened, for example
   `Workflow Copilot: using Claude Haiku 4.5 for this prompt.`

Your next prompt starts fresh: every prompt gets its own suggestion.

---

## Before you start

You need **a Mac** and **Claude Code, already installed and signed in**.

Everything else is checked for you during installation. If your Mac is missing a tool
(Python or Git), macOS will offer to install it; click **Install** and wait a few minutes.

> [!TIP]
> **Never used Terminal?** Terminal is the Mac app where you type commands. Open it by pressing
> <kbd>⌘ Command</kbd> + <kbd>Space</kbd>, typing **Terminal**, and pressing <kbd>Return</kbd>.
> To run a command from this page: copy it, click in the Terminal window, paste
> (<kbd>⌘ Command</kbd> + <kbd>V</kbd>) and press <kbd>Return</kbd>.

---

## Install in 3 steps

### Step 1: Open Terminal

Press <kbd>⌘ Command</kbd> + <kbd>Space</kbd>, type **Terminal**, press <kbd>Return</kbd>.

### Step 2: Copy, paste and run this

```bash
git clone https://github.com/UX-ankit1514/Hooks.git ~/workflow-copilot
cd ~/workflow-copilot
bash scripts/install.sh --global
```

This downloads Workflow Copilot into a folder called **workflow-copilot** in your home folder
and switches it on for **every** Claude Code session. It takes about a minute. When it's done
you'll see a list of green ticks ending with **Done.**

> [!IMPORTANT]
> Keep the `workflow-copilot` folder where it is. Claude Code uses it on every prompt. If you
> ever move it, run `bash scripts/install.sh --global` again from its new location.

### Step 3: Restart Claude Code

Quit Claude Code completely (and any open Claude Code windows in Terminal), then open it again.
Type any prompt. The Workflow Copilot popup appears.

**That's it.**

<details>
<summary><b>Other ways to install</b> (one folder only, suggestions only, no Git)</summary>

<br>

**Choose how it behaves.** Run one of these instead of the last line in Step 2:

| I want… | Run |
|---|---|
| It in **every** Claude Code session *(recommended)* | `bash scripts/install.sh --global` |
| It **only in one project folder** | `bash scripts/install.sh --project ~/path/to/your/project` |
| **Suggestions only**: show the popup's advice, never switch models | add `--no-routing` to either line above |

**Without Git (download a ZIP):**

1. On this GitHub page, click the green **Code** button → **Download ZIP**.
2. Open the downloaded file. You get a folder called **Hooks-main**.
3. Rename it to **workflow-copilot** and move it into your home folder (in Finder: **Go → Home**).
4. In Terminal, run:
   ```bash
   cd ~/workflow-copilot
   bash scripts/install.sh --global
   ```
5. Restart Claude Code.

</details>

---

## Everyday use

**Just use Claude Code normally.** When a suggestion appears, click **Use** or **Keep current**.

### The messages under your prompt

| Message | What it means |
|---|---|
| `Workflow Copilot: using Claude Sonnet 5.5 for this prompt.` | You clicked **Use**. This prompt was answered by that model. |
| `Workflow Copilot: kept your current model (recommended …)` | You clicked **Keep current**. |
| `Workflow Copilot: no answer within 30s, kept your current model …` | The popup timed out. Nothing changed. |
| `Workflow Copilot recommends …, which is already your current model.` | You're already on the best model. No popup needed. |
| `Workflow Copilot recommends GPT-4o … isn't set up yet. Keeping your current model.` | The best fit is a non-Claude model. Claude Code can only switch between Claude models, so nothing changed. |
| `… (Recommendation only: model routing is off for this session.)` | Installed with `--no-routing`, or this session was opened before you installed. Restart Claude Code to switch it on. |
| `Workflow Copilot is unavailable right now … Continuing with your current model.` | Something went wrong behind the scenes. Claude still answers normally. See [Troubleshooting](#troubleshooting). |

### Good to know

- **Claude Code's status bar keeps showing your usual model name.** The message under your prompt
  tells you which model actually answered.
- **No popup** appears for slash commands (like `/help`), when the suggestion is already your
  current model, or in automated scripts (`claude -p`).
- **Every prompt is decided separately.** Accepting once doesn't change your next prompt.

---

## Pause, update or remove it

Open Terminal and copy-paste the line you need:

| I want to… | Run this |
|---|---|
| **Check that everything is working** | `bash ~/workflow-copilot/scripts/doctor.sh` |
| **Pause** it (no popups; Claude works as normal) | `bash ~/workflow-copilot/scripts/pause.sh` |
| **Resume** after pausing | `bash ~/workflow-copilot/scripts/resume.sh` |
| **See suggestions but never switch** models | `bash ~/workflow-copilot/scripts/install.sh --global --no-routing` |
| **Update** to the newest version | `cd ~/workflow-copilot && git pull && bash scripts/install.sh --global` |
| **Remove it completely** | `bash ~/workflow-copilot/scripts/uninstall.sh --global` |

Pause and resume take effect from your next prompt. For everything else, **restart Claude Code**
afterwards. After removing it you can delete the `workflow-copilot` folder.

Installed from a ZIP instead of Git? To update, download the new ZIP, replace the folder, and run
`bash scripts/install.sh --global` inside it.

---

## Troubleshooting

**First, always:** run the health check. It tells you what's wrong and the exact command to fix it.

```bash
bash ~/workflow-copilot/scripts/doctor.sh
```

<details>
<summary><b>Claude Code shows a connection error or "API error"</b></summary>

<br>

Workflow Copilot runs a small helper program on your Mac that Claude Code talks through. It
normally restarts itself, but you can start it manually:

```bash
python3 ~/workflow-copilot/hooks/workflow_copilot_hook.py --start-proxy
```

Still stuck? Switch model-switching off. Claude Code then talks to Anthropic directly again,
and you keep getting suggestions:

```bash
bash ~/workflow-copilot/scripts/install.sh --global --no-routing
```

Then restart Claude Code.
</details>

<details>
<summary><b>I don't see the popup</b></summary>

<br>

- Did you **restart Claude Code** after installing? Sessions opened before installing don't use it.
- The popup may be **behind another window**. Check Mission Control (<kbd>F3</kbd>) or the Dock.
- Is it paused? Run `bash ~/workflow-copilot/scripts/resume.sh`.
- Run the health check (above).
</details>

<details>
<summary><b>"command not found: python3" or "command not found: git"</b></summary>

<br>

Your Mac needs Apple's free developer tools. Run this, click **Install**, wait until it finishes,
then try the installation again:

```bash
xcode-select --install
```
</details>

<details>
<summary><b>The installer says "NOT enabling routing"</b></summary>

<br>

You already use another service that routes Claude Code's traffic (a company gateway or proxy).
Workflow Copilot won't interfere with it, so you get **suggestions only**. Ask whoever set up that
gateway, or see the technical guide on [chaining them](docs/HOW-IT-WORKS.md#install-scopes).
</details>

<details>
<summary><b>I moved or renamed the workflow-copilot folder</b></summary>

<br>

Go to the folder's new location in Terminal and run the installer again:

```bash
cd /path/to/new/location/workflow-copilot
bash scripts/install.sh --global
```
</details>

<details>
<summary><b>Where are the logs?</b></summary>

<br>

In `~/workflow-copilot/logs/`: `hook.log` and `proxy.log`. They record suggestions and your
choices. They **never** contain your prompt text or passwords/keys.
</details>

---

## Privacy and safety

- **It's built not to get in Claude's way.** If a suggestion fails (no internet, an error, a popup
  that can't open), Claude Code simply carries on with your usual model. The one exception: if
  the helper program on your Mac can't run at all, Claude Code can't connect. The health check
  spots this, and [one command fixes it](#troubleshooting).
- **Your Claude account stays yours.** Workflow Copilot runs only on your Mac and passes your
  Claude Code sign-in straight through. It doesn't store it, log it or send it anywhere else.
- **Your prompts stay on your Mac.** Suggestions are currently made by a built-in recommender
  on your computer. Logs record only a prompt's length, never its text. If the online Workflow
  Copilot service is switched on in a future version, your prompt text will be sent to it to get a
  suggestion; this README will say so clearly.
- **Your settings are safe.** The installer backs up your Claude Code settings before changing
  them, changes only its own entries, and the uninstaller removes exactly those.

---

## Current limitations

- **Mac only** (the popup is a macOS window).
- **Claude models only.** Workflow Copilot may *recommend* GPT or Gemini, but Claude Code can only
  switch between Claude models, so those are shown as advice only.
- Requires Claude Code signed in **directly with Anthropic** (Claude subscription or Anthropic API
  key). Not for Amazon Bedrock, Google Vertex or Microsoft Foundry setups.
- Suggestions currently come from a simple built-in recommender. The full Workflow Copilot
  service is coming. Until then you may see a suggestion on most prompts.

---

## How it works

In short: Workflow Copilot adds two small **hooks** (automatic steps) to Claude Code, plus a
small helper program that runs on your Mac.

- When Claude Code **starts**, a hook makes sure the helper is running.
- When you **send a prompt**, a hook asks the helper for the best model and shows you the popup.
- If you click **Use**, the helper sends that one prompt to the recommended model. Everything else
  goes to Anthropic unchanged.

Developers: architecture, settings, the router API and tests are in
**[docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md)**.

---

<sub>Workflow Copilot · <a href="https://workflow-copilot-ten.vercel.app/analyzer">workflow-copilot-ten.vercel.app</a></sub>
