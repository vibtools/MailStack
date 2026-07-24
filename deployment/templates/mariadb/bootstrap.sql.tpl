CREATE DATABASE IF NOT EXISTS `{{MAIL_DB_NAME}}`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS `{{APP_DB_NAME}}`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `{{MAIL_DB_NAME}}`.`mail_domains` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(253) NOT NULL,
  `active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mail_domains_name_unique` (`name`),
  KEY `mail_domains_active_idx` (`active`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `{{MAIL_DB_NAME}}`.`mailboxes` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `domain_id` BIGINT UNSIGNED NOT NULL,
  `local_part` VARCHAR(64) NOT NULL,
  `email` VARCHAR(320) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `maildir` VARCHAR(255) NOT NULL,
  `quota_bytes` BIGINT UNSIGNED NOT NULL DEFAULT 2147483648,
  `active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mailboxes_email_unique` (`email`),
  UNIQUE KEY `mailboxes_domain_local_unique` (`domain_id`, `local_part`),
  KEY `mailboxes_active_idx` (`active`),
  CONSTRAINT `mailboxes_domain_fk`
    FOREIGN KEY (`domain_id`) REFERENCES `{{MAIL_DB_NAME}}`.`mail_domains` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `{{MAIL_DB_NAME}}`.`mail_aliases` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `domain_id` BIGINT UNSIGNED NOT NULL,
  `source` VARCHAR(320) NOT NULL,
  `destination` VARCHAR(320) NOT NULL,
  `active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mail_aliases_source_destination_unique` (`source`, `destination`),
  KEY `mail_aliases_source_active_idx` (`source`, `active`),
  CONSTRAINT `mail_aliases_domain_fk`
    FOREIGN KEY (`domain_id`) REFERENCES `{{MAIL_DB_NAME}}`.`mail_domains` (`id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

INSERT INTO `{{MAIL_DB_NAME}}`.`mail_domains` (`name`, `active`)
VALUES ('{{MAIL_DOMAIN}}', 1)
ON DUPLICATE KEY UPDATE `active` = VALUES(`active`);

CREATE OR REPLACE SQL SECURITY INVOKER VIEW `{{MAIL_DB_NAME}}`.`postfix_virtual_domains` AS
SELECT `name`
FROM `{{MAIL_DB_NAME}}`.`mail_domains`
WHERE `active` = 1;

CREATE OR REPLACE SQL SECURITY INVOKER VIEW `{{MAIL_DB_NAME}}`.`postfix_virtual_mailboxes` AS
SELECT LOWER(m.`email`) AS `email`, m.`maildir` AS `maildir`
FROM `{{MAIL_DB_NAME}}`.`mailboxes` AS m
INNER JOIN `{{MAIL_DB_NAME}}`.`mail_domains` AS d ON d.`id` = m.`domain_id`
WHERE m.`active` = 1
  AND d.`active` = 1
  AND LOWER(m.`email`) = CONCAT(LOWER(m.`local_part`), '@', LOWER(d.`name`))
  AND m.`maildir` = CONCAT(LOWER(d.`name`), '/', LOWER(m.`local_part`), '/Maildir/')
  AND LOWER(m.`local_part`) REGEXP '^[a-z0-9]([a-z0-9._-]{0,62}[a-z0-9])?$'
  AND INSTR(m.`local_part`, '..') = 0;

CREATE OR REPLACE SQL SECURITY INVOKER VIEW `{{MAIL_DB_NAME}}`.`postfix_virtual_aliases` AS
SELECT LOWER(a.`source`) AS `source`, a.`destination` AS `destination`
FROM `{{MAIL_DB_NAME}}`.`mail_aliases` AS a
INNER JOIN `{{MAIL_DB_NAME}}`.`mail_domains` AS d ON d.`id` = a.`domain_id`
WHERE a.`active` = 1 AND d.`active` = 1;

CREATE USER IF NOT EXISTS '{{APP_DB_USER}}'@'localhost' IDENTIFIED BY '{{APP_DB_PASSWORD}}';
ALTER USER '{{APP_DB_USER}}'@'localhost' IDENTIFIED BY '{{APP_DB_PASSWORD}}';
CREATE USER IF NOT EXISTS '{{APP_DB_USER}}'@'127.0.0.1' IDENTIFIED BY '{{APP_DB_PASSWORD}}';
ALTER USER '{{APP_DB_USER}}'@'127.0.0.1' IDENTIFIED BY '{{APP_DB_PASSWORD}}';
CREATE USER IF NOT EXISTS '{{POSTFIX_DB_USER}}'@'localhost' IDENTIFIED BY '{{POSTFIX_DB_PASSWORD}}';
ALTER USER '{{POSTFIX_DB_USER}}'@'localhost' IDENTIFIED BY '{{POSTFIX_DB_PASSWORD}}';
CREATE USER IF NOT EXISTS '{{POSTFIX_DB_USER}}'@'127.0.0.1' IDENTIFIED BY '{{POSTFIX_DB_PASSWORD}}';
ALTER USER '{{POSTFIX_DB_USER}}'@'127.0.0.1' IDENTIFIED BY '{{POSTFIX_DB_PASSWORD}}';

GRANT ALL PRIVILEGES ON `{{APP_DB_NAME}}`.* TO '{{APP_DB_USER}}'@'localhost';
GRANT ALL PRIVILEGES ON `{{APP_DB_NAME}}`.* TO '{{APP_DB_USER}}'@'127.0.0.1';

-- The application may provision and enable/disable mailboxes, but it cannot
-- delete mail-server rows or read stored password hashes.
GRANT SELECT (`id`, `name`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mail_domains` TO '{{APP_DB_USER}}'@'localhost';
GRANT SELECT (`id`, `name`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mail_domains` TO '{{APP_DB_USER}}'@'127.0.0.1';
GRANT SELECT (`id`, `domain_id`, `local_part`, `email`, `maildir`, `quota_bytes`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mailboxes` TO '{{APP_DB_USER}}'@'localhost';
GRANT SELECT (`id`, `domain_id`, `local_part`, `email`, `maildir`, `quota_bytes`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mailboxes` TO '{{APP_DB_USER}}'@'127.0.0.1';
GRANT INSERT (`domain_id`, `local_part`, `email`, `password_hash`, `maildir`, `quota_bytes`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mailboxes` TO '{{APP_DB_USER}}'@'localhost';
GRANT INSERT (`domain_id`, `local_part`, `email`, `password_hash`, `maildir`, `quota_bytes`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mailboxes` TO '{{APP_DB_USER}}'@'127.0.0.1';
GRANT UPDATE (`active`)
  ON `{{MAIL_DB_NAME}}`.`mailboxes` TO '{{APP_DB_USER}}'@'localhost';
GRANT UPDATE (`active`)
  ON `{{MAIL_DB_NAME}}`.`mailboxes` TO '{{APP_DB_USER}}'@'127.0.0.1';
GRANT SELECT (`domain_id`, `source`, `destination`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mail_aliases` TO '{{APP_DB_USER}}'@'localhost';
GRANT SELECT (`domain_id`, `source`, `destination`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mail_aliases` TO '{{APP_DB_USER}}'@'127.0.0.1';
GRANT SELECT ON `{{MAIL_DB_NAME}}`.`postfix_virtual_mailboxes` TO '{{APP_DB_USER}}'@'localhost';
GRANT SELECT ON `{{MAIL_DB_NAME}}`.`postfix_virtual_mailboxes` TO '{{APP_DB_USER}}'@'127.0.0.1';

-- SQL SECURITY INVOKER views require the Postfix lookup account to have
-- column-scoped access to the exact underlying fields used by the views.
-- It never receives the stored secret column or any write/DDL privileges.
GRANT SELECT (`id`, `name`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mail_domains` TO '{{POSTFIX_DB_USER}}'@'localhost';
GRANT SELECT (`id`, `name`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mail_domains` TO '{{POSTFIX_DB_USER}}'@'127.0.0.1';
GRANT SELECT (`domain_id`, `local_part`, `email`, `maildir`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mailboxes` TO '{{POSTFIX_DB_USER}}'@'localhost';
GRANT SELECT (`domain_id`, `local_part`, `email`, `maildir`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mailboxes` TO '{{POSTFIX_DB_USER}}'@'127.0.0.1';
GRANT SELECT (`domain_id`, `source`, `destination`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mail_aliases` TO '{{POSTFIX_DB_USER}}'@'localhost';
GRANT SELECT (`domain_id`, `source`, `destination`, `active`)
  ON `{{MAIL_DB_NAME}}`.`mail_aliases` TO '{{POSTFIX_DB_USER}}'@'127.0.0.1';
GRANT SELECT ON `{{MAIL_DB_NAME}}`.`postfix_virtual_domains` TO '{{POSTFIX_DB_USER}}'@'localhost';
GRANT SELECT ON `{{MAIL_DB_NAME}}`.`postfix_virtual_domains` TO '{{POSTFIX_DB_USER}}'@'127.0.0.1';
GRANT SELECT ON `{{MAIL_DB_NAME}}`.`postfix_virtual_mailboxes` TO '{{POSTFIX_DB_USER}}'@'localhost';
GRANT SELECT ON `{{MAIL_DB_NAME}}`.`postfix_virtual_mailboxes` TO '{{POSTFIX_DB_USER}}'@'127.0.0.1';
GRANT SELECT ON `{{MAIL_DB_NAME}}`.`postfix_virtual_aliases` TO '{{POSTFIX_DB_USER}}'@'localhost';
GRANT SELECT ON `{{MAIL_DB_NAME}}`.`postfix_virtual_aliases` TO '{{POSTFIX_DB_USER}}'@'127.0.0.1';
FLUSH PRIVILEGES;
