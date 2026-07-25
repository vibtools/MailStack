#!/usr/bin/env python3
"""Create, synchronize, and validate MailStack user documentation."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

README_PATH = "documents/README.md"
MANIFEST_PATH = "documents/DOCUMENTATION_MANIFEST.json"
INDEX_START = "<!-- AUTO-DOCUMENT-INDEX:START -->"
INDEX_END = "<!-- AUTO-DOCUMENT-INDEX:END -->"
REQUIRED_DOCUMENTS = {
    "documents/ADMIN_GUIDE.md",
    "documents/BASELINE.md",
    "documents/DOCUMENTATION_POLICY.md",
    "documents/HOW_TO_USE.md",
    "documents/USER_MANUAL.md",
    "documents/phases/PHASE-000-BASELINE.md",
    "documents/phases/PHASE-001-UI-DESIGN-INTAKE-BASELINE.md",
    "documents/phases/PHASE-002-SHARED-UI-FOUNDATION-AND-APPLICATION-SHELL.md",
    "documents/design/UI_FOUNDATION.md",
    "documents/design/SCREEN_CATALOG.md",
    "documents/design/COMPONENT_MATRIX.md",
    "documents/design/RESPONSIVE_SPECIFICATION.md",
    "documents/design/ACCESSIBILITY_SPECIFICATION.md",
    "documents/design/FUTURE_UI_ROADMAP.md",
    "documents/design/IMPLEMENTATION_STATUS.md",
}
REQUIRED_METADATA = {
    "document_id",
    "title",
    "document_type",
    "audience",
    "status",
    "version",
    "last_reviewed",
}
ALLOWED_STATUSES = {"active", "historical", "draft"}
ALLOWED_TYPES = {
    "admin-guide",
    "baseline",
    "documentation-policy",
    "design-reference",
    "how-to",
    "phase",
    "user-manual",
}
REQUIRED_SECTIONS = {
    "admin-guide": {
        "Administrator role",
        "User management",
        "Mailbox administration",
        "Operational health",
        "Security boundaries",
    },
    "baseline": {
        "Baseline identity",
        "Qualification status",
        "Preserved architecture",
        "Change control",
    },
    "documentation-policy": {
        "Documentation baseline",
        "Mandatory feature workflow",
        "Automated synchronization",
        "CI enforcement",
    },
    "design-reference": {
        "Purpose",
        "Scope",
        "Approved baseline",
        "Change control",
    },
    "how-to": {
        "Sign in",
        "Create a mailbox",
        "Read and filter messages",
        "Download an attachment",
        "Enable browser notifications",
    },
    "phase": {
        "Objective",
        "Scope",
        "User-facing changes",
        "How to use",
        "Compatibility",
        "Verification",
        "Documentation impact",
    },
    "user-manual": {
        "Overview",
        "Sign in",
        "Dashboard",
        "Mailboxes",
        "Messages",
        "Notifications",
        "Limits and safety",
    },
}
UNRESOLVED_PATTERN = re.compile(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b", re.IGNORECASE)
PHASE_ID_PATTERN = re.compile(r"^PHASE-\d{3}$")
SOURCE_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class DocumentationError(RuntimeError):
    """Raised when maintained documentation violates the baseline contract."""


@dataclass(frozen=True)
class ManagedDocument:
    path: Path
    relative_path: str
    metadata: dict[str, str]
    body: str
    content: str

    @property
    def document_id(self) -> str:
        return self.metadata["document_id"]

    @property
    def title(self) -> str:
        return self.metadata["title"]

    @property
    def document_type(self) -> str:
        return self.metadata["document_type"]


def canonical_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").upper()
    return slug or "UNTITLED"


def parse_front_matter(path: Path, root: Path) -> ManagedDocument:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise DocumentationError(f"missing YAML-style front matter: {canonical_path(path, root)}")
    marker = content.find("\n---\n", 4)
    if marker == -1:
        raise DocumentationError(f"unterminated front matter: {canonical_path(path, root)}")
    raw_metadata = content[4:marker]
    metadata: dict[str, str] = {}
    for line_number, line in enumerate(raw_metadata.splitlines(), start=2):
        if not line.strip():
            continue
        if ":" not in line:
            raise DocumentationError(
                f"invalid front matter at {canonical_path(path, root)}:{line_number}"
            )
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise DocumentationError(
                f"empty front matter field at {canonical_path(path, root)}:{line_number}"
            )
        if key in metadata:
            raise DocumentationError(
                f"duplicate front matter field {key}: {canonical_path(path, root)}"
            )
        metadata[key] = value
    missing = sorted(REQUIRED_METADATA - metadata.keys())
    if missing:
        raise DocumentationError(
            f"missing metadata {missing}: {canonical_path(path, root)}"
        )
    body = content[marker + len("\n---\n") :]
    return ManagedDocument(
        path=path,
        relative_path=canonical_path(path, root),
        metadata=metadata,
        body=body,
        content=content,
    )


def markdown_sections(body: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"^##\s+(.+?)\s*$", body, flags=re.MULTILINE)
    }


def validate_document(document: ManagedDocument, version: str, *, allow_draft: bool) -> None:
    metadata = document.metadata
    document_type = metadata["document_type"]
    status = metadata["status"]
    if document_type not in ALLOWED_TYPES:
        raise DocumentationError(
            f"unsupported document_type {document_type}: {document.relative_path}"
        )
    if status not in ALLOWED_STATUSES:
        raise DocumentationError(f"unsupported status {status}: {document.relative_path}")
    if status == "draft" and not allow_draft:
        raise DocumentationError(f"draft document cannot pass the release gate: {document.relative_path}")
    if status == "active" and metadata["version"] != version:
        raise DocumentationError(
            f"active document version {metadata['version']} does not match {version}: "
            f"{document.relative_path}"
        )
    try:
        date.fromisoformat(metadata["last_reviewed"])
    except ValueError as exc:
        raise DocumentationError(
            f"invalid last_reviewed date: {document.relative_path}"
        ) from exc
    if document_type == "baseline":
        if not metadata.get("baseline_id"):
            raise DocumentationError(f"missing baseline_id: {document.relative_path}")
        if not SOURCE_COMMIT_PATTERN.fullmatch(metadata.get("source_commit", "")):
            raise DocumentationError(f"invalid source_commit: {document.relative_path}")
    if document_type == "phase":
        phase_id = metadata.get("phase_id", "")
        if not PHASE_ID_PATTERN.fullmatch(phase_id):
            raise DocumentationError(f"invalid or missing phase_id: {document.relative_path}")
        expected_prefix = f"documents/phases/{phase_id}-"
        if not document.relative_path.startswith(expected_prefix):
            raise DocumentationError(
                f"phase filename must start with {expected_prefix}: {document.relative_path}"
            )
    sections = markdown_sections(document.body)
    missing_sections = sorted(REQUIRED_SECTIONS[document_type] - sections)
    if missing_sections:
        raise DocumentationError(
            f"missing sections {missing_sections}: {document.relative_path}"
        )
    if status != "draft" and UNRESOLVED_PATTERN.search(document.body):
        raise DocumentationError(f"unresolved marker in active document: {document.relative_path}")


def load_documents(root: Path, *, allow_draft: bool) -> list[ManagedDocument]:
    documents_root = root / "documents"
    if not documents_root.is_dir():
        raise DocumentationError("missing documents directory")
    missing = sorted(path for path in REQUIRED_DOCUMENTS if not (root / path).is_file())
    if missing:
        raise DocumentationError(f"missing required user documents: {missing}")
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    paths = sorted(
        (
            path
            for path in documents_root.rglob("*.md")
            if canonical_path(path, root) != README_PATH
        ),
        key=lambda item: canonical_path(item, root),
    )
    for path in paths:
        if path.is_symlink():
            raise DocumentationError(
                f"managed documentation cannot be a symlink: {canonical_path(path, root)}"
            )
    documents = [parse_front_matter(path, root) for path in paths]
    seen_ids: dict[str, str] = {}
    seen_phase_ids: dict[str, str] = {}
    for document in documents:
        validate_document(document, version, allow_draft=allow_draft)
        previous = seen_ids.get(document.document_id)
        if previous:
            raise DocumentationError(
                f"duplicate document_id {document.document_id}: {previous}, {document.relative_path}"
            )
        seen_ids[document.document_id] = document.relative_path
        if document.document_type == "phase":
            phase_id = document.metadata["phase_id"]
            previous_phase = seen_phase_ids.get(phase_id)
            if previous_phase:
                raise DocumentationError(
                    f"duplicate phase_id {phase_id}: {previous_phase}, {document.relative_path}"
                )
            seen_phase_ids[phase_id] = document.relative_path
    if seen_phase_ids:
        phase_numbers = sorted(int(phase_id.split("-", 1)[1]) for phase_id in seen_phase_ids)
        expected_numbers = list(range(phase_numbers[-1] + 1))
        if phase_numbers != expected_numbers:
            raise DocumentationError(
                f"phase sequence must be contiguous from PHASE-000: {phase_numbers}"
            )
    return documents


def render_index(documents: list[ManagedDocument]) -> str:
    rows = []
    for document in sorted(
        documents,
        key=lambda item: (item.document_type, item.title.casefold(), item.relative_path),
    ):
        relative_link = document.relative_path.removeprefix("documents/")
        label = document.document_type.replace("-", " ").title()
        rows.append(
            f"| [{document.title}]({relative_link}) | {label} | "
            f"{document.metadata['audience']} | {document.metadata['status']} | "
            f"{document.metadata['version']} |"
        )
    return "\n".join(
        [
            INDEX_START,
            "| Document | Type | Audience | Status | Version |",
            "|---|---|---|---|---|",
            *rows,
            INDEX_END,
        ]
    )


def render_readme(documents: list[ManagedDocument]) -> str:
    index = render_index(documents)
    phase_numbers = [
        int(document.metadata["phase_id"].split("-", 1)[1])
        for document in documents
        if document.document_type == "phase"
    ]
    next_phase_id = f"PHASE-{max(phase_numbers, default=-1) + 1:03d}"
    return f"""# MailStack user documentation

