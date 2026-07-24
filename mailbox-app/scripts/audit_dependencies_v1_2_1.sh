#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
PYTHON=${PYTHON:-python3}
"$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else "Python 3.12 is required")'

# GHSA-g75f-g53v-794x affects only Bleach email linkification with parse_email=True.
# This release requires an explicit parse_email=False keyword on the only Linker call.
"$PYTHON" - "$ROOT/apps/ingestion/parser.py" <<'PY'
import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
linker_calls = []
for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr == "Linker":
        linker_calls.append(node)
if len(linker_calls) != 1:
    raise SystemExit(f"Expected exactly one Bleach Linker call, found {len(linker_calls)}")
keywords = {item.arg: item.value for item in linker_calls[0].keywords if item.arg}
value = keywords.get("parse_email")
if not isinstance(value, ast.Constant) or value.value is not False:
    raise SystemExit("Bleach Linker must explicitly set parse_email=False")
print("Bleach email-linkification advisory scope check: PASS")
PY

grep -q '^bleach==6\.4\.0$' "$ROOT/requirements/locked.txt" || {
  printf 'Required Bleach 6.4.0 security pin is missing.\n' >&2
  exit 1
}
grep -q '^python-dotenv==1\.2\.2$' "$ROOT/requirements/locked.txt" || {
  printf 'Required python-dotenv 1.2.2 security pin is missing.\n' >&2
  exit 1
}

TMP=$(mktemp -d /tmp/vibmail-dependency-audit.XXXXXX)
cleanup() { rm -rf -- "$TMP"; }
trap cleanup EXIT INT TERM
"$PYTHON" -m venv "$TMP/venv"
"$TMP/venv/bin/pip" install --disable-pip-version-check --no-input 'pip-audit==2.10.0'
"$TMP/venv/bin/pip-audit" \
  --requirement "$ROOT/requirements/locked.txt" \
  --disable-pip \
  --no-deps \
  --ignore-vuln GHSA-g75f-g53v-794x
printf 'Online dependency vulnerability audit: PASS\n'
