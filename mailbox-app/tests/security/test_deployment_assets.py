from __future__ import annotations

from pathlib import Path

from apps.mailboxes.forms import MailboxCreateForm

ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_ui_reserves_system_addresses():
    for local_part in ("postmaster", "abuse", "admin"):
        form = MailboxCreateForm({"local_part": local_part})
        assert not form.is_valid()
        assert "reserved" in str(form.errors).lower()


def test_clean_install_and_deploy_create_mail_roots():
    install = read("scripts/install_dependencies.sh")
    deploy = read("scripts/deploy_application.sh")
    expected = "/var/vmail /var/vmail/vibmail.my"
    assert expected in install
    assert expected in deploy
    assert "UID/GID 5000" in deploy


def test_systemd_runtime_directories_are_isolated():
    gunicorn = read("deployment/systemd/vibmail-gunicorn.service")
    ingestion = read("deployment/systemd/vibmail-ingestion.service")
    env_example = read(".env.example")
    assert "RuntimeDirectory=vibmail\n" in gunicorn
    assert "RuntimeDirectory=vibmail-ingestion\n" in ingestion
    assert "INGESTION_LOCK_FILE=/run/vibmail-ingestion/ingestion.lock" in env_example


def test_restore_preserves_service_readable_environment_and_quiesces_postfix():
    restore = read("scripts/restore.sh")
    assert "SERVICES=(vibmail-public-contact postfix dovecot vibmail-ingestion vibmail-gunicorn)" in restore
    assert 'systemctl stop "$service.service"' in restore
    assert 'systemctl start "${ACTIVE_SERVICES[$index]}.service"' in restore
    assert "chown root:vmail /etc/vibmail/vibmail.env" in restore
    assert "chmod 0640 /etc/vibmail/vibmail.env" in restore
    assert 'DB_DEFAULTS_FILE=${DB_BACKUP_DEFAULTS_FILE:-/etc/vibmail/mariadb-backup.cnf}' in restore
    assert 'mariadb "${DB_OPTIONS[@]}" --binary-mode' in restore
    assert "member.issym() or member.islnk() or member.isdev() or member.isfifo()" in restore


def test_backup_quiesces_and_restarts_mail_services():
    backup = read("scripts/backup.sh")
    assert "SERVICES=(vibmail-public-contact postfix dovecot vibmail-ingestion vibmail-gunicorn)" in backup
    assert 'systemctl stop "$service.service"' in backup
    assert "trap cleanup_on_exit EXIT INT TERM" in backup
    assert "restart_services" in backup
    assert 'systemctl start "${ACTIVE_SERVICES[$index]}.service"' in backup
    assert "--add-drop-database" in backup


def test_mariadb_application_role_is_scoped_away_from_mailserver_ddl():
    sql = read("deployment/mariadb/create_vibmail_app_database.sql.template")
    contract = read("deployment/postfix/POSTFIX_INTEGRATION_CONTRACT.md")
    assert "CREATE DATABASE IF NOT EXISTS `vibmail_app`" in sql
    assert "GRANT ALL PRIVILEGES ON `vibmail_app`.*" in sql
    assert "GRANT SELECT, INSERT, UPDATE ON `vibmail`.`mailboxes`" in sql
    assert "GRANT DELETE ON `vibmail`" not in sql
    assert "GRANT DROP ON `vibmail`" not in sql
    assert (
        "never created, replaced, or dropped" in contract.lower()
        or "only postfix mailbox lookup source" in contract.lower()
    )


def test_management_scripts_force_production_environment():
    deploy = read("scripts/deploy_application.sh")
    create_admin = read("scripts/create_admin.sh")
    verify = read("scripts/verify_application.sh")
    restore = read("scripts/restore.sh")
    rollback = read("scripts/rollback.sh")

    for script in (deploy, create_admin, verify, restore, rollback):
        assert "VIBMAIL_ENV_FILE" in script
        assert "DJANGO_SETTINGS_MODULE=config.settings.production" in script

    assert "run_app" in deploy
    assert "runuser -u vmail --preserve-environment" in deploy
    assert "runuser -u vmail --preserve-environment" in create_admin
    assert "runuser -u vmail --preserve-environment" in restore
    assert "runuser -u vmail --preserve-environment" in rollback


def test_virtualenv_permissions_are_normalized_for_vmail_runtime():
    install = read("scripts/install_dependencies.sh")
    deploy = read("scripts/deploy_application.sh")

    for script in (install, deploy):
        assert "chown -R root:vmail" in script
        assert "chmod -R g+rX,o-rwx" in script
        assert "runuser -u vmail -- test -x" in script

    assert "import django.core, MySQLdb" in deploy
    assert deploy.index("chmod -R g+rX,o-rwx") < deploy.index("manage.py migrate")


def test_release_pins_and_verifies_django_security_patch():
    pyproject = read("pyproject.toml")
    locked = read("requirements/locked.txt")
    constraints = read("requirements/constraints.txt")
    preflight = read("scripts/preflight_v1_2_1.sh")
    deploy = read("scripts/deploy_application.sh")
    verify = read("scripts/verify_v1_2_1.sh")

    for source in (pyproject, locked, constraints):
        assert "Django==5.2.16" in source
        assert "Django==5.2.15" not in source

    assert "Required Django 5.2.16 security pin is missing" in preflight
    assert '"Django": "5.2.16"' in deploy
    assert '"bleach": "6.4.0"' in deploy
    assert '"python-dotenv": "1.2.2"' in deploy
    assert '"Django": "5.2.16"' in verify


def test_release_source_cannot_be_the_live_application_tree():
    deploy = read("scripts/deploy_application.sh")
    preflight = read("scripts/preflight_v1_2_1.sh")
    assert '"$APP_ROOT"|"$APP_ROOT"/*' in deploy
    assert "/opt/vibmail/app|/opt/vibmail/app/*" in preflight


def test_dependency_audit_isolated_and_fail_closed():
    audit_script = read("scripts/audit_dependencies_v1_2_1.sh")
    assert "Python 3.12 is required" in audit_script
    assert "pip-audit==2.10.0" in audit_script
    assert "requirements/locked.txt" in audit_script
    assert "--disable-pip" in audit_script
    assert "--no-deps" in audit_script
    assert "mktemp -d" in audit_script


def test_v1_2_1_security_hotfix_pins_and_bleach_scope():
    locked = read("requirements/locked.txt")
    parser = read("apps/ingestion/parser.py")
    audit = read("scripts/audit_dependencies_v1_2_1.sh")
    assert "bleach==6.4.0" in locked
    assert "python-dotenv==1.2.2" in locked
    assert "parse_email=False" in parser
    assert "GHSA-g75f-g53v-794x" in audit
    assert "--ignore-vuln GHSA-g75f-g53v-794x" in audit
