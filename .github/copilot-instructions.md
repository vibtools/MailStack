# MailStack Copilot Instructions

This repository is MailStack, a self-hosted receive-only mail platform built around Ubuntu 24.04, Postfix, Dovecot LMTP, Django, MariaDB, Maildir, Nginx, and Gunicorn.

## Core working rules

1. Read and follow the repository-level guidance in `AI_INSTRUCTIONS.md` and `AGENTS.md` before making changes.
2. Treat the existing product architecture as authoritative. Do not redesign the platform or change core deployment assumptions unless the user explicitly requests it.
3. Keep changes small, scoped, and aligned with the task requested by the user.
4. Prefer reuse of existing project code, utilities, and patterns over introducing new abstractions or duplicate solutions.
5. Preserve deployment, security, installer, and release contracts. A change that breaks installation or release validation is not acceptable.

## Memory and context rules

- Maintain the project memory in `MEMORY.md` as the durable context record for this repository.
- If the user asks for a task or you make any code, config, template, or infrastructure change, keep the memory file synchronized with the actual project state.
- If you cannot update the file directly, provide the exact markdown snippet to add so the user can keep the memory accurate in real-time.

CRITICAL RULE: Whenever a change, update, bug fix, or new feature is implemented in this project during our conversation, you (the AI) must automatically prompt me to update the `MEMORY.md` file, or directly write/suggest the exact markdown updates needed to keep the project memory 100% up-to-date in real-time.

## Repository validation expectations

When a repository file is changed, confirm whether the relevant validation workflow requires regeneration or re-check of:
- `docs/FORENSIC_FILE_INVENTORY.json`
- `python scripts/generate_inventory.py --root .`
- `python scripts/forensic_audit.py --root .`
- relevant app-specific tests or release gates

Do not claim completion without evidence from the relevant validation command(s).

## Delivery standard

When implementing work:
- understand the request,
- inspect the minimal relevant code,
- patch only what is needed,
- verify the result,
- review the final diff for unintended changes,
- keep the project context grounded and accurate for future sessions.
