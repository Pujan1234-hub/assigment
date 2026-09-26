#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import re
import sys

HERE = Path(__file__).resolve().parent
PATCHER = HERE / "patch_v0903_language_weather_safety.py"
spec = importlib.util.spec_from_file_location("floodsafe_v0903_patcher", PATCHER)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# re.sub treats backslashes in a replacement string specially.  Java source
# snippets intentionally contain literal \\n escapes, so use a callable replacement
# to preserve them byte-for-byte.
def safe_regex_once(text, pattern, replacement, label):
    new, count = re.subn(pattern, lambda _m: replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, got {count}")
    return new

mod.regex_once = safe_regex_once

if len(sys.argv) != 2 or sys.argv[1] not in mod.MODES:
    raise SystemExit("usage: run_v0903_patch.py " + "|".join(mod.MODES))
mod.MODES[sys.argv[1]]()
