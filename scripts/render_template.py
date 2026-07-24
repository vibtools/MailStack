#!/usr/bin/env python3
"""Strictly render {{NAME}} tokens from a JSON object or environment."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

TOKEN_RE = re.compile(r"{{([A-Z][A-Z0-9_]*)}}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--values-json", type=Path)
    parser.add_argument("--mode", default="0644")
    args = parser.parse_args()

    values: dict[str, str] = {}
    if args.values_json:
        raw = json.loads(args.values_json.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise SystemExit("values JSON must contain an object")
        values.update({str(k): str(v) for k, v in raw.items()})
    values.update(os.environ)

    text = args.template.read_text(encoding="utf-8")
    missing = sorted({name for name in TOKEN_RE.findall(text) if name not in values})
    if missing:
        raise SystemExit("missing template values: " + ", ".join(missing))

    rendered = TOKEN_RE.sub(lambda match: values[match.group(1)], text)
    unresolved = TOKEN_RE.findall(rendered)
    if unresolved:
        raise SystemExit("unresolved template tokens: " + ", ".join(sorted(set(unresolved))))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_text(rendered, encoding="utf-8", newline="\n")
    temporary.chmod(int(args.mode, 8))
    temporary.replace(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
