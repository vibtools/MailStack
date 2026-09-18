[Unit]
Description=MailStack root update worker
After=network-online.target
Wants=network-online.target
RequiresMountsFor=/opt/vibmail/app /run/vibmail

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/vibmail/app
ExecStart=/opt/vibmail/venv/bin/python /opt/vibmail/app/scripts/update_worker.py
Restart=on-failure
RestartSec=2
PrivateTmp=false
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/run/vibmail /tmp /opt/vibmail /opt/vibmail-public-site /opt/vibmail-upgrades /etc/vibmail /var/backups/vibmail /var/lib/vibmail /var/www
NoNewPrivileges=true
LockPersonality=true
RestrictSUIDSGID=true

[Install]
WantedBy=multi-user.target
