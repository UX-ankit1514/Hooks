#!/bin/bash
# Pause Workflow Copilot: no popups or model switching until you run resume.sh.
# Claude Code keeps working normally. Takes effect from your next prompt.
REPO="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$REPO/scripts/set_env.py" WORKFLOW_COPILOT_DISABLED 1 && echo "Workflow Copilot is paused. Resume any time with: bash \"$REPO/scripts/resume.sh\""