The `documents/` directory is the canonical user-facing documentation baseline for MailStack.
Every maintained feature phase must update its phase record and, when behavior changes, the
relevant user manual, how-to guide, or administrator guide.

## Documentation workflow

```bash
python scripts/manage_documents.py new-phase \\
  --phase-id {next_phase_id} \\
  --title \"Feature title\" \\
  --summary \"What the phase changes for users\"

# Complete the generated phase document and update the affected guides.
python scripts/manage_documents.py sync
python scripts/manage_documents.py check
python scripts/check_documentation_policy.py --base HEAD^ --head HEAD
```

`sync` regenerates this index and `DOCUMENTATION_MANIFEST.json`. CI fails when generated
content is stale, a phase document remains in draft state, or a feature change lacks the
required documentation update.

## Maintained documents

{index}

## Scope boundary

The files in this directory explain supported product behavior and operator workflows. The
engineering, architecture, security, deployment, and release references remain in `../docs/`.
When these sources disagree, the implementation and verified release contracts are authoritative,
and both documentation sets must be corrected in the same change.
"""


def render_manifest(root: Path, documents: list[ManagedDocument]) -> str:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    baseline = next(
        (document for document in documents if document.document_type == "baseline"),
        None,
    )
    if baseline is None:
        raise DocumentationError("baseline document is missing")
    payload = {
        "schema_version": 1,
        "project": "MailStack",
        "release_version": version,
        "baseline_id": baseline.metadata.get("baseline_id", ""),
        "baseline_source_commit": baseline.metadata.get("source_commit", ""),
        "scope": "Managed user, administrator, how-to, policy, baseline, and phase Markdown documents.",
        "summary": {
            "documents": len(documents),
            "active": sum(document.metadata["status"] == "active" for document in documents),
            "historical": sum(
                document.metadata["status"] == "historical" for document in documents
            ),
            "draft": sum(document.metadata["status"] == "draft" for document in documents),
            "phases": sum(document.document_type == "phase" for document in documents),
        },
        "documents": [
            {
                "path": document.relative_path,
                "document_id": document.document_id,
                "title": document.title,
                "document_type": document.document_type,
                "audience": document.metadata["audience"],
                "status": document.metadata["status"],
                "version": document.metadata["version"],
                "last_reviewed": document.metadata["last_reviewed"],
                "phase_id": document.metadata.get("phase_id"),
                "sha256": sha256_text(document.content),
            }
            for document in sorted(documents, key=lambda item: item.relative_path)
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def synchronized_content(root: Path, *, allow_draft: bool) -> tuple[str, str, list[ManagedDocument]]:
    documents = load_documents(root, allow_draft=allow_draft)
    return render_readme(documents), render_manifest(root, documents), documents


def sync(root: Path, *, allow_draft: bool) -> list[ManagedDocument]:
    readme, manifest, documents = synchronized_content(root, allow_draft=allow_draft)
    readme_path = root / README_PATH
    manifest_path = root / MANIFEST_PATH
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    readme_path.write_text(readme, encoding="utf-8", newline="\n")
    manifest_path.write_text(manifest, encoding="utf-8", newline="\n")
    return documents


def check(root: Path) -> list[ManagedDocument]:
    readme, manifest, documents = synchronized_content(root, allow_draft=False)
    readme_path = root / README_PATH
    manifest_path = root / MANIFEST_PATH
    if not readme_path.is_file() or readme_path.read_text(encoding="utf-8") != readme:
        raise DocumentationError(f"generated documentation index is stale: {README_PATH}")
    if not manifest_path.is_file() or manifest_path.read_text(encoding="utf-8") != manifest:
        raise DocumentationError(f"documentation manifest is stale: {MANIFEST_PATH}")
    return documents


def create_phase(root: Path, *, phase_id: str, title: str, summary: str) -> Path:
    phase_id = phase_id.strip().upper()
    if not PHASE_ID_PATTERN.fullmatch(phase_id):
        raise DocumentationError("phase ID must use PHASE-NNN format")
    existing = load_documents(root, allow_draft=True)
    drafts = [document.relative_path for document in existing if document.metadata["status"] == "draft"]
    if drafts:
        raise DocumentationError(f"complete existing draft phase before creating another: {drafts}")
    phase_numbers = [
        int(document.metadata["phase_id"].split("-", 1)[1])
        for document in existing
        if document.document_type == "phase"
    ]
    expected_phase_id = f"PHASE-{max(phase_numbers, default=-1) + 1:03d}"
    if phase_id != expected_phase_id:
        raise DocumentationError(f"next phase must be {expected_phase_id}, received {phase_id}")
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    slug = slugify(title)
    target = root / "documents" / "phases" / f"{phase_id}-{slug}.md"
    if target.exists():
        raise DocumentationError(f"phase document already exists: {canonical_path(target, root)}")
    content = f"""---
