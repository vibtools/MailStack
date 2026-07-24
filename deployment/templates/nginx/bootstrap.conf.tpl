server {
    listen 80;
    listen [::]:80;
    server_name {{PUBLIC_SERVER_NAMES}};
    server_tokens off;

    root /var/www/{{PUBLIC_HOSTNAME}}/current;

    location ^~ /.well-known/acme-challenge/ {
        alias /var/www/letsencrypt/.well-known/acme-challenge/;
        default_type text/plain;
        access_log off;
    }

    location ~ /\.(?!well-known/) { return 404; }
    location / { try_files $uri $uri/ =404; }
}

server {
    listen 80;
    listen [::]:80;
    server_name {{APP_HOSTNAME}} {{MAIL_HOSTNAME}};
    server_tokens off;

    location ^~ /.well-known/acme-challenge/ {
        alias /var/www/letsencrypt/.well-known/acme-challenge/;
        default_type text/plain;
        access_log off;
    }

    location ~ /\.(?!well-known/) { return 404; }
    location / { return 404; }
}
