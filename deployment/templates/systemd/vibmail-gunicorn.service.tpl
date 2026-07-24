[Unit]
Description=MailStack Gunicorn application
After=network-online.target mariadb.service
Wants=network-online.target
RequiresMountsFor=/opt/vibmail/app /var/log/vibmail /var/vmail /var/lib/vibmail/attachments

[Service]
Type=simple
User=vmail
Group=www-data
SupplementaryGroups=vmail
WorkingDirectory=/opt/vibmail/app
EnvironmentFile=/etc/vibmail/vibmail.env
RuntimeDirectory=vibmail
RuntimeDirectoryMode=0750
UMask=0077
ExecStart=/opt/vibmail/venv/bin/gunicorn config.wsgi:application --bind unix:/run/vibmail/gunicorn.sock --umask 0007 --workers {{GUNICORN_WORKERS}} --threads 2 --timeout 60 --access-logfile - --error-logfile -
ExecReload=/bin/kill -s HUP $MAINPID
KillSignal=SIGQUIT
TimeoutStopSec=30
Restart=on-failure
RestartSec=3
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/run/vibmail /var/log/vibmail /var/lib/vibmail/attachments /var/vmail
NoNewPrivileges=true
CapabilityBoundingSet=
LockPersonality=true
RestrictSUIDSGID=true

[Install]
WantedBy=multi-user.target
