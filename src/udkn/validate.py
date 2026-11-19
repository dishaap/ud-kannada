"""
Run the official UD validator (install: scripts/get_validator.sh -> vendor/ud-tools)
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

def validate(conllu_file: str, level: int = 2, lang: str = "kn", max_err: int = 20) -> int:
    """Locate UD validation file and run it on relevant CoNLL-U file."""
    tools = Path(os.environ.get("UD_TOOLS", Path(__file__).resolve().parents[2] / "vendor" / "ud-tools"))
    script = tools / "validate.py"
    if not script.exists():
        print("UD validator not found. Run: bash scripts/get_validator.sh", file=sys.stderr)
        return 2
    cmd = [sys.executable, str(script), "--lang", lang, f"--level={level}", f"--max-err={max_err}", conllu_file]
    return subprocess.call(cmd, cwd=tools)