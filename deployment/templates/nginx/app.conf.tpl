upstream vibmail_gunicorn {
    server unix:/run/vibmail/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    listen [::]:80;
    server_name {{APP_HOSTNAME}};
    server_tokens off;

    location ^~ /.well-known/acme-challenge/ {
        alias /var/www/letsencrypt/.well-known/acme-challenge/;
        default_type text/plain;
        access_log off;
    }

    location ~ /\.(?!well-known/) { return 404; }
    location / { return 301 https://$host$request_uri; }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name {{APP_HOSTNAME}};

    ssl_certificate /etc/letsencrypt/live/{{CERT_NAME}}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{{CERT_NAME}}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_timeout 1d;
    ssl_session_cache shared:VIBMAILTLS:10m;
    ssl_session_tickets off;

    client_max_body_size 2m;
    server_tokens off;

    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy same-origin always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;

    access_log /var/log/vibmail/nginx-access.log;
    error_log /var/log/vibmail/nginx-error.log warn;

    location ~ /\.(?!well-known/) { return 404; }

    location /static/ {
        alias /var/lib/vibmail/static/;
        access_log off;
        expires 7d;
        add_header Cache-Control "public, max-age=604800, immutable";
    }

    location /_protected_attachments/ {
        internal;
        alias /var/lib/vibmail/attachments/;
        default_type application/octet-stream;
        add_header X-Content-Type-Options nosniff always;
        add_header Cache-Control "private, no-store" always;
    }

    location = /health/ready/ {
        allow 127.0.0.1;
        allow ::1;
        deny all;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_pass http://vibmail_gunicorn;
    }

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_redirect off;
        proxy_read_timeout 60s;
        proxy_pass http://vibmail_gunicorn;
    }
}
