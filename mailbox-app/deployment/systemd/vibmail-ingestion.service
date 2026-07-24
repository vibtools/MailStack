[Unit]
Description=MailStack Maildir ingestion worker
After=network-online.target mariadb.service vibmail-gunicorn.service
Wants=network-online.target
RequiresMountsFor=/opt/vibmail/app /var/vmail /var/lib/vibmail/attachments /var/log/vibmail

[Service]
Type=simple
User=vmail
Group=vmail
WorkingDirectory=/opt/vibmail/app
EnvironmentFile=/etc/vibmail/vibmail.env
RuntimeDirectory=vibmail-ingestion
RuntimeDirectoryMode=0750
UMask=0077
ExecStart=/opt/vibmail/venv/bin/python manage.py ingest_maildir --watch
KillSignal=SIGTERM
TimeoutStopSec=45
Restart=on-failure
RestartSec=5
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadOnlyPaths=/var/vmail
ReadWritePaths=/run/vibmail /var/log/vibmail /var/lib/vibmail/attachments
NoNewPrivileges=true
CapabilityBoundingSet=
LockPersonality=true
RestrictSUIDSGID=true

[Install]
WantedBy=multi-user.target
