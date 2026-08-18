#!/usr/bin/env python3
"""Fail-closed release eligibility checks for MailStack tag publication."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

VERSION_PATTERN = re.compile(r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-rc\.(?P<rc>0|[1-9]\d*))?$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
API_VERSION = "2022-11-28"


class ReleaseGateError(RuntimeError):
    """Raised when release publication eligibility cannot be proven."""


@dataclass(frozen=True)
class ReleaseIdentity:
    version: str
    tag: str
    package_version: str
    prerelease: bool
    publish: bool


def normalize_package_version(version: str) -> str:
    match = VERSION_PATTERN.fullmatch(version)
    if not match:
        raise ReleaseGateError(f"unsupported VERSION format: {version!r}")
    base = f"{match.group('major')}.{match.group('minor')}.{match.group('patch')}"
    rc = match.group("rc")
    return f"{base}rc{rc}" if rc is not None else base


def read_package_version(root: Path) -> str:
    pyproject = root / "mailbox-app" / "pyproject.toml"
    try:
        payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        return str(payload["project"]["version"])
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        raise ReleaseGateError(f"unable to read project.version from {pyproject}: {exc}") from exc


def validate_local_identity(
    root: Path,
    *,
    event_name: str,
    ref_type: str,
    ref_name: str,
    sha: str,
) -> ReleaseIdentity:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    expected_package = normalize_package_version(version)
    package_version = read_package_version(root)
    if package_version != expected_package:
        raise ReleaseGateError(
            f"package version mismatch: VERSION={version!r}, project.version={package_version!r}, expected={expected_package!r}"
        )

    prerelease = VERSION_PATTERN.fullmatch(version).group("rc") is not None  # type: ignore[union-attr]
    expected_tag = f"v{version}"
    publish = event_name == "push"
    if publish:
        if ref_type != "tag":
            raise ReleaseGateError(f"release publication requires a tag push, got ref_type={ref_type!r}")
        if ref_name != expected_tag:
            raise ReleaseGateError(f"tag/version mismatch: tag={ref_name!r}, expected={expected_tag!r}")
        if not SHA_PATTERN.fullmatch(sha):
            raise ReleaseGateError(f"invalid release SHA: {sha!r}")
    elif event_name != "workflow_dispatch":
        raise ReleaseGateError(f"unsupported release workflow event: {event_name!r}")

    return ReleaseIdentity(
        version=version,
        tag=expected_tag,
        package_version=package_version,
        prerelease=prerelease,
        publish=publish,
    )


def git_output(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if completed.returncode:
        raise ReleaseGateError((completed.stdout + completed.stderr).strip() or "git command failed")
    return completed.stdout.strip()


def require_exact_main_head(root: Path, sha: str, default_branch: str) -> None:
    ref = f"refs/remotes/origin/{default_branch}"
    git_output(
        root,
        "fetch",
        "--no-tags",
        "--prune",
        "origin",
        f"+refs/heads/{default_branch}:{ref}",
    )
    main_sha = git_output(root, "rev-parse", ref)
    if main_sha != sha:
        raise ReleaseGateError(
            f"tagged SHA is not the current {default_branch} head: tagged={sha}, {default_branch}={main_sha}"
        )


def api_request_json(url: str, token: str) -> tuple[int, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "MailStack-release-gate",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read()
        payload: Any = None
        if body:
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = None
        return exc.code, payload
    except urllib.error.URLError as exc:
        raise ReleaseGateError(f"GitHub API request failed: {exc.reason}") from exc


def require_release_lookup_absent_status(status: int, tag: str) -> None:
    if status == 404:
        return
    if status == 200:
        raise ReleaseGateError(f"GitHub Release already exists for {tag}; refusing overwrite")
    raise ReleaseGateError(f"unable to prove release absence for {tag}; GitHub API status={status}")


def require_release_absent(repository: str, tag: str, token: str, *, api_base: str) -> None:
    encoded_tag = urllib.parse.quote(tag, safe="")
    status, _ = api_request_json(
        f"{api_base}/repos/{repository}/releases/tags/{encoded_tag}",
        token,
    )
    require_release_lookup_absent_status(status, tag)


def payload_has_successful_main_ci(payload: Any, *, sha: str, default_branch: str) -> bool:
    if not isinstance(payload, dict):
        return False
    runs = payload.get("workflow_runs")
    if not isinstance(runs, list):
        return False
    return any(
        isinstance(run, dict)
        and run.get("head_sha") == sha
        and run.get("head_branch") == default_branch
        and run.get("event") == "push"
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
        for run in runs
    )


def require_successful_main_ci(
    repository: str,
    sha: str,
    default_branch: str,
    token: str,
    *,
    api_base: str,
) -> None:
    params = urllib.parse.urlencode(
        {
            "branch": default_branch,
            "event": "push",
            "status": "completed",
            "head_sha": sha,
            "per_page": 100,
        }
    )
    status, payload = api_request_json(
        f"{api_base}/repos/{repository}/actions/workflows/ci.yml/runs?{params}",
        token,
    )
    if status != 200:
        raise ReleaseGateError(f"unable to query main CI evidence; GitHub API status={status}")
    if not payload_has_successful_main_ci(payload, sha=sha, default_branch=default_branch):
        raise ReleaseGateError(f"no successful main push CI found for exact release SHA {sha}")


def write_outputs(path: Path | None, identity: ReleaseIdentity) -> None:
    if path is None:
        return
    values = {
        "version": identity.version,
        "tag": identity.tag,
        "prerelease": "true" if identity.prerelease else "false",
        "publish": "true" if identity.publish else "false",
        "title": f"MailStack {identity.version}",
    }
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--event-name", default=os.getenv("GITHUB_EVENT_NAME", "workflow_dispatch"))
    parser.add_argument("--ref-type", default=os.getenv("GITHUB_REF_TYPE", "branch"))
    parser.add_argument("--ref-name", default=os.getenv("GITHUB_REF_NAME", ""))
    parser.add_argument("--sha", default=os.getenv("GITHUB_SHA", ""))
    parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", ""))
    parser.add_argument("--default-branch", default="main")
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--remote", action="store_true")
    parser.add_argument("--api-base", default=os.getenv("GITHUB_API_URL", "https://api.github.com"))
    args = parser.parse_args()

    root = args.root.resolve()
    try:
        identity = validate_local_identity(
            root,
            event_name=args.event_name,
            ref_type=args.ref_type,
            ref_name=args.ref_name,
            sha=args.sha,
        )
        if args.remote:
            if not identity.publish:
                raise ReleaseGateError("remote publication gate is valid only for a tag push")
            if not args.repository:
                raise ReleaseGateError("GITHUB_REPOSITORY is required for remote publication checks")
            token = os.getenv("GITHUB_TOKEN", "")
            if not token:
                raise ReleaseGateError("GITHUB_TOKEN is required for remote publication checks")
            require_exact_main_head(root, args.sha, args.default_branch)
            require_release_absent(args.repository, identity.tag, token, api_base=args.api_base.rstrip("/"))
            require_successful_main_ci(
                args.repository,
                args.sha,
                args.default_branch,
                token,
                api_base=args.api_base.rstrip("/"),
            )

        write_outputs(args.github_output, identity)
        print(f"RELEASE_VERSION={identity.version}")
        print(f"RELEASE_TAG={identity.tag}")
        print(f"RELEASE_PRERELEASE={'true' if identity.prerelease else 'false'}")
        print(f"RELEASE_MODE={'PUBLISH' if identity.publish else 'VALIDATE_ONLY'}")
        print(f"RELEASE_REMOTE_CHECK={'PASS' if args.remote else 'NOT_REQUESTED'}")
        print("RELEASE_GATE=PASS")
        return 0
    except (OSError, ReleaseGateError) as exc:
        print(f"RELEASE_GATE_FINDING={exc}")
        print("RELEASE_GATE=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
