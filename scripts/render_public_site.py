#!/usr/bin/env python3
"""Render the static public website from strict placeholder tokens."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

TOKENS = {
    "__PUBLIC_HOSTNAME__": "public_hostname",
    "__APP_HOSTNAME__": "app_hostname",
    "__MAIL_HOSTNAME__": "mail_hostname",
    "__MAIL_DOMAIN__": "mail_domain",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--public-hostname", required=True)
    parser.add_argument("--app-hostname", required=True)
    parser.add_argument("--mail-hostname", required=True)
    parser.add_argument("--mail-domain", required=True)
    args = parser.parse_args()

    if args.destination.exists():
        shutil.rmtree(args.destination)
    shutil.copytree(args.source, args.destination, symlinks=False)

    values = vars(args)
    for path in args.destination.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token, key in TOKENS.items():
            text = text.replace(token, values[key])
        if "__" in text and any(token in text for token in TOKENS):
            raise SystemExit(f"unresolved public-site token in {path}")
        path.write_text(text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