document_id: {phase_id.lower()}-{slug.lower()}
title: {title.strip()}
document_type: phase
audience: users-and-operators
status: draft
version: {version}
last_reviewed: {date.today().isoformat()}
phase_id: {phase_id}
---

# {phase_id}: {title.strip()}

## Objective

{summary.strip()}

## Scope

This phase record has been created before implementation. Replace this paragraph with the exact
in-scope components, interfaces, and exclusions before the change is merged.

## User-facing changes

Document the observable behavior introduced, changed, or explicitly preserved by this phase.

## How to use

Add the exact user or administrator workflow, including prerequisites and expected results.

## Compatibility

Record backward-compatibility, migration, data, configuration, security, and rollback effects.

## Verification

Record automated tests, manual acceptance checks, security review, and performance review.

## Documentation impact

List every user guide, administrator guide, how-to document, engineering document, changelog, and
release note updated by this phase.
"""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")
    sync(root, allow_draft=True)
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("sync")
    subparsers.add_parser("check")
    phase_parser = subparsers.add_parser("new-phase")
    phase_parser.add_argument("--phase-id", required=True)
    phase_parser.add_argument("--title", required=True)
    phase_parser.add_argument("--summary", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "new-phase":
            path = create_phase(
                root,
                phase_id=args.phase_id,
                title=args.title,
                summary=args.summary,
            )
            print(f"PHASE_DOCUMENT={canonical_path(path, root)}")
            print("DOCUMENTATION_PHASE_CREATED=DRAFT")
            return 0
        if args.command == "sync":
            documents = sync(root, allow_draft=True)
            print(f"DOCUMENTATION_FILES={len(documents)}")
            print("DOCUMENTATION_SYNC=PASS")
            return 0
        documents = check(root)
        print(f"DOCUMENTATION_FILES={len(documents)}")
        print(
            "DOCUMENTATION_PHASES="
            f"{sum(document.document_type == 'phase' for document in documents)}"
        )
        print("DOCUMENTATION_GATE=PASS")
        return 0
    except DocumentationError as exc:
        print(f"DOCUMENTATION_FINDING={exc}")
        print("DOCUMENTATION_GATE=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
