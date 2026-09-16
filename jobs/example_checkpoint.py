"""Checkpointed Job Example."""

from celery.exceptions import SoftTimeLimitExceeded
from nautobot.apps.jobs import BooleanVar, IntegerVar, Job, register_jobs
from nautobot.dcim.models import Device

name = "Checkpointed Job Example"


# Durable completion marker for the checkpointed Job. A record whose description
# starts with this value has been processed and is skipped on a later run.
CHECKPOINT_DONE_PREFIX = "checkpoint-done: "


class CheckpointedProcessJob(Job):
    """Checkpointed, resumable Job.

    Processes each example record once and records completion durably, so an
    interrupted run resumes instead of restarting. The completion marker is the
    record's own state: a processed record carries ``CHECKPOINT_DONE_PREFIX`` in
    its serial, committed one record at a time. The resume query selects only
    the records that are not yet marked, so a later run skips the work already
    committed. Progress is reported at batch boundaries, not per record.
    The Job catches the soft-time-limit exception and reports how
    far it reached before the hard limit ends it.

    This POC uses the ``serial`` field as the marker to stay self-contained.
    A production Job should use a dedicated status field or a separate progress
    record rather than overloading a data field.
    """

    batch_size = IntegerVar(
        description="Report a progress checkpoint after this many records.",
        default=50,
        min_value=1,
        max_value=10000,
    )
    restart = BooleanVar(
        description="Clear all completion markers first, so the run starts from the beginning.",
        default=False,
    )

    class Meta:
        """Meta attributes."""

        name = "Checkpointed process (resumable)"
        description = "Processes records, commits each completion durably, and resumes on a later run."
        soft_time_limit = 60
        time_limit = 120
        has_sensitive_variables = False

    def run(self, batch_size, restart):  # pylint: disable=arguments-differ
        """Process the records that are not yet marked complete."""
        if restart:
            # Reset the demo: clear the markers so every record is pending again.
            reset_count = 0
            for record in Device.objects.filter(serial__startswith=CHECKPOINT_DONE_PREFIX):
                record.serial = ""
                record.validated_save()
                reset_count += 1
            self.logger.info("Cleared %d completion markers before starting.", reset_count)

        # Resume point: only the records that are not yet marked complete (HLD 8.4).
        pending_pks = list(
            Device.objects.exclude(serial__startswith=CHECKPOINT_DONE_PREFIX).values_list("pk", flat=True)
        )
        total = len(pending_pks)
        if not total:
            self.logger.success("Nothing to do; all records are already complete.")
            return {"processed": 0, "remaining": 0, "interrupted": False}

        already_done = Device.objects.filter(serial__startswith=CHECKPOINT_DONE_PREFIX).count()
        self.logger.info("Resuming. %d records already complete, %d pending.", already_done, total)

        processed = 0
        try:
            for pk in pending_pks:
                record = Device.objects.get(pk=pk)
                # Stand-in for the real per-record work.
                record.serial = f"{CHECKPOINT_DONE_PREFIX}{record.name}"
                # Commit this record before moving on. This write is the checkpoint.
                record.validated_save()
                processed += 1
                if processed % batch_size == 0:
                    # Progress at a batch boundary, not per record.
                    self.logger.info("Checkpoint: %d of %d records complete.", processed, total)
        except SoftTimeLimitExceeded:
            remaining = total - processed
            # Report the position before the hard limit ends the process.
            self.logger.warning(
                "Soft time limit reached. %d of %d records complete, %d remaining. Run again to resume.",
                processed,
                total,
                remaining,
            )
            return {"processed": processed, "remaining": remaining, "interrupted": True}

        self.logger.success("All %d pending records complete.", processed)
        return {"processed": processed, "remaining": 0, "interrupted": False}


register_jobs(
    CheckpointedProcessJob,
)
