from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError

from apps.ingestion.repair import (
    BodyRepairError,
    RepairSourceMismatch,
    RepairSourceMissing,
    RepairSourceTooLarge,
    repair_message_bodies,
)
from apps.messages.models import Message

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Counters:
    scanned: int = 0
    would_update: int = 0
    updated: int = 0
    unchanged: int = 0
    missing: int = 0
    mismatch: int = 0
    oversized: int = 0
    errors: int = 0


class Command(BaseCommand):
    help = "Safely re-parse stored message bodies from their original Maildir source."

    def add_arguments(self, parser):
        parser.add_argument("--mailbox", help="Limit to one mailbox local part")
        parser.add_argument("--message", help="Limit to one message UUID")
        parser.add_argument("--limit", type=int, default=500, help="Maximum messages to inspect (1-5000)")
        parser.add_argument("--dry-run", action="store_true", help="Report changes without modifying data")
        parser.add_argument(
            "--confirm-repair",
            action="store_true",
            help="Required for mutation; confirms body-only repair from Maildir source",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        if limit < 1 or limit > 5000:
            raise CommandError("--limit must be between 1 and 5000")
        if not options["dry_run"] and not options["confirm_repair"]:
            raise CommandError("Mutation requires --confirm-repair; run --dry-run first")

        queryset = Message.objects.select_related("mailbox").order_by("pk")
        if options["mailbox"]:
            queryset = queryset.filter(mailbox__local_part__iexact=options["mailbox"])
        if options["message"]:
            try:
                message_uuid = UUID(options["message"])
            except ValueError as exc:
                raise CommandError("--message must be a valid UUID") from exc
            queryset = queryset.filter(uuid=message_uuid)

        counters = Counters()
        for message in queryset[:limit]:
            counters.scanned += 1
            try:
                result = repair_message_bodies(message, dry_run=options["dry_run"])
            except RepairSourceMissing:
                counters.missing += 1
                continue
            except RepairSourceMismatch:
                counters.mismatch += 1
                continue
            except RepairSourceTooLarge:
                counters.oversized += 1
                continue
            except BodyRepairError as exc:
                counters.errors += 1
                logger.warning(
                    "Message body repair rejected",
                    extra={
                        "event": "message_body_repair_error",
                        "message_uuid": str(message.uuid),
                        "error_type": type(exc).__name__,
                    },
                )
                continue
            except Exception as exc:
                counters.errors += 1
                logger.exception(
                    "Message body repair failed",
                    extra={
                        "event": "message_body_repair_error",
                        "message_uuid": str(message.uuid),
                        "error_type": type(exc).__name__,
                    },
                )
                continue

            if result.status == "would_update":
                counters.would_update += 1
            elif result.status == "updated":
                counters.updated += 1
            else:
                counters.unchanged += 1

        summary = (
            f"scanned={counters.scanned} would_update={counters.would_update} "
            f"updated={counters.updated} unchanged={counters.unchanged} "
            f"missing={counters.missing} mismatch={counters.mismatch} "
            f"oversized={counters.oversized} errors={counters.errors}"
        )
        self.stdout.write(summary)
        if counters.errors:
            raise CommandError("Message body repair completed with errors")
