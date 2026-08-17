from __future__ import annotations

import signal
import threading

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from filelock import FileLock, Timeout

from apps.ingestion.service import ingest_all


class Command(BaseCommand):
    help = "Ingest messages from application Maildirs without moving source files."

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--once", action="store_true")
        mode.add_argument("--watch", action="store_true")
        parser.add_argument("--interval", type=int, default=settings.INGESTION_INTERVAL_SECONDS)
        parser.add_argument("--mailbox")
        parser.add_argument("--rebuild-missing", action="store_true")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        if options["interval"] < 1:
            raise CommandError("--interval must be at least 1 second")
        lock_required = not (options["dry_run"] and not options["watch"])
        lock = None
        if lock_required:
            settings.INGESTION_LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
            lock = FileLock(str(settings.INGESTION_LOCK_FILE))
            try:
                lock.acquire(timeout=0)
            except Timeout as exc:
                raise CommandError("Another ingestion worker already holds the lock") from exc
        stop_event = threading.Event()

        def stop_handler(_signum, _frame):
            stop_event.set()

        signal.signal(signal.SIGTERM, stop_handler)
        signal.signal(signal.SIGINT, stop_handler)
        try:
            while True:
                result = ingest_all(
                    mailbox_local_part=options["mailbox"],
                    dry_run=options["dry_run"],
                    rebuild_missing=options["rebuild_missing"],
                )
                summary = (
                    f"scanned={result.scanned} created={result.created} "
                    f"duplicates={result.duplicates} oversized={result.oversized} "
                    f"errors={result.errors}"
                )
                self.stdout.write(summary)
                if result.errors:
                    self.stderr.write("One or more messages failed; other messages continued.")
                if not options["watch"] or stop_event.is_set():
                    if result.errors:
                        raise CommandError("Ingestion completed with errors")
                    return
                stop_event.wait(options["interval"])
        finally:
            if lock is not None:
                lock.release()
