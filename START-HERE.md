# Workflow Copilot for Claude Code: start here

Workflow Copilot suggests the best Claude model for each prompt you type in Claude Code. A small
popup asks **Use** or **Keep current**. If you click Use, that prompt is answered by the suggested
model. If anything goes wrong, or you don't answer, Claude Code simply carries on as normal.

## What you need
- A Mac (the popup uses macOS)
- Claude Code, already signed in (your own subscription or API key; nothing is shared with anyone)
- Python 3.9 or newer. If you're not sure, step 2 will tell you. (Fix: type `xcode-select --install`)

## Install (about 2 minutes)

1. **Unzip** this folder and move it somewhere permanent, such as your Documents folder.
   (Don't leave it in Downloads. Claude Code will keep pointing to this folder.)
2. Open the **Terminal** app, type `cd ` (with a space), drag the unzipped folder into the Terminal
   window, press Enter.
3. Run **one** of these:

   | I want it… | Type |
   |---|---|
   | in **every** Claude Code session | `bash scripts/install.sh --global` |
   | only in **this folder's** sessions | `bash scripts/install.sh` |
   | to only *show* suggestions, never switch models | add `--no-routing` to either line above |

4. **Quit Claude Code and open it again.** Type a prompt. The popup appears.

## Check it, pause it, remove it
- Check everything: `bash scripts/doctor.sh`
- Pause without uninstalling: open the file `.env` and set `WORKFLOW_COPILOT_DISABLED=1`
- Remove completely: `bash scripts/uninstall.sh --global` (or without `--global` if you installed per folder)

## Good to know
- **Privacy:** by default suggestions are made on your Mac and nothing leaves it. Only if you later
  point `WORKFLOW_COPILOT_API_URL` (in `.env`) at the online Workflow Copilot service is your prompt
  text (first 8,000 characters) sent there, once per prompt. Logs never contain your prompts or keys.
- Claude Code's status bar keeps showing your normal model. The line under your prompt says which
  model actually answered.
- It works with Claude's own models only. If Workflow Copilot suggests a GPT or Gemini model, you'll
  see the suggestion but nothing is switched.
- More detail: README.md
