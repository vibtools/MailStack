#!/usr/bin/env python3
"""Portable Bash runtime discovery for MailStack audit and contract tooling."""
from __future__ import annotations

import atexit
import os
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

_PROBE_MARKER = "MAILSTACK_BASH_OK"


def _add_candidate(candidates: list[str], value: str | os.PathLike[str] | None) -> None:
    if not value:
        return
    text = os.fspath(value)
    key = os.path.normcase(os.path.abspath(text)) if os.path.isabs(text) else os.path.normcase(text)
    if all(
        (os.path.normcase(os.path.abspath(item)) if os.path.isabs(item) else os.path.normcase(item)) != key
        for item in candidates
    ):
        candidates.append(text)


def _windows_git_bash_candidates() -> list[str]:
    candidates: list[str] = []
    git = shutil.which("git")
    if git:
        git_path = Path(git).resolve()
        # Git for Windows normally exposes git.exe from <root>/cmd or <root>/bin.
        roots = [git_path.parent.parent, git_path.parent]
        for root in roots:
            _add_candidate(candidates, root / "bin" / "bash.exe")
            _add_candidate(candidates, root / "usr" / "bin" / "bash.exe")

    for env_name in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(env_name)
        if not base:
            continue
        base_path = Path(base)
        if env_name == "LOCALAPPDATA":
            root = base_path / "Programs" / "Git"
        else:
            root = base_path / "Git"
        _add_candidate(candidates, root / "bin" / "bash.exe")
        _add_candidate(candidates, root / "usr" / "bin" / "bash.exe")
    return candidates


def _candidate_bashes() -> list[str]:
    candidates: list[str] = []
    _add_candidate(candidates, os.environ.get("BASH_EXECUTABLE"))

    if os.name == "nt":
        # Prefer Git Bash over the Windows `bash.exe` WSL launcher. The latter may
        # exist on PATH even when the WSL VM/Docker Desktop backing disk is broken.
        for candidate in _windows_git_bash_candidates():
            _add_candidate(candidates, candidate)

    _add_candidate(candidates, shutil.which("bash"))
    if os.name != "nt":
        _add_candidate(candidates, "/bin/bash")
        _add_candidate(candidates, "/usr/bin/bash")
    return candidates


def _probe(candidate: str) -> tuple[bool, str]:
    path = Path(candidate)
    if os.path.isabs(candidate) and not path.is_file():
        return False, "not found"
    try:
        completed = subprocess.run(
            [candidate, "--noprofile", "--norc", "-c", f"printf '{_PROBE_MARKER}\\n'"],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"{type(exc).__name__}: {exc}"
    if completed.returncode == 0 and _PROBE_MARKER in completed.stdout:
        return True, ""
    detail = (completed.stderr or completed.stdout or f"exit={completed.returncode}").strip()
    return False, " ".join(detail.split())[:300]


@lru_cache(maxsize=1)
def resolve_bash() -> str:
    """Return a verified Bash executable, preferring Git Bash on Windows."""
    failures: list[str] = []
    for candidate in _candidate_bashes():
        ok, detail = _probe(candidate)
        if ok:
            return candidate
        failures.append(f"{candidate}: {detail}")
    joined = "; ".join(failures) if failures else "no Bash candidates were found"
    raise RuntimeError(
        "No usable Bash runtime is available. Install Git for Windows/Git Bash or set "
        f"BASH_EXECUTABLE to a working bash executable. Attempts: {joined}"
    )



def _shell_single_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _bash_path(candidate: str, path: Path) -> str:
    """Translate a host path for the selected Bash runtime when required."""
    if os.name != "nt":
        return path.resolve().as_posix()
    try:
        completed = subprocess.run(
            [candidate, "--noprofile", "--norc", "-c", 'cygpath -u "$1"', "mailstack", str(path)],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Unable to translate Windows path for Bash: {path}: {exc}") from exc
    translated = completed.stdout.strip()
    if completed.returncode or not translated:
        detail = (completed.stderr or completed.stdout or f"exit={completed.returncode}").strip()
        raise RuntimeError(f"Unable to translate Windows path for Bash: {path}: {detail}")
    return translated


@lru_cache(maxsize=1)
def _python3_bridge_bash_env() -> str:
    """Create a process-local BASH_ENV that maps python3 to this Python interpreter."""
    bash = resolve_bash()
    python_path = _bash_path(bash, Path(sys.executable))
    temporary = Path(tempfile.mkdtemp(prefix="mailstack-python3-bridge-"))
    atexit.register(shutil.rmtree, temporary, ignore_errors=True)
    env_file = temporary / "bash_env"
    env_file.write_text(
        "python3() {\n"
        f"  {_shell_single_quote(python_path)} \"$@\"\n"
        "}\n",
        encoding="utf-8",
        newline="\n",
    )
    return _bash_path(bash, env_file)


def bash_environment(*, force_python3_bridge: bool = False) -> dict[str, str]:
    """Return a deterministic environment for Bash-backed repository checks.

    Ubuntu production keeps its native ``python3`` contract. Windows local tests
    receive a process-local BASH_ENV function that maps ``python3`` to the exact
    interpreter running the audit harness, without modifying install.sh or the
    developer machine. ``force_python3_bridge`` exists for platform-independent
    contract testing of the bridge itself.
    """
    environment = os.environ.copy()
    if os.name == "nt" or force_python3_bridge:
        environment["BASH_ENV"] = _python3_bridge_bash_env()
    return environment

def script_argument(path: Path, *, cwd: Path) -> str:
    """Return a Bash-friendly script path relative to cwd when possible."""
    try:
        relative = path.resolve().relative_to(cwd.resolve())
    except ValueError:
        return path.as_posix()
    value = relative.as_posix()
    return value if value.startswith(".") else f"./{value}"


def bash_script_command(path: Path, *arguments: str, cwd: Path) -> list[str]:
    return [
        resolve_bash(),
        "--noprofile",
        "--norc",
        script_argument(path, cwd=cwd),
        *arguments,
    ]


def bash_syntax_command(path: Path, *, cwd: Path) -> list[str]:
    return [
        resolve_bash(),
        "--noprofile",
        "--norc",
        "-n",
        script_argument(path, cwd=cwd),
    ]
