server {
    listen 80;
    listen [::]:80;
    server_name {{PUBLIC_SERVER_NAMES}};
    server_tokens off;

    location ^~ /.well-known/acme-challenge/ {
        alias /var/www/letsencrypt/.well-known/acme-challenge/;
        default_type text/plain;
        access_log off;
    }

    location ~ /\.(?!well-known/) { return 404; }
    location / { return 301 https://{{PUBLIC_HOSTNAME}}$request_uri; }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name {{PUBLIC_SERVER_NAMES}};

    ssl_certificate /etc/letsencrypt/live/{{CERT_NAME}}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{{CERT_NAME}}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_timeout 1d;
    ssl_session_cache shared:VIBMAILPUBTLS:10m;
    ssl_session_tickets off;

    root /var/www/{{PUBLIC_HOSTNAME}}/current;
    index index.html;
    server_tokens off;
    client_max_body_size 64k;

    access_log /var/log/vibmail/public-site-access.log;
    error_log /var/log/vibmail/public-site-error.log warn;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;
    add_header Content-Security-Policy "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests" always;

    location ~ /\.(?!well-known/) { return 404; }

    location = /api/contact/csrf/ {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_pass http://unix:/run/vibmail-public-contact/contact.sock:/csrf/;
    }

    location = /api/contact/ {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_pass http://unix:/run/vibmail-public-contact/contact.sock:/;
    }

    location = /api/contact/health/ {
        allow 127.0.0.1;
        allow ::1;
        deny all;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_pass http://unix:/run/vibmail-public-contact/contact.sock:/health/;
    }

    location /assets/ {
        try_files $uri =404;
        access_log off;
        expires 7d;
        add_header Cache-Control "public, max-age=604800, immutable";
    }

    location / { try_files $uri $uri/ $uri/index.html =404; }
}

server {
    listen 80;
    listen [::]:80;
    server_name {{MAIL_HOSTNAME}};
    server_tokens off;

    location ^~ /.well-known/acme-challenge/ {
        alias /var/www/letsencrypt/.well-known/acme-challenge/;
        default_type text/plain;
        access_log off;
    }
    location / { return 404; }
}
