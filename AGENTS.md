# MailStack Global Agent Rules

**CRITICAL MANDATE FOR ALL AI AGENTS:**

1. **STRICT COMPLIANCE WITH `AI_INSTRUCTIONS.md`:** 
   You must read and unconditionally follow every rule, instruction, and protocol defined in `AI_INSTRUCTIONS.md`. It is the core operational guideline for this project. Failure to adhere to those rules is unacceptable.

2. **MANDATORY REAL-TIME MEMORY UPDATES:**
   Whenever any code change, bug fix, architectural decision, or new feature is implemented during your session, you **MUST** automatically update the `MEMORY.md` file in real-time. The project context in `MEMORY.md` must be kept completely synchronized with the actual codebase at all times. Do not wait for the user to prompt you to update it.

3. **MANDATORY CI WORKFLOW & FORENSIC INVENTORY VALIDATION:**
   Whenever any code change, template edit, design token update, or file modification is made, you **MUST** proactively validate and synchronize all GitHub Actions workflow requirements before concluding:
   - **Regenerate Forensic Inventory:** Whenever ANY file in the repository is modified, created, or deleted, you **MUST** run `python scripts/generate_inventory.py --root .` to synchronize `docs/FORENSIC_FILE_INVENTORY.json`. The CI `INVENTORY_GATE` fails closed if this file is out of date.
   - **Verify Workflow Contracts & Forensic Audit:** You **MUST** run `python scripts/forensic_audit.py --root .` (and relevant test suites like `scripts/test_ui_foundation.py`) and ensure `BLOCKING_FINDINGS=0` and `FORENSIC_AUDIT=PASS` so that any push immediately succeeds in GitHub Actions without CI errors.
   - **Preserve Critical Contracts:** Respect established contracts (e.g., in `base.html`, `app.css` MUST precede `foundation.css`, and frozen design tokens in `test_ui_foundation.py` must match `foundation.css`).

4. **MANDATORY POST-UPDATE GENERATED-CONTRACT CHECK:**
   After every update, before commit or push, do not skip any generated or dependent validation step that can make GitHub Actions fail. If documentation or managed-document metadata changes, run `python scripts/manage_documents.py sync` and then `python scripts/manage_documents.py check`; next run `python scripts/generate_inventory.py --root .` and verify it with `python scripts/generate_inventory.py --root . --check`; finally run `python scripts/forensic_audit.py --root .` and all relevant focused tests. A commit/push is not permitted until documentation manifests, forensic inventory, workflow contracts, and required tests are synchronized and passing. When a CI failure identifies a missing, stale, mismatched, or skipped contract, update this rule or the relevant validation test so the same failure cannot be silently skipped in a later update.
