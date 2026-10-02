#!/bin/bash
# Resume Workflow Copilot after pause.sh. Takes effect from your next prompt.
REPO="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$REPO/scripts/set_env.py" WORKFLOW_COPILOT_DISABLED 0 && echo "Workflow Copilot is back on."
