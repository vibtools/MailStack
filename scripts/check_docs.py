#!/usr/bin/env python3
"""Validate repository documentation, branding metadata and release version consistency."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
REPO_URL = "https://github.com/vibtools/MailStack"
OFFICIAL_LINKS = {"https://vib.tools/", "https://dev.vib.tools/", "https://ygit.net/"}


def fail(message: str) -> None:
    print(f"DOCUMENTATION_FINDING={message}")
    raise SystemExit(1)


def main() -> int:
    required = {
        "README.md", "LICENSE", "NOTICE.md", "ROADMAP.md", "SECURITY.md",
        "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SUPPORT.md", "CITATION.cff",
        "docs/INSTALLATION.md", "docs/BUILD.md", "docs/FOLDER_STRUCTURE.md",
        "docs/API_REFERENCE.md", "docs/CODING_STANDARDS.md", "docs/MAINTENANCE.md",
        "docs/FAQ.md", "docs/TROUBLESHOOTING.md", "docs/DEPENDENCY_REVIEW.md",
        "docs/GITHUB_REPOSITORY_METADATA.md", "docs/SCREENSHOTS.md", "docs/BRANDING.md",
        "docs/LICENSING.md", "docs/FORENSIC_FILE_INVENTORY.json",
        "documents/README.md", "documents/USER_MANUAL.md", "documents/HOW_TO_USE.md",
        "documents/ADMIN_GUIDE.md", "documents/BASELINE.md",
        "documents/DOCUMENTATION_POLICY.md", "documents/DOCUMENTATION_MANIFEST.json",
        "documents/phases/PHASE-000-BASELINE.md",
        "documents/phases/PHASE-001-UI-DESIGN-INTAKE-BASELINE.md",
        "documents/design/UI_FOUNDATION.md", "documents/design/SCREEN_CATALOG.md",
        "documents/design/COMPONENT_MATRIX.md",
        "documents/design/RESPONSIVE_SPECIFICATION.md",
        "documents/design/ACCESSIBILITY_SPECIFICATION.md",
        "documents/design/FUTURE_UI_ROADMAP.md",
        "documents/design/IMPLEMENTATION_STATUS.md",
        "design/README.md", "design/DESIGN_MANIFEST.json",
        "scripts/manage_documents.py", "scripts/manage_designs.py",
        "scripts/check_documentation_policy.py", "scripts/test_documents.py",
        "scripts/test_designs.py",
    }
    missing = sorted(path for path in required if not (ROOT / path).is_file())
    if missing:
        fail(f"missing required files: {missing}")

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    if len(license_text) < 30_000 or "GNU AFFERO GENERAL PUBLIC LICENSE" not in license_text:
        fail("LICENSE does not contain the complete AGPL-3.0 text")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in ("## Overview", "## Key features", "## Architecture", "## Quick start", "## Screenshots", "## Security", "## Roadmap", "## License"):
        if heading not in readme:
            fail(f"README missing section: {heading}")
    for link in OFFICIAL_LINKS | {REPO_URL}:
        if link not in readme:
            fail(f"README missing official link: {link}")

    pyproject = (ROOT / "mailbox-app/pyproject.toml").read_text(encoding="utf-8")
    pep440 = VERSION.replace("-rc.", "rc")
    if f'version = "{pep440}"' not in pyproject:
        fail("pyproject version does not match VERSION")
    install_text = (ROOT / "install.sh").read_text(encoding="utf-8")
    if 'PROJECT_VERSION="$(tr -d' not in install_text:
        fail("installer does not read canonical VERSION")

    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    checked = 0
    for document in sorted(ROOT.rglob("*.md")):
        if any(part in {".git", "dist", "artifacts"} for part in document.relative_to(ROOT).parts):
            continue
        text = document.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for target in link_pattern.findall(line):
                target = target.strip().split("#", 1)[0]
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                resolved = (document.parent / target).resolve()
                try:
                    resolved.relative_to(ROOT)
                except ValueError:
                    fail(f"unsafe link {document.relative_to(ROOT)}:{line_number}: {target}")
                if not resolved.exists():
                    fail(f"broken link {document.relative_to(ROOT)}:{line_number}: {target}")
                checked += 1

    print(f"DOCUMENTS_REQUIRED={len(required)}")
    print(f"LOCAL_LINKS_CHECKED={checked}")
    print(f"RELEASE_VERSION={VERSION}")
    print("DOCUMENTATION_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
