"""Jobs Demonstrating Stream Iterator Patterns."""

from django.db import transaction
from nautobot.apps.jobs import IntegerVar, Job, register_jobs
from nautobot.dcim.models import Device

name = "Stream Iterator Example"


class StreamProcessExampleModelsJob(Job):
    """Streaming read with ``.iterator()`` instead of a for loop over a full queryset.

    A plain ``for record in queryset:`` loads every row into memory at once and
    caches them on the queryset. This Job instead streams rows with
    ``.iterator(chunk_size=N)``, which uses a server-side cursor and never holds
    the whole result set in memory. It reads only the fields it touches with
    ``.only()``, accumulates a bounded batch, and writes each batch with
    ``bulk_update`` inside its own transaction. It logs a per-run
    summary, not one line per object.

    ``bulk_update`` does not run ``clean()`` or signals. That is
    acceptable here because the write only sets a computed ``description`` and the
    goal is throughput on a large set.
    """

    chunk_size = IntegerVar(
        description="Server-side cursor and write batch size for .iterator() and bulk_update.",
        default=100,
        min_value=1,
        max_value=10000,
    )

    class Meta:
        """Meta attributes."""

        name = "Stream-process example models (iterator)"
        description = "Reads a large queryset with .iterator() and writes in batches with bulk_update."
        soft_time_limit = 600
        time_limit = 660
        has_sensitive_variables = False

    @staticmethod
    def _flush(batch):
        """Write one batch with a single UPDATE and return the row count."""
        if not batch:
            return 0
        # One transaction per batch: a failure isolates to this batch.
        with transaction.atomic():
            Device.objects.bulk_update(batch, ["serial"], batch_size=len(batch))
        return len(batch)

    def run(self, chunk_size):  # pylint: disable=arguments-differ
        """Stream the queryset with .iterator() and update it in batches."""
        # .only() loads just the columns this Job touches.
        # .iterator(chunk_size=...) streams rows with a server-side cursor instead
        # of loading and caching the entire queryset in memory.
        queryset = Device.objects.only("pk", "name", "serial")

        updated = 0
        batch = []
        for record in queryset.iterator(chunk_size=chunk_size):
            record.serial = f"{record.name} stream-processed"
            batch.append(record)
            if len(batch) >= chunk_size:
                updated += self._flush(batch)
                self.logger.info("flush")
                batch = []  # Drop the references so memory does not grow.

        # Flush the final partial batch.
        updated += self._flush(batch)

        # Summary logging: one line, not one per object.
        self.logger.info("Stream processing complete. updated=%d chunk_size=%d", updated, chunk_size)
        return {"updated": updated, "chunk_size": chunk_size}


register_jobs(
    StreamProcessExampleModelsJob,
)
