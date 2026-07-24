# Legacy compatibility

The `mailbox-app/deployment`, `mailbox-app/scripts`, and historical documents under `mailbox-app/docs` preserve the original `vibmail.my` v1.2.1 production contract for existing operators. They are retained to avoid breaking upgrades and forensic traceability.

New installations must use the root `install.sh` and `deployment/templates` assets, which are domain-configurable. Do not copy a legacy fixed-domain Nginx or verification file into a new deployment unless you intentionally operate that exact legacy domain.
