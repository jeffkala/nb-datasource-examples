"""POC Jobs for the Mintcookie Jobs app.

Each Job in this module demonstrates one or more requirements from the
"Job Performance and Optimizations" HLD. The HLD section that a Job demonstrates
is named in the Job docstring. The Jobs operate only on this app's own
``MintcookieJobsExampleModel`` so that the POC is self-contained and needs no
DCIM data.

Queue names follow the HLD naming convention (``<backend>-<profile>``). Declaring
them in ``Meta.task_queues`` makes Nautobot create the matching Celery JobQueue
records at registration and limits the runtime queue-selection list to those
queues (HLD 2.1, 5.1). Kubernetes queues (``k8s-*``) require a JobQueue whose
``queue_type`` is ``kubernetes`` plus a cluster, so they are referenced but not
declared here.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from celery.exceptions import SoftTimeLimitExceeded
from django.db import close_old_connections, transaction
from mintcookie_jobs.models import MintcookieJobsExampleModel
from nautobot.apps.jobs import BooleanVar, IntegerVar, Job, ObjectVar, StringVar, register_jobs
from nautobot.extras.models import Job as JobModel
from nautobot.extras.models import JobResult

name = "Mintcookie POC Jobs"  # Grouping shown in the Jobs list.

# Durable completion marker for the checkpointed Job. A record whose description
# starts with this value has been processed and is skipped on a later run.
CHECKPOINT_DONE_PREFIX = "checkpoint-done: "


class HelloLatencyJob(Job):
    """Latency-sensitive Job (HLD 3.2, 4.1).

    A trivial, fast Job. A requester waits for the result, so it declares a short
    soft time limit and targets the dedicated latency queue. The same Job code
    runs unchanged on any queue type (HLD 2.1 dual-backend execution).
    """

    class Meta:
        """Meta attributes."""

        name = "Hello (latency-sensitive)"
        description = "Fast demonstration Job for the latency-sensitive class."
        task_queues = ["celery-latency", "celery-standard"]
        soft_time_limit = 10
        time_limit = 20
        has_sensitive_variables = False

    def run(self):  # pylint: disable=arguments-differ
        """Log a single line and return."""
        self.logger.info("Hello from the latency-sensitive queue.")
        return "ok"


class PopulateExampleModelsJob(Job):
    """Idempotent write Job (HLD 6.1, 6.2, 6.4, 12.1).

    Creates or updates N example records. The Job is idempotent: it upserts on the
    natural key (``name``), so a second run makes no duplicate rows (HLD 12.1).
    Each write is wrapped in its own transaction so one failure does not roll back
    the others (HLD 6.2). Logging is a per-run summary with counts, not one line
    per object (HLD 6.4).
    """

    count = IntegerVar(
        description="How many example records to create or update.",
        default=25,
        min_value=1,
        max_value=1000,
    )

    class Meta:
        """Meta attributes."""

        name = "Populate example models (idempotent)"
        description = "Idempotent bulk upsert with per-item transactions and summary logging."
        task_queues = ["celery-standard"]
        soft_time_limit = 300
        time_limit = 360
        has_sensitive_variables = False

    def run(self, count):  # pylint: disable=arguments-differ
        """Upsert ``count`` records and log a summary."""
        created = 0
        updated = 0
        failed = 0
        for index in range(count):
            record_name = f"mintcookie-poc-{index:04d}"
            try:
                # One transaction per item (HLD 6.2): a single failure is isolated.
                with transaction.atomic():
                    _, was_created = MintcookieJobsExampleModel.objects.update_or_create(
                        name=record_name,
                        defaults={"description": f"POC record {index}"},
                    )
                created += int(was_created)
                updated += int(not was_created)
            except Exception:  # pylint: disable=broad-except
                failed += 1

        # Summary logging (HLD 6.4): counts by outcome, not one entry per object.
        self.logger.info("Upsert complete. created=%d updated=%d failed=%d", created, updated, failed)
        if failed:
            self.logger.warning("%d records failed to write.", failed)
        return {"created": created, "updated": updated, "failed": failed}


class LongRunningReportJob(Job):
    """Long-running Job with checkpointing (HLD 8.1, 8.4).

    Runs several phases. It reports progress at each phase boundary, not per item
    (HLD 8.4). It catches the soft-time-limit exception so it can record where it
    stopped before the hard limit ends the process (HLD 8.1). Nautobot's Cancel
    action is a hard kill, so the soft time limit is the only cooperative
    interruption point.
    """

    phases = IntegerVar(description="Number of phases to run.", default=5, min_value=1, max_value=50)

    class Meta:
        """Meta attributes."""

        name = "Long-running report (checkpointed)"
        description = "Phase-based long Job that checkpoints progress and handles the soft time limit."
        task_queues = ["celery-standard", "k8s-longrun"]
        soft_time_limit = 60
        time_limit = 120
        has_sensitive_variables = False

    def run(self, phases):  # pylint: disable=arguments-differ
        """Run the phases, checkpointing after each one."""
        completed = 0
        try:
            for phase in range(1, phases + 1):
                time.sleep(1)  # Stand-in for real work.
                completed = phase
                # Checkpoint at the phase boundary (HLD 8.4).
                self.logger.info("Completed phase %d of %d.", phase, phases)
        except SoftTimeLimitExceeded:
            # Record the checkpoint before the hard limit stops the process (HLD 8.1).
            self.logger.warning("Soft time limit reached. Completed %d of %d phases.", completed, phases)
            return {"completed_phases": completed, "interrupted": True}

        self.logger.success("All %d phases complete.", phases)
        return {"completed_phases": completed, "interrupted": False}


class SingletonMaintenanceJob(Job):
    """Singleton Job (HLD 12.3).

    Only one instance may run at a time. Nautobot enforces this with a Redis lock
    keyed on the Job, set to time out on the hard time limit. A second concurrent
    run fails with a singleton error instead of duplicating the work.
    """

    class Meta:
        """Meta attributes."""

        name = "Singleton maintenance"
        description = "Demonstrates whole-Job mutual exclusion with is_singleton."
        task_queues = ["celery-standard"]
        is_singleton = True
        soft_time_limit = 60
        time_limit = 120
        has_sensitive_variables = False

    def run(self):  # pylint: disable=arguments-differ
        """Simulate exclusive maintenance work."""
        self.logger.info("Singleton maintenance started; no other instance can run now.")
        time.sleep(5)
        self.logger.success("Singleton maintenance finished.")


class InJobParallelFanOutJob(Job):
    """Fan-out by in-Job parallelism (HLD 7.1 default pattern).

    This is the HLD-recommended fan-out method: one Job processes the whole target
    set with an internal bounded thread pool, holds the outcome in one JobResult,
    and reports one consolidated result with counts by outcome (HLD 7.4, 7.5). The
    ``max_workers`` value is the backpressure control (HLD 7.6). Each worker thread
    closes its database connection so the pool does not leak connections.
    """

    max_workers = IntegerVar(
        description="Concurrent workers. This is the backpressure limit (HLD 7.6).",
        default=4,
        min_value=1,
        max_value=16,
    )
    failure_threshold_percent = IntegerVar(
        description="Stop reporting success if the failure rate exceeds this percentage (HLD 7.5).",
        default=25,
        min_value=1,
        max_value=100,
    )

    class Meta:
        """Meta attributes."""

        name = "Fan-out: in-Job parallelism (recommended)"
        description = "Processes the target set with a bounded thread pool inside one Job."
        task_queues = ["celery-fanout", "k8s-highmem"]
        soft_time_limit = 600
        time_limit = 660
        has_sensitive_variables = False

    @staticmethod
    def _process_one(pk):
        """Process one item. Returns True on success. Runs in a worker thread."""
        try:
            record = MintcookieJobsExampleModel.objects.get(pk=pk)
            # Stand-in for real per-item work (e.g. a device call).
            record.description = f"{record.name} processed"
            record.validated_save()
            return True
        except Exception:  # pylint: disable=broad-except
            return False
        finally:
            # Threads get their own DB connections; close them so the pool does not leak.
            close_old_connections()

    def run(self, max_workers, failure_threshold_percent):  # pylint: disable=arguments-differ
        """Resolve the target set once, then process it concurrently."""
        # Resolve the target set once, pass only primary keys to the workers (HLD 6.3).
        pks = list(MintcookieJobsExampleModel.objects.values_list("pk", flat=True))
        if not pks:
            self.logger.warning("No example records exist. Run 'Populate example models' first.")
            return {"total": 0, "succeeded": 0, "failed": 0}

        succeeded = 0
        failed = 0
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(self._process_one, pk): pk for pk in pks}
            for future in as_completed(futures):
                if future.result():
                    succeeded += 1
                else:
                    failed += 1

        total = len(pks)
        failure_rate = (failed / total) * 100
        # Consolidated outcome with counts (HLD 7.4).
        self.logger.info("Fan-out complete. total=%d succeeded=%d failed=%d", total, succeeded, failed)
        if failure_rate > failure_threshold_percent:
            # Threshold partial-failure mode (HLD 7.5).
            self.logger.error(
                "Failure rate %.1f%% exceeds the %d%% threshold. Treat as a systemic failure.",
                failure_rate,
                failure_threshold_percent,
            )
        return {"total": total, "succeeded": succeeded, "failed": failed}


class FanOutChildJob(Job):
    """Child Job for the parent-to-child fan-out (HLD 7.1 secondary pattern).

    Processes one unit and reports. It has its own JobResult, so it is
    independently visible, cancellable, and repeatable. A child Job must never
    start a further fan-out (HLD 7.1, two levels only).
    """

    item_pk = StringVar(description="Primary key of the record to process.")
    parent_job_result_id = StringVar(
        description="JobResult ID of the parent, for manual linkage (HLD 7.4).",
        default="",
        required=False,
    )

    class Meta:
        """Meta attributes."""

        name = "Fan-out child"
        description = "Processes one unit as its own JobResult. Dispatched by the fan-out parent."
        task_queues = ["celery-fanout"]
        soft_time_limit = 120
        time_limit = 180
        has_sensitive_variables = False
        # Not shown in the main Jobs list; it is invoked by the parent.
        hidden = True

    def run(self, item_pk, parent_job_result_id=""):  # pylint: disable=arguments-differ
        """Process the single record identified by ``item_pk``."""
        if parent_job_result_id:
            self.logger.info("Child of parent JobResult %s.", parent_job_result_id)
        # Re-read the object at the start of run() (HLD 6.3); handle a deleted record.
        try:
            record = MintcookieJobsExampleModel.objects.get(pk=item_pk)
        except MintcookieJobsExampleModel.DoesNotExist:
            self.logger.warning("Record %s no longer exists; nothing to do.", item_pk)
            return "skipped"
        record.description = f"{record.name} processed by child"
        record.validated_save()
        self.logger.success("Processed %s.", record.name, extra={"object": record})
        return "ok"


class FanOutParentJob(Job):
    """Parent-to-child fan-out (HLD 7.1 secondary pattern, 7.4, 7.6).

    Dispatches one child Job per unit. This pattern is NOT a built-in Nautobot
    feature (see the HLD 7.1 viability note): the parent-child linkage is manual
    (the parent writes child JobResult primary keys to its log, HLD 7.4), and
    there is no built-in aggregation. This parent is fire-and-forget: it does not
    wait for the children, so it does not hold a worker slot. ``max_children`` is
    the in-flight limit that the parent owns (HLD 7.6). Prefer
    ``InJobParallelFanOutJob`` unless each unit truly needs its own JobResult.
    """

    max_children = IntegerVar(
        description="In-flight limit. The parent owns this admission control (HLD 7.6).",
        default=10,
        min_value=1,
        max_value=100,
    )

    class Meta:
        """Meta attributes."""

        name = "Fan-out: parent-to-child (use only when needed)"
        description = "Dispatches one child Job per unit. Linkage and aggregation are custom (HLD 7.1)."
        task_queues = ["celery-fanout"]
        soft_time_limit = 300
        time_limit = 360
        has_sensitive_variables = False

    def run(self, max_children):  # pylint: disable=arguments-differ
        """Dispatch up to ``max_children`` child Jobs, one per record."""
        child_job_model = JobModel.objects.get(
            module_name="mintcookie_jobs.jobs",
            job_class_name="FanOutChildJob",
        )
        if not child_job_model.enabled:
            self.logger.error("Child Job is not enabled. Enable 'Fan-out child' before running this parent.")
            return {"dispatched": 0}

        pks = list(MintcookieJobsExampleModel.objects.values_list("pk", flat=True)[:max_children])
        if not pks:
            self.logger.warning("No example records exist. Run 'Populate example models' first.")
            return {"dispatched": 0}

        dispatched = []
        for pk in pks:
            child_result = JobResult.enqueue_job(
                child_job_model,
                self.user,
                str(pk),
                job_kwargs={"parent_job_result_id": str(self.job_result.pk)},
            )
            # Manual parent-to-child linkage (HLD 7.4): record the child JobResult IDs.
            dispatched.append(str(child_result.pk))

        self.logger.info("Dispatched %d child Jobs (in-flight limit %d).", len(dispatched), max_children)
        self.logger.info("Child JobResult IDs: %s", ", ".join(dispatched))
        return {"dispatched": len(dispatched), "child_job_result_ids": dispatched}


class SensitiveCredentialJob(Job):
    """Sensitive variable handling (HLD 15.4, 6.3).

    Accepts a credential as input. Because ``has_sensitive_variables`` is True (the
    default), Nautobot does not store the input values with the JobResult. The Job
    never logs the credential value.
    """

    target = ObjectVar(
        description="Record to act on. Passed by primary key, re-read here (HLD 6.3).",
        model=MintcookieJobsExampleModel,
    )
    secret = StringVar(description="A credential. Its value is never logged or stored.")

    class Meta:
        """Meta attributes."""

        name = "Sensitive credential (no logging)"
        description = "Demonstrates sensitive variable handling; the input is not stored or logged."
        task_queues = ["celery-standard"]
        # Left at the default True so input values are not saved to the database.
        has_sensitive_variables = True

    def run(self, target, secret):  # pylint: disable=arguments-differ
        """Use the credential without logging it."""
        # Never log `secret` or place it in an exception message (HLD 15.4).
        self.logger.info("Received a credential of length %d for %s.", len(secret), target.name)
        self.logger.success("Acted on %s without exposing the credential.", target.name, extra={"object": target})
        return "ok"


class StreamProcessExampleModelsJob(Job):
    """Streaming read with ``.iterator()`` instead of a for loop over a full queryset (HLD 6.1, 6.5).

    A plain ``for record in queryset:`` loads every row into memory at once and
    caches them on the queryset. This Job instead streams rows with
    ``.iterator(chunk_size=N)``, which uses a server-side cursor and never holds
    the whole result set in memory. It reads only the fields it touches with
    ``.only()`` (HLD 6.1), accumulates a bounded batch, and writes each batch with
    ``bulk_update`` inside its own transaction (HLD 6.1, 6.2). It logs a per-run
    summary, not one line per object (HLD 6.4).

    ``bulk_update`` does not run ``clean()`` or signals (HLD 6.6). That is
    acceptable here because the write only sets a computed ``description`` and the
    goal is throughput on a large set.
    """

    chunk_size = IntegerVar(
        description="Server-side cursor and write batch size for .iterator() and bulk_update (HLD 6.1).",
        default=100,
        min_value=1,
        max_value=10000,
    )

    class Meta:
        """Meta attributes."""

        name = "Stream-process example models (iterator)"
        description = "Reads a large queryset with .iterator() and writes in batches with bulk_update."
        task_queues = ["celery-standard", "k8s-highmem"]
        soft_time_limit = 600
        time_limit = 660
        has_sensitive_variables = False

    @staticmethod
    def _flush(batch):
        """Write one batch with a single UPDATE and return the row count."""
        if not batch:
            return 0
        # One transaction per batch (HLD 6.2): a failure isolates to this batch.
        with transaction.atomic():
            MintcookieJobsExampleModel.objects.bulk_update(batch, ["description"], batch_size=len(batch))
        return len(batch)

    def run(self, chunk_size):  # pylint: disable=arguments-differ
        """Stream the queryset with .iterator() and update it in batches."""
        # .only() loads just the columns this Job touches (HLD 6.1).
        # .iterator(chunk_size=...) streams rows with a server-side cursor instead
        # of loading and caching the entire queryset in memory (HLD 6.5).
        queryset = MintcookieJobsExampleModel.objects.only("pk", "name", "description")

        updated = 0
        batch = []
        for record in queryset.iterator(chunk_size=chunk_size):
            record.description = f"{record.name} stream-processed"
            batch.append(record)
            if len(batch) >= chunk_size:
                updated += self._flush(batch)
                self.logger.info("flush")
                batch = []  # Drop the references so memory does not grow (HLD 6.5).

        # Flush the final partial batch.
        updated += self._flush(batch)

        # Summary logging (HLD 6.4): one line, not one per object.
        self.logger.info("Stream processing complete. updated=%d chunk_size=%d", updated, chunk_size)
        return {"updated": updated, "chunk_size": chunk_size}


class CheckpointedProcessJob(Job):
    """Checkpointed, resumable Job (HLD 8.4, 8.1, 12.1).

    Processes each example record once and records completion durably, so an
    interrupted run resumes instead of restarting. The completion marker is the
    record's own state: a processed record carries ``CHECKPOINT_DONE_PREFIX`` in
    its description, committed one record at a time. The resume query selects only
    the records that are not yet marked, so a later run skips the work already
    committed (HLD 8.4). Progress is reported at batch boundaries, not per record
    (HLD 8.4, 6.4). The Job catches the soft-time-limit exception and reports how
    far it reached before the hard limit ends it (HLD 8.1).

    This POC uses the ``description`` field as the marker to stay self-contained.
    A production Job should use a dedicated status field or a separate progress
    record rather than overloading a data field.
    """

    batch_size = IntegerVar(
        description="Report a progress checkpoint after this many records (HLD 8.4).",
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
        task_queues = ["celery-standard", "k8s-longrun"]
        soft_time_limit = 60
        time_limit = 120
        has_sensitive_variables = False

    def run(self, batch_size, restart):  # pylint: disable=arguments-differ
        """Process the records that are not yet marked complete."""
        if restart:
            # Reset the demo: clear the markers so every record is pending again.
            reset_count = 0
            for record in MintcookieJobsExampleModel.objects.filter(description__startswith=CHECKPOINT_DONE_PREFIX):
                record.description = ""
                record.validated_save()
                reset_count += 1
            self.logger.info("Cleared %d completion markers before starting.", reset_count)

        # Resume point: only the records that are not yet marked complete (HLD 8.4).
        pending_pks = list(
            MintcookieJobsExampleModel.objects.exclude(description__startswith=CHECKPOINT_DONE_PREFIX).values_list(
                "pk", flat=True
            )
        )
        total = len(pending_pks)
        if not total:
            self.logger.success("Nothing to do; all records are already complete.")
            return {"processed": 0, "remaining": 0, "interrupted": False}

        already_done = MintcookieJobsExampleModel.objects.filter(description__startswith=CHECKPOINT_DONE_PREFIX).count()
        self.logger.info("Resuming. %d records already complete, %d pending.", already_done, total)

        processed = 0
        try:
            for pk in pending_pks:
                record = MintcookieJobsExampleModel.objects.get(pk=pk)
                # Stand-in for the real per-record work.
                record.description = f"{CHECKPOINT_DONE_PREFIX}{record.name}"
                # Commit this record before moving on. This write is the checkpoint (HLD 8.4).
                record.validated_save()
                processed += 1
                if processed % batch_size == 0:
                    # Progress at a batch boundary, not per record (HLD 8.4, 6.4).
                    self.logger.info("Checkpoint: %d of %d records complete.", processed, total)
        except SoftTimeLimitExceeded:
            remaining = total - processed
            # Report the position before the hard limit ends the process (HLD 8.1).
            self.logger.warning(
                "Soft time limit reached. %d of %d records complete, %d remaining. Run again to resume.",
                processed,
                total,
                remaining,
            )
            return {"processed": processed, "remaining": remaining, "interrupted": True}

        self.logger.success("All %d pending records complete.", processed)
        return {"processed": processed, "remaining": 0, "interrupted": False}


from celery import chord, shared_task
from django.core.cache import cache
from nautobot.apps.jobs import Job, MultiChoiceVar, StringVar

name = "Examples"


@shared_task
def process_item(item_name):
    """Example parallel task."""
    time.sleep(2)
    return {
        "item": item_name,
        "status": "success",
        "details": f"Processed {item_name}",
    }


@shared_task
def aggregate_results(results, job_result_id, username, batch_name):
    """Chord callback."""
    summary = {
        "job_result_id": job_result_id,
        "requested_by": username,
        "batch_name": batch_name,
        "total": len(results),
        "successful": sum(1 for r in results if r.get("status") == "success"),
        "failed": sum(1 for r in results if r.get("status") != "success"),
        "results": results,
    }

    cache.set(f"nautobot-job-chord-summary:{job_result_id}", summary, timeout=3600)
    return summary


class LaunchChordJob(Job):
    batch_name = StringVar(
        description="Friendly name for this batch run.",
        default="example-batch",
    )

    items = MultiChoiceVar(
        choices=(
            ("device-a", "device-a"),
            ("device-b", "device-b"),
            ("device-c", "device-c"),
            ("device-d", "device-d"),
        ),
        description="Select one or more items to process in parallel.",
    )

    class Meta:
        name = "Launch Celery Chord"
        description = "Example Nautobot Job using a Celery chord safely"

    def run(self, *, batch_name, items):
        if not items:
            raise ValueError("You must select at least one item.")

        self.logger.info("Launching chord for %s items", len(items))

        header = [process_item.s(item_name) for item_name in items]
        callback = aggregate_results.s(
            str(self.job_result.id),
            self.user.username,
            batch_name,
        )

        async_result = chord(header)(callback)

        self.logger.info(
            "Submitted chord for JobResult %s with callback task id %s",
            self.job_result.id,
            async_result.id,
        )

        cache.set(
            f"nautobot-job-chord-task:{self.job_result.id}",
            {
                "job_result_id": str(self.job_result.id),
                "batch_name": batch_name,
                "callback_task_id": async_result.id,
                "items": list(items),
                "status": "submitted",
            },
            timeout=3600,
        )

        return {
            "message": "Chord submitted successfully.",
            "job_result_id": str(self.job_result.id),
            "callback_task_id": async_result.id,
            "summary_cache_key": f"nautobot-job-chord-summary:{self.job_result.id}",
        }


register_jobs(
    HelloLatencyJob,
    PopulateExampleModelsJob,
    LongRunningReportJob,
    SingletonMaintenanceJob,
    InJobParallelFanOutJob,
    FanOutChildJob,
    FanOutParentJob,
    SensitiveCredentialJob,
    StreamProcessExampleModelsJob,
    CheckpointedProcessJob,
    LaunchChordJob,
)
