#!/usr/bin/env python3
"""Set one KEY=VALUE in the project's .env (created from .env.example if missing).

  set_env.py KEY VALUE
"""

import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main(argv):
    if len(argv) != 3 or not re.match(r"^[A-Z][A-Z0-9_]*$", argv[1]):
        print(__doc__)
        return 2
    key, value = argv[1], argv[2]
    env = REPO / ".env"
    if not env.exists() and (REPO / ".env.example").exists():
        shutil.copy2(str(REPO / ".env.example"), str(env))
    lines = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    pattern = re.compile(r"^\s*(export\s+)?" + re.escape(key) + r"\s*=")
    updated, found = [], False
    for line in lines:
        if pattern.match(line):
            if not found:
                updated.append("{}={}".format(key, value))
            found = True
        else:
            updated.append(line)
    if not found:
        updated.append("{}={}".format(key, value))
    env.write_text("\n".join(updated) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
