protocols = lmtp
mail_location = maildir:/var/vmail/%d/%n/Maildir
mail_uid = vmail
mail_gid = vmail
first_valid_uid = 5000
last_valid_uid = 5000

ssl = required
ssl_cert = </etc/letsencrypt/live/{{CERT_NAME}}/fullchain.pem
ssl_key = </etc/letsencrypt/live/{{CERT_NAME}}/privkey.pem

userdb {
  driver = static
  args = uid=5000 gid=5000 home=/var/vmail/%d/%n
}

service lmtp {
  user = vmail

  unix_listener /var/spool/postfix/private/dovecot-lmtp {
    mode = 0600
    user = postfix
    group = postfix
  }
}

protocol lmtp {
  postmaster_address = postmaster@{{MAIL_DOMAIN}}
}
