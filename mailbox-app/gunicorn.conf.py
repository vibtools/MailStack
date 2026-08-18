# Gunicorn 25.1+ enables an optional control socket by default.
# MailStack does not use gunicornc; disabling the unused interface avoids
# control-socket writes inside the read-only application working directory.
control_socket_disable = True
